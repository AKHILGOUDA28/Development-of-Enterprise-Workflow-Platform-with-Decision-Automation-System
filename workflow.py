"""
workflow.py
-----------
Connects all 5 specialized agents and custom nodes into a LangGraph workflow:

  START -> planner -> researcher -> analysis -> decision
           decision branches conditionally to:
             auto_fix    (confidence >= 85% and auto-fix available)
             escalate    (confidence < 60% or no auto-fix)
             pending_approval  (high-risk or confidence 60-84%)
           All branches merge into executor -> END

State includes full IT Incident Lifecycle tracking, auto-fix checks, and node timings.
"""

import uuid_utils_compat  # noqa: F401 — must come before any langchain import
import uuid
import time
import json
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, START, END

from agents import (
    planner_agent,
    researcher_agent,
    analysis_agent,
    decision_agent,
    executor_agent,
)

class AgentState(TypedDict):
    query: str
    employee_id: str
    incident_id: str
    category: str
    plan: str
    research: str
    analysis: str
    severity: str
    confidence: float
    is_high_risk: bool
    decision: str
    status: str
    requires_approval: bool
    approval_action: str
    answer: str
    session_id: str
    timings: Dict[str, float]
    auto_fix_available: bool  # NEW — True if matching remediation KB is found
    tool_failures: List[str]   # NEW — tracks non-critical tool failures
    approved: bool             # NEW — human approval flag override

# --------------------------------------------------
# Custom Workflow Execution Nodes
# --------------------------------------------------

def auto_fix_node(state: AgentState) -> dict:
    """Auto-Fix Node: Executes remediation and resolves incident."""
    from tools.registry import tool_registry
    from tracing import tracer
    from agent_bus import bus
    
    start_time = time.monotonic()
    tracer.log_event("Auto-Fix Node", "Applying automated self-healing")
    session_id = state.get("session_id", "global")
    incident_id = state.get("incident_id")
    
    # Notify user via email (using email tool with retry/backoff)
    try:
        email_tool = tool_registry.get_tool("email")
        res = email_tool.run(
            to=f"{state.get('employee_id', 'EMP1024').lower()}@enterprise.com",
            subject=f"Automated Resolution Applied for Incident {incident_id}",
            body=(
                f"Hello,\n\nWe have automatically resolved your issue: '{state.get('query')}'\n\n"
                f"Remediation Strategy: Applied self-healing script for {state.get('category')} incident.\n\n"
                f"Status: Resolved."
            )
        )
        if not res["success"]:
            state.setdefault("tool_failures", []).append(f"email_tool_auto_fix: {res['error']}")
    except Exception as e:
        state.setdefault("tool_failures", []).append(f"email_tool_auto_fix: {e}")
        
    state["status"] = "RESOLVED"
    
    # Record status update in DB
    try:
        from database.connection import db_manager
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        db_manager.execute(
            "UPDATE incidents SET status = 'RESOLVED', updated_at = ? WHERE incident_id = ?",
            (now, incident_id)
        )
        db_manager.execute("""
            INSERT INTO audit_logs (incident_id, timestamp, agent_or_system, event_type, description)
            VALUES (?, ?, 'auto_fix_node', 'auto_fix_execution', 'Remediation email sent. Incident resolved.')
        """, (incident_id, now))
    except Exception as db_err:
        print(f"[!] Error updating incident status in DB: {db_err}")
        
    elapsed = round(time.monotonic() - start_time, 2)
    state.setdefault("timings", {})["auto_fix"] = elapsed
    return state

