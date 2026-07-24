# AI Agent Coordination & Decision Engine

This project implements a stateful **AI Agent Coordination & Decision Engine** where four specialized AI agents collaborate to process user queries using **LangChain**, **LangGraph**, **FastAPI**, **Groq (Llama 3.3)**, and external Tools.

## What has been implemented (Milestone 1 & 2)

- **Agent Foundation**: Created separate cognitive agents (Planner, Researcher, Decision, and Executor) orchestrated sequentially via LangGraph.
- **Common Tool Interface**: Implemented schema-validated base tools with built-in timeout, retry backoffs, and safe fallbacks (`tools/base_tool.py`).
- **5 Functional Connectors**:
  - **Calculator**: Safely evaluates math expressions.
  - **Weather**: Fetches real-time weather using OpenWeatherMap API.
  - **Database**: Queries mock enterprise records.
  - **Email**: Simulates email sending with deliberate SMTP timeout test mode.
  - **Notification**: Logs system alerts.
- **Native LLM Tool Calling**: Decision agent dynamically outputs tool call intents in JSON schemas which are parsed, executed, traced, and looped back to the agent for final answer formulation.
- **Traced Execution**: Fully logs workflow state progression, tool timing metrics, and retry logs (`tracing.py`).
- **End-to-End Tests**: Full E2E tests validating mathematical precision, schema rejections, timeouts, and fallback workflows (`tests.py`).

## File Structure

```
project/
│
├── .env                ← Configure GROQ_API_KEY and MODEL_NAME
├── requirements.txt
│
├── config.py           ← Configures the shared Groq LLM client
├── prompts.py          ← System and human prompt templates
├── memory.py           ← Short-term and long-term memory store
├── workflow.py         ← LangGraph graph compiler
├── tracing.py          ← Custom workflow tracer & execution logger
│
├── agents/             ← Python agent persona package
│   ├── __init__.py
│   ├── planner.py
│   ├── researcher.py
│   ├── decision.py
│   └── executor.py
│
├── tools/              ← Schema-validated external tools
│   ├── __init__.py     ← Registers all tools
│   ├── base_tool.py    ← Common tool interface with retries and fallbacks
│   ├── registry.py     ← Central tool registry
│   ├── calculator.py   ← Arithmetic solver
│   ├── weather.py      ← Weather API connector
│   ├── database.py     ← Database record query tool
│   ├── email.py        ← SMTP simulator
│   └── notification.py ← System alerts logger
│
├── interface.html      ← UI web dashboard showing tracing metrics
├── api.py              ← FastAPI server serving the UI and ask endpoint
└── tests.py            ← Unit tests verifying success/failure workflows
```

## Setup & Running

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Add credentials**:
   Put your Groq API key in the `.env` file:
   ```env
   GROQ_API_KEY=gsk_your_api_key_here
   MODEL_NAME=llama-3.3-70b-versatile
   ```

3. **Run the testing suite**:
   ```bash
   python -m unittest tests.py
   ```

4. **Start the FastAPI server**:
   ```bash
   python api.py
   ```
   Open **`http://localhost:8000`** in your browser.
