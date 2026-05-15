"""Database connection for the trade spend diagnostic workbook.

Provides a thin wrapper around psycopg2 that preserves the
conn.execute().fetchone() / .fetchall() interface used throughout
the tab builder modules.
"""

import os
from decimal import Decimal

import psycopg2
import psycopg2.extensions


# Register a global adapter so psycopg2 returns float instead of Decimal
# for NUMERIC/DECIMAL columns — matches the float arithmetic used throughout.
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    "DEC2FLOAT",
    lambda value, curs: float(value) if value is not None else None,
)
psycopg2.extensions.register_type(DEC2FLOAT)


def connect():
    """Return a ConnectionWrapper using DATABASE_URL."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    return ConnectionWrapper(url)


class ConnectionWrapper:
    """Wraps psycopg2 connection to provide conn.execute() interface."""

    def __init__(self, dsn):
        self._conn = psycopg2.connect(dsn, options="-c search_path=public_staging,public")

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return cur

    def close(self):
        self._conn.close()
