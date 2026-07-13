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
        result = run_workflow(request.query)
        run_mode = "Demo/Simulation Mode" if config.IS_MOCK else "Real-time LLM Output"
        return AgentResponse(
            success  = True,
            query    = result["query"],
            plan     = result["plan"],
            research = result["research"],
            decision = result["decision"],
            answer   = result["answer"],
            mode     = run_mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# --------------------------------------------------
# Entry point
# --------------------------------------------------
if __name__ == "__main__":
    print("\n  AI Agent Coordination & Decision Engine")
    print("  ----------------------------------------")
    print("  Interface : http://localhost:8000")
    print()
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

