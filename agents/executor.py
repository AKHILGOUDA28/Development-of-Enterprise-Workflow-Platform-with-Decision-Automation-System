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
        steps_text = "1. Your request is queued for IT Admin review.\n2. You will be notified automatically once approved."
    elif status in ("AUTO-RESOLUTION", "RESOLVED"):
        status_banner = "✓ RESOLVED (AUTO-FIX — NO TICKET NEEDED)"
        sol_body = (
            f"Your issue was automatically resolved by our AI agents & self-healing tools! "
            f"Because a complete solution was automatically applied, NO support ticket was raised."
        )
        steps_text = (
            "1. Follow the provided automated remediation procedure.\n"
            "2. Verify system connectivity or test the application.\n"
            "3. If the issue is fixed, no further action is required."
        )
    else:
        status_banner = "⚡ ESCALATED (ISSUE UNSOLVABLE VIA AUTOMATION — TICKET RAISED)"
        sol_body = (
            f"This issue could not be resolved automatically (requires physical repair, replacement, or manual technician intervention). "
            f"Support Ticket TKT-{inc_id[-4:]} has been raised and assigned to Tier-2 IT Support."
        )
        steps_text = (
            "1. An IT Support Technician has been notified with Ticket ID TKT-" + str(inc_id[-4:]) + ".\n"
            "2. Check your email for ticket confirmation and updates.\n"
            "3. A technician will contact you directly."
        )

    return f"""Answer:
The AI IT Incident Triage Engine processed query: "{query}"
Status: {status_banner} | Incident ID: {inc_id}

Solution:
{sol_body}

Steps to Implement:
{steps_text}

Conclusion:
Multi-agent pipeline (Planner → Researcher → Analysis → Decision → Executor) processed the issue with {conf}% confidence."""

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
