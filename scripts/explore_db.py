"""Quick database schema exploration."""
import sqlite3
from pathlib import Path

ACTIVE_DB = Path(r"C:\Users\mssha\projects\active\cinderhaven-data\data\cinderhaven_product_master.db")
db = ACTIVE_DB
print(f"Using DB: {db}")
conn = sqlite3.connect(db)
cur = conn.cursor()

tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f"\nTables ({len(tables)}):")
for (t,) in tables:
    n = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    cols = cur.execute(f"PRAGMA table_info([{t}])").fetchall()
    col_names = [c[1] for c in cols]
    print(f"  {t}: {n} rows — {', '.join(col_names)}")

print("\n--- SCAN DATA SAMPLE ---")
row = cur.execute("SELECT * FROM scan_data LIMIT 3").fetchall()
col_names = [d[0] for d in cur.description]
print(f"Columns: {col_names}")
for r in row:
    print(f"  {r}")

print("\n--- DEDUCTIONS SAMPLE ---")
row = cur.execute("SELECT * FROM deductions LIMIT 3").fetchall()
col_names = [d[0] for d in cur.description]
print(f"Columns: {col_names}")
for r in row:
    print(f"  {r}")

print("\n--- DEDUCTION_CODES SAMPLE ---")
row = cur.execute("SELECT * FROM deduction_codes LIMIT 5").fetchall()
col_names = [d[0] for d in cur.description]
print(f"Columns: {col_names}")
for r in row:
    print(f"  {r}")

print("\n--- PROMOTIONS SAMPLE ---")
row = cur.execute("SELECT * FROM promotions LIMIT 3").fetchall()
col_names = [d[0] for d in cur.description]
print(f"Columns: {col_names}")
for r in row:
    print(f"  {r}")

print("\n--- SKU_COSTS SAMPLE ---")
row = cur.execute("SELECT * FROM sku_costs LIMIT 2").fetchall()
col_names = [d[0] for d in cur.description]
print(f"Columns: {col_names}")
for r in row:
    print(f"  {r}")

print("\n--- RETAILERS SAMPLE ---")
row = cur.execute("SELECT * FROM retailers LIMIT 10").fetchall()
col_names = [d[0] for d in cur.description]
print(f"Columns: {col_names}")
for r in row:
    print(f"  {r}")

print("\n--- DISPUTES SAMPLE ---")
row = cur.execute("SELECT * FROM disputes LIMIT 3").fetchall()
col_names = [d[0] for d in cur.description]
print(f"Columns: {col_names}")
for r in row:
    print(f"  {r}")

print("\n--- ORDERS SAMPLE ---")
row = cur.execute("SELECT * FROM orders LIMIT 3").fetchall()
col_names = [d[0] for d in cur.description]
print(f"Columns: {col_names}")
for r in row:
    print(f"  {r}")

conn.close()
