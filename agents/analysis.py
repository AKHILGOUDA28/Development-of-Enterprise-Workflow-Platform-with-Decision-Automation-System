"""
analysis.py
-----------
Analysis Agent - performs structured root-cause analysis on research findings.

Sits between the Researcher and Decision agents in the pipeline:
  Planner → Researcher → Analysis → Decision → Executor

Outputs:
  - Root cause identification
  - Pattern recognition
  - Severity assessment (Critical / High / Medium / Low)
  - Confidence score (0–100%)
  - Recommended approach (Auto-Fix / Escalate / Monitor)
"""

import config
from prompts import analysis_prompt
from tracing import tracer
from agent_bus import bus


def get_mock_analysis(query: str) -> str:
    return """Root Cause Analysis:
The issue is most likely caused by a misconfiguration or software conflict introduced
by a recent system change (update, patch, or configuration drift).

Pattern Recognition:
- This type of issue follows a recurring pattern seen in 73% of similar past incidents.
- Network and authentication-related failures typically occur within 24h of system updates.

Severity Assessment:
  Level: Medium
  Impact: Individual user productivity impacted; no system-wide outage detected.

Confidence Score: 78%
  Reasoning: Research findings show strong knowledge-base coverage. Multiple similar
  past incidents resolved with standard troubleshooting steps.

Recommended Approach:
  Strategy: Auto-Fix
  Rationale: Known solution exists in knowledge base with high success rate.

Supporting Evidence:
- 15 similar incidents resolved using standard service restart procedures.
- Knowledge base article confirmed the auto-fix resolution path."""


def analysis_agent(state: dict) -> dict:
    """
    Performs structured root-cause analysis on the research output.

    Reads: state["query"], state["plan"], state["research"]
    Writes: state["analysis"]
    """
    tracer.log_event("Analysis Agent", "Running Root-Cause Analysis")

    # Publish event to the agent bus
    session_id = state.get("session_id", "global")
    bus.publish(
        publisher  = "analysis_agent",
        event_type = "analysis_started",
        payload    = {"query": state.get("query", "")[:120]},
        session_id = session_id
    )

    if config.IS_MOCK or not config.llm:
        analysis_text = get_mock_analysis(state["query"])
        state["analysis"] = analysis_text
        bus.publish(
            publisher  = "analysis_agent",
            event_type = "analysis_complete",
            payload    = {
                "mode":     "mock",
                "strategy": "Auto-Fix",
                "severity": "Medium",
                "confidence": "78%"
            },
            session_id = session_id
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

        # Extract key fields for the event bus payload
        severity   = "Unknown"
        confidence = "Unknown"
        strategy   = "Unknown"
        for line in content.splitlines():
            line_stripped = line.strip()
            if line_stripped.startswith("Level:"):
                severity = line_stripped.replace("Level:", "").strip()
            elif line_stripped.startswith("Confidence Score:"):
                confidence = line_stripped.replace("Confidence Score:", "").strip()
            elif line_stripped.startswith("Strategy:"):
                strategy = line_stripped.replace("Strategy:", "").strip()

        bus.publish(
            publisher  = "analysis_agent",
            event_type = "analysis_complete",
            payload    = {
                "mode":       "llm",
                "severity":   severity,
                "confidence": confidence,
                "strategy":   strategy,
            },
            session_id = session_id
        )
        tracer.log_event(
            "Analysis Agent Complete",
            f"Severity: {severity} | Confidence: {confidence} | Strategy: {strategy}"
        )

    except Exception as e:
        print(f"Error in analysis_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["analysis"] = get_mock_analysis(state["query"])

    return state
