"""Build the roll-number submission ZIP without credentials or model weights.

Run only after placing the student's real handwritten scan at 230101039.pdf.
"""

import argparse
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROLL = "230101039"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reflection", type=Path, default=ROOT / f"{ROLL}.pdf")
    args = parser.parse_args()
    reflection = args.reflection.resolve()
    if not reflection.is_file():
        raise SystemExit(f"Missing handwritten scan: {reflection}")
    report = ROOT / "report" / "report.pdf"
    if not report.is_file():
        raise SystemExit("Compile report/report.pdf first")
    for path, limit in ((reflection, 3), (report, 8)):
        info = subprocess.check_output(["pdfinfo", str(path)], text=True)
        pages = int(
            next(line.split(":", 1)[1] for line in info.splitlines() if line.startswith("Pages:"))
        )
        if pages > limit:
            raise SystemExit(f"{path.name}: {pages} pages exceeds {limit}")
    tracked = (
        subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"]).decode().split("\0")
    )
    archive = ROOT.parent / f"{ROLL}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for name in sorted(filter(None, tracked)):
            path = ROOT / name
            if path.is_file() and name != f"{ROLL}.pdf":
                output.write(path, name)
        output.write(reflection, f"{ROLL}.pdf")
        for path in sorted((ROOT / "datasets").rglob("*")):
            if path.is_file():
                output.write(path, str(path.relative_to(ROOT)))
    with zipfile.ZipFile(archive) as output:
        assert output.testzip() is None
        assert f"{ROLL}.pdf" in output.namelist()
        assert "report/report.pdf" in output.namelist()
        assert ".env" not in output.namelist()
        assert not any(name.startswith("models/") for name in output.namelist())
    print(archive)


if __name__ == "__main__":
    main()
