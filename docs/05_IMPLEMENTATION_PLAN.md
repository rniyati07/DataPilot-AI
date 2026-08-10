# Implementation Plan

**Project:** AI Data Analyst — Conversational Database Intelligence
**Companion documents:** `01_PRD.md`, `02_TRD.md`, `03_ARCHITECTURE.md`,
`04_AGENT_TOOLS.md`, `06_TESTING_CHECKLIST.md`
**Purpose:** a sequential, phase-by-phase build roadmap Claude Code can
follow directly. Every phase names its goal, concrete tasks, the files it
touches, its dependencies, testable acceptance criteria, and its main risk.

**Today's date, for planning purposes, is 9 August 2026** — the same day
Phase 0 begins under the schedule below. Target code freeze is **11 August
2026**; submission deadline is **12 August 2026**.

No new technology, phase reordering into a horizontal (backend-then-frontend)
strategy, or scope addition is introduced here — this plan sequences exactly
what `01_PRD.md`, `02_TRD.md`, and `03_ARCHITECTURE.md` already define.

---

## 1. Implementation Strategy: Vertical Slices

The build proceeds **vertically**, not horizontally:

```
Frontend skeleton + Backend skeleton + Database + Basic agent + Integration
        ↓
One complete, working, end-to-end flow (Phase 6 milestone)
        ↓
Expand tools (chart → explain → diagrams)
        ↓
Reliability (multi-turn, error recovery)
        ↓
Polish, testing, packaging
```

This is **not** "build the whole backend, then the whole frontend, then
integrate at the end." Every phase from Phase 6 onward keeps the full stack
runnable end-to-end; new capability is added to an already-working system,
never assembled for the first time under deadline pressure on Day 3.

---

## 2. Reference Repository Structure

The phases below refer to this indicative layout (introduced incrementally,
starting in Phase 0):

