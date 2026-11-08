"""Produce the teacher's predictions on validation.jsonl for the three-way comparison (Task 2, step 6).

Uses the SAME prompt and settings as Task 1 (phi3.5, temperature 0, seed 42) so the teacher column
is comparable. Writes raw predictions for score.py.

  python scripts/eval_teacher.py --input data/validation.jsonl --out results/pred_teacher.jsonl
Then:
  python tools/score.py results/pred_teacher.jsonl data/validation.jsonl --out results/teacher_validation.json
"""

import argparse
import json
import os
import sys
import time
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "worker"))
import label_worker  # noqa: E402  (reuses call_teacher + load_prompt)


def get_prediction(prompt_template, text):
    """Retry transport failures while preserving the successful generated string exactly."""
    for attempt in range(3):
        try:
            return label_worker.call_teacher(prompt_template, text)
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/validation.jsonl")
    ap.add_argument("--out", default="results/pred_teacher.jsonl")
    ap.add_argument(
        "--resume",
        action="store_true",
        help="continue a partial run with identical teacher settings",
    )
    a = ap.parse_args()

    prompt_template = label_worker.load_prompt()
    rows = [json.loads(line) for line in open(a.input, encoding="utf-8") if line.strip()]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    done = set()
    if a.resume and os.path.exists(a.out):
        with open(a.out, encoding="utf-8") as existing:
            done = {json.loads(line)["id"] for line in existing if line.strip()}
        if not done <= {row["id"] for row in rows}:
            raise ValueError("Partial predictions contain IDs outside this evaluation set")
    with open(a.out, "a" if a.resume else "w", encoding="utf-8") as out:
        for i, r in enumerate(rows, 1):
            if r["id"] in done:
                continue
            raw = get_prediction(prompt_template, r["text"])
            out.write(json.dumps({"id": r["id"], "prediction": raw}, ensure_ascii=False) + "\n")
            out.flush()
            if i % 20 == 0:
                print(f"{i}/{len(rows)}")
    print(f"wrote {a.out} ({len(rows)} predictions)")


if __name__ == "__main__":
    main()
