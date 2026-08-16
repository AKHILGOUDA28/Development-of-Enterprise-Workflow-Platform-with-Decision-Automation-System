# AI IT Operations Command Center

> **An AI-powered IT Incident Triage and Workflow Automation Platform** that uses coordinated LLM agents, enterprise tools, persistent memory, and policy-controlled actions to investigate, resolve, or escalate IT incidents automatically.

---

## 📺 Live Dashboard

**http://localhost:8000**

| Credential | Username | Password | Role |
|-----------|----------|----------|------|
| Employee | `emp1024` | `password123` | Submit & view own incidents |
| IT Support | `itsupport` | `support123` | Manage incidents & tickets |
| Admin | `admin` | `admin123` | Full access + HITL approvals |

---

## 🏗️ Architecture

```
Employee
   ↓
Incident API (FastAPI)
   ↓
LangGraph Orchestrator
   ↓
┌──────────┬──────────┬──────────┐
│ Planner  │Researcher│ Analysis │
│  Agent   │  Agent   │  Agent   │
└──────────┴──────────┴──────────┘
      ↓ Tool Registry ↓
 KB · Incidents · HR · Calendar
 Web Search · Infra · Ticket
 Email · Notification
   ↓
Decision Agent → Policy Engine
   ↓
┌──────────────┬───────────────┐
│  Auto-Resolve│   Escalate    │
│  (email sent)│ (ticket + HITL)│
└──────────────┴───────────────┘
   ↓
Executor Agent
   ↓
Dashboard · Notifications · Audit Log
```

---

## 🤖 Five Agents

| Agent | Responsibility |
|-------|---------------|
| **Planner** | Breaks incident into structured investigation plan |
| **Researcher** | Calls enterprise tools to gather evidence |
| **Analysis** | Determines root cause, severity, confidence score |
| **Decision** | Policy-controlled routing: Auto-Fix / HITL / Escalate |
| **Executor** | Finalizes resolution, sends notifications |

---

## 🔧 Nine Tools

| Tool | Purpose |
|------|---------|
| Knowledge Base | Searches 100 approved IT resolution articles |
| Incident Database | Finds similar historical incidents |
| HR System | Looks up employee profiles, departments |
| Calendar | Checks maintenance windows & blackout periods |
| Web Search | External technical information |
| Infrastructure | Simulated infrastructure monitoring connector |
| Ticket System | Creates IT support tickets (INC-XXXXX) |
| Email | Sends resolution instructions via Gmail SMTP |
| Notification | Dashboard alerts & system notifications |



## 🗄️ Database Schema

| Table | Rows (seeded) | Purpose |
|-------|--------------|---------|
| `departments` | 10 | Company departments |
| `employees` | 100 | Extended HR profiles |
| `users` | 100+ | Authentication |
| `incidents` | 500+ | Historical incidents |
| `tickets` | 100+ | IT support tickets |
| `knowledge_articles` | 100 | Resolution knowledge base |
| `audit_logs` | 200+ | Complete action trail |
| `agent_events` | 500+ | Agent lifecycle events |
| `tool_executions` | — | Tool monitoring data |
| `notifications` | 80+ | Email/dashboard notifications |
| `long_term_memory` | 30+ | AI verified patterns |
| `workflow_results` | — | Workflow output records |

Supports **SQLite** (local dev) and **Supabase PostgreSQL** (production) — auto-detected via `DATABASE_URL`.

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/AKHILGOUDA28/AI-Agent-Coordination-Decision-Engine.git
cd AI-Agent-Coordination-Decision-Engine
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy and edit .env
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=gsk_your_key_here
MODEL_NAME=llama-3.3-70b-versatile
DATABASE_URL=postgresql://user:pass@host:port/db  # optional; falls back to SQLite
DIRECT_URL=postgresql://...                         # for DDL migrations
JWT_SECRET_KEY=your-secret-key
EMAIL_USER=your@gmail.com
EMAIL_PASSWORD=your-app-password
ALLOWED_ORIGINS=*
```

### 3. Seed Production Data
```bash
python database/seed.py
# Optional: reset all data first
python database/seed.py --reset
```

### 4. Start Server
```bash
python api.py
# or
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open Dashboard
Navigate to **http://localhost:8000** and log in.


