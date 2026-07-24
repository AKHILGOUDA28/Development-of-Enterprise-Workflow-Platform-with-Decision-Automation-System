"""
decision.py
-----------
Decision Support Agent - reviews options and recommends the best solution, using tools when necessary.
"""

import json
import config
from prompts import decision_prompt
from tools.registry import tool_registry
from tracing import tracer

# Tailored Mock Generator Helper
def get_mock_decision(query: str) -> str:
    return f"""Recommended Solution: Auto-fix available. Please proceed with the troubleshooting steps.

Why this solution:
- It matches a known issue in the IT database.
- Restarting services is safe and quick.

Next Steps:
1. Provide the user with the troubleshooting steps.
2. Ensure they verify connectivity after attempting the fix."""


def decision_agent(state: dict) -> dict:
    """
    Reads the query, plan, and research.
    Parses LLM decision; if a tool call format is returned, executes it and loops back to finalise decision.
    Writes the recommended decision into state["decision"].
    """
    tracer.log_event("Decision Agent", "Evaluating IT Incident")

    if config.IS_MOCK or not config.llm:
        state["decision"] = get_mock_decision(state["query"])
        return state

    try:
        chain  = decision_prompt | config.llm
        
        max_iterations = 3
        current_iteration = 0
        chat_history = ""
        
        while current_iteration < max_iterations:
            current_iteration += 1
            response = chain.invoke({
                "query":    state["query"] + chat_history,
                "plan":     state["plan"],
                "research": state["research"]
            })
            content = response.content.strip()

        from utils_parser import extract_tool_calls
        
        while current_iteration < max_iterations:
            current_iteration += 1
            response = chain.invoke({
                "query":    state["query"] + chat_history,
                "plan":     state["plan"],
                "research": state["research"]
            })
            content = response.content.strip()

            tool_calls = extract_tool_calls(content)
            if tool_calls:
                is_tool_call = True
                for tool_call in tool_calls:
                    tool_name = tool_call["tool"]
                    tool_args = tool_call.get("args", {})
                    
                    tracer.log_event("LLM Tool Call Selected (Decision)", f"Tool: {tool_name}, Args: {tool_args}")
                    
                    try:
                        tool = tool_registry.get_tool(tool_name)
                        tool_result = tool.run(**tool_args)
                    except Exception as tool_err:
                        tool_result = {
                            "success": False,
                            "error": str(tool_err),
                            "result": None
                        }
                    
                    tracer.log_event("Tool Execution Finished", f"Success: {tool_result['success']}, Error: {tool_result['error']}")
                    
                    follow_up_prompt = f"\n\n[System Notification: The tool '{tool_name}' was executed with the following result:\n{tool_result['result'] or tool_result['error']}]"
                    chat_history += follow_up_prompt
                
                chat_history += "\n\nYou have executed the tools. Please provide your final 'Recommended Solution' formatting now based on the tool results."
            else:
                is_tool_call = False
                state["decision"] = content
                break

        if "decision" not in state:
            state["decision"] = content

    except Exception as e:
        print(f"Error in decision_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["decision"] = get_mock_decision(state["query"])
    
    return state
