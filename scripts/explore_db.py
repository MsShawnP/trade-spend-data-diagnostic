"""Quick database schema exploration against the Cinderhaven Data Platform."""

import os
import sys

import psycopg2

url = os.environ.get("DATABASE_URL")
if not url:
    print("Error: DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

conn = psycopg2.connect(url)
cur = conn.cursor()

cur.execute("""
    SELECT schemaname, tablename
    FROM pg_tables
    WHERE schemaname IN ('public_marts', 'public_staging', 'public_intermediate')
    ORDER BY schemaname, tablename
""")
tables = cur.fetchall()
print(f"Tables ({len(tables)}):")
for schema, table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
    n = cur.fetchone()[0]
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table))
    cols = [r[0] for r in cur.fetchall()]
    print(f"  {schema}.{table}: {n} rows — {', '.join(cols)}")

conn.close()
