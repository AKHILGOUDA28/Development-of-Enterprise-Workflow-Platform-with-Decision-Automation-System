"""
connection.py
-------------
Unified Database Manager supporting SQLite (local dev) and PostgreSQL (Supabase cloud).

- Auto-detects DATABASE_URL for PostgreSQL; falls back to SQLite if not set.
- Translates SQL placeholders (? → %s) and schema types (AUTOINCREMENT → SERIAL).
- Handles Supabase pgbouncer transaction-mode pooler (autocommit per statement).
- Thread-safe via per-call connection acquisition.
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from dotenv import load_dotenv

# Always load .env first — override=True ensures our .env wins over any partially-loaded env
load_dotenv(override=True)


class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.direct_url   = os.getenv("DIRECT_URL", "").strip()

        # Use PostgreSQL if a valid DATABASE_URL is provided
        self.is_postgres = (
            self.database_url.startswith("postgresql://") or
            self.database_url.startswith("postgres://")
        )

        # SQLite fallback path (all tables in one file)
        self._db_path = os.path.join(os.path.dirname(__file__), "incidents.db")
        self._lock = threading.Lock()

        if self.is_postgres:
            try:
                import psycopg2  # noqa: F401
                print("[*] DatabaseManager: PostgreSQL (Supabase) mode active.")
            except ImportError:
                print("[!] psycopg2-binary not installed — falling back to SQLite.")
                self.is_postgres = False

        if not self.is_postgres:
            print("[*] DatabaseManager: SQLite mode active.")

    def set_db_path(self, path: str):
        """Override SQLite path — used by unit tests."""
        self._db_path = path

    # ------------------------------------------------------------------
    # Internal connection factory
    # ------------------------------------------------------------------
    @contextmanager
    def get_connection(self, use_direct: bool = False):
        """
        Yields an open database connection.

        Args:
            use_direct: If True and PostgreSQL, use DIRECT_URL (session mode)
                        instead of the pooler. Needed for DDL (CREATE TABLE).
        """
        if self.is_postgres:
            import psycopg2
            url = (self.direct_url or self.database_url) if use_direct else self.database_url
            conn = psycopg2.connect(url, sslmode="require")
            conn.autocommit = False
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            db_dir = os.path.dirname(self._db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    # ------------------------------------------------------------------
    # SQL dialect translation
    # ------------------------------------------------------------------
    def _translate(self, query: str, for_ddl: bool = False) -> str:
        """Translate SQLite-style SQL to PostgreSQL dialect when needed."""
        if self.is_postgres:
            # Placeholder translation
            query = query.replace("?", "%s")
            # Type translation
            query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            query = query.replace("integer primary key autoincrement", "serial primary key")
            # ON CONFLICT DO UPDATE — PostgreSQL uses EXCLUDED prefix (already correct in our SQL)
        return query

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def execute(self, query: str, params: tuple = (), ddl: bool = False) -> int:
        """Execute a write query (INSERT/UPDATE/DELETE/CREATE). Returns rowcount."""
        query = self._translate(query, for_ddl=ddl)
        with self.get_connection(use_direct=ddl) as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rowcount = cur.rowcount
            cur.close()
            return rowcount

    def fetchall(self, query: str, params: tuple = ()) -> list:
        """Execute a SELECT and return all rows as list of dicts."""
        query = self._translate(query)
        with self.get_connection() as conn:
            if self.is_postgres:
                from psycopg2.extras import RealDictCursor
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute(query, params)
                rows = [dict(r) for r in cur.fetchall()]
            else:
                cur = conn.cursor()
                cur.execute(query, params)
                rows = [dict(r) for r in cur.fetchall()]
            cur.close()
            return rows

    def fetchone(self, query: str, params: tuple = ()) -> dict | None:
        """Execute a SELECT and return the first row as a dict, or None."""
        query = self._translate(query)
        with self.get_connection() as conn:
            if self.is_postgres:
                from psycopg2.extras import RealDictCursor
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute(query, params)
                row = cur.fetchone()
                res = dict(row) if row else None
            else:
                cur = conn.cursor()
                cur.execute(query, params)
                row = cur.fetchone()
                res = dict(row) if row else None
            cur.close()
            return res


# ---------------------------------------------------------------------------
# Global singleton — import and use throughout the app
# ---------------------------------------------------------------------------
db_manager = DatabaseManager()
