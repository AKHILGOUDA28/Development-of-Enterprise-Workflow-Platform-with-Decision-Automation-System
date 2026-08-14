"""
analysis.py
-----------
Analysis Agent - Performs root-cause analysis, pattern recognition, confidence scoring (0-100%),
severity classification, and high-risk action detection.
"""

import time
import re
import config
from prompts import analysis_prompt
from tracing import tracer
from agent_bus import bus

# High risk keywords that ALWAYS trigger Human-In-The-Loop approval regardless of confidence
HIGH_RISK_KEYWORDS = [
    "disable account", "delete account", "terminate account", "wipe device",
    "factory reset", "reboot server", "restart domain controller", "revoke access",
    "modify permissions", "flush database", "elevate privileges"
]

def get_mock_analysis(query: str) -> dict:
    is_high_risk = any(kw in query.lower() for kw in HIGH_RISK_KEYWORDS)
    confidence = 92.0 if not is_high_risk else 75.0
    severity = "High" if is_high_risk else "Medium"
    strategy = "Pending Approval" if is_high_risk else ("Auto-Fix" if confidence >= 85 else "Escalate")
    
    text = f"""Root Cause Analysis:
The reported issue ("{query}") is identified as a configuration or service mismatch following a system update or network state change.

Pattern Recognition:
- High similarity (92%) with historical incident resolution patterns.
- Standard service remediation steps confirmed in Knowledge Base.

Severity Assessment:
  Level: {severity}
  Impact: User workflow impaired; resolution path identified.

Confidence Score: {int(confidence)}%
  Reasoning: High knowledge base pattern match with validated resolution steps.

Recommended Approach:
  Strategy: {strategy}
  Rationale: {"High-risk enterprise action requires Human-In-The-Loop IT Admin approval." if is_high_risk else "Confidence exceeds 85% threshold for automated remediation."}

Supporting Evidence:
- Verified matching knowledge base entry KB-1001.
- Past incident history shows 90%+ success rate."""
    return {
        "text": text,
        "severity": severity,
        "confidence": confidence,
        "strategy": strategy,
        "is_high_risk": is_high_risk
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
        state["analysis"] = anal_res["text"]
        state["severity"] = anal_res["severity"]
        state["confidence"] = anal_res["confidence"]
        state["is_high_risk"] = anal_res["is_high_risk"]
        
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["analysis"] = elapsed

        bus.publish(
            publisher="analysis_agent",
            event_type="analysis_complete",
            payload={
                "mode": "mock",
                "severity": anal_res["severity"],
                "confidence": f"{anal_res['confidence']}%",
                "strategy": anal_res["strategy"],
                "elapsed_s": elapsed
            },
            session_id=session_id
        )
        return state

    try:
        chain = analysis_prompt | config.llm
        response = chain.invoke({
            "query": state["query"],
            "plan": state["plan"],
            "research": state["research"],
        })
        content = response.content.strip()
        state["analysis"] = content

        # Parse metrics from LLM output
        severity = "Medium"
        confidence = 85.0
        strategy = "Auto-Fix"

        for line in content.splitlines():
            line_str = line.strip()
            if "Level:" in line_str:
                sev_match = re.search(r"(Critical|High|Medium|Low)", line_str, re.IGNORECASE)
                if sev_match:
                    severity = sev_match.group(1).capitalize()
            elif "Confidence Score:" in line_str:
                conf_match = re.search(r"(\d+)", line_str)
                if conf_match:
                    confidence = float(conf_match.group(1))

        query_lower = state["query"].lower()
        is_high_risk = any(kw in query_lower for kw in HIGH_RISK_KEYWORDS)

        state["severity"] = severity
        state["confidence"] = confidence
        state["is_high_risk"] = is_high_risk

        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["analysis"] = elapsed

        bus.publish(
            publisher="analysis_agent",
            event_type="analysis_complete",
            payload={
                "mode": "llm",
                "severity": severity,
                "confidence": f"{confidence}%",
                "is_high_risk": is_high_risk,
                "elapsed_s": elapsed
            },
            session_id=session_id
        )

    except Exception as e:
        print(f"Error in analysis_agent: {e}")
        anal_res = get_mock_analysis(state["query"])
        state["analysis"] = anal_res["text"]
        state["severity"] = anal_res["severity"]
        state["confidence"] = anal_res["confidence"]
        state["is_high_risk"] = anal_res["is_high_risk"]
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["analysis"] = elapsed

    return state
