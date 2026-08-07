"""
workflow.py
-----------
Connects all five agents into a proper LangGraph workflow.

Flow:
  START → planner → researcher → analysis → decision → executor → END

The shared state is a plain dict with these keys:
  query     - the user's question (input)
  plan      - filled by planner_agent
  research  - filled by researcher_agent
  analysis  - filled by analysis_agent (NEW)
  decision  - filled by decision_agent
  answer    - filled by executor_agent (final output)
  session_id - optional session identifier for event bus routing

Usage:
  from workflow import run_workflow
  result = run_workflow("My VPN stopped working after the Windows update.")
"""

import uuid
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agents import (
    planner_agent,
    researcher_agent,
    analysis_agent,
    decision_agent,
    executor_agent,
)


# --------------------------------------------------
# Shared state structure
# --------------------------------------------------
class AgentState(TypedDict):
    query:      str
    plan:       str
    research:   str
    analysis:   str      # NEW — root-cause analysis output
    decision:   str
    answer:     str
    session_id: str      # NEW — used for event bus routing


# --------------------------------------------------
# Build the LangGraph workflow
# --------------------------------------------------
def build_graph():
    """Creates and compiles the 5-agent state graph."""
    graph = StateGraph(AgentState)

    # Add each agent as a node
    graph.add_node("planner",    planner_agent)
    graph.add_node("researcher", researcher_agent)
    graph.add_node("analysis",   analysis_agent)   # NEW
    graph.add_node("decision",   decision_agent)
    graph.add_node("executor",   executor_agent)

    # Connect the nodes in sequence
    graph.add_edge(START,        "planner")
    graph.add_edge("planner",    "researcher")
    graph.add_edge("researcher", "analysis")   # NEW edge
    graph.add_edge("analysis",   "decision")   # updated from researcher → decision
    graph.add_edge("decision",   "executor")
    graph.add_edge("executor",   END)

    return graph.compile()


# Compile once when this file is imported
agent_graph = build_graph()


# --------------------------------------------------
# Main function to run the full pipeline
# --------------------------------------------------
def run_workflow(query: str, session_id: str = None) -> dict:
    """
    Runs the full 5-agent pipeline for a given query.

    Returns a dict with:
      query, plan, research, analysis, decision, answer, session_id
    """
    from tracing import tracer
    from agent_bus import bus

    session_id = session_id or str(uuid.uuid4())[:8].upper()
    tracer.start_trace(query)

    bus.publish(
        publisher  = "workflow",
        event_type = "workflow_started",
        payload    = {"query": query[:120], "session_id": session_id},
        session_id = session_id
    )

    initial_state: AgentState = {
        "query":      query,
        "plan":       "",
        "research":   "",
        "analysis":   "",
        "decision":   "",
        "answer":     "",
        "session_id": session_id,
    }

    result = agent_graph.invoke(initial_state)

    tracer.log_event(
        "Workflow Completed",
        f"Session: {session_id} | Answer length: {len(result.get('answer', ''))}"
    )

    bus.publish(
        publisher  = "workflow",
        event_type = "workflow_finished",
        payload    = {
            "session_id":     session_id,
            "answer_length":  len(result.get("answer", "")),
            "analysis_found": bool(result.get("analysis", "").strip()),
        },
        session_id = session_id
    )

    return result
