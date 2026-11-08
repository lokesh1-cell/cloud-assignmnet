"""Download available dataset objects, including partial teacher checkpoints."""

from pathlib import Path
import sys

sys.path.insert(0, "worker")
import storage

for prefix in ("teacher/", "v1/"):
    for key in storage.list_keys("datasets", prefix):
        target = Path("datasets") / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(storage.read_text("datasets", key))
        print(f"exported datasets/{key}")
