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
            SELECT incident_id, issue, category, severity, status, resolution_strategy
            FROM incidents
            WHERE issue LIKE ? OR category LIKE ? OR resolution_strategy LIKE ?
            ORDER BY updated_at DESC LIMIT 5
        """, (q_wildcard, q_wildcard, q_wildcard))

        if rows:
            res = [
                f"Incident: {row['incident_id']}, Category: {row['category']}, Severity: {row['severity']}, Status: {row['status']}, Strategy: {row['resolution_strategy']}\n  Issue: {row['issue']}"
                for row in rows
            ]
            return "\n\n".join(res)
        
        return f"No matching past incidents found in database for query '{query}'."
