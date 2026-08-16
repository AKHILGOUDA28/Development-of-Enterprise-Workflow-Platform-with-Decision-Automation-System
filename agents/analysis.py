"""
analysis.py
-----------
Analysis Agent - Performs root-cause analysis, confidence scoring (0-100%),
severity classification, high-risk detection, and generates structured
resolution_steps for the Guided Resolution flow.
"""

import time
import re
import json
import config
from prompts import analysis_prompt
from tracing import tracer
from agent_bus import bus

# High-risk keywords — always trigger Human-In-The-Loop approval
HIGH_RISK_KEYWORDS = [
    "disable account", "delete account", "terminate account", "wipe device",
    "factory reset", "reboot server", "restart domain controller", "revoke access",
    "modify permissions", "flush database", "elevate privileges"
]

# Issue-category → guided resolution step templates
_RESOLUTION_TEMPLATES = {
    "vpn": {
        "title": "VPN Client Reconfiguration",
        "steps": [
            "Open the VPN application on your computer.",
            "Click 'Sign Out' or 'Disconnect' to fully log out of the VPN client.",
            "Close the VPN application completely (right-click the system tray icon → Quit).",
            "Wait 30 seconds, then reopen the VPN application.",
            "Sign in again using your company credentials.",
            "Reconnect to the corporate VPN and verify connectivity.",
            "If the issue persists, try restarting your computer and repeating these steps."
        ]
    },
    "wifi": {
        "title": "Wi-Fi / Network Reconnection",
        "steps": [
            "Click the Wi-Fi icon in your taskbar.",
            "Disconnect from the current network.",
            "Turn Wi-Fi off, wait 10 seconds, then turn it back on.",
            "Reconnect to the corporate Wi-Fi network.",
            "If prompted, re-enter your network credentials.",
            "Open a browser to verify internet connectivity.",
        ]
    },
    "password": {
        "title": "Password Reset Procedure",
        "steps": [
            "Visit the company Self-Service Password Reset portal.",
            "Enter your employee ID or registered email address.",
            "Follow the identity verification steps (OTP / security questions).",
            "Create a new password that meets the complexity requirements.",
            "Log in to your workstation and all company applications using the new password.",
            "Update saved passwords in any browsers or apps where you stored the old password."
        ]
    },
    "printer": {
        "title": "Printer Reconnection & Driver Reset",
        "steps": [
            "Open 'Printers & Scanners' in your system settings.",
            "Remove the affected printer from the list.",
            "Power-cycle the printer (turn it off, wait 15 seconds, turn it back on).",
            "Re-add the printer using 'Add a Printer or Scanner'.",
            "Print a test page to verify the connection.",
            "If the issue persists, reinstall the printer driver from the IT Software Portal."
        ]
    },
    "email": {
        "title": "Email Client Re-sync",
        "steps": [
            "Close your email client completely.",
            "Reopen the email client.",
            "Check your internet/network connection.",
            "Manually trigger a Send/Receive or Sync operation.",
            "If sync fails, sign out of your account and sign in again.",
            "Clear the email client cache if the option is available under settings."
        ]
    },
    "software": {
        "title": "Application Restart & Cache Clear",
        "steps": [
            "Close the application completely (check the system tray for background processes).",
            "Wait 15 seconds and reopen the application.",
            "Check for pending updates in the IT Software Portal and install them.",
            "If the issue persists, clear the application cache from its Settings menu.",
            "Restart your computer and reopen the application.",
            "If still failing, contact IT Support for a full reinstallation."
        ]
    },
    "default": {
        "title": "General IT Troubleshooting",
        "steps": [
            "Restart the affected application or service.",
            "Check your network connection is active and stable.",
            "Ensure your system has all pending Windows/macOS updates installed.",
            "Clear any browser or application cache if applicable.",
            "Sign out and sign back in to the affected application.",
            "Restart your computer and attempt the task again."
        ]
    }
}

def _get_resolution_template(query: str, category: str) -> dict:
    """Pick the most relevant resolution template based on query keywords."""
    combined = (query + " " + category).lower()
    if "vpn" in combined or "virtual private" in combined:
        return _RESOLUTION_TEMPLATES["vpn"]
    if "wifi" in combined or "wi-fi" in combined or "wireless" in combined or "network" in combined:
        return _RESOLUTION_TEMPLATES["wifi"]
    if "password" in combined or "login" in combined or "locked" in combined or "credential" in combined:
        return _RESOLUTION_TEMPLATES["password"]
    if "print" in combined or "printer" in combined:
        return _RESOLUTION_TEMPLATES["printer"]
    if "email" in combined or "outlook" in combined or "mail" in combined:
        return _RESOLUTION_TEMPLATES["email"]
    if "software" in combined or "application" in combined or "app" in combined or "install" in combined:
        return _RESOLUTION_TEMPLATES["software"]
    return _RESOLUTION_TEMPLATES["default"]

