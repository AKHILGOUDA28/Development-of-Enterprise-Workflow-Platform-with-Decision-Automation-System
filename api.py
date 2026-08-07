"""
api.py
------
FastAPI backend for the AI Agent Coordination & Decision Engine.

Endpoints:
  GET  /              - serves the HTML interface (interface.html)
  GET  /health        - JSON health check
  POST /ask           - runs the 5-agent LangGraph workflow
  POST /tickets       - create a new ticket
  GET  /tickets       - list all tickets
  GET  /tickets/{id}  - get a specific ticket
  PUT  /tickets/{id}  - update ticket status
  GET  /knowledge     - returns knowledge base JSON
  GET  /memory        - returns all long-term memory entries
  POST /memory        - saves a key-value fact to long-term memory
  DELETE /memory/{key}- deletes a memory entry
  GET  /events        - returns recent agent communication events
  GET  /tools/stats   - returns tool usage statistics
  GET  /agents/status - returns last run status of each agent

Run with:
  python api.py

Then open:
  http://localhost:8000        ← HTML interface
  http://localhost:8000/docs   ← Swagger API docs
"""

import uuid_utils_compat  # noqa: F401 — must come before any langchain import
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3
import uuid

from workflow import run_workflow


# --------------------------------------------------
# App setup
# --------------------------------------------------
app = FastAPI(
    title="AI Agent Coordination & Decision Engine",
    description=(
        "5-Agent Pipeline: Planner → Researcher → Analysis → Decision → Executor. "
        "Includes Tool Monitoring, Persistent Memory, and Agent Event Bus."
    ),
    version="2.0.0"
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
    success:    bool
    query:      str
    plan:       str
    research:   str
    analysis:   str       # NEW — root-cause analysis output
    decision:   str
    answer:     str
    mode:       str
    session_id: str       # NEW — session identifier
    trace_logs: list = []


class MemoryEntry(BaseModel):
    key:   str
    value: str


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
        "version": "2.0.0",
        "agents":  ["planner", "researcher", "analysis", "decision", "executor"],
        "message": "AI Agent Coordination & Decision Engine is live!"
    }


@app.post("/ask", response_model=AgentResponse, tags=["Agents"])
def ask(request: QuestionRequest):
    """
    Runs the full 5-agent workflow on the given query.

    Flow: Planner → Researcher → Analysis → Decision → Executor

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
            success    = True,
            query      = result["query"],
            plan       = result["plan"],
            research   = result["research"],
            analysis   = result.get("analysis", ""),
            decision   = result["decision"],
            answer     = result["answer"],
            mode       = run_mode,
            session_id = result.get("session_id", ""),
            trace_logs = tracer.get_logs()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# Ticket System Endpoints
# --------------------------------------------------
class TicketCreate(BaseModel):
    user:     str
    issue:    str
    priority: str

class TicketUpdate(BaseModel):
    status: str

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), "database", "tickets.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            user      TEXT,
            issue     TEXT,
            priority  TEXT,
            status    TEXT
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
    cursor = conn.execute(
        "UPDATE tickets SET status = ? WHERE ticket_id = ?",
        (ticket_update.status, ticket_id)
    )
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
# Long-Term Memory Endpoints
# --------------------------------------------------
@app.get("/memory", tags=["Memory"])
def get_all_memory():
    """Returns all long-term memory entries."""
    from memory import long_memory
    return long_memory.show_all()

@app.post("/memory", tags=["Memory"])
def save_memory(entry: MemoryEntry):
    """Saves a key-value fact to long-term memory (persisted across restarts)."""
    from memory import long_memory
    long_memory.save(entry.key, entry.value)
    return {"message": f"Memory saved: {entry.key}"}

@app.delete("/memory/{key}", tags=["Memory"])
def delete_memory(key: str):
    """Removes a key from long-term memory."""
    from memory import long_memory
    deleted = long_memory.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory key '{key}' not found")
    return {"message": f"Memory key '{key}' deleted"}

@app.get("/memory/search/{query}", tags=["Memory"])
def search_memory(query: str):
    """Full-text search across long-term memory keys and values."""
    from memory import long_memory
    return long_memory.search(query)


# --------------------------------------------------
# Agent Event Bus Endpoints
# --------------------------------------------------
@app.get("/events", tags=["Events"])
def get_events(session_id: Optional[str] = None, event_type: Optional[str] = None, limit: int = 50):
    """Returns recent agent communication events from the event bus."""
    from agent_bus import bus
    return bus.get_events(session_id=session_id, event_type=event_type, limit=limit)

@app.get("/events/stats", tags=["Events"])
def get_event_stats():
    """Returns summary statistics about the agent event bus."""
    from agent_bus import bus
    return bus.get_stats()

@app.get("/events/sessions", tags=["Events"])
def get_event_sessions():
    """Returns all session IDs that have events."""
    from agent_bus import bus
    return {"sessions": bus.get_all_sessions()}


# --------------------------------------------------
# Tool Monitoring Endpoints
# --------------------------------------------------
@app.get("/tools/stats", tags=["Monitoring"])
def get_tool_stats():
    """Returns per-tool usage statistics: call counts, success rates, avg latency."""
    from tools.registry import tool_registry
    return tool_registry.get_tool_stats()

@app.get("/tools/list", tags=["Monitoring"])
def list_tools():
    """Returns all registered tool names and their descriptions."""
    from tools.registry import tool_registry
    tools = tool_registry.get_all_tools()
    return [
        {
            "name":        t.name,
            "description": t.description,
        }
        for t in tools
    ]


# --------------------------------------------------
# Agent Status Endpoint
# --------------------------------------------------
@app.get("/agents/status", tags=["Monitoring"])
def get_agents_status():
    """Returns the list of active agents and their roles in the pipeline."""
    from agent_bus import bus
    stats = bus.get_stats()
    breakdown = stats.get("event_type_breakdown", {})
    agents = [
        {
            "name":        "planner_agent",
            "role":        "Planner",
            "description": "Breaks down the IT issue into a step-by-step resolution plan",
            "runs":        breakdown.get("plan_ready", 0),
            "order":       1,
        },
        {
            "name":        "researcher_agent",
            "role":        "Researcher",
            "description": "Queries knowledge base, incident DB, and web search for solutions",
            "runs":        breakdown.get("research_complete", 0),
            "order":       2,
        },
        {
            "name":        "analysis_agent",
            "role":        "Analysis",
            "description": "Performs root-cause analysis, severity scoring, and confidence assessment",
            "runs":        breakdown.get("analysis_complete", 0),
            "order":       3,
        },
        {
            "name":        "decision_agent",
            "role":        "Decision",
            "description": "Determines whether to auto-fix or escalate; triggers ticket/email tools",
            "runs":        breakdown.get("decision_complete", 0),
            "order":       4,
        },
        {
            "name":        "executor_agent",
            "role":        "Executor",
            "description": "Synthesizes all outputs into the final professional response",
            "runs":        breakdown.get("workflow_complete", 0),
            "order":       5,
        },
    ]
    return {"agents": agents, "total_workflows": breakdown.get("workflow_finished", 0)}


# --------------------------------------------------
# Entry point
# --------------------------------------------------
if __name__ == "__main__":
    print("\n  AI Agent Coordination & Decision Engine  v2.0")
    print("  -----------------------------------------------")
    print("  Interface  : http://localhost:8000")
    print("  API Docs   : http://localhost:8000/docs")
    print("  Events     : http://localhost:8000/events")
    print("  Memory     : http://localhost:8000/memory")
    print("  Tool Stats : http://localhost:8000/tools/stats")
    print()
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
