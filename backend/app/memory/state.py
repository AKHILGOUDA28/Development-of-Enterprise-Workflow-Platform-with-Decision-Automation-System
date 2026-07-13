from typing import TypedDict

class AgentState(TypedDict):
    query: str
    plan: str
    research: str
    decision: str
    final_answer: str