"""Verify actual S3 model bytes against release manifests and training lineage."""

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, "worker")
import storage

client = storage._s3_client()
train_sha = Path("datasets/v1/train.sha256").read_text().split()[0]
models = {}
for version in ("v1", "v2"):
    directory = Path("models") / version
    manifest = (directory / "files.sha256").read_text().splitlines()
    verified = []
    for line in manifest:
        expected, name = line.split("  ", 1)
        key = f"{version}/{name}"
        response = client.get_object(Bucket="models", Key=key)
        digest = hashlib.sha256()
        body = response["Body"]
        try:
            for chunk in body.iter_chunks(chunk_size=1024 * 1024):
                digest.update(chunk)
        finally:
            body.close()
        actual = digest.hexdigest()
        assert actual == expected, f"S3 checksum mismatch: {key}"
        verified.append({"key": key, "bytes": response["ContentLength"], "sha256": actual})
    info = json.loads((directory / "version_info.json").read_text())
    assert info["version"] == version
    assert info["base_model"] == "EleutherAI/pythia-70m"
    assert info["teacher_model"] == "phi3.5"
    assert info["training_data_sha256"] == train_sha
    assert 0 < info["training_examples"] <= 1500
    remote_checksum = storage.read_text("models", f"{version}/model.sha256")
    assert remote_checksum == (directory / "model.sha256").read_text()
    with (Path("models") / f"{version}.tar.gz").open("rb") as archive:
        archive_digest = hashlib.file_digest(archive, "sha256").hexdigest()
    assert archive_digest == remote_checksum.split()[0]
    models[version] = {
        "files": verified,
        "archive_sha256": archive_digest,
        "training_examples": info["training_examples"],
        "training_data_sha256": train_sha,
    }
result = {"models": models, "train_sha256": train_sha, "all_checksums_verified": True}
Path("results/fresh/storage_verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(
    "Both model versions, tokenizers, file hashes, release checksums, and training lineage verified in S3."
)
