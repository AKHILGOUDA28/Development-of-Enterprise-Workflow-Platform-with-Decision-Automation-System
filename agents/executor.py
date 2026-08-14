"""
executor.py
-----------
Executor Agent - Synthesizes all multi-agent findings into a final enterprise IT response.
"""

import time
import config
from prompts import executor_prompt
from tracing import tracer
from agent_bus import bus

def get_mock_answer(state: dict) -> str:
    inc_id = state.get("incident_id", "INC-1025")
    status = state.get("status", "AUTO-RESOLUTION")
    query = state.get("query", "")
    conf = int(state.get("confidence", 85.0))
    requires_app = state.get("requires_approval", False)

    if requires_app:
        status_banner = "⚠ PENDING IT ADMIN APPROVAL"
        sol_body = f"This request involves elevated IT permissions or security policy override. Incident {inc_id} has been submitted to the IT Admin Approval Queue."
    elif status == "AUTO-RESOLUTION":
        status_banner = "✓ RESOLVED (AUTO-FIX)"
        sol_body = f"Automated self-healing completed for incident {inc_id} (Confidence: {conf}%). Remediation steps applied."
    else:
        status_banner = "⚡ ESCALATED TO IT TICKET"
        sol_body = f"Incident {inc_id} has been escalated to Tier-2 IT Support for technician review."

    return f"""Answer:
The AI IT Incident Triage Engine processed query: "{query}"
Status: {status_banner} | Incident ID: {inc_id}

Solution:
{sol_body}

Steps to Implement:
1. Verify system connectivity and network adapter status.
2. Check email inbox for incident update confirmation.
3. If issue persists, reply to ticket {inc_id} or contact IT Helpdesk.

Conclusion:
Multi-agent pipeline completed (Planner → Researcher → Analysis → Decision → Executor) with {conf}% decision confidence."""

def executor_agent(state: dict) -> dict:
    start_time = time.monotonic()
    tracer.log_event("Executor Agent", "Generating Final Response")
    session_id = state.get("session_id", "global")

    bus.publish(
        publisher="executor_agent",
        event_type="response_generation_started",
        payload={"query": state.get("query", "")[:120]},
        session_id=session_id
    )

    if config.IS_MOCK or not config.llm:
        answer = get_mock_answer(state)
        state["answer"] = answer
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["executor"] = elapsed
        bus.publish(
            publisher="executor_agent",
            event_type="workflow_complete",
            payload={"mode": "mock", "elapsed_s": elapsed},
            session_id=session_id
        )
        return state

    try:
        chain = executor_prompt | config.llm
        result = chain.invoke({
            "query": state["query"],
            "plan": state["plan"],
            "research": state["research"],
            "analysis": state.get("analysis", ""),
            "decision": state["decision"],
        })
        state["answer"] = result.content
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["executor"] = elapsed

        bus.publish(
            publisher="executor_agent",
            event_type="workflow_complete",
            payload={"mode": "llm", "answer_length": len(result.content), "elapsed_s": elapsed},
            session_id=session_id
        )
    except Exception as e:
        print(f"Error in executor_agent: {e}")
        answer = get_mock_answer(state)
        state["answer"] = answer
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["executor"] = elapsed

    return state
