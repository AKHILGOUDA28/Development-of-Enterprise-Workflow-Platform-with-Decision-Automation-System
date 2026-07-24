"""
workflow.py
-----------
Connects all four agents into a proper LangGraph workflow.

Flow:
  START → planner_agent → researcher_agent → decision_agent → executor_agent → END

The shared state is a plain dict with these keys:
  query    - the user's question (input)
  plan     - filled by planner_agent
  research - filled by researcher_agent
  decision - filled by decision_agent
  answer   - filled by executor_agent (final output)

Usage:
  from workflow import run_workflow
  result = run_workflow("How can AI help in healthcare?")
"""

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agents import planner_agent, researcher_agent, decision_agent, executor_agent


# --------------------------------------------------
# Shared state structure
# --------------------------------------------------
class AgentState(TypedDict):
    query:    str
    plan:     str
    research: str
    decision: str
    answer:   str


# --------------------------------------------------
# Build the LangGraph workflow
# --------------------------------------------------
def build_graph():
    """Creates and compiles the multi-agent state graph."""
    graph = StateGraph(AgentState)

    # Add each agent as a node
    graph.add_node("planner",    planner_agent)
    graph.add_node("researcher", researcher_agent)
    graph.add_node("decision",   decision_agent)
    graph.add_node("executor",   executor_agent)

    # Connect the nodes in sequence
    graph.add_edge(START,        "planner")
    graph.add_edge("planner",    "researcher")
    graph.add_edge("researcher", "decision")
    graph.add_edge("decision",   "executor")
    graph.add_edge("executor",   END)

    return graph.compile()


# Compile once when this file is imported
agent_graph = build_graph()


# --------------------------------------------------
# Main function to run the full pipeline
# --------------------------------------------------
def run_workflow(query: str) -> dict:
    """
    Runs the full 4-agent pipeline for a given query.

    Returns a dict with:
      query, plan, research, decision, answer
    """
    from tracing import tracer
    tracer.start_trace(query)

    initial_state = {
        "query":    query,
        "plan":     "",
        "research": "",
        "decision": "",
        "answer":   ""
    }

    result = agent_graph.invoke(initial_state)
    tracer.log_event("Workflow Completed", f"Final Answer Length: {len(result.get('answer', ''))}")
    return result
