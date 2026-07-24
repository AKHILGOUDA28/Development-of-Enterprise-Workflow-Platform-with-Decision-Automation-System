"""
researcher.py
-------------
Researcher Agent - gathers relevant knowledge for each step of the plan.
"""

import json
import config
from prompts import researcher_prompt
from tools.registry import tool_registry
from tracing import tracer


# Tailored Mock Generator Helper
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
    Writes gathered research into state["research"].
    """
    tracer.log_event("Research Agent", "Starting IT Support Research")
    if config.IS_MOCK or not config.llm:
        state["research"] = get_mock_research(state["query"])
        return state

    try:
        chain  = researcher_prompt | config.llm
        
        # We allow up to 3 tool calls in a row for the researcher
        max_iterations = 3
        current_iteration = 0
        
        chat_history = ""
        
        while current_iteration < max_iterations:
            current_iteration += 1
            response = chain.invoke({
                "query": state["query"] + chat_history,
                "plan":  state["plan"]
            })
            content = response.content.strip()

        from utils_parser import extract_tool_calls
        
        while current_iteration < max_iterations:
            current_iteration += 1
            response = chain.invoke({
                "query": state["query"] + chat_history,
                "plan":  state["plan"]
            })
            content = response.content.strip()

            tool_calls = extract_tool_calls(content)
            if tool_calls:
                is_tool_call = True
                for tool_call in tool_calls:
                    tool_name = tool_call["tool"]
                    tool_args = tool_call.get("args", {})
                    
                    tracer.log_event("LLM Tool Call Selected (Research)", f"Tool: {tool_name}, Args: {tool_args}")
                    
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
                
                chat_history += "\n\nYou have executed the tools. Please provide your final 'Research Findings' formatting now based on the tool results."
            else:
                is_tool_call = False
                state["research"] = content
                break
                
        if "research" not in state:
            state["research"] = content

    except Exception as e:
        print(f"Error in researcher_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["research"] = get_mock_research(state["query"])
    
    return state
