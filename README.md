# 🤖 AI Agent Coordination & Decision Engine

An Agentic AI platform that automatically investigates employee IT issues,
uses enterprise tools to find solutions, gives guided troubleshooting steps,
and raises a support ticket when the issue cannot be solved.

---

## 🔄 Complete Agent + Tool Workflow

Employee Reports IT Issue
          │
          ▼
     🗂️ Planner Agent
          │
          │ Creates investigation plan
          ▼
    🔍 Researcher Agent
          │
          │ Uses tools to collect evidence
          ▼
   ┌──────────────────────┐
   │      ENTERPRISE      │
   │        TOOLS         │
   ├──────────────────────┤
   │ 📚 Knowledge Base    │
   │ 🗃️ Incident Database │
   │ 👥 HR System         │
   │ 🏢 Infrastructure    │
   │ 📅 Calendar          │
   │ 🌐 Web Search        │
   └──────────┬───────────┘
              │
              │ Evidence
              ▼
       📊 Analysis Agent
              │
              │ Root Cause
              │ Severity
              │ Confidence
              ▼
       ⚖️ Decision Agent
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
   Confidence    Low Confidence
     >= 60%          < 60%
        │              │
        ▼              ▼
  Guided Solution   🎫 Create Ticket
        │              │
        ▼              ▼
    Employee       IT Support
      Tries
        │
   ┌────┴────┐
   │         │
   ▼         ▼
  Fixed    Not Fixed
   │         │
   ▼         ▼
RESOLVED    🔄 Retry
             │
             ▼
      Alternative Solution
             │
             ▼
       Employee Tries Again
             │
        ┌────┴────┐
        │         │
        ▼         ▼
      Fixed    Still Failed
        │         │
        ▼         ▼
    RESOLVED  🎫 Create Ticket
                  │
                  ▼
              IT Support
---

## 🤖 AI Agents

### 1. Planner Agent
Reads the employee issue and creates an investigation plan.

Example:
"VPN is disconnecting"

Plan:
- Search known VPN solutions
- Check similar incidents
- Check infrastructure
- Check maintenance
- Find the best resolution

### 2. Researcher Agent
Uses tools to collect evidence.

It decides which tools are useful and gathers information for the
Analysis Agent.

### 3. Analysis Agent
Analyzes the collected evidence.

It determines:
- Root cause
- Issue category
- Severity
- Confidence score
- Recommended solution

Example:

Root Cause: VPN client configuration problem
Confidence: 88%
Solvable: Yes

### 4. Decision Agent
Decides what should happen next.

Confidence >= 60%
        ↓
Guided Resolution

Confidence < 60%
        ↓
Create IT Support Ticket

### 5. Executor Agent
Finalizes the result and prepares the response shown to the employee
or IT Support.


---

## 🔧 9 Enterprise Tools

### 1. Knowledge Base
Searches structured IT troubleshooting knowledge.

Used when:
The AI needs known solutions and step-by-step instructions.

### 2. Incident Database
Searches previous incidents.

Used when:
The AI wants to know whether similar issues were solved before.

### 3. HR System
Provides employee and department information.

Used when:
Employee or organizational information is required.

### 4. Infrastructure Monitor
Checks simulated infrastructure/server health.

Used when:
The issue may be caused by VPN, server, network, or infrastructure problems.

### 5. Calendar System
Checks maintenance windows and blackout periods.

Used when:
The issue may be caused by planned maintenance.

### 6. Web Search
Provides additional technical information.

Used when:
The internal Knowledge Base does not contain enough information.

### 7. Email
Sends resolution instructions and status messages.

Used when:
The employee needs instructions or an incident update.

### 8. Ticket System
Creates an IT Support ticket.

Used when:
The AI cannot confidently solve the issue or troubleshooting attempts fail.

### 9. Notification
Creates internal dashboard notifications.

Used when:
IT Support needs to be notified about an important event.


---

## 🔄 Complete Agent + Tool Workflow

Employee
   ↓
Reports Issue
   ↓
Planner Agent
   ↓
Creates Investigation Plan
   ↓
Researcher Agent
   ↓
Uses Tools
   ├── Knowledge Base
   ├── Incident Database
   ├── HR System
   ├── Infrastructure Monitor
   ├── Calendar
   └── Web Search
   ↓
Research Evidence
   ↓
Analysis Agent
   ↓
Root Cause + Severity + Confidence
   ↓
Decision Agent
   ↓
 ┌──────────────────────┐
 │ Confidence >= 60%    │
 └──────────┬───────────┘
            ↓
     Guided Resolution
            ↓
      Employee Tries
            ↓
       ┌────┴────┐
       ↓         ↓
     Fixed    Not Fixed
       ↓         ↓
   RESOLVED    Retry
                 ↓
        Alternative Solution
                 ↓
           Still Failed?
                 ↓
          Ticket System
                 ↓
            IT Support


---

## 🧠 Example

Employee reports:

"My Outlook is disconnected and I cannot send or receive emails."

### Planner Agent
Creates an investigation plan.

### Researcher Agent
Uses:

Knowledge Base
→ Finds Outlook troubleshooting steps

Incident Database
→ Finds similar solved incidents

Infrastructure Monitor
→ Checks whether Outlook/email services are healthy

Calendar
→ Checks for planned maintenance

### Analysis Agent

Example result:

Root Cause:
Outlook authentication/session issue

Confidence:
88%

Solvable:
Yes

### Decision Agent

Because confidence is high:

