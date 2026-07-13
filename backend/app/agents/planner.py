"""
Planner Agent
=============
Breaks the user's query into a structured, step-by-step execution plan.
Does NOT answer the user's question – only creates the plan.
"""
from langchain_core.prompts import ChatPromptTemplate

from app.config import llm


# Prompt Template

PLANNER_SYSTEM_PROMPT = """
You are an Enterprise Planning Agent.

Your responsibilities are:
1. Understand the user's request.
2. Break it into logical, actionable execution steps.
3. Do NOT answer the user's question directly.
4. Only produce a structured execution plan.

Return your output in EXACTLY this format:

Goal:
<one-line goal statement>

Execution Plan:
1. <step 1>
2. <step 2>
3. <step 3>
4. <step 4>
""".strip()

planner_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", "{query}"),
    ]
)



# Agent Function

def planner_agent(state: dict) -> dict:
    """
    Planner Agent node for LangGraph.

    Reads:
        state["query"]  – the user's original question

    Writes:
        state["plan"]   – the structured execution plan
    """
    chain = planner_prompt | llm
    response = chain.invoke({"query": state["query"]})
    state["plan"] = response.content
    return state