## 📊 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | JWT login |
| `POST` | `/ask` | Submit incident → full workflow |
| `GET` | `/incidents` | List incidents (filterable) |
| `GET` | `/incidents/{id}` | Incident detail + audit trail |
| `PUT` | `/incidents/{id}/status` | Update status (IT Support+) |
| `POST` | `/incidents/{id}/approve` | HITL approve (Admin+) |
| `POST` | `/incidents/{id}/reject` | HITL reject (Admin+) |
| `GET` | `/analytics/summary` | KPI dashboard data |
| `GET` | `/analytics/trends` | 30-day incident trend |
| `GET` | `/analytics/agent-performance` | Agent timing stats |
| `GET` | `/employees` | Employee list (IT Support+) |
| `GET` | `/departments` | Department list |
| `GET` | `/knowledge` | Knowledge base (filterable) |
| `GET` | `/audit-logs` | Paginated audit trail |
| `GET` | `/policy/table` | Full policy rule table |
| `POST` | `/policy/evaluate` | Test a policy decision |
| `GET` | `/tools/stats` | Tool health metrics |
| `GET` | `/tools/executions` | Tool execution history |
| `GET` | `/notifications` | Recent notifications |
| `GET` | `/memory` | AI long-term memory |
| `GET` | `/observability/metrics` | System observability |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API docs (Swagger) |

---

## 📋 Testing

```bash
# Unit tests
python -m pytest tests/ -v

# Policy engine smoke test
python services/policy_engine.py

# Seed script dry run
python database/seed.py --reset
```

---

## 🔒 Security Features

- **JWT Authentication** — 24-hour tokens, HS256
- **RBAC** — Employee / IT Support / Admin roles
- **Rate Limiting** — Sliding window, 60 req/min per IP
- **Policy Engine** — Hard rules between AI and tool execution
- **Audit Logging** — Every action recorded with actor, timestamp, payload
- **HITL** — High-risk actions always require human approval
- **Environment variables** — No secrets in source code

---

## 🌐 Deployment

| Component | Recommended Platform |
|-----------|---------------------|
| Frontend (dashboard) | Serve via FastAPI static / Vercel |
| Backend API | Render / Railway / Fly.io / Docker |
| Database | Supabase PostgreSQL |
| LLM | Groq API (Llama 3.3 70B) |
| Email | Gmail SMTP / Microsoft Graph |

---

## 📁 Project Structure

```
AI-Agent-Coordination/
├── api.py                  # FastAPI REST API (all endpoints)
├── workflow.py             # LangGraph workflow orchestrator
├── agent_bus.py            # Event bus for agent coordination
├── auth.py                 # JWT + RBAC
├── config.py               # LLM + environment config
├── prompts.py              # LangChain prompt templates
├── memory.py               # Long-term memory manager
├── tracing.py              # LangSmith tracer wrapper
├── benchmark.py            # Evaluation benchmark suite
├── performance_test.py     # Concurrent load testing
│
├── agents/
│   ├── planner.py          # Planner Agent
│   ├── researcher.py       # Researcher Agent
│   ├── analysis.py         # Analysis Agent
│   ├── decision.py         # Decision Agent
│   └── executor.py         # Executor Agent
│
├── tools/
│   ├── base_tool.py        # Base tool class (timeout, retry, backoff)
│   ├── registry.py         # Tool registry + stats
│   ├── knowledge_tool.py   # KB search
│   ├── database_tool.py    # Historical incident search
│   ├── hr_tool.py          # Employee/department lookup
│   ├── calendar_tool.py    # Maintenance window check
│   ├── web_search_tool.py  # External tech search
│   ├── weather_tool.py     # Infrastructure monitoring (simulated)
│   ├── ticket_tool.py      # Ticket creation
│   ├── email_tool.py       # Email notification
│   └── notification_tool.py# Dashboard notification
│
├── database/
│   ├── connection.py       # SQLite + PostgreSQL manager
│   ├── init_db.py          # Schema creation + bootstrap seed
│   └── seed.py             # Production seed (500 incidents, 100 KB articles…)
│
├── services/
│   ├── policy_engine.py    # Enterprise action policy table
│   └── audit_service.py    # Centralized audit logging service
│
├── interface.html          # AI IT Operations Command Center (production dashboard)
├── analysis.html           # Analytics deep-dive page
│
├── tests/
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_database.py
│   ├── test_policy.py
│   └── test_workflow.py
│
├── Dockerfile              # Multi-stage production Docker build
├── requirements.txt
├── .env                    # Secrets (never commit)
├── .gitignore
└── README.md
```

