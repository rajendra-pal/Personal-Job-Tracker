import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    company      TEXT NOT NULL,
    role         TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'applied',
    applied_on   TEXT NOT NULL,
    notes        TEXT DEFAULT '',
    link         TEXT DEFAULT ''
);
"""

VALID_STATUSES = ("applied", "interview", "offer", "rejected")


@contextmanager
def get_connection(db_path):
    """Yield a connection that is properly closed after use."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # access columns by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path):
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)
