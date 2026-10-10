"""Write the deterministic regional extract from the downloaded archives.

Rows are copied as text (no type inference) so the extract is byte-faithful
to the source CSV. The extract, the two metadata files and ``manifest.json``
go to ``data/raw/`` and are committed; nothing downstream ever modifies them.

Region: Nevada. NURE rows with ``state == "NV"`` and ``smpmedia == "SEDIMENT"``
(all sample sources; stream/soil filtering happens downstream with an
exclusion log). MRDS rows with ``state == "Nevada"`` and
``country == "United States"`` (all commodities and development statuses, so
prospects of the target commodity can be handled explicitly downstream).

Usage::

    python -m prospectivity.extract            # write data/raw/* from data/archive/*
    python -m prospectivity.extract --check    # recompute and compare to data/raw/
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile

from prospectivity.acquire import (
    MANIFEST_PATH,
    PROJECT_ROOT,
    RAW_DIR,
    SOURCES,
    archive_record,
    sha256_of,
)

REGION = {
    "name": "Nevada",
    "nure_filter": {"state": "NV", "smpmedia": "SEDIMENT"},
    "mrds_filter": {"state": "Nevada", "country": "United States"},
}
EXTRACTS = {
    "nure": "nure_nv_sediment.csv",
    "mrds": "mrds_nv.csv",
}


def _filter_csv(data: bytes, keep: dict[str, str]) -> tuple[bytes, int, int]:
    """Filter CSV rows on exact column equality, preserving text verbatim.

    Returns (csv_bytes, rows_in, rows_out). Output uses ``csv.QUOTE_MINIMAL``
    with ``\\n`` line endings, so repeated runs are byte-identical.
    """
    text = data.decode("utf-8", errors="strict")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    idx = {c: header.index(c) for c in keep}
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    n_in = n_out = 0
    for row in reader:
        n_in += 1
        if all(row[i] == v for i, v in ((idx[c], v) for c, v in keep.items())):
            writer.writerow(row)
            n_out += 1
    return out.getvalue().encode("utf-8"), n_in, n_out


def build(write: bool = True) -> dict:
    """Build the extract (and manifest); return the manifest dict."""
    manifest: dict = {
        "region": REGION,
        "note": (
            "Archives are not committed (see data/archive/ in .gitignore). The extract "
            "is written once and never modified; verify with "
            "`python -m prospectivity.extract --check`."
        ),
        "sources": {},
        "extracts": {},
    }
    for key, src in SOURCES.items():
        rec = archive_record(src)
        keep = REGION["nure_filter"] if key == "nure" else REGION["mrds_filter"]
        with zipfile.ZipFile(src.archive) as z:
            members = {i.filename: i.file_size for i in z.infolist()}
            csv_bytes = z.read(src.csv_member)
            meta_bytes = z.read(src.meta_member)
        extract_bytes, n_in, n_out = _filter_csv(csv_bytes, keep)
        rec["archive_members"] = members
        rec["csv_sha256"] = hashlib.sha256(csv_bytes).hexdigest()
        rec["csv_rows"] = n_in
        rec["meta_sha256"] = hashlib.sha256(meta_bytes).hexdigest()
        manifest["sources"][key] = rec
        out_name = EXTRACTS[key]
        manifest["extracts"][key] = {
            "file": f"data/raw/{out_name}",
            "filter": keep,
            "rows": n_out,
            "sha256": hashlib.sha256(extract_bytes).hexdigest(),
            "metadata_file": f"data/raw/{src.meta_member}",
        }
        if write:
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            (RAW_DIR / out_name).write_bytes(extract_bytes)
            (RAW_DIR / src.meta_member).write_bytes(meta_bytes)
    if write:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def check() -> list[str]:
    """Recompute the extract from the archives and compare with data/raw/."""
    fresh = build(write=False)
    committed = json.loads(MANIFEST_PATH.read_text())
    problems: list[str] = []
    for key in SOURCES:
        a, b = fresh["extracts"][key], committed["extracts"][key]
        if a["sha256"] != b["sha256"] or a["rows"] != b["rows"]:
            problems.append(
                f"{key}: recomputed extract differs ({a['rows']} rows, {a['sha256'][:12]})"
            )
        on_disk = sha256_of(PROJECT_ROOT / b["file"])
        if on_disk != b["sha256"]:
            problems.append(
                f"{key}: {b['file']} on disk {on_disk[:12]} != manifest {b['sha256'][:12]}"
            )
        if fresh["sources"][key]["archive_sha256"] != committed["sources"][key]["archive_sha256"]:
            problems.append(f"{key}: archive sha256 differs from manifest")
    return problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    if args.check:
        probs = check()
        for x in probs:
            print("FAIL", x)
        print("extract reproduces" if not probs else f"{len(probs)} problem(s)")
        return 1 if probs else 0
    if MANIFEST_PATH.is_file():
        print(f"{MANIFEST_PATH} exists; the extract is write-once. Use --check.", file=sys.stderr)
        return 1
    m = build(write=True)
    for key, e in m["extracts"].items():
        print(f"{key}: {e['rows']} rows -> {e['file']} sha256 {e['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
