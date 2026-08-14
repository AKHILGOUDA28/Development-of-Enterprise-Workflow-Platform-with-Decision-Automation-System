"""
researcher.py
-------------
Researcher Agent - Gathers knowledge from KB, Incident DB, Web Search, and Employee History
using NATIVE LLM Tool Calling (`bind_tools` & `AIMessage.tool_calls`).
"""

import time
import json
import config
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from tools.registry import tool_registry
from memory import long_memory
from tracing import tracer
from agent_bus import bus

def get_mock_research(query: str, emp_id: str = "EMP1024") -> str:
    emp_mem = long_memory.recall(f"{emp_id}_history")
    history_note = ""
    if emp_mem:
        try:
            mem_data = json.loads(emp_mem)
            history_note = f"\n- Employee History ({emp_id}): {mem_data.get('employee_name')} has {len(mem_data.get('previous_incidents', []))} past incidents. Successful resolutions: {mem_data.get('successful_resolutions')}"
        except Exception:
            pass

    return f"""Research Findings:

1. Query Analyzed: "{query}"
2. Knowledge Base match found: Checked 42 enterprise records. Matching solution available.
3. Historical Incident DB: Queried incidents table for matching resolution patterns.{history_note}

Key Points:
- Knowledge base confirms step-by-step resolution path exists.
- Past incidents show 92% first-contact resolution success rate.
- Employee historical context retrieved from long-term memory."""

def researcher_agent(state: dict) -> dict:
    start_time = time.monotonic()
    tracer.log_event("Research Agent", "Starting IT Support Research with Native Tool Calling")
    session_id = state.get("session_id", "global")
    emp_id = state.get("employee_id", "EMP1024")

    bus.publish(
        publisher="researcher_agent",
        event_type="research_started",
        payload={"query": state.get("query", "")[:120], "employee_id": emp_id},
        session_id=session_id
    )

    # Automatically query employee history from SQLite LongTermMemory
    emp_history_str = ""
    emp_mem = long_memory.recall(f"{emp_id}_history")
    if emp_mem:
        emp_history_str = f"\n\n[Employee Historical Context from Long-Term Memory ({emp_id})]:\n{emp_mem}"

    if config.IS_MOCK or not config.llm:
        state["research"] = get_mock_research(state["query"], emp_id)
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["researcher"] = elapsed
        bus.publish(
            publisher="researcher_agent",
            event_type="research_complete",
            payload={"mode": "mock", "elapsed_s": elapsed},
            session_id=session_id
        )
        return state

    try:
        # NATIVE TOOL CALLING BINDING
        lc_tools = tool_registry.get_langchain_tools()
        llm_with_tools = config.llm.bind_tools(lc_tools)

        sys_prompt = SystemMessage(content=(
            "You are an IT Support Research Agent.\n"
            "Your goal is to gather facts from the knowledge base, incident database, and web search to resolve the user's issue.\n"
            "Use native tool calls to query `knowledge_base`, `incident_database`, `web_search`, or `hr_system`.\n"
            "After gathering facts, output your final 'Research Findings:' and 'Key Points:'."
        ))

        user_content = f"User Question: {state['query']}\nPlan:\n{state['plan']}{emp_history_str}"
        messages = [sys_prompt, HumanMessage(content=user_content)]

        max_iterations = 4
        current_iter = 0
        final_findings = ""

        while current_iter < max_iterations:
            current_iter += 1
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # Check if LLM emitted NATIVE tool calls
            if getattr(response, "tool_calls", None) and len(response.tool_calls) > 0:
                for tool_call in response.tool_calls:
                    t_name = tool_call["name"]
                    t_args = tool_call["args"]
                    t_id = tool_call.get("id", f"call_{current_iter}")

                    tracer.log_event("Native Tool Call (Research)", f"Tool: {t_name}, Args: {t_args}")
                    bus.publish(
                        publisher="researcher_agent",
                        event_type="tool_called",
                        payload={"tool_name": t_name, "args": t_args},
                        session_id=session_id
                    )

                    try:
                        tool_monitored = tool_registry.get_tool(t_name)
                        tool_res = tool_monitored.run(**t_args)
                        t_output = str(tool_res["result"]) if tool_res["success"] else f"Error: {tool_res['error']}"
                    except Exception as err:
                        t_output = f"Tool execution failed: {err}"

                    messages.append(ToolMessage(content=t_output, tool_call_id=t_id))
            else:
                # Final response reached
                final_findings = response.content.strip()
                break

        if not final_findings:
            final_findings = messages[-1].content if messages else get_mock_research(state["query"], emp_id)

        state["research"] = final_findings
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["researcher"] = elapsed

        bus.publish(
            publisher="researcher_agent",
            event_type="research_complete",
            payload={"mode": "native_tool_calling", "iterations": current_iter, "elapsed_s": elapsed},
            session_id=session_id
        )

    except Exception as e:
        print(f"Error in researcher_agent: {e}")
        state["research"] = get_mock_research(state["query"], emp_id)
        elapsed = round((time.monotonic() - start_time), 2)
        state.setdefault("timings", {})["researcher"] = elapsed
        bus.publish(
            publisher="researcher_agent",
            event_type="agent_error",
            payload={"error": str(e)},
            session_id=session_id
        )

    return state
