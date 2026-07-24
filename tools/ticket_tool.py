import sqlite3
import os
import uuid
from pydantic import BaseModel
from tools.base_tool import BaseTool

class TicketToolSchema(BaseModel):
    user: str
    issue: str
    priority: str

class TicketTool(BaseTool):
    name = "ticket_system"
    description = "Creates a new IT support ticket."
    args_schema = TicketToolSchema

    def _execute(self, user: str, issue: str, priority: str) -> str:
        db_path = os.path.join(os.path.dirname(__file__), "..", "database", "tickets.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                user TEXT,
                issue TEXT,
                priority TEXT,
                status TEXT
            )
        ''')
        
        ticket_id = f"INC{str(uuid.uuid4().int)[:5]}"
        cursor.execute("INSERT INTO tickets (ticket_id, user, issue, priority, status) VALUES (?, ?, ?, ?, ?)",
                       (ticket_id, user, issue, priority, "Open"))
        conn.commit()
        conn.close()

        return f"Ticket Created Successfully. Ticket ID: {ticket_id}"
