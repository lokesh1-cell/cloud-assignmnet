"""Restore exact generated shard files without changing their teacher reply strings."""

from pathlib import Path
import os
import sys

sys.path.insert(0, "worker")
import storage

for path in sorted(Path("datasets/teacher").glob("shard-*.jsonl")):
    if "GROUP" in os.environ:
        shard = int(path.stem.split("-")[-1])
        base = 2 * int(os.environ["GROUP"])
        if shard not in (base, base + 1):
            path.unlink()
            continue
    key = f"teacher/{path.name}"
    storage.write_text("datasets", key, path.read_text())
    print(f"restored datasets/{key}")
