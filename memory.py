"""
memory.py
---------
Memory system for the AI Agent Coordination & Decision Engine.

ShortTermMemory  - remembers the current conversation (cleared each session)
LongTermMemory   - persists important facts across server restarts (SQLite or PostgreSQL)
"""

import os
from datetime import datetime, timezone
from threading import Lock


# ---------------------------------------------------------------------------
# Short-Term Memory (in-memory, per session)
# ---------------------------------------------------------------------------
class ShortTermMemory:
    """Stores conversation history for the current session."""

    def __init__(self):
        self.history = []

    def add(self, role: str, message: str) -> None:
        self.history.append({
            "role":      role,
            "message":   message,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        })

    def get(self) -> list:
        return self.history

    def clear(self) -> None:
        self.history = []

    def to_context_string(self) -> str:
        """Returns conversation history as a formatted string for LLM context."""
        lines = []
        for entry in self.history[-10:]:  # last 10 turns
            lines.append(f"[{entry['role'].upper()}]: {entry['message']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Long-Term Memory (persistent — SQLite or PostgreSQL via db_manager)
# ---------------------------------------------------------------------------
class LongTermMemory:
    """
    Stores important facts that should be remembered across sessions.

    In production: delegates to the global db_manager (Postgres or SQLite).
    In unit tests: can be redirected to an isolated SQLite DB by setting DB_PATH.
    """

    def __init__(self):
        self._lock = Lock()
        self._db_manager = None   # None → use global singleton
        self._test_db_path = None # only used when DB_PATH is overridden by tests
        self._init_db()

    # ------------------------------------------------------------------
    # Test-compatibility shim: allow tests to set DB_PATH directly
    # ------------------------------------------------------------------
    @property
    def DB_PATH(self):
        from database.connection import db_manager
        return self._test_db_path or db_manager._db_path

    @DB_PATH.setter
    def DB_PATH(self, val: str):
        """
        When a test overrides DB_PATH, we switch to an isolated SQLite db_manager
        so the global Postgres connection is not affected.
        """
        self._test_db_path = val
        # Build a fresh SQLite-only manager pointed at the test path
        import sqlite3
        from contextlib import contextmanager

        class _IsolatedSQLite:
            """Minimal db_manager interface backed by a single SQLite file."""
            def __init__(self, path):
                self._db_path = path
                os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
                self.is_postgres = False

            @contextmanager
            def _conn(self):
                conn = sqlite3.connect(self._db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                try:
                    yield conn
                    conn.commit()
                finally:
                    conn.close()

            def execute(self, query, params=(), **kw):
                with self._conn() as conn:
                    cur = conn.cursor()
                    cur.execute(query, params)
                    rc = cur.rowcount
                    cur.close()
                    return rc

            def fetchall(self, query, params=()):
                with self._conn() as conn:
                    cur = conn.cursor()
                    cur.execute(query, params)
                    rows = [dict(r) for r in cur.fetchall()]
                    cur.close()
                    return rows

            def fetchone(self, query, params=()):
                with self._conn() as conn:
                    cur = conn.cursor()
                    cur.execute(query, params)
                    row = cur.fetchone()
                    res = dict(row) if row else None
                    cur.close()
                    return res

        self._db_manager = _IsolatedSQLite(val)

    def _get_db(self):
        """Return whichever db_manager is active (global or test-isolated)."""
        if self._db_manager is not None:
            return self._db_manager
        from database.connection import db_manager
        return db_manager

    def _init_db(self) -> None:
        """Creates the memory table if it doesn't exist."""
        self._get_db().execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

    def save(self, key: str, value: str) -> None:
        """Saves or updates a key-value fact."""
        now = datetime.now(timezone.utc).isoformat() + "Z"
        with self._lock:
            self._get_db().execute(
                """
                INSERT INTO long_term_memory (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, str(value), now)
            )

    def recall(self, key: str) -> str | None:
        """Retrieves the value for a key, or None if not found."""
        with self._lock:
            row = self._get_db().fetchone(
                "SELECT value FROM long_term_memory WHERE key = ?", (key,)
            )
            return row["value"] if row else None

    def delete(self, key: str) -> bool:
        """Removes a key from memory. Returns True if deleted, False if not found."""
        with self._lock:
            rc = self._get_db().execute(
                "DELETE FROM long_term_memory WHERE key = ?", (key,)
            )
            return rc > 0

    def show_all(self) -> list:
        """Returns all stored key-value facts as a list of dicts."""
        with self._lock:
            return self._get_db().fetchall(
                "SELECT key, value, updated_at FROM long_term_memory ORDER BY updated_at DESC"
            )

    def search(self, query: str) -> list:
        """Simple text search across keys and values."""
        q = f"%{query.lower()}%"
        with self._lock:
            return self._get_db().fetchall(
                """
                SELECT key, value, updated_at FROM long_term_memory
                WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ?
                ORDER BY updated_at DESC
                """,
                (q, q)
            )


# ---------------------------------------------------------------------------
# Shared singletons — import these across the app
# ---------------------------------------------------------------------------
short_memory = ShortTermMemory()
long_memory  = LongTermMemory()
