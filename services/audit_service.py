"""
audit_service.py
----------------
Centralized audit logging service for the AI IT Incident Platform.

Provides a single, consistent interface for recording all system events:
  - Agent lifecycle events (started, completed, errors)
  - Tool executions (name, args, result, latency)
  - Policy decisions (allowed, blocked, requires_approval)
  - User actions (status updates, HITL approvals/rejections)
  - System events (workflow started/completed, notifications sent)

All other modules should use this service instead of writing audit log
inserts directly, ensuring consistent format and centralized control.
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Optional


class AuditService:
    """Centralized audit logger that writes to the audit_logs DB table."""

    def _write(
        self,
        incident_id: str,
        agent_or_system: str,
        event_type: str,
        description: str,
        payload: Optional[dict] = None,
    ) -> bool:
        """Internal write method with error isolation."""
        try:
            from database.connection import db_manager
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            db_manager.execute(
                "INSERT INTO audit_logs "
                "(incident_id, timestamp, agent_or_system, event_type, description, payload) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    incident_id or "SYSTEM",
                    now,
                    agent_or_system,
                    event_type,
                    description,
                    json.dumps(payload) if payload else None,
                )
            )
            return True
        except Exception as e:
            print(f"[AuditService] Warning: Failed to write audit log: {e}")
            return False

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------
    def log_agent_start(self, incident_id: str, agent_name: str, context: dict = None) -> bool:
        return self._write(
            incident_id=incident_id,
            agent_or_system=agent_name,
            event_type="agent_started",
            description=f"{agent_name.replace('_', ' ').title()} started processing incident.",
            payload=context,
        )

    def log_agent_complete(self, incident_id: str, agent_name: str, elapsed_s: float, result_summary: str = "", context: dict = None) -> bool:
        payload = {"elapsed_s": elapsed_s, **(context or {})}
        return self._write(
            incident_id=incident_id,
            agent_or_system=agent_name,
            event_type="agent_completed",
            description=f"{agent_name.replace('_', ' ').title()} completed in {elapsed_s:.2f}s. {result_summary}",
            payload=payload,
        )

    def log_agent_error(self, incident_id: str, agent_name: str, error: str, context: dict = None) -> bool:
        payload = {"error": error, **(context or {})}
        return self._write(
            incident_id=incident_id,
            agent_or_system=agent_name,
            event_type="agent_error",
            description=f"{agent_name.replace('_', ' ').title()} encountered an error: {error[:200]}",
            payload=payload,
        )

    # ------------------------------------------------------------------
    # Tool executions
    # ------------------------------------------------------------------
    def log_tool_call(
        self,
        incident_id: str,
        tool_name: str,
        args: dict,
        result: Any,
        success: bool,
        latency_ms: float,
        error: str = None,
    ) -> bool:
        """Log tool execution to both audit_logs and tool_executions tables."""
        # Write to audit_logs
        status = "SUCCESS" if success else "FAILED"
        self._write(
            incident_id=incident_id,
            agent_or_system=tool_name,
            event_type="tool_execution",
            description=f"Tool '{tool_name}' executed — {status} in {latency_ms:.0f}ms.",
            payload={"args": args, "success": success, "latency_ms": latency_ms, "error": error},
        )
        # Write to tool_executions table for monitoring dashboard
        try:
            from database.connection import db_manager
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            db_manager.execute(
                "INSERT INTO tool_executions (tool_name, success, error, latency_ms, args, result, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    tool_name,
                    1 if success else 0,
                    error,
                    latency_ms,
                    json.dumps(args)[:500],
                    str(result)[:500] if result else None,
                    now,
                )
            )
        except Exception as e:
            print(f"[AuditService] Warning: Could not write tool_executions: {e}")
        return success

    # ------------------------------------------------------------------
    # Workflow events
    # ------------------------------------------------------------------
    def log_workflow_started(self, incident_id: str, query: str, employee_id: str, session_id: str) -> bool:
        return self._write(
            incident_id=incident_id,
            agent_or_system="workflow",
            event_type="workflow_started",
            description=f"AI Triage Workflow started for incident {incident_id}.",
            payload={"query": query[:200], "employee_id": employee_id, "session_id": session_id},
        )

    def log_workflow_completed(self, incident_id: str, status: str, timings: dict, session_id: str) -> bool:
        total_time = sum(timings.values()) if timings else 0
        return self._write(
            incident_id=incident_id,
            agent_or_system="workflow",
            event_type="workflow_completed",
            description=f"Workflow completed for {incident_id}. Final status: {status}. Total time: {total_time:.2f}s.",
            payload={"status": status, "timings": timings, "session_id": session_id},
        )

    # ------------------------------------------------------------------
    # Decision & HITL events
    # ------------------------------------------------------------------
    def log_decision(
        self,
        incident_id: str,
        decision: str,
        severity: str,
        confidence: float,
        requires_approval: bool,
        reason: str,
    ) -> bool:
        return self._write(
            incident_id=incident_id,
            agent_or_system="decision_agent",
            event_type="lifecycle_decision",
            description=f"Decision: {decision}. Severity: {severity}. Confidence: {confidence:.1f}%. Approval required: {requires_approval}.",
            payload={"decision": decision, "severity": severity, "confidence": confidence, "reason": reason},
        )

    def log_hitl_approval(self, incident_id: str, approved_by: str, notes: str) -> bool:
        return self._write(
            incident_id=incident_id,
            agent_or_system="hitl_system",
            event_type="hitl_approved",
            description=f"Human-in-the-Loop action APPROVED by {approved_by}.",
            payload={"approved_by": approved_by, "notes": notes},
        )

    def log_hitl_rejection(self, incident_id: str, rejected_by: str, notes: str) -> bool:
        return self._write(
            incident_id=incident_id,
            agent_or_system="hitl_system",
            event_type="hitl_rejected",
            description=f"Human-in-the-Loop action REJECTED by {rejected_by}.",
            payload={"rejected_by": rejected_by, "notes": notes},
        )

    # ------------------------------------------------------------------
    # User actions
    # ------------------------------------------------------------------
    def log_user_action(self, incident_id: str, user: str, action: str, details: str = "", metadata: dict = None) -> bool:
        return self._write(
            incident_id=incident_id,
            agent_or_system=user,
            event_type="user_action",
            description=f"User '{user}' performed action: {action}. {details}",
            payload=metadata,
        )

    # ------------------------------------------------------------------
    # System / notification events
    # ------------------------------------------------------------------
    def log_notification(self, incident_id: str, channel: str, recipient: str, status: str) -> bool:
        return self._write(
            incident_id=incident_id,
            agent_or_system="notification_service",
            event_type="notification_sent",
            description=f"Notification sent via {channel} to {recipient}. Status: {status}.",
            payload={"channel": channel, "recipient": recipient, "status": status},
        )

    def log_policy_event(self, incident_id: str, action: str, decision: str, reason: str) -> bool:
        return self._write(
            incident_id=incident_id,
            agent_or_system="policy_engine",
            event_type=f"policy_{decision.lower()}",
            description=f"Policy evaluation for '{action}': {decision}. {reason[:200]}",
            payload={"action": action, "decision": decision, "reason": reason},
        )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def get_incident_trail(self, incident_id: str) -> list:
        """Retrieve the complete audit trail for a single incident."""
        try:
            from database.connection import db_manager
            return db_manager.fetchall(
                "SELECT * FROM audit_logs WHERE incident_id = ? ORDER BY id ASC",
                (incident_id,)
            )
        except Exception as e:
            print(f"[AuditService] Error fetching trail for {incident_id}: {e}")
            return []

    def get_recent_logs(self, limit: int = 100, event_type: str = None, agent: str = None) -> list:
        """Fetch recent audit logs with optional filtering."""
        try:
            from database.connection import db_manager
            query = "SELECT * FROM audit_logs"
            params = []
            conditions = []
            if event_type:
                conditions.append("event_type = ?")
                params.append(event_type)
            if agent:
                conditions.append("agent_or_system = ?")
                params.append(agent)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)
            return db_manager.fetchall(query, tuple(params))
        except Exception as e:
            print(f"[AuditService] Error fetching recent logs: {e}")
            return []

    def get_tool_execution_stats(self) -> dict:
        """Return tool execution statistics grouped by tool_name."""
        try:
            from database.connection import db_manager
            rows = db_manager.fetchall(
                "SELECT tool_name, "
                "COUNT(*) as total, "
                "SUM(success) as successes, "
                "AVG(latency_ms) as avg_latency_ms, "
                "MAX(latency_ms) as max_latency_ms "
                "FROM tool_executions "
                "GROUP BY tool_name ORDER BY total DESC"
            )
            result = {}
            for r in rows:
                tn = r["tool_name"]
                total = r["total"] or 1
                result[tn] = {
                    "total_calls": total,
                    "successes": r["successes"] or 0,
                    "failures": total - (r["successes"] or 0),
                    "success_rate": round((r["successes"] or 0) / total * 100, 1),
                    "avg_latency_ms": round(r["avg_latency_ms"] or 0, 1),
                    "max_latency_ms": round(r["max_latency_ms"] or 0, 1),
                }
            return result
        except Exception as e:
            print(f"[AuditService] Error fetching tool stats: {e}")
            return {}


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
audit_service = AuditService()
