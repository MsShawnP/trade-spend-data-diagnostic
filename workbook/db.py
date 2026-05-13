"""Database connection for the trade spend diagnostic workbook.

Provides a thin wrapper around psycopg2 that preserves the
conn.execute().fetchone() / .fetchall() interface used throughout
the tab builder modules.
"""

import os

import psycopg2


def connect():
    """Return a ConnectionWrapper using DATABASE_URL."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    return ConnectionWrapper(url)


class ConnectionWrapper:
    """Wraps psycopg2 connection to provide SQLite-compatible execute()."""

    def __init__(self, dsn):
        self._conn = psycopg2.connect(dsn)

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return cur

    def close(self):
        self._conn.close()

    @property
    def connection(self):
        return self._conn
