"""
decision.py
-----------
Decision Support Agent - reviews options and recommends the best solution, using tools when necessary.
"""

import config
from prompts import decision_prompt
from tools.registry import tool_registry
from utils_parser import extract_tool_calls
from tracing import tracer
from agent_bus import bus


def get_mock_decision(query: str) -> str:
    return """Recommended Solution: Auto-fix available. Please proceed with the troubleshooting steps.

Why this solution:
- It matches a known issue in the IT database.
- Restarting services is safe and quick.

Next Steps:
1. Provide the user with the troubleshooting steps.
2. Ensure they verify connectivity after attempting the fix."""


def decision_agent(state: dict) -> dict:
    """
    Reads the query, plan, research, and analysis.
    Parses LLM response; if tool calls are detected, executes them all and loops
    back to finalise the decision. Writes result into state["decision"].
    """
    tracer.log_event("Decision Agent", "Evaluating IT Incident")
    session_id = state.get("session_id", "global")

    bus.publish(
        publisher  = "decision_agent",
        event_type = "decision_started",
        payload    = {"analysis_available": bool(state.get("analysis", "").strip())},
        session_id = session_id
    )

    if config.IS_MOCK or not config.llm:
        state["decision"] = get_mock_decision(state["query"])
        bus.publish(
            publisher  = "decision_agent",
            event_type = "decision_complete",
            payload    = {"mode": "mock", "action": "Auto-Fix"},
            session_id = session_id
        )
        return state

    try:
        chain = decision_prompt | config.llm

        max_iterations = 5
        current_iteration = 0
        chat_history = ""
        content = ""

        while current_iteration < max_iterations:
            current_iteration += 1
            response = chain.invoke({
                    "query":    state["query"] + chat_history,
                    "plan":     state["plan"],
                    "research": state["research"],
                    "analysis": state.get("analysis", ""),
                })
            content = response.content.strip()

            tool_calls = extract_tool_calls(content)
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool", "")
                    tool_args = tool_call.get("args", {})

                    tracer.log_event(
                        "LLM Tool Call (Decision)",
                        f"Tool: {tool_name}, Args: {tool_args}"
                    )

                    try:
                        tool = tool_registry.get_tool(tool_name)
                        tool_result = tool.run(**tool_args)
                    except Exception as tool_err:
                        tool_result = {
                            "success": False,
                            "error": str(tool_err),
                            "result": None
                        }

                    tracer.log_event(
                        "Tool Execution Finished",
                        f"Success: {tool_result['success']}, Error: {tool_result['error']}"
                    )

                    result_text = tool_result["result"] or tool_result["error"] or "No output"
                    chat_history += (
                        f"\n\n[System: Tool '{tool_name}' executed. Result: {result_text}]"
                    )

                chat_history += (
                    "\n\nAll tools executed. Now provide your final "
                    "'Recommended Solution' based on the tool results."
                )
            else:
                # No tool calls — this is the final decision text
                state["decision"] = content
                bus.publish(
                    publisher  = "decision_agent",
                    event_type = "decision_complete",
                    payload    = {"mode": "llm", "iterations": current_iteration},
                    session_id = session_id
                )
                break

        if "decision" not in state:
            state["decision"] = content

    except Exception as e:
        print(f"Error in decision_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["decision"] = get_mock_decision(state["query"])
        bus.publish(
            publisher  = "decision_agent",
            event_type = "agent_error",
            payload    = {"error": str(e)},
            session_id = session_id
        )

    return state
