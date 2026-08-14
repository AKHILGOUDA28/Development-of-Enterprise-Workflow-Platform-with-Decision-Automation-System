"""
decision.py
-----------
Decision Agent - Evaluates confidence scores & risk level to determine IT Incident Lifecycle action:
  - Confidence >= 85%: AUTO-RESOLUTION (Auto-Fix)
  - Confidence 60–84% OR High-Risk Action: PENDING_APPROVAL (Human-in-the-Loop required)
  - Confidence < 60%: ESCALATION (Create Ticket & Escalate)

Executes tools natively (`bind_tools` & `AIMessage.tool_calls`).
"""

import time
import uuid
import os
import config
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from tools.registry import tool_registry
from tracing import tracer
from agent_bus import bus

# Use unified db_manager (supports both SQLite and PostgreSQL)
from database.connection import db_manager as _db

def record_incident_in_db(state: dict, status: str, action: str, reason: str, requires_approval: bool):
    inc_id = state.get("incident_id") or f"INC-{str(uuid.uuid4().int)[:5]}"
    state["incident_id"] = inc_id

    emp_id    = state.get("employee_id", "EMP1024")
    query     = state.get("query", "")
    category  = state.get("category", "General IT")
    severity  = state.get("severity", "Medium")
    confidence = float(state.get("confidence", 85.0))
    priority  = "High" if severity in ("High", "Critical") else "Medium" if severity == "Medium" else "Low"

    try:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        _db.execute("""
            INSERT INTO incidents (
                incident_id, incident_number, employee_id, employee_name, issue,
                category, priority, severity, confidence,
                status, assigned_to, assigned_team, resolution_strategy,
                requires_approval, approval_action, approval_reason, approval_status,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(incident_id) DO UPDATE SET
                status=excluded.status,
                confidence=excluded.confidence,
                requires_approval=excluded.requires_approval,
                approval_status=excluded.approval_status,
                updated_at=excluded.updated_at
        """, (
            inc_id, inc_id, emp_id, "Employee", query,
            category, priority, severity, confidence,
            status,
            "IT Auto-Bot" if status == "AUTO-RESOLUTION" else "IT Support",
            "Network Team" if "network" in category.lower() else "IT Team",
            action,
            1 if requires_approval else 0,
            action if requires_approval else None,
            reason if requires_approval else None,
            "PENDING" if requires_approval else "N/A",
            now, now
        ))

        # Log to audit_logs
        _db.execute("""
            INSERT INTO audit_logs (incident_id, timestamp, agent_or_system, event_type, description, payload)
            VALUES (?,?,'decision_agent','lifecycle_transition',?,?)
        """, (inc_id, now, f"Status set to {status}. Rationale: {reason}", action))

    except Exception as err:
        print(f"Error persisting incident to DB: {err}")

def get_mock_decision(state: dict) -> dict:
    conf = float(state.get("confidence", 87.0))
    is_high_risk = state.get("is_high_risk", False)
    query = state.get("query", "")

    if is_high_risk or (60.0 <= conf < 85.0):
        status = "PENDING_APPROVAL"
        action = f"Human Approval Required: High-risk enterprise action for '{query[:40]}'"
        reason = f"Confidence is {int(conf)}% or requires elevated IT Admin privilege."
        requires_app = True
    elif conf >= 85.0:
        status = "AUTO-RESOLUTION"
        action = "AUTO-FIX"
        reason = f"Confidence ({int(conf)}%) exceeds 85% auto-resolution threshold."
        requires_app = False
    else:
        status = "ESCALATION"
        action = "ESCALATE_TO_IT"
        reason = f"Confidence ({int(conf)}%) is below 60% threshold. Creating support ticket."
        requires_app = False

    text = f"""Decision Lifecycle Summary:
- Incident Status: {status}
- Decision Strategy: {action}
- Confidence Score: {int(conf)}%
- Rationale: {reason}

Actions Taken:
{"- Paused in Approval Queue for IT Admin review." if requires_app else ("- Applied automated resolution path." if status == "AUTO-RESOLUTION" else "- Created incident escalation ticket.")}"""

    return {
        "text": text,
        "status": status,
        "action": action,
        "reason": reason,
        "requires_approval": requires_app
    }

