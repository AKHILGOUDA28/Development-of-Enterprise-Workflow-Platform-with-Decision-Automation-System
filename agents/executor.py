"""
executor.py
-----------
Executor Agent - synthesises all outputs and writes the final response.
"""

import config
from prompts import executor_prompt
from tracing import tracer
from agent_bus import bus


def get_mock_answer(query: str) -> str:
    return f"""Answer:
The Coordination Engine has successfully processed the query: "{query}".

Solution:
A five-agent coordination framework (Planner → Researcher → Analysis → Decision → Executor)
orchestrated via LangGraph with persistent memory and real-time tool integration.

Steps to Implement:
1. Review the requirements.txt file and install necessary packages.
2. Set your Groq API Key in the local .env configuration file.
3. Run python api.py to start the web service and view the UI dashboard.

Conclusion:
This multi-agent coordination system provides robust orchestration, unified session state memory,
intelligent tool selection, root-cause analysis, and an enterprise monitoring dashboard."""


def executor_agent(state: dict) -> dict:
    """
    Reads everything in the state.
    Writes the final polished answer into state["answer"].
    """
    tracer.log_event("Executor Agent", "Generating Final Response")
    session_id = state.get("session_id", "global")

    bus.publish(
        publisher  = "executor_agent",
        event_type = "response_generation_started",
        payload    = {"query": state.get("query", "")[:120]},
        session_id = session_id
    )

    if config.IS_MOCK or not config.llm:
        answer = get_mock_answer(state["query"])
        state["answer"] = answer
        bus.publish(
            publisher  = "executor_agent",
            event_type = "workflow_complete",
            payload    = {"mode": "mock", "answer_length": len(answer)},
            session_id = session_id
        )
        return state

    try:
        chain  = executor_prompt | config.llm
        result = chain.invoke({
            "query":    state["query"],
            "plan":     state["plan"],
            "research": state["research"],
            "analysis": state.get("analysis", ""),
            "decision": state["decision"],
        })
        state["answer"] = result.content
        bus.publish(
            publisher  = "executor_agent",
            event_type = "workflow_complete",
            payload    = {"mode": "llm", "answer_length": len(result.content)},
            session_id = session_id
        )
    except Exception as e:
        print(f"Error in executor_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["answer"] = get_mock_answer(state["query"])
        bus.publish(
            publisher  = "executor_agent",
            event_type = "agent_error",
            payload    = {"error": str(e)},
            session_id = session_id
        )

    return state
