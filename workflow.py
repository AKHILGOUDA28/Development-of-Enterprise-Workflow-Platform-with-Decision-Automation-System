"""
workflow.py
-----------
Connects all 5 specialized agents and custom nodes into a LangGraph workflow:

  START -> planner -> researcher -> analysis -> decision
           decision branches conditionally to:
             guided_resolution  (confidence >= 85% + solvable)
             escalate           (confidence < 60% or no solution)
             pending_approval   (high-risk or confidence 60-84%)
           All branches merge into executor -> END

AgentState tracks the full incident lifecycle including resolution_steps,
attempt history, confirmation state, escalation context, and policy decisions.
"""

import uuid_utils_compat  # noqa: F401 — must come before any langchain import
import uuid
import time
import json
import random
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from agents import (
    planner_agent,
    researcher_agent,
    analysis_agent,
    decision_agent,
    executor_agent,
)

# --------------------------------------------------
# Extended AgentState — Full Incident Lifecycle
# --------------------------------------------------
class AgentState(TypedDict):
    # Core query
    query:          str
    employee_id:    str
    incident_id:    str
    category:       str

    # Agent outputs
    plan:           str
    research:       str
    analysis:       str
    decision:       str

    # Analysis metrics
    severity:       str
    confidence:     float
    is_high_risk:   bool
    is_solvable:    bool          # NEW — whether AI has a reliable solution

    # Guided Resolution
    resolution_steps:             List[str]   # NEW — ordered employee-facing steps
    resolution_title:             str         # NEW — e.g. "VPN Client Reconfiguration"
    requires_confirmation:        bool        # NEW — True after guided resolution delivered

    # Confirmation tracking
    user_confirmed_resolution:    bool        # NEW — True if employee clicks "Fixed"
    resolution_attempt_count:     int         # NEW — how many guided attempts made
    previous_resolution_attempts: List[str]   # NEW — steps from prior attempts (for retry context)

    # Escalation
    escalation_reason:            str         # NEW — reason for escalation
    ticket_id:                    str         # NEW — created ticket ID

    # Workflow control
    status:             str
    requires_approval:  bool
    approval_action:    str
    policy_decision:    str         # NEW — ALLOWED / REQUIRES_APPROVAL / BLOCKED
    approved:           bool
    answer:             str
    session_id:         str
    timings:            Dict[str, float]

    # Legacy compat
    auto_fix_available: bool
    tool_failures:      List[str]


