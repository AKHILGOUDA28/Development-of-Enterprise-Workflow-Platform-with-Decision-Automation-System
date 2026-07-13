"""
decision.py
-----------
Decision Support Agent - reviews options and recommends the best solution.
"""

import config
from prompts import decision_prompt


# Tailored Mock Generator Helper
def get_mock_decision(query: str) -> str:
    return f"""Recommended Solution: Sequential 4-Agent Orchestration Graph

Why this solution:
- High readability: Each node performs a single, testable business logic operation.
- Resiliency: The engine can gracefully switch to simulated/mock mode when API credentials are unset.

Risks to consider:
- Rate limits on external LLM APIs (e.g. Groq free tier).
- Missing configuration files or invalid credentials.

Next Steps:
1. Update your GROQ_API_KEY in the .env file if you wish to run live LLM requests.
2. Launch the server using "python api.py".
3. Open http://localhost:8000 to interact with the engine."""


def decision_agent(state: dict) -> dict:
    """
    Reads the query, plan, and research.
    Writes the recommended decision into state["decision"].
    """
    if config.IS_MOCK or not config.llm:
        state["decision"] = get_mock_decision(state["query"])
        return state

    try:
        chain  = decision_prompt | config.llm
        result = chain.invoke({
            "query":    state["query"],
            "plan":     state["plan"],
            "research": state["research"]
        })
        state["decision"] = result.content
    except Exception as e:
        print(f"Error in decision_agent (switching to mock mode): {e}")
        config.IS_MOCK = True
        state["decision"] = get_mock_decision(state["query"])
    
    return state
