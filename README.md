# AI Agent Coordination & Decision Engine

This project implements a basic **AI Agent Coordination & Decision Engine** where four specialized AI agents collaborate to process user queries using **LangChain**, **LangGraph**, **FastAPI**, and the **Groq Llama 3.3** model.

## What has been implemented

- Configured LangChain, LangGraph, and required project dependencies.
- Configured the Groq LLM using a shared configuration.
- Created four AI agents:
  - Planner Agent
  - Researcher Agent
  - Decision Agent
  - Executor Agent
- Implemented prompt templates for each agent.
- Established a sequential workflow using LangGraph.
- Implemented shared state (memory) for agent communication.
- Developed a FastAPI server with REST API endpoints.
- Created a basic testing interface using FastAPI Swagger UI.

## How it works

**Planner Agent**
- Understands the user's request.
- Breaks the request into logical execution steps.

**Researcher Agent**
- Collects relevant information based on the execution plan.
- Summarizes useful findings.

**Decision Agent**
- Analyzes the research results.
- Evaluates possible options.
- Recommends the best solution.

**Executor Agent**
- Combines the outputs from all previous agents.
- Generates the final response for the user.

The agents execute sequentially using a **LangGraph workflow**, where the output of one agent becomes the input for the next agent through a shared state.

## Key Features

- Multi-Agent Coordination using LangGraph.
- Shared LLM configuration using Groq Llama 3.3.
- Modular AI agent architecture.
- Shared state for agent communication.
- FastAPI REST API for interacting with the workflow.
- Automatic API testing using FastAPI Swagger UI.

## Technologies Used

- Python
- FastAPI
- LangChain
- LangGraph
- Groq (Llama 3.3)
- python-dotenv

## How to Run

### Install dependencies

```bash
pip install -r requirements.txt

Put your Groq API key in the `.env` file:

```env
GROQ_API_KEY=gsk_your_api_key_here
MODEL_NAME=llama-3.3-70b-versatile

Start the FastAPI server:

python api.py