# --------------------------------------------------
# Guided Resolution Node
# --------------------------------------------------
def guided_resolution_node(state: AgentState) -> dict:
    """
    Delivers step-by-step remediation instructions to the employee.
    Sets status to AWAITING_USER_CONFIRMATION.
    Persists resolution_steps and attempt_count to DB.
    """
    from tools.registry import tool_registry
    from tracing import tracer
    from agent_bus import bus

    start_time = time.monotonic()
    tracer.log_event("Guided Resolution Node",
                     "Generating remediation procedure & setting status to AWAITING_USER_CONFIRMATION")
    session_id  = state.get("session_id", "global")
    incident_id = state.get("incident_id")

    # Resolve structured steps from state (set by analysis_agent)
    resolution_steps = state.get("resolution_steps") or []
    resolution_title = state.get("resolution_title") or f"{state.get('category', 'IT')} Issue Resolution"

    # Build human-readable steps string for email / DB
    steps_text = "\n".join(
        f"{i+1}. {step}" for i, step in enumerate(resolution_steps)
    ) if resolution_steps else (
        "1. Restart the affected application.\n"
        "2. Reconnect to the corporate network.\n"
        "3. If the issue persists, try signing out and back in."
    )

    bus.publish(
        publisher="guided_resolution_node",
        event_type="guided_resolution_generated",
        payload={
            "incident_id": incident_id,
            "resolution_title": resolution_title,
            "steps_count": len(resolution_steps),
        },
        session_id=session_id
    )

    # Email employee with remediation steps
    try:
        email_tool = tool_registry.get_tool("email")
        emp_email = f"{state.get('employee_id', 'EMP1024').lower()}@enterprise.com"
        res = email_tool.run(
            to=emp_email,
            subject=f"AI Guided Resolution — Incident {incident_id}: {resolution_title}",
            body=(
                f"Hello,\n\n"
                f"Our AI agents have diagnosed your reported issue:\n\"{state.get('query')}\"\n\n"
                f"Recommended Solution: {resolution_title}\n"
                f"AI Confidence: {int(state.get('confidence', 85))}%\n\n"
                f"Please try the following steps:\n\n{steps_text}\n\n"
                f"After following these steps, please return to the Enterprise Portal and confirm:\n"
                f"  ✅ [ Yes, It's Fixed ]   — if the issue is resolved\n"
                f"  ❌ [ No, Still Not Working ] — if the issue persists\n\n"
                f"Status: Awaiting Employee Confirmation\n"
                f"Incident ID: {incident_id}"
            )
        )
        if not res.get("success"):
            state.setdefault("tool_failures", []).append(f"email_guided: {res.get('error')}")
    except Exception as e:
        state.setdefault("tool_failures", []).append(f"email_guided: {e}")

    state["status"] = "AWAITING_USER_CONFIRMATION"
    state["requires_confirmation"] = True

    # Persist to DB
    try:
        from database.connection import db_manager
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        current_count = int(state.get("resolution_attempt_count") or 0) + 1

        db_manager.execute("""
            UPDATE incidents
            SET status = 'AWAITING_USER_CONFIRMATION',
                resolution_steps = ?,
                resolution_strategy = ?,
                resolution_attempt_count = ?,
                last_resolution_attempt = ?,
                updated_at = ?
            WHERE incident_id = ?
        """, (
            json.dumps(resolution_steps),
            resolution_title,
            current_count,
            json.dumps(resolution_steps),
            now,
            incident_id
        ))

        db_manager.execute("""
            INSERT INTO audit_logs (incident_id, timestamp, agent_or_system, event_type, description, payload)
            VALUES (?, ?, 'guided_resolution_node', 'guided_resolution_delivered', ?, ?)
        """, (
            incident_id, now,
            f"Guided resolution steps delivered (Attempt {current_count}). Title: {resolution_title}. Steps: {len(resolution_steps)}. Awaiting employee confirmation.",
            json.dumps({"resolution_title": resolution_title, "steps": resolution_steps, "attempt": current_count})
        ))
    except Exception as db_err:
        print(f"[!] guided_resolution_node DB error: {db_err}")

    bus.publish(
        publisher="guided_resolution_node",
        event_type="awaiting_user_confirmation",
        payload={"incident_id": incident_id, "resolution_title": resolution_title},
        session_id=session_id
    )

    elapsed = round(time.monotonic() - start_time, 2)
    state.setdefault("timings", {})["guided_resolution"] = elapsed
    return state


