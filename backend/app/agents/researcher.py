"""
Researcher Agent
================
Gathers and summarises relevant knowledge for each step of the execution plan.
Does NOT make decisions or generate the final answer.
"""
from langchain_core.prompts import ChatPromptTemplate

from app.config import llm


# Prompt Template

RESEARCHER_SYSTEM_PROMPT = """
You are an Enterprise Research Agent.

Your responsibilities are:
1. Read the execution plan carefully.
2. Gather relevant knowledge for every step.
3. Summarise important facts concisely.
4. Do NOT make decisions.
5. Do NOT generate the final answer.

Return your output in EXACTLY this format:

Research Summary:

Step 1:
<findings for step 1>

Step 2:
<findings for step 2>

Step 3:
<findings for step 3>

Key Findings:
- <finding 1>
- <finding 2>
- <finding 3>
""".strip()

RESEARCHER_HUMAN_TEMPLATE = """
User Query:
{query}

Execution Plan:
{plan}
""".strip()

research_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", RESEARCHER_SYSTEM_PROMPT),
        ("human", RESEARCHER_HUMAN_TEMPLATE),
    ]
)


# Agent Function

def researcher_agent(state: dict) -> dict:
    """
    Researcher Agent node for LangGraph.

    Reads:
        state["query"]     – the user's original question
        state["plan"]      – the execution plan from PlannerAgent

    Writes:
        state["research"]  – summarised research findings
    """
    chain = research_prompt | llm
    response = chain.invoke(
        {
            "query": state["query"],
            "plan": state["plan"],
        }
    )
    state["research"] = response.content
    return state