"""Export actual bucket objects and verify all command IDs and modulo shard assignments."""

import collections
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, "worker")
import storage

pool = [json.loads(line) for line in Path("data/commands_pool.jsonl").read_text().splitlines()]
expected = {row["id"]: i % 2 for i, row in enumerate(pool)}
actual = collections.Counter()
for shard in range(2):
    key = f"teacher/shard-{shard}.jsonl"
    text = storage.read_text("datasets", key)
    path = Path("datasets") / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    for row in rows:
        assert expected[row["id"]] == shard, row["id"]
        actual[row["id"]] += 1
assert actual == collections.Counter(row["id"] for row in pool), "Missing or repeated command ID"
for key in ("v1/train.jsonl", "v1/train.sha256"):
    path = Path("datasets") / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(storage.read_text("datasets", key))
train = Path("datasets/v1/train.jsonl")
digest = hashlib.sha256(train.read_bytes()).hexdigest()
assert digest == Path("datasets/v1/train.sha256").read_text().split()[0]
report = {
    "input_ids": len(pool),
    "unique_label_ids": len(actual),
    "shards": 2,
    "exactly_once": True,
    "modulo_verified": True,
    "train_sha256": digest,
}
Path("results/fresh/shard_verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
