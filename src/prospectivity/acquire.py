"""Acquire the two USGS archives and record their provenance.

The archives (about 65 MB together) live in ``data/archive/`` and are not
committed. What is committed is ``data/raw/manifest.json`` (URLs, HTTP
response headers, SHA-256 of each archive) and the deterministic regional
extract written by :mod:`prospectivity.extract`.

Usage::

    python -m prospectivity.acquire            # download both archives (network)
    python -m prospectivity.acquire --verify   # check archives against the manifest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_DIR = PROJECT_ROOT / "data" / "archive"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "manifest.json"


@dataclass(frozen=True)
class Source:
    key: str
    url: str
    archive: Path
    csv_member: str
    meta_member: str
    description: str


SOURCES: dict[str, Source] = {
    "nure": Source(
        key="nure",
        url="https://mrdata.usgs.gov/nure/sediment/nuresed-csv.zip",
        archive=ARCHIVE_DIR / "nure" / "nuresed-csv.zip",
        csv_member="nuresed.csv",
        meta_member="nurehssr.met",
        description=(
            "USGS NURE Hydrogeochemical and Stream Sediment Reconnaissance, "
            "sediment database, whole-country CSV (public domain)"
        ),
    ),
    "mrds": Source(
        key="mrds",
        url="https://mrdata.usgs.gov/mrds/mrds-csv.zip",
        archive=ARCHIVE_DIR / "mrds" / "mrds-csv.zip",
        csv_member="mrds.csv",
        meta_member="mrds.met",
        description="USGS Mineral Resources Data System (MRDS), flattened CSV (public domain)",
    ),
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def headers_path(src: Source) -> Path:
    return src.archive.with_name(src.archive.name + ".headers")


def parse_headers_file(path: Path) -> dict[str, str]:
    """Parse a ``curl -D`` style header dump into a dict (last response wins)."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("HTTP/"):
            out = {"status": line.strip()}
        elif ":" in line:
            k, v = line.split(":", 1)
            k = k.strip().lower()
            if k == "set-cookie":  # session cookie, not provenance
                continue
            out[k] = v.strip()
    return out


def download(src: Source, *, timeout: int = 600) -> Path:
    """Stream the archive to disk and save the response headers next to it."""
    src.archive.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(src.url, headers={"User-Agent": "mineral-prospectivity/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, src.archive.open("wb") as out:
        lines = [f"HTTP/1.1 {resp.status} {resp.reason}"]
        lines += [f"{k}: {v}" for k, v in resp.getheaders() if k.lower() != "set-cookie"]
        headers_path(src).write_text("\n".join(lines) + "\n")
        for chunk in iter(lambda: resp.read(1 << 20), b""):
            out.write(chunk)
    return src.archive


def archive_record(src: Source) -> dict:
    """Provenance record for one archive: URL, headers, size, SHA-256."""
    if not src.archive.is_file():
        raise FileNotFoundError(f"{src.archive} missing; run `python -m prospectivity.acquire`")
    hdrs = parse_headers_file(headers_path(src))
    return {
        "key": src.key,
        "description": src.description,
        "url": src.url,
        "archive": src.archive.relative_to(PROJECT_ROOT).as_posix(),
        "downloaded_at_utc": hdrs.get("date", ""),
        "http_headers": hdrs,
        "archive_bytes": src.archive.stat().st_size,
        "archive_sha256": sha256_of(src.archive),
        "csv_member": src.csv_member,
        "meta_member": src.meta_member,
    }


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def verify(manifest: dict | None = None) -> list[str]:
    """Return problems (empty list = archives match the committed manifest)."""
    manifest = manifest or load_manifest()
    problems: list[str] = []
    for key, src in SOURCES.items():
        rec = manifest["sources"][key]
        if not src.archive.is_file():
            problems.append(f"{key}: archive missing at {src.archive}")
            continue
        digest = sha256_of(src.archive)
        if digest != rec["archive_sha256"]:
            problems.append(f"{key}: sha256 {digest} != manifest {rec['archive_sha256']}")
    return problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true", help="check archives against manifest")
    args = p.parse_args(argv)
    if args.verify:
        probs = verify()
        for x in probs:
            print("FAIL", x)
        print("archives match manifest" if not probs else f"{len(probs)} problem(s)")
        return 1 if probs else 0
    for src in SOURCES.values():
        print(f"downloading {src.url} -> {src.archive}")
        download(src)
        print(f"  {src.archive.stat().st_size} bytes sha256 {sha256_of(src.archive)}")
    print(f"done at {datetime.now(UTC).isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
