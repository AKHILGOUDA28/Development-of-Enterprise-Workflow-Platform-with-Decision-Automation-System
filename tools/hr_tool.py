"""
hr_tool.py
----------
Simulated HR System Integration Tool.

Allows agents to look up employee information, department details,
on-call schedules, and manager assignments from a simulated HR database.
"""

from pydantic import BaseModel, Field
from typing import Optional
from tools.base_tool import BaseTool


# ---------------------------------------------------------------------------
# Pydantic Schema
# ---------------------------------------------------------------------------
class HRLookupSchema(BaseModel):
    query: str = Field(..., description="Employee name, ID, or department to look up")
    lookup_type: str = Field(
        default="employee",
        description="Type of lookup: 'employee', 'department', 'oncall', 'manager'"
    )


# ---------------------------------------------------------------------------
# Simulated HR Data Store
# ---------------------------------------------------------------------------
EMPLOYEE_DB = {
    "EMP001": {
        "name": "Alice Johnson",
        "department": "IT Infrastructure",
        "role": "Senior Systems Administrator",
        "email": "alice.johnson@company.com",
        "manager": "EMP005",
        "location": "Floor 3, Building A",
        "status": "Active"
    },
    "EMP002": {
        "name": "Bob Martinez",
        "department": "Network Operations",
        "role": "Network Engineer",
        "email": "bob.martinez@company.com",
        "manager": "EMP006",
        "location": "Floor 2, Building B",
        "status": "Active"
    },
    "EMP003": {
        "name": "Carol Patel",
        "department": "Security Operations",
        "role": "Cybersecurity Analyst",
        "email": "carol.patel@company.com",
        "manager": "EMP007",
        "location": "Floor 5, Building A",
        "status": "Active"
    },
    "EMP004": {
        "name": "David Kim",
        "department": "IT Helpdesk",
        "role": "IT Support Specialist",
        "email": "david.kim@company.com",
        "manager": "EMP005",
        "location": "Floor 1, Building C",
        "status": "Active"
    },
    "EMP005": {
        "name": "Elena Torres",
        "department": "IT Infrastructure",
        "role": "IT Infrastructure Manager",
        "email": "elena.torres@company.com",
        "manager": "EMP008",
        "location": "Floor 3, Building A",
        "status": "Active"
    },
}

DEPARTMENT_DB = {
    "IT Infrastructure": {
        "head": "Elena Torres",
        "members": 12,
        "location": "Floor 3, Building A",
        "responsibilities": "Server management, cloud infrastructure, storage, backups",
        "escalation_email": "it-infra@company.com"
    },
    "Network Operations": {
        "head": "Frank Lee",
        "members": 8,
        "location": "Floor 2, Building B",
        "responsibilities": "LAN/WAN, VPN, firewall, network monitoring",
        "escalation_email": "netops@company.com"
    },
    "Security Operations": {
        "head": "Grace Nguyen",
        "members": 6,
        "location": "Floor 5, Building A",
        "responsibilities": "Threat monitoring, vulnerability assessment, incident response",
        "escalation_email": "security@company.com"
    },
    "IT Helpdesk": {
        "head": "Henry Brown",
        "members": 15,
        "location": "Floor 1, Building C",
        "responsibilities": "Level 1 & 2 support, ticketing, user onboarding",
        "escalation_email": "helpdesk@company.com"
    },
}

ONCALL_SCHEDULE = {
    "IT Infrastructure": {"oncall": "Alice Johnson", "backup": "EMP004", "phone": "+1-555-0101"},
    "Network Operations": {"oncall": "Bob Martinez", "backup": "EMP003", "phone": "+1-555-0102"},
    "Security Operations": {"oncall": "Carol Patel", "backup": "EMP002", "phone": "+1-555-0103"},
    "IT Helpdesk": {"oncall": "David Kim", "backup": "EMP001", "phone": "+1-555-0104"},
}


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------
class HRTool(BaseTool):
    name = "hr_system"
    description = (
        "Looks up employee information, department details, on-call schedules, "
        "and manager assignments from the enterprise HR system."
    )
    args_schema = HRLookupSchema

    def _execute(self, query: str, lookup_type: str = "employee") -> str:
        query_lower = query.lower().strip()

        if lookup_type == "employee":
            # Search by ID or name
            for emp_id, emp in EMPLOYEE_DB.items():
                if query_lower in emp["name"].lower() or query_lower == emp_id.lower():
                    return (
                        f"Employee Record:\n"
                        f"  ID: {emp_id}\n"
                        f"  Name: {emp['name']}\n"
                        f"  Role: {emp['role']}\n"
                        f"  Department: {emp['department']}\n"
                        f"  Email: {emp['email']}\n"
                        f"  Location: {emp['location']}\n"
                        f"  Status: {emp['status']}"
                    )
            return f"No employee found matching '{query}'."

        elif lookup_type == "department":
            for dept_name, dept in DEPARTMENT_DB.items():
                if query_lower in dept_name.lower():
                    return (
                        f"Department: {dept_name}\n"
                        f"  Head: {dept['head']}\n"
                        f"  Members: {dept['members']}\n"
                        f"  Location: {dept['location']}\n"
                        f"  Responsibilities: {dept['responsibilities']}\n"
                        f"  Escalation Email: {dept['escalation_email']}"
                    )
            return f"No department found matching '{query}'."

        elif lookup_type == "oncall":
            for dept_name, oncall in ONCALL_SCHEDULE.items():
                if query_lower in dept_name.lower():
                    return (
                        f"On-Call Schedule for {dept_name}:\n"
                        f"  Current On-Call: {oncall['oncall']}\n"
                        f"  Backup: {oncall['backup']}\n"
                        f"  Contact Phone: {oncall['phone']}"
                    )
            return f"No on-call schedule found for '{query}'."

        elif lookup_type == "manager":
            for emp_id, emp in EMPLOYEE_DB.items():
                if query_lower in emp["name"].lower() or query_lower == emp_id.lower():
                    mgr_id = emp.get("manager", "")
                    mgr = EMPLOYEE_DB.get(mgr_id, {})
                    if mgr:
                        return (
                            f"Manager for {emp['name']}:\n"
                            f"  Name: {mgr['name']}\n"
                            f"  Role: {mgr['role']}\n"
                            f"  Email: {mgr['email']}"
                        )
                    return f"Manager not found for '{query}'."
            return f"No employee found matching '{query}'."

        return f"Unknown lookup type '{lookup_type}'. Use: employee, department, oncall, or manager."


# Singleton instance
hr_tool = HRTool()
