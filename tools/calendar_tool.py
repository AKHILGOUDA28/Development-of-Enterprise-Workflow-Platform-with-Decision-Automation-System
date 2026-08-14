"""
calendar_tool.py
----------------
Simulated Enterprise Calendar & Scheduling Tool.

Allows agents to check maintenance windows, schedule work orders,
find available time slots, and verify blackout periods.
"""

from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool


# ---------------------------------------------------------------------------
# Pydantic Schema
# ---------------------------------------------------------------------------
class CalendarQuerySchema(BaseModel):
    query: str = Field(..., description="Resource name, team, or date to query")
    action: str = Field(
        default="check_availability",
        description=(
            "Action to perform: 'check_availability', 'maintenance_windows', "
            "'schedule_work', 'blackout_dates'"
        )
    )


# ---------------------------------------------------------------------------
# Simulated Calendar Data
# ---------------------------------------------------------------------------
MAINTENANCE_WINDOWS = [
    {
        "id": "MW-2026-08-10",
        "title": "Network Core Switch Patching",
        "team": "Network Operations",
        "start": "2026-08-10 02:00",
        "end": "2026-08-10 05:00",
        "impact": "VPN and remote access downtime expected",
        "approved": True
    },
    {
        "id": "MW-2026-08-15",
        "title": "Active Directory Domain Controller Upgrade",
        "team": "IT Infrastructure",
        "start": "2026-08-15 01:00",
        "end": "2026-08-15 04:00",
        "impact": "User authentication disruption during window",
        "approved": True
    },
    {
        "id": "MW-2026-08-22",
        "title": "Firewall Rule Set Update",
        "team": "Security Operations",
        "start": "2026-08-22 22:00",
        "end": "2026-08-22 23:30",
        "impact": "Brief internet connectivity interruption",
        "approved": False
    },
]

BLACKOUT_DATES = [
    {"date": "2026-08-15", "reason": "Company All-Hands Meeting — no major changes allowed"},
    {"date": "2026-08-31", "reason": "Quarter End — financial systems freeze"},
    {"date": "2026-12-24", "reason": "Holiday Blackout Period"},
    {"date": "2026-12-25", "reason": "Holiday Blackout Period"},
]

AVAILABILITY_SLOTS = {
    "IT Infrastructure": [
        "Mon–Fri: 09:00–17:00 (business hours support)",
        "Emergency after-hours: +1-555-0101",
        "Next available maintenance window: 2026-08-10 02:00–05:00"
    ],
    "Network Operations": [
        "24/7 on-call rotation active",
        "Scheduled work: Tue/Thu 08:00–12:00",
        "Next available slot: 2026-08-07 08:00"
    ],
    "Security Operations": [
        "24/7 SOC monitoring",
        "Scheduled reviews: Mon 10:00–12:00",
        "Next available slot: 2026-08-11 10:00"
    ],
}


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------
class CalendarTool(BaseTool):
    name = "calendar_system"
    description = (
        "Checks maintenance windows, schedules work orders, finds team availability, "
        "and verifies blackout dates from the enterprise calendar system."
    )
    args_schema = CalendarQuerySchema

    def _execute(self, query: str, action: str = "check_availability") -> str:
        query_lower = query.lower().strip()

        if action == "maintenance_windows":
            # Filter by team or show all
            relevant = [
                mw for mw in MAINTENANCE_WINDOWS
                if query_lower in mw["team"].lower() or query_lower in mw["title"].lower()
                or query_lower == "all"
            ]
            if not relevant:
                relevant = MAINTENANCE_WINDOWS  # show all if no match
            lines = ["Upcoming Maintenance Windows:"]
            for mw in relevant:
                approved = "✓ Approved" if mw["approved"] else "⚠ Pending Approval"
                lines.append(
                    f"\n  [{mw['id']}] {mw['title']}\n"
                    f"    Team: {mw['team']}\n"
                    f"    Window: {mw['start']} → {mw['end']}\n"
                    f"    Impact: {mw['impact']}\n"
                    f"    Status: {approved}"
                )
            return "\n".join(lines)

        elif action == "blackout_dates":
            lines = ["Blackout Dates (no changes allowed):"]
            for bd in BLACKOUT_DATES:
                lines.append(f"  • {bd['date']}: {bd['reason']}")
            return "\n".join(lines)

        elif action == "check_availability":
            for team, slots in AVAILABILITY_SLOTS.items():
                if query_lower in team.lower():
                    lines = [f"Availability — {team}:"]
                    for slot in slots:
                        lines.append(f"  • {slot}")
                    return "\n".join(lines)
            return (
                f"Team '{query}' not found. Known teams: "
                + ", ".join(AVAILABILITY_SLOTS.keys())
            )

        elif action == "schedule_work":
            # Find next available date that is not a blackout date
            now = datetime.now()
            blackout_dates = {bd["date"] for bd in BLACKOUT_DATES}
            days_ahead = 2
            proposed_time = now + timedelta(days=days_ahead)
            while proposed_time.strftime("%Y-%m-%d") in blackout_dates and days_ahead < 30:
                days_ahead += 1
                proposed_time = now + timedelta(days=days_ahead)

            proposed_str = proposed_time.strftime("%Y-%m-%d 02:00")
            return (
                f"Work Order Scheduled:\n"
                f"  Task: {query}\n"
                f"  Proposed Time: {proposed_str}\n"
                f"  Status: Pending Manager Approval\n"
                f"  Reference ID: WO-{now.strftime('%Y%m%d%H%M')}"
            )


        return (
            f"Unknown action '{action}'. Use: "
            "check_availability, maintenance_windows, blackout_dates, schedule_work."
        )


# Singleton instance
calendar_tool = CalendarTool()