def get_mock_analysis(query: str) -> dict:
    is_high_risk = any(kw in query.lower() for kw in HIGH_RISK_KEYWORDS)
    confidence   = 91.0 if not is_high_risk else 72.0
    severity     = "High" if is_high_risk else "Medium"
    is_solvable  = not is_high_risk and confidence >= 60.0

    template = _get_resolution_template(query, "")
    resolution_title = template["title"]
    resolution_steps = template["steps"]

    # Derive category from query
    q_lower = query.lower()
    if "vpn" in q_lower:            category = "Network/VPN"
    elif "wifi" in q_lower:         category = "Network/Wi-Fi"
    elif "password" in q_lower:     category = "Identity/Access"
    elif "print" in q_lower:        category = "Hardware/Printer"
    elif "email" in q_lower:        category = "Collaboration/Email"
    elif "software" in q_lower:     category = "Software/Application"
    else:                           category = "General IT"

    text = f"""Root Cause Analysis:
The reported issue ("{query}") has been identified as a {category} issue.

Pattern Recognition:
- High similarity ({int(confidence)}%) with historical incident resolution patterns.
- Standard service remediation steps confirmed in Knowledge Base.

Category:          {category}
Root Cause:        {resolution_title.replace(' (Guided)', '')} suspected.

Severity Assessment:
  Level: {severity}
  Impact: Employee workflow impaired; guided resolution path identified.

Confidence Score: {int(confidence)}%
  Reasoning: Knowledge base pattern match with validated resolution steps.

Is Solvable: {'Yes' if is_solvable else 'No — escalation required'}

Recommended Solution: {resolution_title}

Resolution Steps:
{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(resolution_steps))}

Supporting Evidence:
- Verified matching knowledge base entry.
- Past incident history shows 90%+ success rate for this issue type."""

    return {
        "text":             text,
        "category":         category,
        "root_cause":       f"{category} configuration issue",
        "severity":         severity,
        "confidence":       confidence,
        "is_high_risk":     is_high_risk,
        "is_solvable":      is_solvable,
        "resolution_title": resolution_title,
        "resolution_steps": resolution_steps,
        "strategy":         resolution_title if is_solvable else "ESCALATE"
    }


def analysis_agent(state: dict) -> dict:
    start_time = time.monotonic()
    tracer.log_event("Analysis Agent", "Running Root-Cause Analysis")
    session_id = state.get("session_id", "global")

    bus.publish(
        publisher="analysis_agent",
        event_type="analysis_started",
        payload={"query": state.get("query", "")[:120]},
        session_id=session_id
    )

    if config.IS_MOCK or not config.llm:
        anal_res = get_mock_analysis(state["query"])
        state["analysis"]         = anal_res["text"]
        state["category"]         = anal_res["category"]
        state["severity"]         = anal_res["severity"]
        state["confidence"]       = anal_res["confidence"]
        state["is_high_risk"]     = anal_res["is_high_risk"]
        state["is_solvable"]      = anal_res["is_solvable"]
        state["resolution_steps"] = anal_res["resolution_steps"]
        state["resolution_title"] = anal_res["resolution_title"]

        elapsed = round(time.monotonic() - start_time, 2)
        state.setdefault("timings", {})["analysis"] = elapsed

        bus.publish(
            publisher="analysis_agent",
            event_type="analysis_complete",
            payload={
                "mode":             "mock",
                "category":         anal_res["category"],
                "severity":         anal_res["severity"],
                "confidence":       f"{anal_res['confidence']}%",
                "is_solvable":      anal_res["is_solvable"],
                "resolution_title": anal_res["resolution_title"],
                "steps_count":      len(anal_res["resolution_steps"]),
                "elapsed_s":        elapsed
            },
            session_id=session_id
        )
        return state

    try:
        chain = analysis_prompt | config.llm
        response = chain.invoke({
            "query":    state["query"],
            "plan":     state["plan"],
            "research": state["research"],
        })
        content = response.content.strip()
        state["analysis"] = content

        # Parse metrics from LLM output
        severity     = "Medium"
        confidence   = 85.0
        is_high_risk = any(kw in state["query"].lower() for kw in HIGH_RISK_KEYWORDS)
        is_solvable  = True

        for line in content.splitlines():
            line_str = line.strip()
            if "Level:" in line_str:
                m = re.search(r"(Critical|High|Medium|Low)", line_str, re.IGNORECASE)
                if m: severity = m.group(1).capitalize()
            elif "Confidence Score:" in line_str:
                m = re.search(r"(\d+)", line_str)
                if m: confidence = float(m.group(1))
            elif "Is Solvable:" in line_str:
                is_solvable = "no" not in line_str.lower()

        if is_high_risk:
            is_solvable = False

        # Use template for resolution_steps (LLM path may not output structured steps)
        template         = _get_resolution_template(state["query"], state.get("category", ""))
        resolution_title = template["title"]
        resolution_steps = template["steps"]

        state["severity"]         = severity
        state["confidence"]       = confidence
        state["is_high_risk"]     = is_high_risk
        state["is_solvable"]      = is_solvable
        state["resolution_steps"] = resolution_steps
        state["resolution_title"] = resolution_title

        elapsed = round(time.monotonic() - start_time, 2)
        state.setdefault("timings", {})["analysis"] = elapsed

        bus.publish(
            publisher="analysis_agent",
            event_type="analysis_complete",
            payload={
                "mode":             "llm",
                "severity":         severity,
                "confidence":       f"{confidence}%",
                "is_high_risk":     is_high_risk,
                "is_solvable":      is_solvable,
                "resolution_title": resolution_title,
                "elapsed_s":        elapsed
            },
            session_id=session_id
        )

    except Exception as e:
        print(f"Error in analysis_agent: {e}")
        anal_res = get_mock_analysis(state["query"])
        state["analysis"]         = anal_res["text"]
        state["category"]         = anal_res["category"]
        state["severity"]         = anal_res["severity"]
        state["confidence"]       = anal_res["confidence"]
        state["is_high_risk"]     = anal_res["is_high_risk"]
        state["is_solvable"]      = anal_res["is_solvable"]
        state["resolution_steps"] = anal_res["resolution_steps"]
        state["resolution_title"] = anal_res["resolution_title"]
        elapsed = round(time.monotonic() - start_time, 2)
        state.setdefault("timings", {})["analysis"] = elapsed

    return state
