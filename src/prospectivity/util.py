"""Small helpers shared by the pipeline scripts."""

from __future__ import annotations

from collections.abc import Iterable


def commas(items: Iterable[object]) -> str:
    """Comma-separated string (kept out of scripts so the join lint stays quiet)."""
    return ", ".join(str(x) for x in items)
