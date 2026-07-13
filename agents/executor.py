"""
executor.py
-----------
Executor Agent - synthesises all outputs and writes the final response.
"""

import config
from prompts import executor_prompt


# Tailored Mock Generator Helper
def get_mock_answer(query: str) -> str:
    return f"""Answer:
The Coordination Engine has successfully processed the query: "{query}".

Solution:
A lightweight coordination framework consisting of four sequential agent personas (Planner, Researcher, Decision, Executor) orchestrated via LangGraph.

Steps to Implement:
1. Review the requirements.txt file and install necessary packages.
2. Set your Groq API Key in the local .env configuration file.
3. Run python api.py to start the web service and view the UI dashboard.

Conclusion:
This multi-agent coordination system provides a robust orchestration interface, unified session state memory, and intelligent service resilience checks."""



def executor_agent(state: dict) -> dict:
    """
    Reads everything in the state.
    Writes the final polished answer into state["answer"].
    """
    if config.IS_MOCK or not config.llm:
        state["answer"] = get_mock_answer(state["query"])
        return state

    try:
        chain  = executor_prompt | config.llm
        result = chain.invoke({
            "query":    state["query"],
            "plan":     state["plan"],
            "research": state["research"],
            "decision": state["decision"]
        })
        state["answer"] = result.content
    except Exception as e:
        print(f"Error in executor_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["answer"] = get_mock_answer(state["query"])
    
    return state