def decision_agent(state: dict) -> dict:
    start_time = time.monotonic()
    tracer.log_event("Decision Agent", "Evaluating IT Incident Lifecycle & Decision Rules")
    session_id = state.get("session_id", "global")

    bus.publish(
        publisher="decision_agent",
        event_type="decision_started",
        payload={"query": state.get("query", "")[:120]},
        session_id=session_id
    )

    conf = float(state.get("confidence", 85.0))
    is_high_risk = state.get("is_high_risk", False)

    # Determine Lifecycle Status based on Confidence & Risk Rules
    if state.get("approved"):
        lifecycle_status = "AUTO-RESOLUTION"
        decision_action = "AUTO-FIX"
        decision_reason = "IT Admin approval granted. Initiating automated remediation."
        requires_approval = False
    elif is_high_risk or (60.0 <= conf < 85.0):
        lifecycle_status = "PENDING_APPROVAL"
        decision_action = "REQUIRE_APPROVAL"
        decision_reason = f"Action involves high-risk privileges or confidence ({int(conf)}%) requires human verification."
        requires_approval = True
    elif conf >= 85.0:
        lifecycle_status = "AUTO-RESOLUTION"
        decision_action = "AUTO-FIX"
        decision_reason = f"High confidence ({int(conf)}%) allows automated self-healing."
        requires_approval = False
    else:
        lifecycle_status = "ESCALATION"
        decision_action = "CREATE_TICKET_ESCALATE"
        decision_reason = f"Low confidence ({int(conf)}%) requires tier-2 IT escalation."
        requires_approval = False

    record_incident_in_db(state, lifecycle_status, decision_action, decision_reason, requires_approval)

    state["status"] = lifecycle_status
    state["requires_approval"] = requires_approval
    state["approval_action"] = decision_action if requires_approval else None

    if config.IS_MOCK or not config.llm:
        dec_res = get_mock_decision(state)
        state["decision"] = dec_res["text"]
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["decision"] = elapsed
        bus.publish(
            publisher="decision_agent",
            event_type="decision_complete",
            payload={"status": lifecycle_status, "requires_approval": requires_approval, "elapsed_s": elapsed},
            session_id=session_id
        )
        return state

    try:
        # Native Tool Calling for Decision Execution (Ticket creation, Email notification)
        lc_tools = tool_registry.get_langchain_tools()
        llm_with_tools = config.llm.bind_tools(lc_tools)

        sys_prompt = SystemMessage(content=(
            "You are an IT Support Decision Agent.\n"
            f"The Incident Status is determined as: {lifecycle_status}.\n"
            "If status is ESCALATION, invoke `ticket_system` tool to create a ticket and `email` to inform the user.\n"
            "If status is AUTO-RESOLUTION, invoke `email` tool to send remediation steps.\n"
            "If status is PENDING_APPROVAL, issue notification to approval queue."
        ))

        user_content = (
            f"Query: {state['query']}\n"
            f"Analysis: {state.get('analysis', '')}\n"
            f"Confidence: {conf}%\n"
            f"Lifecycle Decision: {lifecycle_status}"
        )

        messages = [sys_prompt, HumanMessage(content=user_content)]

        max_iterations = 3
        current_iter = 0
        final_decision_text = ""

        while current_iter < max_iterations:
            current_iter += 1
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if getattr(response, "tool_calls", None) and len(response.tool_calls) > 0:
                for tool_call in response.tool_calls:
                    t_name = tool_call["name"]
                    t_args = tool_call["args"]
                    t_id = tool_call.get("id", f"call_dec_{current_iter}")

                    tracer.log_event("Native Tool Call (Decision)", f"Tool: {t_name}, Args: {t_args}")
                    bus.publish(
                        publisher="decision_agent",
                        event_type="tool_called",
                        payload={"tool_name": t_name, "args": t_args},
                        session_id=session_id
                    )

                    try:
                        tool_monitored = tool_registry.get_tool(t_name)
                        tool_res = tool_monitored.run(**t_args)
                        t_output = str(tool_res["result"]) if tool_res["success"] else f"Error: {tool_res['error']}"
                    except Exception as err:
                        t_output = f"Tool execution failed: {err}"

                    messages.append(ToolMessage(content=t_output, tool_call_id=t_id))
            else:
                final_decision_text = response.content.strip()
                break

        if not final_decision_text:
            final_decision_text = f"Decision Strategy: {decision_action}\nStatus: {lifecycle_status}\nRationale: {decision_reason}"

        state["decision"] = final_decision_text
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["decision"] = elapsed

        bus.publish(
            publisher="decision_agent",
            event_type="decision_complete",
            payload={"status": lifecycle_status, "requires_approval": requires_approval, "elapsed_s": elapsed},
            session_id=session_id
        )

    except Exception as e:
        print(f"Error in decision_agent: {e}")
        dec_res = get_mock_decision(state)
        state["decision"] = dec_res["text"]
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["decision"] = elapsed

    return state