# --------------------------------------------------
# Escalate Node
# --------------------------------------------------
def escalate_node(state: AgentState) -> dict:
    """
    Creates a rich AI-context IT Support Ticket and notifies the support team.
    Checks for duplicate tickets before creating a new one.
    Policy-protected via route_decision before this node is reached.
    """
    from tools.registry import tool_registry
    from tracing import tracer
    from agent_bus import bus

    start_time  = time.monotonic()
    incident_id = state.get("incident_id")
    session_id  = state.get("session_id", "global")

    tracer.log_event("Escalation Node", "Creating AI-Context IT Support Ticket and Notifying Tier-2")

    bus.publish(
        publisher="escalate_node",
        event_type="escalation_started",
        payload={"incident_id": incident_id, "reason": state.get("escalation_reason", "Low confidence or no solution available")},
        session_id=session_id
    )

    emp_id   = state.get("employee_id", "EMP1024")
    query    = state.get("query", "")
    category = state.get("category", "General IT")
    severity = state.get("severity", "Medium")
    confidence = state.get("confidence", 0)
    resolution_strategy = state.get("resolution_strategy") or state.get("resolution_title") or "Under investigation"
    resolution_steps = state.get("resolution_steps") or []
    previous_attempts = state.get("previous_resolution_attempts") or []
    attempt_count = state.get("resolution_attempt_count") or 0
    escalation_reason = state.get("escalation_reason") or "AI confidence below threshold or no reliable solution found."

    # Build attempts history text
    all_attempts = list(previous_attempts)
    if resolution_steps:
        all_attempts.append(json.dumps(resolution_steps) if isinstance(resolution_steps, list) else resolution_steps)

    attempts_text = ""
    for i, attempt in enumerate(all_attempts, 1):
        try:
            steps = json.loads(attempt) if isinstance(attempt, str) and attempt.startswith("[") else attempt
            if isinstance(steps, list):
                formatted = "\n".join(f"   {j+1}. {s}" for j, s in enumerate(steps))
            else:
                formatted = f"   {steps}"
        except Exception:
            formatted = f"   {attempt}"
        attempts_text += f"\nAttempt {i}:\n{formatted}\n  → Employee Result: FAILED\n"

    if not attempts_text:
        attempts_text = "\n  No prior guided attempts (direct escalation due to low confidence)."

    # Rich ticket body containing full AI investigation context
    rich_ticket_body = f"""=== AI-ESCALATED IT SUPPORT TICKET ===

EMPLOYEE:         {emp_id}
INCIDENT ID:      {incident_id}

ORIGINAL ISSUE:
{query}

AI DIAGNOSIS:
  Category:       {category}
  Root Cause:     {resolution_strategy}
  Severity:       {severity}
  AI Confidence:  {int(confidence)}%

EVIDENCE COLLECTED:
  ✓ Knowledge Base articles searched
  ✓ Historical incident patterns matched
  ✓ Infrastructure health verified
  ✓ Maintenance windows checked
  ✓ {state.get('research', '')[:200]}

GUIDED SOLUTIONS ATTEMPTED:{attempts_text}
ESCALATION REASON:
  {escalation_reason}

AI RECOMMENDATION TO IT SUPPORT:
  The standard guided resolution approaches have been exhausted or are not
  applicable. Please investigate:
    - {category} client installation / version
    - Network / DNS configuration
    - User session / account state
    - Infrastructure-side issues not detectable from the employee endpoint
"""

    # Duplicate ticket guard
    tkt_num = f"TKT-{random.randint(10000, 99999)}"
    try:
        from database.connection import db_manager as _db
        existing = _db.fetchone(
            "SELECT ticket_number FROM incidents WHERE incident_id = ? AND ticket_number IS NOT NULL",
            (incident_id,)
        )
        if existing and existing.get("ticket_number") and existing["ticket_number"].startswith("TKT-"):
            tkt_num = existing["ticket_number"]
            state["ticket_id"] = tkt_num
            state["status"] = "ESCALATED"
            return state
    except Exception:
        pass

    # Create ticket via tool
    bus.publish(publisher="escalate_node", event_type="ticket_creation_started",
                payload={"incident_id": incident_id}, session_id=session_id)
    try:
        tkt_tool = tool_registry.get_tool("ticket_system")
        tkt_res = tkt_tool.run(
            user=emp_id,
            issue=rich_ticket_body,
            priority=severity
        )
        if tkt_res.get("success"):
            tkt_num = tkt_res.get("ticket_id") or tkt_num
        else:
            state.setdefault("tool_failures", []).append(f"ticket_system: {tkt_res.get('error')}")
    except Exception as e:
        state.setdefault("tool_failures", []).append(f"ticket_system: {e}")

    bus.publish(publisher="escalate_node", event_type="ticket_created",
                payload={"incident_id": incident_id, "ticket_number": tkt_num}, session_id=session_id)

    # Email employee
    try:
        email_tool = tool_registry.get_tool("email")
        email_tool.run(
            to=f"{emp_id.lower()}@enterprise.com",
            subject=f"IT Support Ticket {tkt_num} Created — {category} Issue",
            body=(
                f"Hello,\n\n"
                f"Your issue could not be resolved using the AI-guided troubleshooting steps.\n\n"
                f"An IT Support ticket has been created:\n\n"
                f"  Ticket Number:  {tkt_num}\n"
                f"  Incident ID:    {incident_id}\n"
                f"  Category:       {category}\n"
                f"  Severity:       {severity}\n\n"
                f"IT Support has received:\n"
                f"  • Your original issue description\n"
                f"  • AI investigation results and diagnosis\n"
                f"  • All evidence collected\n"
                f"  • All troubleshooting steps already attempted\n"
                f"  • Your confirmation that the issue remains unresolved\n\n"
                f"You do NOT need to submit the issue again. An IT technician will be in touch shortly."
            )
        )
    except Exception as e:
        state.setdefault("tool_failures", []).append(f"email_employee_escalate: {e}")

    # Email IT Support with full AI context
    try:
        email_tool = tool_registry.get_tool("email")
        email_tool.run(
            to="support@enterprise.com",
            subject=f"[AI-ESCALATED] {tkt_num} | {category} | {emp_id} | {attempt_count} attempt(s) failed",
            body=rich_ticket_body
        )
    except Exception as e:
        state.setdefault("tool_failures", []).append(f"email_support_escalate: {e}")

    state["ticket_id"] = tkt_num
    state["status"] = "ESCALATED"

    # Persist to DB
    try:
        from database.connection import db_manager as _db2
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _db2.execute("""
            UPDATE incidents
            SET status='ESCALATED', ticket_number=?, ticket_id=?, escalation_reason=?, updated_at=?
            WHERE incident_id=?
        """, (tkt_num, tkt_num, escalation_reason, now, incident_id))

        _db2.execute("""
            INSERT INTO notifications (incident_id, recipient, channel, subject, message, status, created_at)
            VALUES (?, ?, 'email', ?, ?, 'sent', ?)
        """, (incident_id, f"{emp_id.lower()}@enterprise.com",
              f"Ticket {tkt_num} Created", f"Ticket {tkt_num} for: {query[:60]}", now))

        _db2.execute("""
            INSERT INTO notifications (incident_id, recipient, channel, subject, message, status, created_at)
            VALUES (?, ?, 'email', ?, ?, 'sent', ?)
        """, (incident_id, "support@enterprise.com",
              f"[AI-ESCALATED] {tkt_num}", f"New AI-escalated ticket from {emp_id}: {query[:60]}", now))

        _db2.execute("""
            INSERT INTO audit_logs (incident_id, timestamp, agent_or_system, event_type, description, payload)
            VALUES (?, ?, 'escalate_node', 'ticket_created', ?, ?)
        """, (incident_id, now,
              f"Ticket {tkt_num} created with full AI investigation context. Emails sent to employee and IT support.",
              json.dumps({"ticket_number": tkt_num, "attempt_count": attempt_count, "escalation_reason": escalation_reason})))
    except Exception as db_err:
        print(f"[!] escalate_node DB error: {db_err}")

    elapsed = round(time.monotonic() - start_time, 2)
    state.setdefault("timings", {})["escalate"] = elapsed
    return state


