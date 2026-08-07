"""
researcher.py
-------------
Researcher Agent - gathers relevant knowledge for each step of the plan.
"""

import config
from prompts import researcher_prompt
from tools.registry import tool_registry
from utils_parser import extract_tool_calls
from tracing import tracer
from agent_bus import bus


def get_mock_research(query: str) -> str:
    return f"""Research Findings:

Step 1: Analyzed "{query}".
Step 2: Found relevant IT knowledge base solutions.
Step 3: Searched incident database for similar past issues.

Key Points:
- Restarting services solves 90% of connectivity issues.
- If hardware is involved, check physical connections.
- Ensure correct access privileges."""


def researcher_agent(state: dict) -> dict:
    """
    Reads the query and plan.
    Calls tools in a loop if the LLM requests them.
    Writes gathered research into state["research"].
    """
    tracer.log_event("Research Agent", "Starting IT Support Research")
    session_id = state.get("session_id", "global")

    bus.publish(
        publisher  = "researcher_agent",
        event_type = "research_started",
        payload    = {"query": state.get("query", "")[:120]},
        session_id = session_id
    )

    if config.IS_MOCK or not config.llm:
        state["research"] = get_mock_research(state["query"])
        bus.publish(
            publisher  = "researcher_agent",
            event_type = "research_complete",
            payload    = {"mode": "mock", "tool_calls": 0},
            session_id = session_id
        )
        return state

    try:
        chain = researcher_prompt | config.llm

        max_iterations = 5
        current_iteration = 0
        chat_history = ""
        content = ""

        while current_iteration < max_iterations:
            current_iteration += 1
            response = chain.invoke({
                "query": state["query"] + chat_history,
                "plan":  state["plan"]
            })
            content = response.content.strip()

            tool_calls = extract_tool_calls(content)
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool", "")
                    tool_args = tool_call.get("args", {})

                    tracer.log_event(
                        "LLM Tool Call (Research)",
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
                    "'Research Findings' based on the tool results."
                )
            else:
                # No tool calls — this is the final research text
                state["research"] = content
                bus.publish(
                    publisher  = "researcher_agent",
                    event_type = "research_complete",
                    payload    = {"mode": "llm", "iterations": current_iteration},
                    session_id = session_id
                )
                break

        if "research" not in state:
            state["research"] = content

    except Exception as e:
        print(f"Error in researcher_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["research"] = get_mock_research(state["query"])
        bus.publish(
            publisher  = "researcher_agent",
            event_type = "agent_error",
            payload    = {"error": str(e)},
            session_id = session_id
        )

    return state
