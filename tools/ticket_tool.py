import uuid
from pydantic import BaseModel
from tools.base_tool import BaseTool
from database.connection import db_manager

class TicketToolSchema(BaseModel):
    user: str
    issue: str
    priority: str

class TicketTool(BaseTool):
    name = "ticket_system"
    description = "Creates a new IT support ticket."
    args_schema = TicketToolSchema

    def _execute(self, user: str, issue: str, priority: str) -> str:
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                "user"    TEXT,
                issue     TEXT,
                priority  TEXT,
                status    TEXT
            )
        ''', ddl=True)
        
        ticket_id = f"INC{str(uuid.uuid4().int)[:5]}"
        db_manager.execute(
            "INSERT INTO tickets (ticket_id, \"user\", issue, priority, status) VALUES (?, ?, ?, ?, ?)",
            (ticket_id, user, issue, priority, "Open")
        )

        return f"Ticket Created Successfully. Ticket ID: {ticket_id}"