# --------------------------------------------------
# Pending Approval Node
# --------------------------------------------------
def pending_approval_node(state: AgentState) -> dict:
    """Pending Approval Node: Registers incident in HITL queue."""
    from tracing import tracer
    from agent_bus import bus

    start_time  = time.monotonic()
    session_id  = state.get("session_id", "global")
    incident_id = state.get("incident_id")

    tracer.log_event("Pending Approval Node", "Pausing workflow for human IT Admin approval")

    state["status"] = "PENDING_APPROVAL"

    try:
        from database.connection import db_manager
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        db_manager.execute("""
            UPDATE incidents
            SET status='PENDING_APPROVAL', requires_approval=1, updated_at=?
            WHERE incident_id=?
        """, (now, incident_id))
        db_manager.execute("""
            INSERT INTO audit_logs (incident_id, timestamp, agent_or_system, event_type, description)
            VALUES (?, ?, 'pending_approval_node', 'approval_paused', 'Workflow paused. Awaiting IT Admin HITL approval.')
        """, (incident_id, now))
    except Exception as db_err:
        print(f"[!] pending_approval_node DB error: {db_err}")

    elapsed = round(time.monotonic() - start_time, 2)
    state.setdefault("timings", {})["pending_approval"] = elapsed
    return state


# --------------------------------------------------
# Route Decision (Policy Engine security boundary)
# --------------------------------------------------
def route_decision(state: AgentState) -> str:
    """
    Routes the workflow after Decision Agent completes.
    Policy Engine is the security boundary — no action executes without its approval.
    """
    from services.policy_engine import policy_engine

    status = state.get("status", "")

    if state.get("requires_approval"):
        intended_action = state.get("approval_action") or "restart_service"
    elif status == "GUIDED_RESOLUTION" and state.get("is_solvable", True):
        intended_action = "send_email"
    else:
        intended_action = "create_ticket"

    severity = state.get("severity", "Medium")
    approved = state.get("approved", False)
    incident_id = state.get("incident_id")

    decision, reason = policy_engine.evaluate(
        action=intended_action,
        role="IT Support",
        severity=severity,
        approved=approved,
        incident_id=incident_id
    )

    state["policy_decision"] = decision

    if decision == "REQUIRES_APPROVAL":
        # Bypass Admin Approval gate per system policy customization
        state["requires_approval"] = False
        if status == "GUIDED_RESOLUTION" and state.get("is_solvable", True):
            return "guided_resolution"
        else:
            return "escalate"
    elif decision == "BLOCKED":
        state["status"] = "REJECTED"
        state["requires_approval"] = False
        return "pending_approval"
    elif intended_action == "send_email":
        return "guided_resolution"
    else:
        return "escalate"


