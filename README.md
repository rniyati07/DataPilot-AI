# DataPilot AI

A conversational AI data analyst — upload a SQLite database and ask questions
about it in natural language. Built for the Sairam Hackathon 2026 / iTech AI
Innovation Hackathon 2026.

> **Status:** Batch 1 complete (Phases 0-3 — foundation, frontend skeleton,
> backend skeleton, Database Manager + SQLite upload). The LangChain agent
> and its five tools (`get_schema`, `execute_query`, `generate_chart`,
> `generate_flowchart`, `explain_data`) land in Batch 2. See `docs/` for the
> full specification.

## Architecture

```
React Frontend  →  FastAPI Backend  →  Database Manager  →  Active SQLite DB
```

See `docs/03_ARCHITECTURE.md` for the full system design.

## Prerequisites

- Python 3.11+
- Node.js 18+

## Setup — Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Seed the sample e-commerce database (idempotent, safe to re-run)
python data/seed.py

# Copy environment config
copy ..\.env.example ..\.env   # Windows
# cp ../.env.example ../.env   # macOS/Linux

uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`. Health check: `GET /api/health`.

## Setup — Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Environment Variables

See `.env.example` at the repo root for the full list (LLM provider config,
`DATABASE_URL`, `DATABASE_UPLOAD_DIR`, CORS origins, etc). The application
starts successfully without an LLM API key — the agent is not wired in yet.

## Uploading a database

Click "Upload SQLite Database" in the UI and choose a `.db`, `.sqlite`, or
`.sqlite3` file. It becomes the active database for your browser session
immediately. If no database is uploaded, the seeded sample `ecommerce.db`
(customers, categories, products, orders, order_items, inventory, payments)
is used automatically.

Each browser tab/session has its own active database — uploading a database
in one session never affects another session.

## Running backend tests

```bash
cd backend
venv\Scripts\python.exe -m pytest -q
```

## Project Structure

```
DataPilot AI/
├── docs/                  # Source-of-truth specification (PRD, TRD, architecture, etc.)
├── frontend/              # React + Vite + Tailwind
│   └── src/
│       ├── components/    # ChatWindow, DatabaseUpload, MessageBubble, etc.
│       ├── api/client.js  # Backend API client
│       └── lib/session.js # Session id issuance
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app + CORS
│   │   ├── config.py      # Environment-driven settings
│   │   ├── routes/        # /api/chat, /api/schema, /api/database/*, /api/health
│   │   ├── db/            # Database Manager, engine factory, access layer
│   │   ├── models/         # Pydantic request/response schemas
│   │   └── session/       # In-memory session → active-database mapping
│   ├── data/               # seed.py + ecommerce.db (committed) + uploads/ (gitignored)
│   └── tests/
├── .env.example
└── .gitignore
```

## Documentation

The complete specification lives in `docs/`:

1. `01_PRD.md` — Product requirements
2. `02_TRD.md` — Technical requirements/design
3. `03_ARCHITECTURE.md` — System architecture
4. `04_AGENT_TOOLS.md` — Agent tool contracts (Batch 2)
5. `05_IMPLEMENTATION_PLAN.md` — Phase-by-phase build plan
6. `06_TESTING_CHECKLIST.md` — Testing and acceptance criteria
