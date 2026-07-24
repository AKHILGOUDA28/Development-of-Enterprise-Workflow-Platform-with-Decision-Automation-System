import sqlite3
import os
from pydantic import BaseModel
from tools.base_tool import BaseTool

class DatabaseToolSchema(BaseModel):
    query: str

class DatabaseTool(BaseTool):
    name = "incident_database"
    description = "Searches the incident database for past IT issues and solutions."
    args_schema = DatabaseToolSchema

    def _execute(self, query: str) -> str:
        db_path = os.path.join(os.path.dirname(__file__), "..", "database", "incidents.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                ticket_id TEXT PRIMARY KEY,
                issue TEXT,
                status TEXT,
                solution TEXT
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM incidents")
        if cursor.fetchone()[0] == 0:
            mock_data = [
                ("INC1001", "VPN not connecting", "Closed", "Restart VPN"),
                ("INC1002", "Printer offline", "Closed", "Restart printer"),
                ("INC1003", "Laptop slow", "Open", "Pending"),
                ("INC1004", "Email not syncing", "Closed", "Restart Outlook")
            ]
            cursor.executemany("INSERT INTO incidents VALUES (?, ?, ?, ?)", mock_data)
            conn.commit()

        cursor.execute("SELECT ticket_id, issue, status, solution FROM incidents WHERE issue LIKE ? OR solution LIKE ?", 
                       ('%' + query + '%', '%' + query + '%'))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            res = [f"Ticket: {row[0]}, Issue: {row[1]}, Status: {row[2]}, Solution: {row[3]}" for row in rows]
            return "\n".join(res)
        return "No similar past incidents found."
