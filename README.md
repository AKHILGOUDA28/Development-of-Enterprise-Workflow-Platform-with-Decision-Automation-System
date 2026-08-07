# AI Agent Coordination & Decision Engine

An enterprise-grade **AI Multi-Agent Coordination Platform** built with **LangChain**, **LangGraph**, **FastAPI**, **Groq (Llama 3.3)**, and **SQLite**.

The system coordinates **5 specialized AI agents** through a structured pipeline: Planner → Researcher → Analysis → Decision → Executor. It integrates 9 enterprise tools, a persistent long-term memory system, a pub-sub agent event bus, real-time monitoring APIs, and a premium dark-mode enterprise dashboard.

---

## Milestones Completed

| Milestone | Status | Description |
|---|---|---|
| **Milestone 1** — Agent Foundation | ✅ Done | 4-agent pipeline, 5 tools, FastAPI, SQLite, Dashboard |
| **Milestone 2** — Tool Integration | ✅ Done | 4 new enterprise tools, tool registry monitoring, 9 tools total |
| **Milestone 3** — Agent Coordination & Memory | ✅ Done | Analysis Agent, Event Bus, SQLite long-term memory, /events /memory APIs |

---

## 5-Agent Coordination Pipeline

```
User Incident Form (Name, Email, Category, Priority, Description)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                   LangGraph State Graph                         │
  │                                                                 │
  │  Planner Agent  →  Researcher Agent  →  Analysis Agent          │
  │  (Plan steps)     (KB + DB + Web)      (Root cause + severity)  │
  │                                              │                  │
  │                              ┌───────────────┘                 │
  │                              ▼                                  │
  │              Decision Agent  →  Executor Agent                  │
  │           (Auto-fix or Escalate)  (Final professional response) │
  └─────────────────────────────────────────────────────────────────┘
         │
         ▼
  Final Resolution on Dashboard + Email notification to user
```

---

## AI Agents

| Agent | Role | New in v2? |
|---|---|---|
| **Planner** | Breaks the issue into a logical troubleshooting plan | — |
| **Researcher** | Queries Knowledge Base, Incident DB, Web Search, HR System | Enhanced |
| **Analysis** ⭐ | Performs root-cause analysis, severity scoring (Critical/High/Medium/Low), confidence score (0–100%), and recommends Auto-Fix or Escalate | **NEW** |
| **Decision** | Evaluates analysis output; invokes ticket_system, email, calendar, weather tools | Enhanced |
| **Executor** | Synthesizes all outputs into a final professional response | Enhanced |

---

## Enterprise Tools (9 Total)

| Tool | Description | New in v2? |
|---|---|---|
| `knowledge_base` | Searches `knowledge_base.json` for known IT solutions | — |
| `incident_database` | Queries `incidents.db` for historical past tickets | — |
| `ticket_system` | Creates a new support ticket in `tickets.db` with a unique `INC` ID | — |
| `email` | Sends a real email via Gmail SMTP to the user's provided address | — |
| `notification` | Logs an in-app system alert | — |
| `hr_system` ⭐ | Employee lookups, department info, on-call schedules, manager assignments | **NEW** |
| `weather_service` ⭐ | Weather conditions, data center environmental monitoring, severe alerts | **NEW** |
| `calendar_system` ⭐ | Maintenance windows, blackout dates, scheduling, availability | **NEW** |
| `web_search` ⭐ | Enterprise IT knowledge gateway search — curated article summaries | **NEW** |

All tools extend `BaseTool` with: Pydantic schema validation, retry with exponential backoff, timeout protection.

---

## Agent Communication Event Bus

The `AgentEventBus` (`agent_bus.py`) provides a thread-safe **publish-subscribe** system for inter-agent coordination:

```python
from agent_bus import bus

# Agents publish lifecycle events
bus.publish("analysis_agent", "analysis_complete", {
    "severity": "High",
    "confidence": "85%",
    "strategy": "Escalate"
}, session_id="ABC123")

# API consumers retrieve events
events = bus.get_events(session_id="ABC123")
stats  = bus.get_stats()
```

---

## Persistent Long-Term Memory

`LongTermMemory` is backed by **SQLite** — facts survive server restarts:

```python
from memory import long_memory

long_memory.save("vpn_provider", "Cisco AnyConnect")
long_memory.recall("vpn_provider")   # → "Cisco AnyConnect"
long_memory.search("cisco")          # → [{"key": "vpn_provider", ...}]
long_memory.show_all()               # → all entries
long_memory.delete("vpn_provider")   # → True
```

---

## Dashboard (UI)

The enterprise dashboard (`interface.html`) features:

- **Sidebar Navigation**: 7 sections — Dashboard, Incidents, Knowledge Base, Tool Monitor, Agent Events, Memory Inspector, System Logs
- **5-Agent Pipeline Visualization**: Live animated status cards (Pending → Running → Completed) for all 5 agents
- **Incident Form**: Employee details, category dropdown, priority selector, issue description
- **Output Panels**: Per-agent output panels (Plan, Research, Analysis, Decision, Executor Preview) + Final Resolution box
- **Tool Monitor**: Table with per-tool call counts, success rates, avg latency, last used time
- **Agent Events Feed**: Colored event timeline from the pub-sub bus, with session filtering
- **Memory Inspector**: Live view of SQLite long-term memory with add/delete operations
- **System Logs Terminal**: Dark-themed trace log output

---

## API Endpoints (v2.0)

### Core
| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/`           | Serves HTML Dashboard |
| `GET`  | `/health`     | JSON health check (v2.0) |
| `POST` | `/ask`        | Runs the full 5-agent workflow |

### Tickets
| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/tickets`          | All tickets |
| `GET`  | `/tickets/{id}`     | Specific ticket |
| `POST` | `/tickets`          | Create ticket manually |
| `PUT`  | `/tickets/{id}`     | Update ticket status |

### Data
| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/knowledge`       | Knowledge base JSON |

### Long-Term Memory ⭐
| Method | Endpoint | Description |
|---|---|---|
| `GET`    | `/memory`              | All memory entries |
| `POST`   | `/memory`              | Save key-value fact |
| `DELETE` | `/memory/{key}`        | Delete a memory entry |
| `GET`    | `/memory/search/{q}`   | Full-text search |

### Agent Events ⭐
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/events`           | Recent bus events (filterable by session/type) |
| `GET` | `/events/stats`     | Event bus statistics |
| `GET` | `/events/sessions`  | All active session IDs |

