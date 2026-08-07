"""
planner.py
----------
Planner Agent - takes the user's query and creates a step-by-step plan.
"""

import config
from prompts import planner_prompt
from tracing import tracer
from agent_bus import bus


def get_mock_plan(query: str) -> str:
    return f"""Goal: Define execution plan to solve: "{query}"

Execution Plan:
1. Scope Definition: Map query inputs to enterprise system features.
2. Knowledge Retrieval: Retrieve domain-specific facts and industry data.
3. System Recommendation: Compare different implementation paths.
4. Response Assembly: Synthesize all agent findings into the final response."""


def planner_agent(state: dict) -> dict:
    """
    Reads the user's question.
    Writes a structured step-by-step plan into state["plan"].
    """
    tracer.log_event("Planner Agent", "Generating Resolution Plan")
    session_id = state.get("session_id", "global")

    bus.publish(
        publisher  = "planner_agent",
        event_type = "plan_started",
        payload    = {"query": state.get("query", "")[:120]},
        session_id = session_id
    )

    if config.IS_MOCK or not config.llm:
        plan = get_mock_plan(state["query"])
        state["plan"] = plan
        bus.publish(
            publisher  = "planner_agent",
            event_type = "plan_ready",
            payload    = {"mode": "mock", "steps": 4},
            session_id = session_id
        )
        return state

    try:
        chain  = planner_prompt | config.llm
        result = chain.invoke({"query": state["query"]})
        state["plan"] = result.content
        bus.publish(
            publisher  = "planner_agent",
            event_type = "plan_ready",
            payload    = {"mode": "llm", "plan_length": len(result.content)},
            session_id = session_id
        )
    except Exception as e:
        print(f"Error in planner_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["plan"] = get_mock_plan(state["query"])
        bus.publish(
            publisher  = "planner_agent",
            event_type = "agent_error",
            payload    = {"error": str(e)},
            session_id = session_id
        )

    return state
