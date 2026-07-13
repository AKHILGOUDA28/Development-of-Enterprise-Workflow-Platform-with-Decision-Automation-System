"""
researcher.py
-------------
Researcher Agent - gathers relevant knowledge for each step of the plan.
"""

import config
from prompts import researcher_prompt


# Tailored Mock Generator Helper
def get_mock_research(query: str) -> str:
    return f"""Research Findings:

Step 1 (Scope): The request "{query}" benefits from a modular workflow structure.
Step 2 (Retrieval): Multi-agent setups reduce context limit exhaustion and focus reasoning on specific sub-tasks.
Step 3 (Recommendation): Utilizing LangGraph enables structured state transitions and sequential execution pipelines.

Key Points:
- Separating planning from execution increases predictability of LLM outputs.
- Short-term conversation logging enables system context awareness.
- Long-term state management allows persisting user configs across sessions."""


def researcher_agent(state: dict) -> dict:
    """
    Reads the query and plan.
    Writes gathered research into state["research"].
    """
    if config.IS_MOCK or not config.llm:
        state["research"] = get_mock_research(state["query"])
        return state

    try:
        chain  = researcher_prompt | config.llm
        result = chain.invoke({
            "query": state["query"],
            "plan":  state["plan"]
        })
        state["research"] = result.content
    except Exception as e:
        print(f"Error in researcher_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["research"] = get_mock_research(state["query"])
    
    return state
