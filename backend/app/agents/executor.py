"""
Executor Agent
==============
Synthesises the plan, research, and decision into a polished final response
for the end user.  This is the last node in the workflow graph.
"""
from langchain_core.prompts import ChatPromptTemplate

from app.config import llm



# Prompt Template

EXECUTOR_SYSTEM_PROMPT = """
You are an Enterprise Response & Execution Agent.

Your responsibilities are:
1. Read the user's original request.
2. Review the execution plan.
3. Review the research findings.
4. Review the recommended decision.
5. Generate a professional, well-structured final response.
6. Do NOT expose internal reasoning or chain-of-thought.
7. Present only the polished final answer.

Return your output in EXACTLY this format:

Final Response

Overview:
<brief overview>

Recommended Solution:
<clear recommendation>

Implementation Steps:
1. <step 1>
2. <step 2>
3. <step 3>
4. <step 4>

Conclusion:
<concluding statement>
""".strip()

EXECUTOR_HUMAN_TEMPLATE = """
User Query:
{query}

Execution Plan:
{plan}

Research Findings:
{research}

Decision Recommendation:
{decision}
""".strip()

executor_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", EXECUTOR_SYSTEM_PROMPT),
        ("human", EXECUTOR_HUMAN_TEMPLATE),
    ]
)


# Agent Function

def executor_agent(state: dict) -> dict:
    """
    Executor Agent node for LangGraph.

    Reads:
        state["query"]        – the user's original question
        state["plan"]         – the execution plan from PlannerAgent
        state["research"]     – findings from ResearcherAgent
        state["decision"]     – recommendation from DecisionAgent

    Writes:
        state["final_answer"] – the polished final response for the user
    """
    chain = executor_prompt | llm
    response = chain.invoke(
        {
            "query": state["query"],
            "plan": state["plan"],
            "research": state["research"],
            "decision": state["decision"],
        }
    )
    state["final_answer"] = response.content
    return state