"""Create the tables and load the sample invoices through the real pipeline
(validation -> extraction -> duplicate check -> database).

    python scripts/seed.py            # reset and load samples/invoices/*.pdf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402
from app.pipeline import process_upload  # noqa: E402

SAMPLES = Path(__file__).resolve().parent.parent / "samples" / "invoices"


def main():
    db.init_schema()
    db.reset_all()
    files = sorted(SAMPLES.glob("*.pdf"))
    flagged = 0
    for f in files:
        r = process_upload(f.name, f.read_bytes(), user="seed")
        mark = ""
        if r.duplicates:
            flagged += 1
            mark = f"  <-- {r.duplicates[0][1].label} ({r.duplicates[0][1].score:.2f})"
        print(("OK  " if r.ok else "ERR ") + f"{f.name}: {r.message}{mark}")
    print(f"\nLoaded {len(files)} invoices into {db.DIALECT}; {flagged} flagged as duplicates.")


if __name__ == "__main__":
    main()
