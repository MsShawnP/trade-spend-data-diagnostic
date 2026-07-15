"""Seed the deduction-tracking tables (schema DDL + static reference data).

Applies two SQL files in sequence:
  1. seed_deduction_schema.sql — creates 13 new tables (retailers,
     retailer_rules, deduction_codes, edi_requirements, orders,
     order_lines, shipments, pack_records, remittances, deductions,
     disputes, dispute_evidence, post_audit_claims).
  2. seed_deduction_static.sql — populates the four reference tables
     (retailers, retailer_rules, deduction_codes, edi_requirements)
     with static seed data.

Run after the base pipeline (01–06) so the base tables exist.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from shared import DB_PATH

SCRIPTS_DIR = Path(__file__).resolve().parent


def apply_sql(con: sqlite3.Connection, filename: str) -> None:
    sql_path = SCRIPTS_DIR / filename
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file missing: {sql_path}")
    sql = sql_path.read_text(encoding="utf-8")
    con.executescript(sql)
    con.commit()
    print(f"  [OK] Applied {filename}")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        print("Seeding deduction tables...")
        apply_sql(con, "seed_deduction_schema.sql")
        apply_sql(con, "seed_deduction_static.sql")

        cur = con.cursor()
        for table in ("retailers", "retailer_rules", "deduction_codes", "edi_requirements"):
            n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:<22} {n:>4} rows")

    print("Done.")


if __name__ == "__main__":
    main()
