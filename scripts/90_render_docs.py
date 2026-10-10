"""Step 90: run the test suite, record its counts, and render the documents.

`cairn render` only covers report.tmpl.md; README, walkthrough and resume bullet
also quote ledger numbers, so they are rendered the same way and fail on any
unresolved key. The test count is recorded here so it is a ledger value too.
"""

import re
import subprocess
import sys
from pathlib import Path

from cairn import load_ledger, record
from cairn.numbers import render

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    (ROOT / "README.tmpl.md", ROOT / "README.md"),
    (ROOT / "docs" / "walkthrough.tmpl.md", ROOT / "docs" / "walkthrough.md"),
    (ROOT / "docs" / "resume_bullet.tmpl.md", ROOT / "docs" / "resume_bullet.md"),
]

proc = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(ROOT / "tests")],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
summary = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", summary)) else 0
failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", summary)) else 0
record("tests.n_passed", passed)
record("tests.n_failed", failed)
print(f"pytest: {summary}")
if proc.returncode != 0:
    print(proc.stdout[-3000:])
    raise SystemExit("test suite failed")

ledger = load_ledger()
for src, dst in DOCS:
    text, missing = render(src.read_text(), ledger)
    if missing:
        raise SystemExit(f"{src.name}: unresolved placeholders {sorted(set(missing))}")
    dst.write_text(text)
    print(f"rendered {dst.relative_to(ROOT)}")
