"""
api.py
------
FastAPI backend for the AI Agent Coordination & Decision Engine.

Endpoints:
  GET  /      - serves the HTML interface (interface.html)
  GET  /health - JSON health check
  POST /ask   - runs the 4-agent LangGraph workflow

Run with:
  python api.py

Then open:
  http://localhost:8000        ← HTML interface
  http://localhost:8000/docs   ← Swagger API docs
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
import uuid

from workflow import run_workflow


# --------------------------------------------------
# App setup
# --------------------------------------------------
app = FastAPI(
    title="AI Agent Coordination & Decision Engine",
    description="Planner → Researcher → Decision → Executor Agent Coordination Graph",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the HTML file (same folder as api.py)
HTML_FILE = os.path.join(os.path.dirname(__file__), "interface.html")


# --------------------------------------------------
# Request / Response models
# --------------------------------------------------
class QuestionRequest(BaseModel):
    query: str


class AgentResponse(BaseModel):
    success:  bool
    query:    str
    plan:     str
    research: str
    decision: str
    answer:   str
    mode:     str
    trace_logs: list = []


# --------------------------------------------------
# Endpoints
# --------------------------------------------------
@app.get("/", response_class=FileResponse, include_in_schema=False)
def serve_interface():
    """Serves the HTML testing interface."""
    if not os.path.exists(HTML_FILE):
        raise HTTPException(status_code=404, detail="interface.html not found.")
    return FileResponse(HTML_FILE)


@app.get("/health", tags=["Health"])
def health_check():
    """JSON health check — confirms the API is running."""
    return {
        "status":  "running",
        "message": "AI Agent Coordination & Decision Engine is live!"
    }


@app.post("/ask", response_model=AgentResponse, tags=["Agents"])
def ask(request: QuestionRequest):
    """
    Runs the full 4-agent workflow on the given query.

    Flow: Planner → Researcher → Decision → Executor

    Returns all intermediate outputs plus the final answer.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        import config
        from tracing import tracer
        result = run_workflow(request.query)
        run_mode = "Demo/Simulation Mode" if config.IS_MOCK else "Real-time LLM Output"
        return AgentResponse(
            success  = True,
            query    = result["query"],
            plan     = result["plan"],
            research = result["research"],
            decision = result["decision"],
            answer   = result["answer"],
            mode     = run_mode,
            trace_logs = tracer.get_logs()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# Ticket System Endpoints
# --------------------------------------------------

class TicketCreate(BaseModel):
    user: str
    issue: str
    priority: str

class TicketUpdate(BaseModel):
    status: str

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), "database", "tickets.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Ensure table exists
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            user TEXT,
            issue TEXT,
            priority TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    return conn

@app.post("/tickets", tags=["Tickets"])
def create_ticket(ticket: TicketCreate):
    conn = get_db_connection()
    ticket_id = f"INC{str(uuid.uuid4().int)[:5]}"
    conn.execute(
        "INSERT INTO tickets (ticket_id, user, issue, priority, status) VALUES (?, ?, ?, ?, ?)",
        (ticket_id, ticket.user, ticket.issue, ticket.priority, "Open")
    )
    conn.commit()
    conn.close()
    return {"ticket_id": ticket_id, "message": "Ticket created successfully"}

@app.get("/tickets", tags=["Tickets"])
def get_all_tickets():
    conn = get_db_connection()
    tickets = conn.execute("SELECT * FROM tickets ORDER BY ticket_id DESC").fetchall()
    conn.close()
    return [dict(t) for t in tickets]

@app.get("/tickets/{ticket_id}", tags=["Tickets"])
def get_ticket(ticket_id: str):
    conn = get_db_connection()
    ticket = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    conn.close()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return dict(ticket)

@app.put("/tickets/{ticket_id}", tags=["Tickets"])
def update_ticket(ticket_id: str, ticket_update: TicketUpdate):
    conn = get_db_connection()
    cursor = conn.execute("UPDATE tickets SET status = ? WHERE ticket_id = ?", (ticket_update.status, ticket_id))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket not found")
    conn.close()
    return {"message": "Ticket updated successfully"}

@app.get("/knowledge", tags=["Data"])
def get_knowledge_base():
    """Returns the JSON knowledge base for the UI."""
    kb_path = os.path.join(os.path.dirname(__file__), "database", "knowledge_base.json")
    if not os.path.exists(kb_path):
        return []
    import json
    with open(kb_path, "r") as f:
        return json.load(f)

# --------------------------------------------------
# Entry point
# --------------------------------------------------
if __name__ == "__main__":
    print("\n  AI Agent Coordination & Decision Engine")
    print("  ----------------------------------------")
    print("  Interface : http://localhost:8000")
    print()
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