### Monitoring ⭐
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tools/stats`    | Per-tool call counts, success rates, avg latency |
| `GET` | `/tools/list`     | All registered tools and descriptions |
| `GET` | `/agents/status`  | Agent pipeline status and run counts |

---

## Technology Stack

| Layer | Technology |
|---|---|
| **LLM** | Groq — `llama-3.3-70b-versatile` |
| **Agent Orchestration** | LangGraph + LangChain |
| **Backend API** | FastAPI + Uvicorn |
| **Databases** | SQLite (`incidents.db`, `tickets.db`, `memory.db`) |
| **Knowledge Base** | JSON file (`knowledge_base.json`) |
| **Email** | Python `smtplib` + Gmail SMTP |
| **Frontend** | Vanilla HTML / CSS / JavaScript (dark mode) |
| **Configuration** | `python-dotenv` |

---

## Project Structure

```
AI-Agent-Coordination-Decision-Engine/
│
├── .env                     ← API keys and email credentials
├── requirements.txt         ← Python dependencies
│
├── config.py                ← Loads .env, initializes Groq LLM
├── prompts.py               ← System prompt templates for all 5 agents
├── workflow.py              ← LangGraph pipeline (5-agent graph)
├── tracing.py               ← Runtime event logger
├── memory.py                ← Short-term + SQLite long-term memory
├── agent_bus.py             ← Pub-sub agent event bus ⭐ NEW
├── utils_parser.py          ← JSON tool-call extractor
│
├── agents/                  ← Agent persona modules
│   ├── planner.py
│   ├── researcher.py        ← Tool calling loop + bus events
│   ├── analysis.py          ← Root-cause analysis ⭐ NEW
│   ├── decision.py          ← Tool calling + email trigger loop
│   └── executor.py
│
├── tools/                   ← Enterprise tools
│   ├── base_tool.py         ← Base class with retries and validation
│   ├── registry.py          ← Registry with usage monitoring ⭐ ENHANCED
│   ├── knowledge_tool.py    ← Knowledge Base search
│   ├── database_tool.py     ← Incident Database query
│   ├── ticket_tool.py       ← Support ticket creation
│   ├── email_tool.py        ← Gmail SMTP email sender
│   ├── notification_tool.py ← In-app alert logger
│   ├── hr_tool.py           ← HR system simulation ⭐ NEW
│   ├── weather_tool.py      ← Weather/environmental monitoring ⭐ NEW
│   ├── calendar_tool.py     ← Scheduling/maintenance windows ⭐ NEW
│   └── web_search_tool.py   ← IT knowledge search ⭐ NEW
│
├── database/                ← Persistent storage
│   ├── knowledge_base.json  ← 20+ known IT issues and solutions
│   ├── incidents.db         ← Historical incident database
│   ├── tickets.db           ← Active support tickets
│   └── memory.db            ← Long-term memory store ⭐ NEW
│
├── api.py                   ← FastAPI server (20 endpoints)
├── interface.html           ← Enterprise Dashboard v2.0
└── tests.py                 ← 39-test suite
```

---

## Setup & Running

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Edit the `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=llama-3.3-70b-versatile

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

> **Note**: For Gmail, generate a 16-character **App Password** from Google Account → Security → 2-Step Verification → App Passwords.

### 3. Run the test suite

```bash
python -m unittest tests.py -v
```

All **39 tests** should pass, covering:
- Original tools (Knowledge, Database, Ticket, Email, Notification)
- New enterprise tools (HR, Weather, Calendar, Web Search)
- Tool registry monitoring (9 tools, call tracking, success rates)
- Agent event bus (pub/sub, filtering, session isolation, stats)
- Persistent long-term memory (save/recall/delete/search, cross-instance persistence)
- 5-agent workflow (all fields, Analysis output, unique session IDs, bus events)

### 4. Start the server

```bash
python api.py
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### 5. Use the dashboard

1. Fill in **Employee Name**, **ID**, **Department**, and **Email**
2. Select **Issue Category** and **Priority**
3. Describe your issue
4. Click **Analyze Incident**
5. Watch the **5-agent pipeline** animate in real-time
6. Navigate to **Tool Monitor** to see live tool statistics
7. Navigate to **Agent Events** to see the pub-sub coordination feed
8. Navigate to **Memory Inspector** to view/add persistent facts

---

## Data Flow Example

**Input**: *"My laptop cannot connect to the company VPN after today's Windows update."*

| Step | Agent | Action |
|---|---|---|
| 1 | Planner | Creates 4-step VPN troubleshooting plan |
| 2 | Researcher | Finds VPN solutions in KB + DB + Web Search; looks up HR on-call |
| 3 | Analysis | Root cause: driver/config conflict from Windows Update. Severity: Medium. Confidence: 80% |
| 4 | Decision | Detects known fix → calls `email` tool to send auto-fix steps to user |
| 5 | Executor | Generates: "Restart VPN Service → Flush DNS → Reinstall Client" |

**Output**: Professional resolution on screen + email sent + ticket created (if escalated) + events logged to bus.

---

## License

This project was developed as part of an AI Systems internship/project — Milestones 1–3.