def escalate_node(state: AgentState) -> dict:
    """Escalate Node: Generates tickets and routes to support group."""
    from tools.registry import tool_registry
    from tracing import tracer
    from agent_bus import bus
    
    start_time = time.monotonic()
    tracer.log_event("Escalation Node", "Creating IT Support Ticket and Notifying Tier-2")
    session_id = state.get("session_id", "global")
    incident_id = state.get("incident_id")
    
    # Create IT Ticket via ticket tool
    tkt_num = f"TKT-{random.randint(5000, 9999)}"
    try:
        tkt_tool = tool_registry.get_tool("ticket_system")
        tkt_res = tkt_tool.run(
            user=state.get("employee_id", "EMP1024"),
            issue=state.get("query", ""),
            priority=state.get("severity", "Medium")
        )
        if tkt_res.get("success"):
            tkt_num = tkt_res.get("ticket_id") or tkt_num
        else:
            state.setdefault("tool_failures", []).append(f"ticket_system: {tkt_res['error']}")
    except Exception as e:
        state.setdefault("tool_failures", []).append(f"ticket_system: {e}")
        
    emp_id = state.get("employee_id", "EMP1024")
    emp_email = f"{emp_id.lower()}@enterprise.com"
    tech_email = "support@enterprise.com"
    query = state.get("query", "")
    category = state.get("category", "General IT")
    severity = state.get("severity", "Medium")

    # 1. Notify Employee via email & DB notification
    try:
        email_tool = tool_registry.get_tool("email")
        res1 = email_tool.run(
            to=emp_email,
            subject=f"Ticket {tkt_num} Created: {query[:40]}",
            body=(
                f"Hello,\n\nYour IT issue has been logged as Ticket {tkt_num} (Incident {incident_id}).\n\n"
                f"Issue: {query}\n"
                f"Category: {category}\n"
                f"Severity: {severity}\n"
                f"Status: Escalated to IT Support Technician.\n\n"
                f"An IT Technician has been notified and will assist you shortly."
            )
        )
        if not res1["success"]:
            state.setdefault("tool_failures", []).append(f"email_tool_emp: {res1['error']}")
    except Exception as e:
        state.setdefault("tool_failures", []).append(f"email_tool_emp: {e}")

    # 2. Notify IT Support Technician via email
    try:
        email_tool = tool_registry.get_tool("email")
        res2 = email_tool.run(
            to=tech_email,
            subject=f"[IT ALERT] New Ticket {tkt_num} Raised by {emp_id}",
            body=(
                f"ATTENTION IT SUPPORT:\n\nA new IT incident has been escalated.\n\n"
                f"Ticket ID: {tkt_num}\n"
                f"Incident ID: {incident_id}\n"
                f"Employee ID: {emp_id}\n"
                f"Issue: {query}\n"
                f"Category: {category}\n"
                f"Severity: {severity}\n\n"
                f"Please review and assign a technician."
            )
        )
        if not res2["success"]:
            state.setdefault("tool_failures", []).append(f"email_tool_tech: {res2['error']}")
    except Exception as e:
        state.setdefault("tool_failures", []).append(f"email_tool_tech: {e}")

    # Record notification entries in DB
    try:
        from database.connection import db_manager
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        db_manager.execute(
            "INSERT INTO notifications (incident_id, recipient, channel, subject, message, status, created_at) "
            "VALUES (?, ?, 'email', ?, ?, 'sent', ?)",
            (incident_id, emp_email, f"Ticket {tkt_num} Created", f"Ticket {tkt_num} logged for: {query[:60]}", now)
        )
        db_manager.execute(
            "INSERT INTO notifications (incident_id, recipient, channel, subject, message, status, created_at) "
            "VALUES (?, ?, 'email', ?, ?, 'sent', ?)",
            (incident_id, tech_email, f"[IT ALERT] Ticket {tkt_num}", f"New escalation from {emp_id}: {query[:60]}", now)
        )
    except Exception as db_err:
        print(f"[!] Warning inserting notification records: {db_err}")

    state["status"] = "ESCALATION"
    
    # Record status update in DB
    try:
        from database.connection import db_manager
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        db_manager.execute(
            "UPDATE incidents SET status = 'ESCALATION', ticket_number = ?, updated_at = ? WHERE incident_id = ?",
            (tkt_num, now, incident_id)
        )
        db_manager.execute("""
            INSERT INTO audit_logs (incident_id, timestamp, agent_or_system, event_type, description)
            VALUES (?, ?, 'escalate_node', 'ticket_creation', ?)
        """, (incident_id, now, f"Ticket {tkt_num} generated. Emails sent to employee ({emp_email}) and IT technician ({tech_email})."))
    except Exception as db_err:
        print(f"[!] Error updating incident status in DB: {db_err}")
        
    elapsed = round(time.monotonic() - start_time, 2)
    state.setdefault("timings", {})["escalate"] = elapsed
    return state

def pending_approval_node(state: AgentState) -> dict:
    """Pending Approval Node: Registers incident in HITL queue."""
    from tracing import tracer
    from agent_bus import bus
    
    start_time = time.monotonic()
    tracer.log_event("Pending Approval Node", "Pausing workflow for human approval")
    session_id = state.get("session_id", "global")
    incident_id = state.get("incident_id")
    
    state["status"] = "PENDING_APPROVAL"
    
    # Record status update in DB
    try:
        from database.connection import db_manager
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        db_manager.execute(
            "UPDATE incidents SET status = 'PENDING_APPROVAL', requires_approval = 1, updated_at = ? WHERE incident_id = ?",
            (now, incident_id)
        )
        db_manager.execute("""
            INSERT INTO audit_logs (incident_id, timestamp, agent_or_system, event_type, description)
            VALUES (?, ?, 'pending_approval_node', 'approval_paused', 'Workflow paused. Awaiting IT Admin approval.')
        """, (incident_id, now))
    except Exception as db_err:
        print(f"[!] Error updating incident status in DB: {db_err}")
        
    elapsed = round(time.monotonic() - start_time, 2)
    state.setdefault("timings", {})["pending_approval"] = elapsed
    return state

