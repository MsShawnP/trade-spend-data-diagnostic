"""Quick check of recovery rate calculations against the Cinderhaven Data Platform."""

import os
import sys

import psycopg2

url = os.environ.get("DATABASE_URL")
if not url:
    print("Error: DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

conn = psycopg2.connect(url)
cur = conn.cursor()

cur.execute("SELECT MAX(week_ending) FROM fct_scan_data")
max_scan = cur.fetchone()[0]

cur.execute("SELECT SUM(recovered_amount) FROM stg_disputes")
rec = cur.fetchone()[0]

cur.execute("""
    SELECT SUM(d.amount) FROM stg_deductions d
    JOIN stg_disputes dis ON dis.deduction_id = d.deduction_id
""")
all_time = cur.fetchone()[0]

cur.execute("""
    SELECT SUM(d.amount) FROM stg_deductions d
    JOIN stg_disputes dis ON dis.deduction_id = d.deduction_id
    WHERE d.deduction_date > (%s::date - interval '365 days')::date AND d.deduction_date <= %s
""", (max_scan, max_scan))
trailing = cur.fetchone()[0]

print(f"max_scan: {max_scan}")
print(f"Recovered: ${rec:,.0f}")
print(f"All-time disputed: ${all_time:,.0f}  rate={rec/all_time:.1%}")
print(f"Trailing disputed: ${trailing:,.0f}  rate={rec/trailing:.1%}")

conn.close()
