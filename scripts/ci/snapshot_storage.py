"""Download available dataset objects, including partial teacher checkpoints."""

from pathlib import Path
import os
import sys

sys.path.insert(0, "worker")
import storage

for prefix in ("teacher/", "v1/"):
    for key in storage.list_keys("datasets", prefix):
        if prefix == "teacher/" and "SHARD_BASE" in os.environ:
            shard = int(Path(key).stem.split("-")[-1])
            base = int(os.environ["SHARD_BASE"])
            if shard not in (base, base + 1):
                continue
        target = Path("datasets") / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(storage.read_text("datasets", key))
        print(f"exported datasets/{key}")
