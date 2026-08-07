"""
memory.py
---------
Memory system for the AI Agent Coordination & Decision Engine.

ShortTermMemory  - remembers the current conversation (cleared each session)
LongTermMemory   - persists important facts across server restarts via SQLite
"""

import os
import sqlite3
from datetime import datetime
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
            "timestamp": datetime.utcnow().isoformat() + "Z"
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
# Long-Term Memory (SQLite-backed, persistent across restarts)
# ---------------------------------------------------------------------------
class LongTermMemory:
    """
    Stores important facts that should be remembered across sessions.

    Backed by SQLite so data persists across server restarts.
    Schema: key TEXT, value TEXT, updated_at TEXT
    """

    DB_PATH = os.path.join(
        os.path.dirname(__file__), "database", "memory.db"
    )

    def __init__(self):
        self._lock = Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Creates the memory table if it doesn't exist."""
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    key        TEXT PRIMARY KEY,
                    value      TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def _connect(self):
        conn = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, key: str, value: str) -> None:
        """Saves or updates a key-value fact."""
        now = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            with self._connect() as conn:
                conn.execute(
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
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT value FROM long_term_memory WHERE key = ?", (key,)
                ).fetchone()
                return row["value"] if row else None

    def delete(self, key: str) -> bool:
        """Removes a key from memory. Returns True if deleted, False if not found."""
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    "DELETE FROM long_term_memory WHERE key = ?", (key,)
                )
                return cursor.rowcount > 0

    def show_all(self) -> list:
        """Returns all stored key-value facts as a list of dicts."""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT key, value, updated_at FROM long_term_memory ORDER BY updated_at DESC"
                ).fetchall()
                return [dict(row) for row in rows]

    def search(self, query: str) -> list:
        """
        Simple text search across keys and values.
        Returns matching entries as a list of dicts.
        """
        query_lower = f"%{query.lower()}%"
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT key, value, updated_at FROM long_term_memory
                    WHERE LOWER(key) LIKE ? OR LOWER(value) LIKE ?
                    ORDER BY updated_at DESC
                    """,
                    (query_lower, query_lower)
                ).fetchall()
                return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Shared singletons — import these across the app
# ---------------------------------------------------------------------------
short_memory = ShortTermMemory()
long_memory  = LongTermMemory()
