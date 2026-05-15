"""Verify connectivity to the Cinderhaven Data Platform.

Replaces the SQLite build_db.py — the data now lives in Postgres.
"""

import os
import sys

import psycopg2


def check_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Error: DATABASE_URL environment variable not set.", file=sys.stderr)
        print("See .env.example for connection string templates.", file=sys.stderr)
        sys.exit(1)

    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fct_scan_data")
        count = cur.fetchone()[0]
        print(f"Connected. fct_scan_data: {count:,} rows")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    check_connection()
