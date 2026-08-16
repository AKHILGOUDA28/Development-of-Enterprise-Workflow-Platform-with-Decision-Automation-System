"""
database_tool.py
----------------
Incident Database Query Tool.
Searches historical IT incident records from database using db_manager.
"""

from pydantic import BaseModel, Field
from tools.base_tool import BaseTool
from database.connection import db_manager

class DatabaseToolSchema(BaseModel):
    query: str = Field(..., description="IT issue keyword or category to query in past incident records")

class DatabaseTool(BaseTool):
    name = "incident_database"
    description = "Searches the incident database for past IT issues, severity, and resolution strategies."
    args_schema = DatabaseToolSchema

    def _execute(self, query: str) -> str:
        q_wildcard = f"%{query}%"
        rows = db_manager.fetchall("""
            SELECT incident_id, issue, category, severity, status, resolution_strategy, user_confirmed_resolution, resolution_attempt_count
            FROM incidents
            WHERE issue LIKE ? OR category LIKE ? OR resolution_strategy LIKE ?
            ORDER BY updated_at DESC LIMIT 5
        """, (q_wildcard, q_wildcard, q_wildcard))

        if rows:
            res = []
            for row in rows:
                confirmed = "YES" if row.get("user_confirmed_resolution") == 1 else "NO"
                attempts = row.get("resolution_attempt_count") or 0
                res.append(
                    f"Incident ID: {row['incident_id']}\n"
                    f"Issue: {row['issue']}\n"
                    f"Category: {row['category']}\n"
                    f"Severity: {row['severity']}\n"
                    f"Status: {row['status']}\n"
                    f"Resolution Strategy: {row['resolution_strategy'] or 'N/A'}\n"
                    f"Confirmed by Employee: {confirmed}\n"
                    f"Resolution Attempt Count: {attempts}"
                )
            return "\n\n".join(res)
        
        return f"No matching past incidents found in database for query '{query}'."
