"""
planner.py
----------
Planner Agent - breaks down the user's IT issue into an executable resolution plan.
Tracks timing for dashboard observability.
"""

import time
import config
from prompts import planner_prompt
from tracing import tracer
from agent_bus import bus

def get_mock_plan(query: str) -> str:
    return f"""Goal: Resolve IT Incident for: "{query}"

Execution Plan:
1. Scope & Categorization: Classify issue into domain (Network, Hardware, Security, Software).
2. Historical & KB Retrieval: Query Knowledge Base and Incident DB for matching resolution paths.
3. Root Cause Analysis: Evaluate pattern correlation, impact severity, and resolution confidence.
4. Decision & Remediation: Route to Auto-Fix (Confidence >= 85%), Human Approval (60-84%), or Ticket Escalation (<60%)."""

def planner_agent(state: dict) -> dict:
    start_time = time.monotonic()
    tracer.log_event("Planner Agent", "Generating Resolution Plan")
    session_id = state.get("session_id", "global")

    bus.publish(
        publisher="planner_agent",
        event_type="plan_started",
        payload={"query": state.get("query", "")[:120]},
        session_id=session_id
    )

    if config.IS_MOCK or not config.llm:
        plan = get_mock_plan(state["query"])
        state["plan"] = plan
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["planner"] = elapsed
        bus.publish(
            publisher="planner_agent",
            event_type="plan_ready",
            payload={"mode": "mock", "elapsed_s": elapsed},
            session_id=session_id
        )
        return state

    try:
        chain = planner_prompt | config.llm
        result = chain.invoke({"query": state["query"]})
        state["plan"] = result.content
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["planner"] = elapsed
        bus.publish(
            publisher="planner_agent",
            event_type="plan_ready",
            payload={"mode": "llm", "plan_length": len(result.content), "elapsed_s": elapsed},
            session_id=session_id
        )
    except Exception as e:
        print(f"Error in planner_agent: {e}")
        state["plan"] = get_mock_plan(state["query"])
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["planner"] = elapsed
        bus.publish(
            publisher="planner_agent",
            event_type="agent_error",
            payload={"error": str(e)},
            session_id=session_id
        )

    return state
