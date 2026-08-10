# DataPilot AI

A conversational AI data analyst — upload a SQLite database and ask questions
about it in natural language. Built for the Sairam Hackathon 2026 / iTech AI
Innovation Hackathon 2026.

> **Status:** Batch 2 complete (Phases 0-6). You can ask a natural-language
> question and get a real answer from your database. Two of the five agent
> tools are implemented — `get_schema` and `execute_query`. The remaining
> three (`generate_chart`, `explain_data`, `generate_flowchart`) land in
> Batch 3. See `docs/` for the full specification.

## Architecture

```
React Frontend
    →  FastAPI Backend
        →  LangChain Agent  →  get_schema / execute_query
            →  Database Manager  →  Active SQLite DB
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
`DATABASE_URL`, `DATABASE_UPLOAD_DIR`, query guards, CORS origins, etc).

### Enabling the AI analyst

Chat requires an LLM API key. Set these in `.env`:

```
LLM_PROVIDER=openai        # openai | gemini | anthropic
LLM_MODEL=                 # optional; a sensible per-provider default is used
LLM_API_KEY=your-key-here
```

The backend still starts and serves `/api/health` and all `/api/database/*`
endpoints without a key — chat returns a structured `llm_unavailable`
message instead of crashing.

## Example questions

- "Show me the top 5 products by revenue."
- "How many customers are in the database?"
- "Which category has the most products?"

Every data-producing answer returns the generated SQL alongside the result
table, so you can always see exactly what ran.

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
│   │   ├── agent/         # LLM provider factory, tool registry, agent service
│   │   ├── tools/         # get_schema, execute_query
│   │   ├── db/            # Database Manager, engine factory, access layer, SQL validator
│   │   ├── models/         # Pydantic request/response schemas
│   │   └── session/       # In-memory session → active-database mapping + context
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
