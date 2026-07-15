"""Shared constants and utilities for the Cinderhaven generation pipeline."""

from __future__ import annotations

from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "cinderhaven_product_master.db"

REGIONAL_CHAIN_NAMES = frozenset({
    "Kroger",
    "Sprouts",
    "Regional Group",
})


def gtin_invalid(gtin: str | None) -> bool:
    """Return True if the GTIN-14 is missing, malformed, or fails check-digit
    validation (weights 1,3 alternating from the leftmost digit)."""
    if not gtin or len(gtin) != 14 or not gtin.isdigit():
        return True
    d = [int(c) for c in gtin]
    s = sum(d[i] * (1 if (12 - i) % 2 == 0 else 3) for i in range(13))
    return (10 - s % 10) % 10 != d[13]


def upc_missing(upc: str | None) -> bool:
    """Return True if the UPC is missing or a known placeholder value."""
    if upc is None:
        return True
    s = str(upc).strip()
    return s == "" or s in ("TBD", "N/A", "0", "00000000000", "000000000000")
