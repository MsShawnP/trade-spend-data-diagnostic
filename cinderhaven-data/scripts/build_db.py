"""Build the Cinderhaven SQLite dataset from scratch.

Deterministic generation pipeline: seeds RNG with fixed seeds so the
output is reproducible. Produces a 50-SKU, 157-week dataset matching
the cinderhaven-data-platform Postgres structure.

Regenerates on demand if the DB is missing. No-op if present.

Order of operations:
  0. Seed `product_master` from scripts/seed_product_master.sql
  1. 01_generate_stores.py          — store directory
  2. 02_generate_distribution.py    — SKU x store authorizations + deauths
  3. 02b_generate_chargebacks.py    — defect-driven chargebacks
  4. 03_generate_costs.py           — sku_costs (wholesale, COGS, etc.)
  5. 04_generate_promos.py          — promotions table (incl promo_cost, funding_mechanism)
  6. 04b_generate_price_history.py  — price history per SKU x retailer
  7. 05_generate_scan_data.py       — weekly scan data (the big one)
  8. 06_validate_dataset.py         — sanity-check the base tables
  -- Deduction pipeline (extends the DB with 13 tables) --
  9. 07_seed_deduction_tables.py    — schema DDL + static seeds
 10. 08_generate_orders.py          — purchase orders + order_lines
 11. 09_generate_pack_records.py    — pack/label/evidence records
 12. 10_generate_shipments.py       — shipment records + BOL/POD/ASN
 13. 11_generate_deductions.py      — deduction records + double-dips
 14. 12_generate_post_audit_claims.py — retroactive audit clawbacks
 15. 13_generate_remittances.py     — payment events bundling deductions
 16. 14_generate_disputes.py        — dispute filings + evidence
 17. 15_validate_deductions.py      — deduction-specific validation

Usage:
  python scripts/build_db.py                        # build if missing
  python scripts/build_db.py --force                # rebuild even if DB exists
  python scripts/build_db.py --output /path/to.db   # write the built DB elsewhere
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

from shared import DB_PATH

ROOT = Path(__file__).resolve().parent.parent
SEED_SQL = Path(__file__).resolve().parent / "seed_product_master.sql"

# Order matters: each script reads from tables built by earlier ones.
PIPELINE = [
    "01_generate_stores.py",
    "02_generate_distribution.py",
    "02b_generate_chargebacks.py",
    "03_generate_costs.py",
    "04_generate_promos.py",
    "04b_generate_price_history.py",
    "05_generate_scan_data.py",
    "06_validate_dataset.py",
    # Deduction pipeline (extends the base with 13 new tables)
    "07_seed_deduction_tables.py",
    "08_generate_orders.py",
    "09_generate_pack_records.py",
    "10_generate_shipments.py",
    "11_generate_deductions.py",
    "12_generate_post_audit_claims.py",
    "13_generate_remittances.py",
    "14_generate_disputes.py",
    "15_validate_deductions.py",
]


def seed_product_master() -> None:
    """Load the product_master seed from SQL."""
    if not SEED_SQL.exists():
        raise FileNotFoundError(
            f"Seed file missing: {SEED_SQL}. "
            "Cannot bootstrap product_master without it."
        )
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        with SEED_SQL.open(encoding="utf-8") as f:
            con.executescript(f.read())
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM product_master").fetchone()[0]
        print(f"  [OK] Seeded product_master ({n} rows)")


def run_script(name: str) -> None:
    script = Path(__file__).resolve().parent / name
    if not script.exists():
        raise FileNotFoundError(f"Pipeline script missing: {script}")
    print(f"  -> Running {name}...")
    # Same Python interpreter that's running build_db.py — ensures the same
    # virtualenv / dependencies are used. Inherits stdout/stderr so progress
    # output streams through to the caller (Streamlit Cloud logs, terminal).
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{name} exited with status {result.returncode}. "
            f"Build aborted; the DB may be in a partial state."
        )


def build(force: bool = False, output: Path | None = None) -> None:
    if DB_PATH.exists() and not force:
        size_mb = DB_PATH.stat().st_size / (1024 * 1024)
        print(f"Database already exists ({size_mb:.1f} MB) — skipping build.")
        print(f"  Path: {DB_PATH}")
        print("  Pass --force to rebuild from scratch.")
        return

    if force and DB_PATH.exists():
        print(f"Removing existing {DB_PATH.name} (--force)...")
        DB_PATH.unlink()
        for sidecar in (DB_PATH.with_suffix(".db-wal"), DB_PATH.with_suffix(".db-shm")):
            if sidecar.exists():
                sidecar.unlink()

    print("Building Cinderhaven dataset...")
    print("Step 0: seed product_master")
    seed_product_master()

    for i, name in enumerate(PIPELINE, start=1):
        print(f"Step {i}: {name}")
        run_script(name)

    if output is not None:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DB_PATH, output)
        DB_PATH.unlink()
        for sidecar in (DB_PATH.with_suffix(".db-wal"), DB_PATH.with_suffix(".db-shm")):
            if sidecar.exists():
                sidecar.unlink()
        final_path = output
    else:
        final_path = DB_PATH

    size_mb = final_path.stat().st_size / (1024 * 1024)
    print(f"\nBuild complete. Database is {size_mb:.1f} MB at {final_path}.")


def main() -> int:
    p = argparse.ArgumentParser(description="Build the Cinderhaven SQLite dataset.")
    p.add_argument(
        "--force", action="store_true",
        help="Rebuild from scratch even if the DB already exists.",
    )
    p.add_argument(
        "--output", type=Path, default=None,
        help="Copy the built database to this path (default: data/ inside this repo).",
    )
    args = p.parse_args()
    try:
        build(force=args.force, output=args.output)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