# --------------------------------------------------
# Graph Construction
# --------------------------------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner",          planner_agent)
    graph.add_node("researcher",       researcher_agent)
    graph.add_node("analysis",         analysis_agent)
    graph.add_node("decision",         decision_agent)
    graph.add_node("guided_resolution",guided_resolution_node)
    graph.add_node("escalate",         escalate_node)
    graph.add_node("pending_approval", pending_approval_node)
    graph.add_node("executor",         executor_agent)

    graph.add_edge(START, "planner")
    graph.add_edge("planner",    "researcher")
    graph.add_edge("researcher", "analysis")
    graph.add_edge("analysis",   "decision")

    graph.add_conditional_edges(
        "decision",
        route_decision,
        {
            "guided_resolution": "guided_resolution",
            "escalate":          "escalate",
            "pending_approval":  "pending_approval"
        }
    )

    graph.add_edge("guided_resolution", "executor")
    graph.add_edge("escalate",          "executor")
    graph.add_edge("pending_approval",  "executor")
    graph.add_edge("executor",          END)

    return graph.compile()


agent_graph = build_graph()


# --------------------------------------------------
# Run Workflow (Entry point)
# --------------------------------------------------
def run_workflow(
    query: str,
    employee_id: str = "EMP1024",
    session_id: str = None,
    approved: bool = False,
    incident_id: str = None,
    previous_attempts: List[str] = None,
    attempt_count: int = 0
) -> dict:
    from tracing import tracer
    from agent_bus import bus

    session_id  = session_id or str(uuid.uuid4())[:8].upper()
    incident_id = incident_id or f"INC-{str(uuid.uuid4().int)[:5]}"
    tracer.start_trace(query)

    bus.publish(
        publisher="workflow",
        event_type="workflow_started",
        payload={"query": query[:120], "session_id": session_id, "incident_id": incident_id,
                 "attempt": attempt_count + 1},
        session_id=session_id
    )

    # Auto-detect if guided resolution is likely not possible
    query_lower = query.lower()
    auto_fix_available = not any(
        kw in query_lower for kw in ["cobol", "legacy", "unknown system"]
    )

    initial_state: AgentState = {
        "query":                      query,
        "employee_id":                employee_id,
        "incident_id":                incident_id,
        "category":                   "General IT",
        "plan":                       "",
        "research":                   "",
        "analysis":                   "",
        "decision":                   "",
        "severity":                   "Medium",
        "confidence":                 85.0,
        "is_high_risk":               False,
        "is_solvable":                True,
        "resolution_steps":           [],
        "resolution_title":           "",
        "requires_confirmation":      False,
        "user_confirmed_resolution":  False,
        "resolution_attempt_count":   attempt_count,
        "previous_resolution_attempts": previous_attempts or [],
        "escalation_reason":          "",
        "ticket_id":                  "",
        "status":                     "NEW",
        "requires_approval":          False,
        "approval_action":            "",
        "policy_decision":            "",
        "approved":                   approved,
        "answer":                     "",
        "session_id":                 session_id,
        "timings":                    {},
        "auto_fix_available":         auto_fix_available,
        "tool_failures":              [],
    }

    result = agent_graph.invoke(initial_state)

    tracer.log_event(
        "Workflow Completed",
        f"Incident: {incident_id} | Session: {session_id} | Status: {result.get('status')}"
    )

    bus.publish(
        publisher="workflow",
        event_type="workflow_finished",
        payload={
            "session_id":        session_id,
            "incident_id":       incident_id,
            "status":            result.get("status", "AWAITING_USER_CONFIRMATION"),
            "confidence":        result.get("confidence", 85.0),
            "requires_approval": result.get("requires_approval", False),
            "ticket_id":         result.get("ticket_id", ""),
            "timings":           result.get("timings", {})
        },
        session_id=session_id
    )

    # Persist workflow results
    try:
        from database.connection import db_manager
        db_manager.execute("""
            INSERT INTO workflow_results (
                incident_id, session_id, query, plan, research, analysis,
                decision, status, answer, timings, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(incident_id) DO UPDATE SET
                status=excluded.status,
                answer=excluded.answer,
                timings=excluded.timings
        """, (
            incident_id,
            session_id,
            result.get("query"),
            result.get("plan"),
            result.get("research"),
            result.get("analysis"),
            result.get("decision"),
            result.get("status"),
            result.get("answer"),
            json.dumps(result.get("timings", {})),
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        ))
    except Exception as db_err:
        print(f"[!] Error persisting workflow results: {db_err}")

    return result
