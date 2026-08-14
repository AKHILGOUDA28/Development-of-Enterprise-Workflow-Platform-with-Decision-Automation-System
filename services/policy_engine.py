"""
policy_engine.py
----------------
Enterprise Policy Engine for the AI IT Incident Platform.

Sits between the Decision Agent and actual tool execution to enforce:
  - Auto-allowed actions (email, notification, ticket creation)
  - Conditionally-allowed actions (low-risk configuration changes)
  - Human-approval-required actions (account disable, data deletion)
  - Fully blocked actions (critical infrastructure without change approval)

Architecture:
    LLM Decision
         ↓
    Policy Engine (this module)
         ↓
    Permission Check (role + severity + action type)
         ↓
    ALLOWED → Execute tool
    REQUIRES_APPROVAL → Queue for HITL
    BLOCKED → Log and reject
"""

import json
import time
from datetime import datetime, timezone
from typing import Tuple
from enum import Enum


class PolicyDecision(str, Enum):
    ALLOWED = "ALLOWED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    BLOCKED = "BLOCKED"


# ---------------------------------------------------------------------------
# Policy Rule Table
# ---------------------------------------------------------------------------
# Format: (action_key, description, decision, requires_roles, notes)
POLICY_RULES = {
    # ── Auto-Allowed Actions (no human gate) ───────────────────────────────
    "send_email": PolicyDecision.ALLOWED,
    "send_notification": PolicyDecision.ALLOWED,
    "create_ticket": PolicyDecision.ALLOWED,
    "search_knowledge_base": PolicyDecision.ALLOWED,
    "search_incidents": PolicyDecision.ALLOWED,
    "lookup_employee": PolicyDecision.ALLOWED,
    "check_calendar": PolicyDecision.ALLOWED,
    "web_search": PolicyDecision.ALLOWED,
    "check_infrastructure": PolicyDecision.ALLOWED,
    "view_audit_log": PolicyDecision.ALLOWED,

    # ── Conditionally Allowed (allowed for IT Support / Admin, not Employee) ─
    "update_ticket": PolicyDecision.ALLOWED,
    "assign_incident": PolicyDecision.ALLOWED,
    "close_ticket": PolicyDecision.ALLOWED,
    "run_diagnostic": PolicyDecision.ALLOWED,
    "restart_service": PolicyDecision.REQUIRES_APPROVAL,
    "change_network_config": PolicyDecision.REQUIRES_APPROVAL,
    "reset_user_password": PolicyDecision.REQUIRES_APPROVAL,
    "unlock_account": PolicyDecision.ALLOWED,                   # low-risk

    # ── Requires Human Approval ────────────────────────────────────────────
    "disable_user_account": PolicyDecision.REQUIRES_APPROVAL,
    "enable_user_account": PolicyDecision.REQUIRES_APPROVAL,
    "revoke_vpn_access": PolicyDecision.REQUIRES_APPROVAL,
    "grant_admin_rights": PolicyDecision.REQUIRES_APPROVAL,
    "revoke_admin_rights": PolicyDecision.REQUIRES_APPROVAL,
    "install_software_bulk": PolicyDecision.REQUIRES_APPROVAL,
    "firewall_rule_change": PolicyDecision.REQUIRES_APPROVAL,
    "create_service_account": PolicyDecision.REQUIRES_APPROVAL,
    "bulk_email": PolicyDecision.REQUIRES_APPROVAL,

    # ── Always Blocked (require separate change management process) ─────────
    "delete_user_data": PolicyDecision.BLOCKED,
    "delete_account": PolicyDecision.BLOCKED,
    "modify_production_database": PolicyDecision.BLOCKED,
    "shutdown_production_server": PolicyDecision.BLOCKED,
    "disable_security_monitoring": PolicyDecision.BLOCKED,
    "export_all_user_data": PolicyDecision.BLOCKED,
    "modify_audit_logs": PolicyDecision.BLOCKED,
    "bypass_mfa": PolicyDecision.BLOCKED,
}

# Actions that always require approval for Critical/High severity incidents
HIGH_SEVERITY_REQUIRES_APPROVAL = {
    "send_email",
    "create_ticket",
    "restart_service",
}

# Role-based action restrictions
ROLE_RESTRICTIONS = {
    "Employee": {
        "blocked": {
            "disable_user_account", "enable_user_account", "revoke_vpn_access",
            "grant_admin_rights", "revoke_admin_rights", "install_software_bulk",
            "firewall_rule_change", "create_service_account", "bulk_email",
            "restart_service", "change_network_config", "reset_user_password",
            "assign_incident", "update_ticket", "close_ticket",
        }
    },
    "IT Support": {
        "blocked": {
            "delete_user_data", "delete_account", "modify_production_database",
            "shutdown_production_server", "disable_security_monitoring",
            "export_all_user_data", "modify_audit_logs", "bypass_mfa",
        }
    },
    "Admin": {
        "blocked": {
            # Even admins can't bypass the fully-blocked list
            "modify_audit_logs", "bypass_mfa",
        }
    },
}


