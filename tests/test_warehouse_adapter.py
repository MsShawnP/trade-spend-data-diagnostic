"""Tests for the client-warehouse adapter (the reference connection pattern).

Skipped unless the shared ``lailara_engagement`` lib is installed. Builds a tiny
SQLite "client warehouse" with DELIBERATELY non-canonical table/column names, so
the test proves the config schema-map does real work (not an identity pass) and
that warehouse rows go through the same POS specs + required declarations as a
CSV. The full committed DB reproduces $32,323,140 / 1.06% (verified manually; the
20s, 1.3M-row pull is too slow to unit-test).
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

pytest.importorskip("lailara_engagement")

import warehouse_adapter  # noqa: E402

AS_OF = pd.Timestamp("2025-12-27")   # Saturday
WEEKS = [(AS_OF - timedelta(weeks=k)).strftime("%Y-%m-%d") for k in range(3)]


def _build_warehouse(path: Path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE client_scans (Loc TEXT, Item TEXT, WeekEnd TEXT, U REAL, ScanUSD REAL)")
    conn.execute("CREATE TABLE client_deds (DedID TEXT, DedType TEXT, Amt REAL, DedDate TEXT)")
    for w in WEEKS:                                   # 2 stores × 3 weeks × $100 = $600
        conn.executemany("INSERT INTO client_scans VALUES (?,?,?,?,?)",
                         [("0012", "CHP-AS-001", w, 4, 100.0), ("0034", "CHP-AS-001", w, 4, 100.0)])
    conn.executemany("INSERT INTO client_deds VALUES (?,?,?,?)", [
        ("DED-1", "spoilage", 50.0, "2025-12-01"),
        ("DED-2", "promo_billback", 999.0, "2025-12-01"),   # excluded from waste
    ])
    conn.commit(); conn.close()


def _cfg(d: Path, db: Path, *, scan_cols=None):
    import yaml
    scan_cols = scan_cols or {"store_id": "Loc", "sku": "Item", "week_ending": "WeekEnd",
                              "units_sold": "U", "dollars_sold": "ScanUSD"}
    p = d / "engagement.warehouse.yml"
    p.write_text(yaml.safe_dump({
        "client": {"name": "Cinderhaven Provisions (demo)"}, "engagement": {"id": "T-1"},
        "as_of_date": "2025-12-27", "demo": True,
        "basis": {"week_convention": "week_ending_saturday", "scan_basis": "retail_scan"},
        "warehouse": {"kind": "sqlite", "path": str(db),
                      "tables": {"scans": "client_scans", "deductions": "client_deds"},
                      "columns": {"scans": scan_cols,
                                  "deductions": {"deduction_id": "DedID", "deduction_type": "DedType",
                                                 "amount": "Amt", "deduction_date": "DedDate"}}}},
    ), encoding="utf-8")
    return p


def test_adapter_pulls_maps_validates_and_computes(tmp_path):
    db = tmp_path / "wh.db"; _build_warehouse(db)
    cfg = _cfg(tmp_path, db)
    res = warehouse_adapter.run(str(cfg), str(tmp_path / "out"))
    assert res["status"] == "ok"
    assert res["revenue"] == 600.00                 # 2 × 3 × $100
    assert res["waste"] == 50.00                    # spoilage only; promo_billback excluded
    assert res["basis"] == "retail scan"
    html = Path(res["report"]).read_text(encoding="utf-8")
    assert "retail scan revenue" in html
    assert "no table names hardcoded" in html
    assert "Source" in html and "warehouse" in html  # provenance
    assert "DRAFT" in html


def test_bad_schema_map_blocks_with_readiness_report(tmp_path):
    db = tmp_path / "wh.db"; _build_warehouse(db)
    # Map dollars_sold to a column that doesn't exist -> the SELECT alias yields
    # nothing; simulate a mis-map by pointing week_ending at the units column.
    cfg = _cfg(tmp_path, db, scan_cols={"store_id": "Loc", "sku": "Item",
                                        "week_ending": "U",   # numbers, not dates
                                        "units_sold": "U", "dollars_sold": "ScanUSD"})
    res = warehouse_adapter.run(str(cfg), str(tmp_path / "out"))
    assert res["status"] == "blocked"
    assert "scans" in res["blocked_files"]


def test_missing_week_convention_declaration_errors(tmp_path):
    import yaml
    db = tmp_path / "wh.db"; _build_warehouse(db)
    cfg = tmp_path / "engagement.warehouse.yml"
    cfg.write_text(yaml.safe_dump({
        "client": {"name": "x"}, "engagement": {"id": "y"}, "as_of_date": "2025-12-27", "demo": True,
        "basis": {"scan_basis": "retail_scan"},   # no week_convention
        "warehouse": {"kind": "sqlite", "path": str(db),
                      "tables": {"scans": "client_scans", "deductions": "client_deds"}}}), encoding="utf-8")
    with pytest.raises(Exception):
        warehouse_adapter.run(str(cfg), str(tmp_path / "out"))
