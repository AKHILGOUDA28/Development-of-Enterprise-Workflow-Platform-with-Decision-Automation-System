AI Agent Coordination & Decision Engine
This project coordinates four AI agents (Planner, Researcher, Decision, and Executor) to process enterprise queries using LangGraph and FastAPI.

What has been implemented
Configured LangChain, LangGraph, and required environment dependencies.
Created the core AI agent personas (Planner, Researcher, Decision, and Executor).
Centralized all prompt templates to standardize agent roles.
Established a sequential workflow graph using LangGraph to pass shared state.
Integrated a dual-layer memory system supporting short-term session logs and long-term key-value storage.
Built a command-line interface (CLI) to test and run agents step-by-step.
Developed a FastAPI server to run the graph and expose API endpoints.
Designed a web-based dashboard to visualize progress and intermediate agent outputs.
How it works
Planner: Reads the question and creates a step-by-step plan.
Researcher: Gathers facts and domain context for each step of the plan.
Decision: Evaluates the gathered info and recommends the best solution.
Executor: Combines everything into the final polished answer.
The agents run in sequence, passing the output of one agent as context to the next using a LangGraph state workflow.

Key Features
Multi-Agent Orchestration: Automates complex tasks by dividing them among specialized agents.
Real-time LLM Output: Uses the Groq Llama 3.3 model for intelligent reasoning.
Service Resilience: If the Groq API key is missing or invalid, the engine automatically falls back to an offline simulated mode to prevent application crashes.
Shared memory: Supports short-term session logging and long-term key-value storage.
Interactive Dashboard: A single-page HTML interface to view intermediate agent steps and the final answer.
How to run
Install requirements: pip install -r requirements.txt

Put your Groq API key in the .env file: GROQ_API_KEY=gsk_your_api_key_here

Start the FastAPI server: python api.py
