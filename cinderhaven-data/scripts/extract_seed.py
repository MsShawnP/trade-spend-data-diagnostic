"""Extract current product_master from platform DB as SQL INSERT statements."""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "cinderhaven_product_master.db"
OUT = Path(__file__).resolve().parent / "seed_product_master.sql"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT * FROM product_master ORDER BY sku").fetchall()
cols = [desc[0] for desc in conn.execute("SELECT * FROM product_master LIMIT 1").description]

print(f"Extracting {len(rows)} SKUs from product_master...")

lines = []
lines.append("-- Cinderhaven Provisions product master (50 SKUs)")
lines.append("-- Extracted from cinderhaven-data-platform on 2026-05-17")
lines.append("-- Source of truth: platform Postgres → this seed file")
lines.append("")
lines.append("DROP TABLE IF EXISTS product_master;")
lines.append("")

# Build CREATE TABLE from actual schema
schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='product_master'").fetchone()
if schema:
    lines.append(schema[0] + ";")
else:
    col_defs = ", ".join(f"{c} TEXT" for c in cols)
    lines.append(f"CREATE TABLE product_master ({col_defs});")

lines.append("")
lines.append(f"-- {len(rows)} SKUs across 3 product lines")
lines.append("")

for row in rows:
    values = []
    for val in row:
        if val is None:
            values.append("NULL")
        elif isinstance(val, (int, float)):
            values.append(str(val))
        else:
            escaped = str(val).replace("'", "''")
            values.append(f"'{escaped}'")
    lines.append(f"INSERT INTO product_master VALUES ({', '.join(values)});")

lines.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

conn.close()
print(f"Written to {OUT}")
print(f"  Columns: {len(cols)}")
print(f"  Rows: {len(rows)}")
print(f"  Product lines: {set(r['product_line'] for r in rows)}")