```
repo/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── SqlPanel.jsx
│   │   │   ├── ResultTable.jsx
│   │   │   ├── ChartRenderer.jsx
│   │   │   ├── DiagramRenderer.jsx
│   │   │   ├── StatusIndicator.jsx
│   │   │   ├── ErrorBanner.jsx
│   │   │   └── DatabaseUpload.jsx
│   │   ├── api/client.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json / vite.config.js / tailwind.config.js
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes/{chat.py, schema.py, database.py, health.py}
│   │   ├── agent/{agent_service.py, tool_registry.py, llm_provider.py, memory.py}
│   │   ├── tools/{get_schema.py, execute_query.py, generate_chart.py, generate_flowchart.py, explain_data.py}
│   │   ├── db/{engine.py, access_layer.py, sql_validator.py, database_manager.py}
│   │   ├── viz/plotly_builder.py
│   │   ├── diagrams/mermaid_builder.py
│   │   ├── models/schemas.py
│   │   └── session/store.py
│   ├── tests/test_*.py
│   ├── data/{ecommerce.db, seed.py, uploads/}
│   ├── requirements.txt
│   └── Dockerfile
├── docs/  (this document set)
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Scope Classification (applies across all phases)

| Tier | Contents |
|---|---|
| **MUST HAVE** | The five required tools (`04_AGENT_TOOLS.md`), SQLite database upload/switch with the seeded database as default (Phase 3, PRD §5.9), and the core conversational experience: chat UI, NL→SQL→result, bar/line/pie charts, ER + process diagrams. |
| **SHOULD HAVE** | SQL transparency, multi-turn context, error correction/retry, streaming *if feasible*, Docker, unit tests. |
| **BONUS** | Scatter charts, decision-tree diagrams, query history, CSV export, PNG/PDF export, multi-database swap demonstration — attempted **only** after everything in MUST/SHOULD is stable. |
| **OUT OF SCOPE** | Voice input, collaborative sharing, custom dashboard builder, authentication, RAG, microservices, distributed infrastructure. |

Bonus features must never delay a MUST or SHOULD item. This ordering governs
every phase below.

---

## 4. Phases

Each phase lists **Goal / Tasks / Files & Modules Affected / Dependencies /
Acceptance Criteria / Potential Risks**.

### Phase 0 — Repository and Environment Setup
**Tier:** MUST
**Goal:** A minimal, runnable skeleton exists; frontend and backend each
start independently with no functionality yet.
**Tasks:**
- Initialize git repository and `.gitignore`: exclude Node/Python build
  artifacts, `venv`, `.env`, the runtime SQLite artifacts
  `*.db-wal`, `*.db-shm`, `*.db-journal`, and the contents of the
  session-upload storage directory (`data/uploads/*`, keeping the directory
  itself via a `.gitkeep`) — uploaded databases are session-scoped runtime
  data, never committed. The seed `data/ecommerce.db` file itself is
  **not** ignored — it is intentionally committed once seeded in Phase 3,
  so a judge can clone the repository and reproduce the demo immediately
  without a seed step. `.env.example` is committed; `.env` is not.
- Create `.env.example` mirroring every variable in `02_TRD.md` §10 (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `DATABASE_URL`, `DATABASE_UPLOAD_DIR`, `DATABASE_UPLOAD_MAX_MB`, `BACKEND_HOST`, `BACKEND_PORT`, `CORS_ALLOWED_ORIGINS`, `VITE_API_BASE_URL`).
- Scaffold `frontend/` via Vite + React + Tailwind.
- Scaffold `backend/` package structure (empty modules per §2 above) and `requirements.txt` (FastAPI, Pydantic, SQLAlchemy, LangChain, provider SDKs, Plotly, pytest).
**Files/modules affected:** repo root, `frontend/*`, `backend/app/*` (stubs), `.env.example`, `.gitignore`.
**Dependencies:** none (first phase).
**Acceptance criteria:** `npm run dev` serves a blank Vite page; the FastAPI app boots under `uvicorn` without errors; `.env.example` lists every TRD §10 variable; nothing sensitive is committed.
**Potential risks:** Node/Python version drift across a 3–5 person team — pin versions in the (later) README from the start rather than discovering mismatches on Day 3.

---

### Phase 1 — Frontend Skeleton
**Tier:** MUST
**Goal:** A functional ChatGPT-like UI shell exists, driven by mock data,
before any backend logic is ready.
**Tasks:**
- Build all nine components named in `03_ARCHITECTURE.md` §8: `ChatWindow`, `MessageBubble`, `SqlPanel`, `ResultTable`, `ChartRenderer`, `DiagramRenderer`, `StatusIndicator`, `ErrorBanner`, `DatabaseUpload`.
- `ChatWindow` owns session id + message list local state (React state/context — no Redux, per TRD §2).
- `MessageBubble` conditionally renders `SqlPanel → ResultTable → ChartRenderer/DiagramRenderer` in that fixed order for agent turns (PRD §5.6 order).
- `DatabaseUpload` (mock mode) — a simple file-picker affordance plus an "Active database: …" label; wired to mocked upload responses for now, matching the shape agreed in Phase 2/3.
- Stub `api/client.js` returning mocked response envelopes matching the shape agreed in Phase 2.
**Files/modules affected:** `frontend/src/components/*.jsx`, `frontend/src/App.jsx`, `frontend/src/api/client.js` (mock mode).
**Dependencies:** Phase 0.
**Acceptance criteria:** a user can type a message, see it appended, and see a mocked agent response rendered in the correct component order; `StatusIndicator` and `ErrorBanner` render correctly for mocked loading/error states; `DatabaseUpload` shows a mocked active-database label and accepts a file selection.
**Potential risks:** over-investing in visual polish this early — explicitly time-boxed; deep styling is Phase 14's job, not this one.

---

### Phase 2 — Backend Skeleton
**Tier:** MUST
**Goal:** FastAPI app with the required routes (chat, schema, database
management, health) and locked-in Pydantic response contracts, returning
canned (not yet agent-driven) responses.
**Tasks:**
- `app/main.py` app instance + CORS configured from `CORS_ALLOWED_ORIGINS`.
- `routes/chat.py` — `POST /api/chat`, returns a canned but correctly-shaped response envelope (message, sql, table, chart, diagram, error — per Architecture §8/§5).
- `routes/schema.py` — `GET /api/schema` stub.
- `routes/database.py` — `POST /api/database/upload`, `GET /api/database/current`, `DELETE /api/database/current` stubs, returning a canned active-database name for now (real validation/storage lands in Phase 3).
- `routes/health.py` — `GET /api/health`.
- `models/schemas.py` — Pydantic request/response models, finalizing the response envelope shape used by every later phase.
**Files/modules affected:** `backend/app/main.py`, `backend/app/routes/*.py`, `backend/app/models/schemas.py`, `backend/app/config.py`.
**Dependencies:** Phase 0.
**Acceptance criteria:** the Phase 1 frontend can call the real `/api/chat` and `/api/database/*` endpoints and receive canned-but-correctly-shaped responses instead of mocks; `/api/health` returns `200`.
**Potential risks:** the response envelope shape drifting later once real tool output is wired in — lock it here against `03_ARCHITECTURE.md` §5/§8 so Phase 6+ never needs to change `MessageBubble`'s rendering logic, only its data source.

---

### Phase 3 — Database Manager, SQLite Upload, and Sample Database
**Tier:** MUST
**Goal:** the seeded SQLite e-commerce database exists as the default
dataset, the Database Manager and SQLite upload path exist end-to-end, and
the Database Access Layer/Inspector are wired to whichever database is
currently active — **not** hardcoded to the seed file. This phase is
pulled forward in the build order (relative to a database-agnostic plan)
precisely because the active-database concept affects every downstream
tool phase (PRD §5.9, task brief "database upload support early").
**Tasks:**
- Write `data/seed.py` creating the seven tables (`customers`, `categories`, `products`, `orders`, `order_items`, `inventory`, `payments`) with the foreign-key relationships shown in `03_ARCHITECTURE.md` §10, populated with a small but realistic dataset (tens of rows per table — enough for meaningful aggregation/trend demos, not so much that generation eats Day 1). This becomes the default/sample database (PRD §5.9), committed as `data/ecommerce.db`.
- `db/engine.py` — engine factory that builds a SQLAlchemy engine from an arbitrary resolved database path/URL (no longer assuming a single global engine tied to `DATABASE_URL`).
- `db/database_manager.py` — the Database Manager (TRD §5): `validate_upload()` (extension + genuine-SQLite header check), `register_database()` (stores the file under `DATABASE_UPLOAD_DIR` with a generated, session-scoped filename — path-traversal-safe), `get_active_database(session_id)` (returns the seed database's path until/unless the session has uploaded one), `get_connection(session_id)` (hands the resolved engine to the Database Access Layer), `cleanup_session_database(session_id)`.
- `db/access_layer.py` — the single module that imports SQLAlchemy's engine/`Inspector`; obtains its target engine via `database_manager.get_connection(session_id)` rather than a hardcoded engine; no other module opens its own connection (Architecture Rule 5/7/13).
- Wire `routes/database.py` (stubbed in Phase 2) to the real Database Manager: `POST /api/database/upload` (validate → register → mark active), `GET /api/database/current` (active database name/source), `DELETE /api/database/current` (revert session to the default database).
- `frontend/src/components/DatabaseUpload.jsx` — real implementation replacing its Phase 1 mock, calling the endpoints above and showing the active-database indicator.
**Files/modules affected:** `backend/data/seed.py`, `backend/data/ecommerce.db`, `backend/app/db/engine.py`, `backend/app/db/access_layer.py`, `backend/app/db/database_manager.py`, `backend/app/routes/database.py`, `frontend/src/components/DatabaseUpload.jsx`.
**Dependencies:** Phase 0, Phase 2 (route stubs).
**Acceptance criteria:** the seed script is re-runnable/idempotent; a throwaway script confirms the Inspector can list all seven seed tables with correct columns and foreign keys when no upload has occurred; uploading a second, differently-shaped SQLite test file through `POST /api/database/upload` makes `GET /api/database/current` report it as active and changes what the Access Layer sees for that session — with no code change required; an invalid (non-SQLite, or wrong-extension) upload is rejected and leaves the previously-active database untouched; one session's upload is not visible to a second session's requests (FR-16).
**Potential risks:** spending too long hand-crafting "realistic" seed data — cap effort; a plausible small dataset is sufficient for demo purposes. Also: under-scoping this phase because it looks like "just" the old database phase — it now also carries the Database Manager and the upload API, which several later phases (4, 5, 6) depend on; do not compress it to fit the old single-database phase's time budget.

---

### Phase 4 — `get_schema`
**Tier:** MUST
**Goal:** the first of the five mandatory tools, implemented and
independently testable per `04_AGENT_TOOLS.md`, operating against
whichever database the Database Manager reports as active.
**Tasks:** implement `tools/get_schema.py` exactly to the Tool 1 contract (input/output schema, session-scoped cache with `refresh` support keyed to the session's active database, error handling).
**Files/modules affected:** `backend/app/tools/get_schema.py`, `backend/app/session/store.py` (cache hook only — full session store lands in Phase 7).
**Dependencies:** Phase 3.
**Acceptance criteria:** matches `04_AGENT_TOOLS.md` Tool 1 §12 testing requirements — tables/columns/types/relationships returned correctly for the default database; no hardcoded schema; structured output; graceful handling of an unreachable database; switching a session's active database (via Phase 3's upload endpoint) and re-calling `get_schema` returns the new database's schema, not a cached/stale one.
**Potential risks:** low — flagged as the lowest-risk of the five tool phases.

---

### Phase 5 — `execute_query`
**Tier:** MUST
**Goal:** the second tool — the system's security boundary (Clarification 2)
— implemented per the Tool 2 contract, enforced uniformly against
whichever database is currently active.
**Tasks:**
- `db/sql_validator.py` — the keyword/multi-statement guard, built as its own independently unit-testable module (word-boundary regex, not a full SQL parser, per Clarification 2's "practical validation" guidance).
- `tools/execute_query.py` — wraps the validator + `db/access_layer.py`'s read-only execution path, row-limit enforcement (`HARD_ROW_CEILING` env-configured), and a statement timeout.
- Begin `backend/tests/test_execute_query.py` now (not deferred to Phase 15), given this tool's security weight.
**Files/modules affected:** `backend/app/db/sql_validator.py`, `backend/app/tools/execute_query.py`, `backend/app/db/access_layer.py` (execution helper), `backend/tests/test_execute_query.py`.
**Dependencies:** Phase 3.
**Acceptance criteria:** matches `04_AGENT_TOOLS.md` Tool 2 §12 — every destructive statement type and multi-statement input rejected before touching the database; valid SELECT/aggregation/JOIN/ORDER BY/LIMIT succeed; the word-boundary regression test (a column like `updated_at` is not falsely rejected) and the quoted-literal regression test (`SELECT 'delete' AS status` is not falsely rejected) both pass explicitly.
**Potential risks:** over-engineering a full SQL parser — explicitly avoided per Clarification 2; keep the validator lightweight and regex/keyword-based.

---

### Phase 6 — LangChain Agent (Day 1 milestone)
**Tier:** MUST — **this is the single most important milestone in the whole
plan.**
**Goal:** the first complete, end-to-end natural-language-to-database flow
works through the real UI.
**Tasks:**
- `agent/llm_provider.py` — provider factory selected by `LLM_PROVIDER`.
- `agent/tool_registry.py` — registers `get_schema` + `execute_query` (only these two at this phase).
- `agent/agent_service.py` — the LangChain tool-calling agent executor (explicitly **not** `create_sql_agent` or any generic black-box SQL agent — per the task brief's mandatory-tools constraint).
- Wire `routes/chat.py` to call `agent_service` instead of the Phase 2 canned response.
- Point `frontend/src/api/client.js` at the real endpoint, removing the mock.
**Files/modules affected:** `backend/app/agent/*.py`, `backend/app/routes/chat.py`, `frontend/src/api/client.js`.
**Dependencies:** Phases 1, 2, 4, 5.
**Acceptance criteria:** "Show me the top 5 products by revenue." works end-to-end through the real UI, using `get_schema` + `execute_query` only (chart and explanation are not required yet at this specific phase — a correct result table is enough to satisfy this milestone).
**Potential risks:** this phase is the single point everything downstream depends on — if it slips past 9 August, every later phase compresses. Protect this phase above all others; if behind schedule, cut scope from *later* phases (streaming, decision trees, Docker) before letting Phase 6 slip.

---

### Phase 7 — Multi-Turn Conversation
**Tier:** SHOULD
**Goal:** session-scoped memory so follow-up questions resolve correctly
(FR-8).
**Tasks:** implement `session/store.py` in full — an in-memory dict keyed by `session_id`, holding the LangChain conversation memory object and the most recent result set(s) (Architecture §7); bound the memory window (recent turns, not full verbatim history); wire `agent_service.py` to load/save it per request.
**Files/modules affected:** `backend/app/session/store.py`, `backend/app/agent/memory.py`, `backend/app/agent/agent_service.py`.
**Dependencies:** Phase 6.
**Acceptance criteria:** the three-turn Journey A sequence ("top 5 products" → "now show their trend" → "which one grew fastest?") resolves pronouns/entity references correctly.
**Potential risks:** unbounded memory growth over a long demo session — cap the turn window per TRD §13 from the start, not as an afterthought.

---

### Phase 8 — `generate_chart`
**Tier:** MUST (bar/line/pie) — scatter is BONUS.
**Goal:** the third tool; the visualization layer comes online end-to-end.
**Tasks:** `viz/plotly_builder.py` (deterministic shape-analysis + Plotly spec builder per `04_AGENT_TOOLS.md` Tool 3 §8); `tools/generate_chart.py` wrapping it; register in `tool_registry.py`; implement real `ChartRenderer.jsx` via `react-plotly.js`, replacing its Phase 1 mock.
**Files/modules affected:** `backend/app/viz/plotly_builder.py`, `backend/app/tools/generate_chart.py`, `backend/app/agent/tool_registry.py`, `frontend/src/components/ChartRenderer.jsx`.
**Dependencies:** Phase 6 (agent must exist to call it); Phase 3 (needs real result shapes to test against).
**Acceptance criteria:** bar/line/pie charts render inline in chat, responsive and titled with labeled axes (NFR-6); charts are correctly *not* forced for non-chartable/scalar results.
**Potential risks:** low; if time-constrained, scatter is deferred to the bonus pass (Phase 18 territory) without affecting this phase's MUST-have deliverable.

---

### Phase 9 — `explain_data`
**Tier:** MUST
**Goal:** the fourth tool; the natural-language insight layer.
**Tasks:** `tools/explain_data.py` per Tool 5's contract — empty-result fast path, large-result aggregation-before-LLM path (Clarification 3), constrained prompt construction, deterministic fallback on LLM failure; register in `tool_registry.py`.
**Files/modules affected:** `backend/app/tools/explain_data.py`, `backend/app/agent/tool_registry.py`.
**Dependencies:** Phase 6.
**Acceptance criteria:** explanations reference only data actually present (no invented facts, per PRD §5.5); empty results produce a friendly deterministic message with no LLM call made.
**Potential risks:** the LLM producing unsupported claims — mitigated by the constrained-prompt design in `04_AGENT_TOOLS.md`; verify this manually during this phase rather than waiting until Phase 15.

---

### Phase 10 — `generate_flowchart`
**Tier:** MUST (ER + process) — decision tree is BONUS.
**Goal:** the fifth and final tool; diagram generation comes online.
**Tasks:** `diagrams/mermaid_builder.py` (ER rendering driven by `get_schema`'s output shape; process rendering driven entirely by an agent-supplied `context.steps` graph — the module holds no hardcoded/default process template for any dataset, including the seeded e-commerce one); `tools/generate_flowchart.py`; register in `tool_registry.py`; extend `agent_service.py`'s prompting/reasoning so the agent derives `context.steps` itself before calling the tool for a process request; implement real `DiagramRenderer.jsx` via the `mermaid` npm package, replacing its Phase 1 mock.
**Files/modules affected:** `backend/app/diagrams/mermaid_builder.py`, `backend/app/tools/generate_flowchart.py`, `backend/app/agent/tool_registry.py`, `backend/app/agent/agent_service.py`, `frontend/src/components/DiagramRenderer.jsx`.
**Dependencies:** Phase 4 (needs `get_schema`'s output shape for the ER path), Phase 6.
**Acceptance criteria:** Journey B's two turns ("draw the ER diagram" and "flowchart of how orders move through the system") both render correctly; the ER diagram reflects the live schema, not a hardcoded one (same proof technique as Phase 4's acceptance test); the process diagram's steps come from agent-supplied `context.steps`, and a `"process"` call with no steps supplied returns `generation_failed` rather than any default diagram (Correction 1 regression check).
**Potential risks:** malformed Mermaid syntax breaking the chat pane — mitigated by the structural pre-return validation specified in `04_AGENT_TOOLS.md` Tool 4 §8/§9; test with intentionally malformed input during this phase, not just at Phase 15.

---

### Phase 11 — SQL Transparency
**Tier:** SHOULD
**Goal:** every data-producing turn visibly shows SQL → table → chart →
explanation, in that exact order (PRD §5.6, FR-9).
**Tasks:** ensure `routes/chat.py` composes the full response envelope (`sql`, `table`, `chart`, `diagram`, `explanation`) in the mandated order; finalize `SqlPanel.jsx`'s collapsible behavior.
**Files/modules affected:** `backend/app/routes/chat.py`, `backend/app/models/schemas.py`, `frontend/src/components/SqlPanel.jsx`.
**Dependencies:** Phases 5, 8, 9.
**Acceptance criteria:** every data-producing answer displays generated SQL in a collapsible section, followed by the result table, the visualization (when applicable), and the explanation — matching PRD §5.6 exactly.
**Potential risks:** low; primarily wiring, since the envelope shape was locked in Phase 2.

---

### Phase 12 — Error Recovery
**Tier:** SHOULD (and functionally required by FR-10)
**Goal:** the self-correction loop from `03_ARCHITECTURE.md` §6 is
implemented in code, not just described.
**Tasks:** in `agent_service.py`, catch `execute_query` failures, surface the raw `sql_error` message back to the agent as a tool result, allow exactly one `get_schema` re-check + `execute_query` retry, and compose a graceful, human-readable failure message (never the raw driver error) if the retry also fails.
**Files/modules affected:** `backend/app/agent/agent_service.py`, `backend/app/models/schemas.py` (error envelope shape).
**Dependencies:** Phases 4, 5, 6.
**Acceptance criteria:** Journey C ("Show me sales by revenues") completes correctly with a brief correction note; a query engineered to fail twice is confirmed to stop after exactly one retry and fall back gracefully — never a raw stack trace, never an unbounded loop.
**Potential risks:** relying on prompt instructions alone to cap the retry at one — this must be an explicit counter in code (mirroring Clarification 2's "don't rely on the prompt alone" philosophy, applied here to retry-count enforcement as well).

---

### Phase 13 — Streaming / SSE
**Tier:** SHOULD, explicitly **not a blocker** (Clarification 1).
**Goal:** progressive status events during agent/tool activity, attempted
only once the core system (Phases 0–12) is stable.
**Tasks:** add an SSE-capable path for `POST /api/chat` (or a parallel streaming route) emitting the event types named in the task brief: `thinking`, `checking_schema`, `running_query`, `building_chart`, `generating_explanation`, `complete`, `error`; wire `StatusIndicator.jsx` to consume them; keep the Phase 2/6 plain-JSON response path fully intact as the default/fallback.
**Files/modules affected:** `backend/app/routes/chat.py` (additive SSE variant), `frontend/src/api/client.js`, `frontend/src/components/StatusIndicator.jsx`.
**Dependencies:** Phases 6–12 all stable.
**Acceptance criteria:** when enabled, `StatusIndicator` reflects real tool-activity events; if SSE is skipped or reverted for time reasons, the JSON fallback still satisfies every functional requirement with zero regression to earlier phases.
**Potential risks:** this is explicitly the **first phase to cut** if the schedule is tight — implement it as additive/isolated (a separate route or a feature flag) precisely so cutting it never requires touching Phases 0–12's working code.

---

### Phase 14 — UX Polish
**Tier:** SHOULD
**Goal:** the usability pass supporting NFR-5 (15% of hackathon score).
**Tasks:** refine loading indicators, tool-activity states, error message copy, Markdown rendering in message bubbles, SQL syntax highlighting, table styling, chart/diagram container sizing, responsive breakpoints (`sm`/`md`/`lg`), and empty states (no schema found, no results).
**Files/modules affected:** `frontend/src/components/*.jsx` (styling passes), `frontend/tailwind.config.js`.
**Dependencies:** Phases 1–13.
**Acceptance criteria:** the UI remains usable at common desktop and tablet breakpoints (TRD §2); no broken layouts with long SQL text, large tables, or wide charts/diagrams.
**Potential risks:** scope creep into animations or other visual flourishes not required by NFR-5 — explicitly excluded per the task brief.

---

### Phase 15 — Testing
**Tier:** SHOULD (unit tests) / MUST (the four manual journeys)
**Goal:** critical unit tests exist and the four PRD demo journeys run
cleanly end-to-end, including the database upload/switch journey.
**Tasks:** `backend/tests/test_*.py` for all five tools plus the Database Manager — SQL safety, schema discovery, chart-type selection, empty-result handling, invalid-query handling, upload validation (valid/invalid files, path-traversal attempts), session isolation, error handling (TRD §11); manually run Journeys A/B/C/D per PRD §8 against the running application, using `06_TESTING_CHECKLIST.md` as the script.
**Files/modules affected:** `backend/tests/*.py`.
**Dependencies:** Phases 3–12.
**Acceptance criteria:** the pytest suite passes locally; all four demo journeys complete without a crash or an unhandled error (PRD §13, success criteria 2 and 7).
**Potential risks:** unit tests are the bonus-tier item here per TRD §11 — if time-constrained, the four manual journeys are the non-negotiable minimum; do not let unit-test authoring crowd out journey verification.

---

### Phase 16 — Docker
**Tier:** SHOULD, preferred not mandatory (NFR-7).
**Goal:** `docker-compose up` reliably brings up the full application.
**Tasks:** `frontend/Dockerfile`, `backend/Dockerfile`, `docker-compose.yml` with a mounted volume covering `ecommerce.db` and `DATABASE_UPLOAD_DIR` so both the demo database and any session-uploaded databases persist across container restarts during judging (TRD §12).
**Files/modules affected:** `frontend/Dockerfile`, `backend/Dockerfile`, `docker-compose.yml`.
**Dependencies:** Phases 0–15 stable.
**Acceptance criteria:** a clean clone brought up via `docker compose up` serves a fully working application.
**Potential risks:** explicitly de-prioritized below a working local (non-Docker) app — if Docker proves unstable this close to freeze, ship the documented local-run path in the README and skip Docker rather than risk destabilizing an already-working application.

---

### Phase 17 — README and Repository Preparation
**Tier:** MUST (submission requirement, PRD §13 criterion 5–6)
**Goal:** the repository is submission-ready from a clean clone.
**Tasks:** write `README.md` — setup instructions (both Docker and local paths), architecture overview, tool documentation summary, environment variables (including `DATABASE_UPLOAD_DIR`/`DATABASE_UPLOAD_MAX_MB`), how to upload a SQLite database and how the default/sample database is used if none is uploaded, team information, example queries, optional screenshots; verify no secrets are committed, `.env` is ignored, `.env.example` is present and accurate, and a genuinely clean clone runs end-to-end using only documented steps.
**Files/modules affected:** `README.md`, `.env.example`, `.gitignore`.
**Dependencies:** Phases 0–16.
**Acceptance criteria:** PRD §13 success criteria 5 and 6 are met in full.
**Potential risks:** low if drafted incrementally starting Phase 0; high if deferred entirely to 11 August — recommend keeping a running README draft from Day 1 rather than writing it from scratch on freeze day.

---

### Phase 18 — Final Feature Freeze
**Tier:** MUST
**Goal:** code is frozen on 11 August 2026 in a fully submission-ready state.
**Tasks:** run the full `06_TESTING_CHECKLIST.md`, including the Final Hackathon Submission Checklist; confirm bonus items are attempted **only** if every MUST/SHOULD item is already stable; no new features are started after this point.
**Files/modules affected:** none (verification-only phase).
**Dependencies:** all prior phases.
**Acceptance criteria:** PRD §13 success criteria 1–7 are all satisfied.
**Potential risks:** the temptation to add "just one more" bonus feature after freeze — explicitly disallowed; any remaining time on 11–12 August goes to verification and the demo video, not new code.

---

## 5. Daily Execution Mapping

| Date | Phases | Most Important Milestone |
|---|---|---|
| **9 August — Foundation** | 0, 1, 2, 3, 4, 5, 6 | **One complete, working database-upload-or-default → NL → SQL → database → React flow.** |
| **10 August — Core Intelligence** | 7, 8, 9, 10, 11, 12 | **All five required tools working end-to-end.** |
| **11 August — Productization** | 13, 14, 15, 16, 17, 18 | **Code frozen and GitHub submission-ready.** |
| **12 August — Submission** | *(no major development)* | Demo video, final GitHub verification, final README check, final submission, emergency fixes only. |

Because 9 August is the plan's actual starting day, Phases 0–6 are today's
literal target — Phase 6 (the LangChain agent milestone) is the single
highest-priority item to land before the day ends.

---

## 6. Document Relationship

This plan sequences the features defined in `01_PRD.md`, the technology
choices in `02_TRD.md`, the components/data-flow in `03_ARCHITECTURE.md`, and
the tool contracts in `04_AGENT_TOOLS.md`, into a concrete build order.
Verification of each phase's acceptance criteria is detailed further in
`06_TESTING_CHECKLIST.md`. No phase introduces a component, technology, or
requirement not already present in the first three documents.