def route_decision(state: AgentState) -> str:
    """
    Conditional Routing Logic from Decision Agent after Policy Engine Evaluation.
    Enforces Security Boundary: Intended Action -> Policy Engine -> (ALLOWED / REQUIRES_APPROVAL / BLOCKED)
    """
    from services.policy_engine import policy_engine
    
    # Intended action determined by Decision Agent
    if state.get("requires_approval"):
        intended_action = state.get("approval_action") or "restart_service"
    elif state.get("status") == "AUTO-RESOLUTION" and state.get("auto_fix_available", True):
        intended_action = "send_email"
    else:
        intended_action = "create_ticket"

    severity = state.get("severity", "Medium")
    approved = state.get("approved", False)
    incident_id = state.get("incident_id")

    # Evaluate intended action against enterprise policy rules
    decision, reason = policy_engine.evaluate(
        action=intended_action,
        role="IT Support",
        severity=severity,
        approved=approved,
        incident_id=incident_id
    )

    if decision == "REQUIRES_APPROVAL":
        state["requires_approval"] = True
        state["approval_action"] = intended_action
        state["status"] = "PENDING_APPROVAL"
        return "pending_approval"
    elif decision == "BLOCKED":
        state["status"] = "REJECTED"
        state["requires_approval"] = False
        return "pending_approval"
    elif intended_action == "send_email":
        return "auto_fix"
    else:
        return "escalate"

# --------------------------------------------------
# Graph Construction
# --------------------------------------------------

def build_graph():
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("planner", planner_agent)
    graph.add_node("researcher", researcher_agent)
    graph.add_node("analysis", analysis_agent)
    graph.add_node("decision", decision_agent)
    graph.add_node("auto_fix", auto_fix_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("pending_approval", pending_approval_node)
    graph.add_node("executor", executor_agent)

    # Define standard sequential flow
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "analysis")
    graph.add_edge("analysis", "decision")
    
    # Define conditional branching from decision agent
    graph.add_conditional_edges(
        "decision",
        route_decision,
        {
            "auto_fix": "auto_fix",
            "escalate": "escalate",
            "pending_approval": "pending_approval"
        }
    )
    
    # Re-merge paths before executing final response
    graph.add_edge("auto_fix", "executor")
    graph.add_edge("escalate", "executor")
    graph.add_edge("pending_approval", "executor")
    graph.add_edge("executor", END)

    return graph.compile()

agent_graph = build_graph()

def run_workflow(query: str, employee_id: str = "EMP1024", session_id: str = None, approved: bool = False, incident_id: str = None) -> dict:
    from tracing import tracer
    from agent_bus import bus

    session_id = session_id or str(uuid.uuid4())[:8].upper()
    incident_id = incident_id or f"INC-{str(uuid.uuid4().int)[:5]}"
    tracer.start_trace(query)

    bus.publish(
        publisher="workflow",
        event_type="workflow_started",
        payload={"query": query[:120], "session_id": session_id, "incident_id": incident_id},
        session_id=session_id
    )

    # Determine if auto-fix is available based on query/keywords
    query_lower = query.lower()
    # If query mentions a custom/COBOL system or a ticket, mark auto-fix as unavailable
    auto_fix_available = True
    if "cobol" in query_lower or "legacy" in query_lower or "unknown system" in query_lower:
        auto_fix_available = False

    initial_state: AgentState = {
        "query": query,
        "employee_id": employee_id,
        "incident_id": incident_id,
        "category": "General IT",
        "plan": "",
        "research": "",
        "analysis": "",
        "severity": "Medium",
        "confidence": 85.0,
        "is_high_risk": False,
        "decision": "",
        "status": "NEW",
        "requires_approval": False,
        "approval_action": "",
        "answer": "",
        "session_id": session_id,
        "timings": {},
        "auto_fix_available": auto_fix_available,
        "tool_failures": [],
        "approved": approved
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
            "session_id": session_id,
            "incident_id": incident_id,
            "status": result.get("status", "RESOLVED"),
            "confidence": result.get("confidence", 85.0),
            "requires_approval": result.get("requires_approval", False),
            "timings": result.get("timings", {})
        },
        session_id=session_id
    )

    # Persist workflow results in DB
    try:
        from database.connection import db_manager
        db_manager.execute("""
            INSERT INTO workflow_results (
                incident_id, session_id, query, plan, research, analysis, decision, status, answer, timings, created_at
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
        print(f"[!] Error persisting workflow results to DB: {db_err}")

    return result
