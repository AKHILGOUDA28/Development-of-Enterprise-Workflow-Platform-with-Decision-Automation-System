"""
Decision Agent
==============
Analyses the plan and research findings, then recommends the best solution.
Does NOT generate the final user-facing response.
"""
from langchain_core.prompts import ChatPromptTemplate

from app.config import llm


# Prompt Template
DECISION_SYSTEM_PROMPT = """
You are an Enterprise Decision Support Agent.

Your responsibilities are:
1. Analyse the execution plan.
2. Evaluate the research findings.
3. Compare possible approaches.
4. Recommend the best solution.
5. Clearly explain your reasoning.
6. Do NOT generate the final response for the user.

Return your output in EXACTLY this format:

Decision Summary

Recommended Solution:
<solution>

Reasoning:
- <reason 1>
- <reason 2>
- <reason 3>

Potential Risks:
- <risk 1>
- <risk 2>

Recommended Next Steps:
1. <step 1>
2. <step 2>
3. <step 3>
""".strip()

DECISION_HUMAN_TEMPLATE = """
User Query:
{query}

Execution Plan:
{plan}

Research Findings:
{research}
""".strip()

decision_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", DECISION_SYSTEM_PROMPT),
        ("human", DECISION_HUMAN_TEMPLATE),
    ]
)


# Agent Function

def decision_agent(state: dict) -> dict:
    """
    Decision Agent node for LangGraph.

    Reads:
        state["query"]     – the user's original question
        state["plan"]      – the execution plan from PlannerAgent
        state["research"]  – findings from ResearcherAgent

    Writes:
        state["decision"]  – the recommended decision and reasoning
    """
    chain = decision_prompt | llm
    response = chain.invoke(
        {
            "query": state["query"],
            "plan": state["plan"],
            "research": state["research"],
        }
    )
    state["decision"] = response.content
    return state