class PolicyEngine:
    """
    Evaluate whether a proposed action is allowed given:
      - The action type (tool/action name)
      - The actor's role (Employee, IT Support, Admin)
      - The incident severity (Low, Medium, High, Critical)
      - Whether human approval has been granted
    """

    def evaluate(
        self,
        action: str,
        role: str = "IT Support",
        severity: str = "Medium",
        approved: bool = False,
        incident_id: str = None,
    ) -> Tuple[PolicyDecision, str]:
        """
        Returns: (PolicyDecision, reason_string)
        """
        action_lower = action.lower().replace(" ", "_").replace("-", "_")

        # 1. Check if action is in the policy table
        base_decision = POLICY_RULES.get(action_lower, PolicyDecision.REQUIRES_APPROVAL)

        # 2. Check role-based restrictions
        role_block_set = ROLE_RESTRICTIONS.get(role, {}).get("blocked", set())
        if action_lower in role_block_set:
            return (
                PolicyDecision.BLOCKED,
                f"Action '{action}' is not permitted for role '{role}'."
            )

        # 3. Fully-blocked actions cannot proceed under any circumstance
        if base_decision == PolicyDecision.BLOCKED:
            reason = (
                f"Action '{action}' is permanently blocked by enterprise policy. "
                "A formal change management request must be submitted."
            )
            self._log_policy_decision(action, PolicyDecision.BLOCKED, reason, severity, role, incident_id)
            return PolicyDecision.BLOCKED, reason

        # 4. High-severity incidents escalate some auto-allowed actions
        if severity in ("High", "Critical") and action_lower in HIGH_SEVERITY_REQUIRES_APPROVAL:
            if not approved:
                reason = (
                    f"Action '{action}' normally auto-allowed, but severity is '{severity}'. "
                    "Human approval required before execution on Critical/High incidents."
                )
                self._log_policy_decision(action, PolicyDecision.REQUIRES_APPROVAL, reason, severity, role, incident_id)
                return PolicyDecision.REQUIRES_APPROVAL, reason

        # 5. Actions requiring approval — check if approved
        if base_decision == PolicyDecision.REQUIRES_APPROVAL:
            if approved:
                reason = f"Action '{action}' requires approval — human approval has been granted. Proceeding."
                self._log_policy_decision(action, PolicyDecision.ALLOWED, reason, severity, role, incident_id)
                return PolicyDecision.ALLOWED, reason
            else:
                reason = (
                    f"Action '{action}' requires human approval per enterprise policy. "
                    "Incident has been queued in HITL approval queue."
                )
                self._log_policy_decision(action, PolicyDecision.REQUIRES_APPROVAL, reason, severity, role, incident_id)
                return PolicyDecision.REQUIRES_APPROVAL, reason

        # 6. Allowed action
        reason = f"Action '{action}' is permitted by enterprise policy for role '{role}'."
        self._log_policy_decision(action, PolicyDecision.ALLOWED, reason, severity, role, incident_id)
        return PolicyDecision.ALLOWED, reason

    def get_policy_table(self) -> list:
        """Return the full policy table for display in dashboard."""
        rows = []
        for action, decision in POLICY_RULES.items():
            rows.append({
                "action": action.replace("_", " ").title(),
                "action_key": action,
                "decision": decision,
                "notes": self._get_notes(action, decision),
            })
        return rows

    def _get_notes(self, action: str, decision: PolicyDecision) -> str:
        notes_map = {
            PolicyDecision.ALLOWED: "Auto-executed without human gate",
            PolicyDecision.REQUIRES_APPROVAL: "Queued in HITL approval queue. IT Admin or IT Support must approve.",
            PolicyDecision.BLOCKED: "Permanently blocked. Requires formal change management.",
        }
        return notes_map.get(decision, "")

    def _log_policy_decision(self, action: str, decision: PolicyDecision, reason: str, severity: str, role: str, incident_id: str):
        """Log policy decisions to the audit table."""
        try:
            from database.connection import db_manager
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            db_manager.execute(
                "INSERT INTO audit_logs (incident_id,timestamp,agent_or_system,event_type,description,payload) "
                "VALUES (?,?,?,?,?,?)",
                (
                    incident_id or "SYSTEM",
                    now,
                    "policy_engine",
                    f"policy_{decision.lower()}",
                    f"Policy check for '{action}': {decision}",
                    json.dumps({
                        "action": action,
                        "decision": decision,
                        "severity": severity,
                        "role": role,
                        "reason": reason,
                    })
                )
            )
        except Exception as e:
            print(f"[PolicyEngine] Warning: Could not log decision to DB: {e}")


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
policy_engine = PolicyEngine()


if __name__ == "__main__":
    # Quick smoke test
    test_cases = [
        ("send_email", "IT Support", "Medium", False),
        ("disable_user_account", "IT Support", "High", False),
        ("disable_user_account", "IT Support", "High", True),
        ("delete_user_data", "Admin", "Low", True),
        ("bypass_mfa", "Admin", "Low", True),
        ("create_ticket", "Employee", "Low", False),
        ("grant_admin_rights", "Employee", "Low", False),
    ]

    print("\n── Policy Engine Test ──────────────────────────────────")
    for action, role, severity, approved in test_cases:
        decision, reason = policy_engine.evaluate(action, role, severity, approved)
        print(f"  [{decision:>20}] {action:<30} role={role}, sev={severity}, approved={approved}")
        print(f"                           → {reason[:80]}")
    print("────────────────────────────────────────────────────────\n")
