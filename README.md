# QueryVista

### Talk to your data. Get answers.

QueryVista is a conversational data analyst. Ask a question in plain English and an
LLM-powered agent inspects your database's live schema, writes read-only SQL, runs it,
and returns the query, the rows, a fitting visualization, and a grounded explanation —
in one conversation.

[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)](https://vite.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.3-1C3C3C?logo=langchain&logoColor=white)](https://langchain.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Plotly](https://img.shields.io/badge/Plotly-3-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/javascript)
[![Mermaid](https://img.shields.io/badge/Mermaid-11-FF3670?logo=mermaid&logoColor=white)](https://mermaid.js.org)
[![Tests](https://img.shields.io/badge/backend_tests-290_passing-3fb950)](#16-testing)

![QueryVista landing page](screenshots/queryvista-landing-hero.png)

---

## Table of Contents

| | | |
|---|---|---|
| [1. Overview](#1-overview) | [8. Visualization & Diagram Engine](#8-visualization--diagram-engine) | [15. Example Conversations](#15-example-conversations) |
| [2. The Problem](#2-the-problem) | [9. Conversational Intelligence](#9-conversational-intelligence) | [16. Testing](#16-testing) |
| [3. The QueryVista Approach](#3-the-queryvista-approach) | [10. The Five Agent Tools](#10-the-five-agent-tools) | [17. Deployment](#17-deployment) |
| [4. Quick Start](#4-quick-start) | [11. Schema Discovery](#11-schema-discovery) | [18. Running with Docker](#18-running-with-docker) |
| [5. Architecture](#5-architecture) | [12. Read-Only Safety](#12-read-only-safety) | [19. Hackathon Context](#19-hackathon-context) |
| [6. Conversation Flow](#6-conversation-flow) | [13. Session Model](#13-session-model) | [20. Team](#20-team) |
| [7. Data Source Flexibility](#7-data-source-flexibility) | [14. Error Recovery](#14-error-recovery) | [21. License](#21-license) |

---

## 1. Overview

QueryVista bridges the gap between non-technical stakeholders and structured business
data. Instead of waiting on analysts to write SQL, a product manager can type:

> **"Show me revenue by category for the last quarter as a pie chart."**

And receive, in seconds:

- The exact SQL the agent generated
- The result rows in a sortable table
- A Plotly pie chart (auto-chosen because the request asks for a share)
- A natural-language explanation grounded in the returned data

The agent is not a black box. Every capability is an explicit, testable tool:

1. `get_schema` — live schema discovery
2. `execute_query` — validated read-only execution
3. `generate_chart` — deterministic chart selection + Plotly spec
4. `generate_flowchart` — deterministic Mermaid diagrams (ER / process)
5. `explain_data` — LLM-backed explanation with aggregate fallback

---

## 2. The Problem

Structured business data (sales, customers, orders, inventory) lives in relational
databases. Non-technical stakeholders cannot query it directly. They must file tickets,
wait for analysts, and often receive static screenshots that cannot be explored.

Existing BI tools are powerful but have a steep learning curve and assume SQL literacy.
Conversational NL-to-SQL chatbots exist but usually stop at returning a table — no
visualization, no explanation, no diagram, and no guarantee the SQL is read-only or
correct.

---

## 3. The QueryVista Approach

QueryVista combines:

- **A conversational frontend** — chat, tables, charts, diagrams, SQL viewer
- **A FastAPI backend** — async, CORS, SSE-ready
- **A LangChain tool-calling agent** — not a generic SQL agent; five explicit tools
- **Deterministic engines** — Plotly spec builder, Mermaid diagram builder
- **SQLite only** — file-based, zero-config, runs anywhere

The agent reasons with these tools in sequence:

```
User question
    → get_schema (if schema unknown)
    → execute_query (read-only SQL, row/timeout limits)
    → generate_chart (if data shape + intent warrant it)
    → explain_data (grounded explanation)
    → generate_flowchart (if structure/process question)
```

---

## 4. Quick Start

### Prerequisites

- Python 3.11+
- Node 18+

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Seed the sample e-commerce database (idempotent)
python data/seed.py

# Copy environment config
# Windows:
copy ..\.env.example ..\.env
# macOS/Linux:
cp ../.env.example ../.env

uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`. Health: `GET /api/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Environment Variables

See `.env.example` at the repo root for the full list.

To enable the AI analyst, set:

```env
LLM_PROVIDER=openai        # openai | gemini | anthropic
LLM_MODEL=                 # optional override
LLM_API_KEY=your-key-here
```

---

## 5. Architecture

```
┌─────────────────┐     HTTP/SSE     ┌──────────────────┐
│  React Frontend │ ◄──────────────► │  FastAPI Backend │
│  (Vite dev /    │                  │  (Uvicorn)       │
│   Nginx prod)   │                  │                  │
└─────────────────┘                  └────────┬─────────┘
                                              │
                                    ┌─────────┴─────────┐
                                    │  Session Store    │
                                    │  (in-memory)      │
                                    └─────────┬─────────┘
                                              │
                                    ┌─────────┴─────────┐
                                    │ Database Manager  │
                                    │ (upload / active) │
                                    └─────────┬─────────┘
                                              │
                                    ┌─────────┴─────────┐
                                    │  Database Access  │
                                    │     Layer         │
                                    │  (SQLAlchemy)     │
                                    └─────────┬─────────┘
                                              │
                                    ┌─────────┴─────────┐
                                    │   SQLite File     │
                                    │  (default/upload) │
                                    └───────────────────┘
```

- **No Redis, PostgreSQL, or MCP** — SQLite is the only database
- **Session state is in-memory** — lost on backend restart
- **Docker Compose available** — see [Running with Docker](#18-running-with-docker)

---

## 6. Conversation Flow

1. User opens dashboard → sees landing page
2. User optionally uploads a `.db` / `.sqlite` / `.sqlite3` file (max 50 MB)
3. User starts a conversation (each thread gets its own session ID)
4. User asks a natural-language question
5. Backend routes through the agent:
   - `get_schema` discovers tables/columns/types/PK/FK
   - `execute_query` runs validated read-only SQL
   - `generate_chart` builds Plotly spec from data shape + intent
   - `explain_data` provides grounded explanation
   - `generate_flowchart` renders Mermaid (ER / process / decision)
6. Frontend renders: answer + SQL panel + table + chart + explanation + diagram
7. Follow-ups resolve against conversation memory (bounded window) and last result set

---

## 7. Data Source Flexibility

| Source | Description |
|--------|-------------|
| **Default** | Seeded e-commerce DB (`backend/data/ecommerce.db`) — committed, idempotent seed |
| **Upload** | User provides SQLite file → validated, stored in `backend/data/uploads/`, becomes active DB for that session |
| **Clear** | Reverts session to default DB |

Upload validation: extension allowlist, size limit, **SQLite header check** (`SQLite format 3\0`).

---

## 8. Visualization & Diagram Engine

### Chart Selection (deterministic, no LLM)

| Data shape | Intent hint | Chart type |
|------------|-------------|------------|
| Single numeric series over time | "trend", "over time" | Line |
| Categorical + numeric | "compare", "by category" | Bar |
| Part-of-whole | "share", "proportion", "%" | Pie |
| Two numeric series | "correlation", "vs" | Scatter |
| Single value | — | None (table only) |

Palette: shared cyan/indigo/violet theme across all chart types.

### Diagrams (deterministic, no LLM)

- **ER** — live schema → `erDiagram` (tables, columns, types, PK, FK)
- **Process** — agent-supplied step graph → `flowchart TD`
- **Decision** — entities/description → decision tree (bonus)

---

## 9. Conversational Intelligence

- **Multi-turn context** — bounded window (6 turns) + last result set
- **Pronoun/entity resolution** — "now show their trend" → re-queries if needed
- **Self-correction** — exactly 1 retry on `execute_query` SQL errors
- **Grounded explanations** — aggregates passed to LLM for >50 rows; fallback for LLM failure
- **No hallucination** — agent never invents table/column names; must call `get_schema` first

---

## 10. The Five Agent Tools

| Tool | Purpose | LLM call? |
|------|---------|-----------|
| `get_schema` | Discover tables, columns, types, PK, FK | No |
| `execute_query` | Run read-only SELECT/WITH, row/timeout limits | No |
| `generate_chart` | Build Plotly spec from data + intent | No |
| `explain_data` | Natural-language explanation of result | Yes |
| `generate_flowchart` | Build Mermaid ER / process / decision | No |

All tools use **structured Pydantic I/O** — no free-text parsing.

---

## 11. Schema Discovery

`get_schema` uses SQLAlchemy Inspector against the **currently active database** (default
or session upload). Returns structured JSON with:

```json
{
  "tables": [
    {
      "name": "products",
      "columns": [
        {"name": "id", "type": "INTEGER", "primary_key": true, "nullable": false},
        {"name": "name", "type": "VARCHAR(150)", "primary_key": false, "nullable": false}
      ],
      "foreign_keys": [{"column": "category_id", "references": "categories.id"}]
    }
  ]
}
```

---

## 12. Read-Only Safety

`execute_query` rejects any statement containing forbidden keywords at word boundaries,
with quoted-string masking:

```python
FORBIDDEN = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", ...}
```

False positives avoided:
- `SELECT updated_at FROM orders` ✅ (not `UPDATE`)
- `SELECT 'delete' AS status` ✅ (quoted)

---

## 13. Session Model

- `X-Session-Id` header on every request (frontend generates UUID, stores in localStorage)
- Each conversation thread → new session ID → isolated backend context
- In-memory session store holds:
  - Active database path (default or upload)
  - Schema cache (invalidated on DB switch)
  - Conversation memory (bounded)
  - Last result set (for follow-ups)

---

## 14. Error Recovery

- **Single retry** on `execute_query` SQL errors (ContextVar-budgeted, not prompt-based)
- **LLM unavailability** → structured error envelope, no crash
- **Upload validation failure** → 400 with user-safe message
- **No uncaught exceptions** cross tool boundaries

---

## 15. Example Conversations

> **User:** "What are the top 5 categories by revenue?"
> 
> **Agent:** Runs query → bar chart → explanation → "Electronics leads at $124K"
> 
> **User:** "Show me the ER diagram for this database."
> 
> **Agent:** Calls `generate_flowchart` with `diagram_type: "er"` → renders Mermaid
> 
> **User:** "Compare revenue by month for 2023."
> 
> **Agent:** Line chart (time-series intent) → explains seasonal peaks

---

## 16. Testing

```bash
cd backend
pytest -q
```

**290 tests pass** across 19 modules, covering the SQL validator and its named
false-positive regressions (`SELECT 'delete' AS status`, `updated_at`), read-only
enforcement, upload validation and path-traversal handling, session isolation, dynamic
schema discovery, chart-type selection, Mermaid generation, conversation memory, bounded
error recovery, and SQL transparency. Agent tests drive a scripted fake chat model, so the
suite is deterministic and needs no API key.

Frontend checks:

```bash
cd frontend
npm run lint     # oxlint
npm run build    # production build
```

Both pass. The test suite is meaningful but not exhaustive — there is no automated
browser/E2E layer, and the UI has been verified manually.

---

## 17. Deployment

QueryVista currently runs as a documented local two-process setup: Uvicorn serving the
FastAPI backend, and Vite serving the frontend (`npm run build` produces a static bundle in
`frontend/dist`).

**Docker Compose is also available** — see [Running with Docker](#18-running-with-docker).

---

## 18. Running with Docker

QueryVista can be run entirely with Docker. This requires Docker Desktop to be
installed on your machine.

### Prerequisites

- Docker Desktop (or equivalent Docker Engine + Compose v2)
- A `.env` file at the repo root (copy from `.env.example`)

### Environment

Copy `.env.example` to `.env` and fill in your LLM credentials:

```bash
cp .env.example .env
```

The backend reads `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_API_KEY` from `.env`.
These are passed into the backend container via Compose and are **never** baked
into the image or committed to the repository.

### Build and run

```bash
docker compose up --build
```

### Stop

```bash
docker compose down
```

### Access

| Service  | URL                     |
|----------|-------------------------|
| Frontend | http://localhost:5173  |
| Backend  | http://localhost:8000  |

Open the frontend URL in your browser. The Swagger API docs are available at
`http://localhost:8000/docs`.

### Persistence

Two named Docker volumes keep state across container restarts and recreations:

- `queryvista-data` — the SQLite database (`backend/data/ecommerce.db`)
- `queryvista-uploads` — user-uploaded SQLite files

Database writes and uploaded files survive `docker compose down` / `up` because
they live in volumes, not in the writable container layer. **Do not** run
`docker compose down -v` unless you intend to delete this data.

### Logs

```bash
docker compose logs backend        # backend (FastAPI/Uvicorn)
docker compose logs frontend       # frontend (Nginx)
docker compose logs -f backend     # follow backend logs
```

### Limitations

- The session model is in-memory (per the application design). Sessions are lost
  when the backend container is recreated. Run a single backend instance.
- There is no Redis, PostgreSQL, or MCP server — SQLite is the only database.

---

## 19. Hackathon Context

QueryVista was built for the **iTech AI Innovation Hackathon 2026** (1–7 August 2026),
under the challenge *Building Intelligent LLM Agents for Database Interaction &
Visualization*.

The challenge asks for a conversational application in which an LLM agent understands
natural-language data questions, queries a real database, visualizes the results, explains
them, and does so through custom function-calling tools. QueryVista addresses that with an
agent whose entire capability surface is five explicitly-defined tools — schema discovery,
validated read-only execution, chart generation, diagram generation, and explanation —
composed at runtime against whichever database the session has connected.

---

## 20. Team

QueryVista was built by a team of student developers for the **iTech AI Innovation Hackathon 2026**.

| Member | Role | Contribution |
|---|---|---|
| **Niyati R** | AI/ML & Agent Engineering | LLM agent, tool orchestration, SQL reasoning |
| **Likitha T** | Backend & Database Engineering | API layer, database integration, query execution |
| **Akshaya VM** | Frontend & Visualization Engineering | React interface, charts, diagrams, user experience |

---

## 21. License

No license file is currently included in this repository. All rights reserved by the
authors unless a license is added.