→ Guided Resolution

Employee receives:

1. Close Outlook
2. Sign out of the account
3. Reopen Outlook
4. Sign in again
5. Test Send/Receive

### Employee Response

If employee selects:

"Yes, It's Fixed"

→ Incident becomes RESOLVED
→ Successful resolution can be stored in memory

If employee selects:

"Still Not Working"

→ System investigates again
→ Finds an alternative solution

If the alternative also fails:

→ Ticket is created
→ IT Support receives the complete history


---

## 🎫 Intelligent Ticket Escalation

The ticket contains more than just the original issue.

Example:

Ticket: TKT-10452

Employee Issue:
Outlook disconnected

AI Diagnosis:
Authentication/session problem

Confidence:
84%

Attempt 1:
Re-authentication

Result:
Failed

Attempt 2:
Outlook profile troubleshooting

Result:
Failed

Reason for Escalation:
Guided troubleshooting attempts failed.

This allows IT Support to continue from the point where the AI stopped.


---

## 🧠 Knowledge Base

The Knowledge Base contains structured IT resolution data.

Each article can contain:

- Issue
- Symptoms
- Possible Causes
- Resolution Steps
- Success Rate
- Confidence History
- Verified Resolution Data

Example:

Issue:
VPN disconnecting

Steps:
1. Restart VPN client
2. Sign in again
3. Reconnect VPN
4. Test connection

If employees successfully solve the issue, that successful resolution
can become useful historical evidence for future incidents.


---

## 🔄 Closed-Loop AI

The system does not simply give an answer and assume the problem is fixed.

It follows:

AI Investigation
      ↓
Solution
      ↓
Employee Tries
      ↓
Employee Feedback
      ↓
 ┌────┴─────┐
 ↓          ↓
Solved    Failed
 ↓          ↓
Resolved   Retry
             ↓
      Alternative Solution
             ↓
          Ticket


---

## 👥 Users

### Employee
- Reports IT issues
- Receives guided solutions
- Tries troubleshooting steps
- Confirms whether it worked
- Retries or raises a ticket

### IT Support
- Receives escalated tickets
- Reviews AI investigation
- Sees attempted solutions
- Resolves unresolved issues
- Updates incident status

### Admin
- Manages users
- Monitors agents
- Monitors tools
- Views logs and analytics
- Monitors overall platform


---

## 🗄️ Data Stored

The system stores:

- Employee information
- Incidents
- Historical incidents
- Knowledge articles
- Tickets
- Agent events
- Tool executions
- Audit logs
- Notifications
- Verified resolution memory
- Workflow results

Development:
SQLite

Production:
PostgreSQL / Supabase


---

## 🛠️ Technology Stack

LLM:
Llama 3.3 70B via Groq

AI:
LangChain + LangGraph

Backend:
FastAPI + Python

Database:
SQLite / PostgreSQL

Authentication:
JWT + RBAC

Email:
Gmail SMTP

Observability:
Agent Bus + LangSmith

Deployment:
Docker


---

## 📁 Main Project Structure

AI-Agent-Coordination-Decision-Engine/
│
├── api.py
├── workflow.py
├── agent_bus.py
├── memory.py
│
├── agents/
│   ├── planner.py
│   ├── researcher.py
│   ├── analysis.py
│   ├── decision.py
│   └── executor.py
│
├── tools/
│   ├── base_tool.py
│   ├── registry.py
│   ├── knowledge_tool.py
│   ├── database_tool.py
│   ├── hr_tool.py
│   ├── calendar_tool.py
│   ├── web_search_tool.py
│   ├── infrastructure_tool.py
│   ├── ticket_tool.py
│   ├── email_tool.py
│   └── notification_tool.py
│
├── database/
│   ├── connection.py
│   ├── seed.py
│   └── knowledge_base.json
│
├── services/
│   ├── policy_engine.py
│   └── audit_service.py
│
├── interface.html
├── requirements.txt
├── Dockerfile
├── LICENSE
└── README.md


---

## 🚀 Quick Start

### Clone

git clone https://github.com/AKHILGOUDA28/AI-Agent-Coordination-Decision-Engine.git

cd AI-Agent-Coordination-Decision-Engine

### Create Environment

python -m venv venv

### Windows

venv\Scripts\activate

### Install Packages

pip install -r requirements.txt

### Configure .env

Add:

GROQ_API_KEY=your_api_key
MODEL_NAME=llama-3.3-70b-versatile
JWT_SECRET_KEY=your_secret_key

### Seed Database

python database/seed.py

### Start Application

python api.py

Open:

http://localhost:8000


---

## 🔌 Important API

POST /auth/login
→ Login

POST /ask
→ Submit IT issue and start AI workflow

GET /incidents
→ View incidents

GET /incidents/{id}
→ View incident details

GET /knowledge
→ View Knowledge Base

GET /tools/stats
→ Tool statistics

GET /tools/executions
→ Tool execution history

GET /memory
→ AI resolution memory

GET /audit-logs
→ Audit history

GET /observability/metrics
→ System metrics

GET /health
→ System health

GET /docs
→ Swagger API documentation


---

## 🧪 Testing

Run:

pytest -v

The project tests:

- Agents
- Tools
- Database
- Policy Engine
- Workflow
- Failure handling


---


## 🎯 One-Line Description

An Agentic AI IT incident platform where coordinated AI agents use enterprise tools and historical knowledge to investigate employee issues, provide guided solutions, learn from feedback, and escalate unresolved problems to IT Support.
