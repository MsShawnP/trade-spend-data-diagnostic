"""Inspect platform DB to understand what scripts need to produce."""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "cinderhaven_product_master.db"
conn = sqlite3.connect(DB)

print("=== sku_costs columns ===")
cols = [r[1] for r in conn.execute("PRAGMA table_info(sku_costs)").fetchall()]
print(cols)

print("\n=== scan_data date range ===")
r = conn.execute("SELECT MIN(week_ending), MAX(week_ending), COUNT(DISTINCT week_ending) FROM scan_data").fetchone()
print(f"  {r[0]} to {r[1]} ({r[2]} weeks)")

print("\n=== stores retailers ===")
rows = conn.execute("SELECT retailer, COUNT(*) FROM stores GROUP BY retailer ORDER BY COUNT(*) DESC").fetchall()
for r in rows:
    print(f"  {r[0]:25s} {r[1]:>5}")

print("\n=== deductions volume ===")
r = conn.execute("SELECT COUNT(*), MIN(deduction_date), MAX(deduction_date) FROM deductions").fetchone()
print(f"  {r[0]} deductions, {r[1]} to {r[2]}")

print("\n=== deductions by type ===")
rows = conn.execute("SELECT deduction_type, COUNT(*) FROM deductions GROUP BY deduction_type ORDER BY COUNT(*) DESC").fetchall()
for r in rows:
    print(f"  {r[0]:20s} {r[1]:>6}")

print("\n=== disputes volume ===")
r = conn.execute("SELECT COUNT(*) FROM disputes").fetchone()
print(f"  {r[0]} disputes")

print("\n=== all tables ===")
rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for r in rows:
    count = conn.execute(f"SELECT COUNT(*) FROM [{r[0]}]").fetchone()[0]
    print(f"  {r[0]:30s} {count:>8}")

conn.close()
