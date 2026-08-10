# Technical Requirements Document (TRD)

**Project:** AI Data Analyst — Conversational Database Intelligence
**Companion documents:** `01_PRD.md` (product scope), `03_ARCHITECTURE.md`
(system structure)
**Guiding constraint:** feature-complete by 11 August 2026 — every choice
below is optimized for reliable, fast implementation by a 3–5 person team,
not for long-term scale.

---

## 1. Technology Stack Summary

| Layer | Choice | Alternative considered | Why this choice |
|---|---|---|---|
| Frontend | React + Vite + Tailwind CSS | Next.js | Vite gives near-instant dev startup and HMR; no server-rendering requirement exists, so Next.js's extra complexity (routing conventions, SSR) buys nothing for a single-page chat app under time pressure. Tailwind avoids hand-writing CSS for chat bubbles, tables, and cards. |
| Backend | Python + FastAPI + Pydantic | Flask, Django | FastAPI gives async request handling (needed for streaming and for concurrent LLM/tool calls), automatic request/response validation via Pydantic, and native SSE support — with far less boilerplate than Django and better typing than Flask. |
| Agent orchestration | LangChain | LlamaIndex, CrewAI, AutoGen, custom | LangChain has first-class custom-tool/function-calling support and conversation-memory primitives, which map directly onto the five mandated tools and the multi-turn requirement. LlamaIndex is retrieval-document-centric (not needed — no RAG). CrewAI/AutoGen add multi-agent coordination overhead the problem statement does not require (single agent, five tools). |
| LLM provider | Configurable via environment variables (OpenAI / Gemini / Anthropic-compatible) | Hardcoded single provider | Judges may test with different API keys/providers; provider lock-in is a risk. LangChain's chat-model interface abstracts the provider so swapping requires only env-var and client-instantiation changes, not agent rewrites. |
| Database (initial) | SQLite — either the seeded demo database or a user-uploaded `.db`/`.sqlite`/`.sqlite3` file | Postgres, MySQL | No official database exists yet (see PRD §12). SQLite requires zero setup, ships inside the repo, and is trivial for judges to run locally; it is also the simplest format for a user to upload directly through the browser. SQLAlchemy keeps the door open to Postgres/MySQL later via `DATABASE_URL` alone. |
| Database abstraction | SQLAlchemy Core + Inspector | Raw `sqlite3`, an ORM-only approach | SQLAlchemy's `Inspector` API gives dynamic schema discovery (tables, columns, types, foreign keys) across multiple database backends for free — required by FR-3. SQLAlchemy Core (not full ORM) keeps query execution close to raw SQL, which the LLM is generating directly. |
| Database source management | Lightweight in-process **Database Manager** (custom module, no new infrastructure) | Cloud object storage, a dedicated database-orchestration service | The hackathon needs only session-scoped file validation, storage, and active-database lookup (PRD §5.9). A custom module reusing the existing SQLAlchemy engine/Inspector plumbing satisfies this with zero new moving parts; a storage service or orchestration layer would add infrastructure the 3-day timeline cannot justify. |
| Visualization | Plotly (Python) → JSON spec → `react-plotly.js` | Matplotlib images, Chart.js, D3 | Plotly figures serialize to JSON, so the backend can decide *what* to chart while the frontend stays a thin renderer — this matches Rule 9 (visualization logic separated from the LLM, rendering separated from decision-making). Matplotlib would require shipping static images, losing interactivity and responsiveness (NFR-6). |
| Diagrams | Mermaid.js (frontend rendering of LLM/tool-generated Mermaid syntax) | Graphviz, custom SVG generation | Mermaid syntax is plain text the LLM can generate directly and reliably; the frontend renders it client-side with the `mermaid` npm package. This matches Rule 10 (diagram *generation* separated from diagram *rendering*) and needs no server-side image rendering pipeline. |
| Testing | Pytest | unittest | Pytest's fixtures and parametrization make it fast to write tool-level unit tests (bonus scope) with minimal ceremony. |
| Deployment | Docker + Docker Compose (frontend + backend services) | Bare-metal run scripts only | Docker Compose gives judges a single reliable "run locally" path (submission requirement) while remaining simple — two services, no orchestration layer. |

---

## 2. Frontend Requirements

- **Framework:** React 18+ with Vite as the build tool; functional
  components and hooks only (no class components).
- **Styling:** Tailwind CSS utility classes; no separate CSS-in-JS library,
  to minimize dependencies and build complexity.
- **Core views/components:**
  - `ChatWindow` — message list + input box, owns session state.
  - `MessageBubble` — renders a single turn (user or agent).
  - `SqlPanel` — collapsible "Generated SQL" block.
  - `ResultTable` — tabular query results.
  - `ChartRenderer` — renders a Plotly spec via `react-plotly.js`.
  - `DiagramRenderer` — renders Mermaid syntax via the `mermaid` package.
  - `StatusIndicator` — shows current agent/tool activity
    ("Checking schema…", "Running query…", etc.) and loading spinners.
  - `ErrorBanner` — user-facing, non-technical error messages.
  - `DatabaseUpload` — lets the user upload/select a SQLite database and
    shows which database is currently active for the session (PRD §5.9).
- **Networking:** the frontend talks only to the FastAPI backend, never
  directly to the database (Architecture Rule 1). Chat responses are
  streamed via **Server-Sent Events (SSE)** where practical; a plain
  request/response JSON fallback is acceptable if streaming a given step is
  not feasible in the time available.
- **Responsiveness:** layouts must remain usable at common desktop and
  tablet breakpoints (Tailwind's default `sm`/`md`/`lg` breakpoints are
  sufficient — no dedicated native-mobile design work is required for this
  hackathon).
- **State management:** local component state / React context is sufficient
  given a single-session, single-page application; no external state library
  (e.g., Redux) is warranted.

---

## 3. Backend Requirements

- **Framework:** FastAPI with Pydantic v2 models for all request/response
  bodies, so tool inputs/outputs and API contracts are enforced by type,
  not convention (supports NFR-2 and "structured tool inputs/outputs").
- **API surface (indicative, finalized in `03_ARCHITECTURE.md`):**
  - `POST /api/chat` — accepts a user message + session id, returns/streams
    the agent's response (text, SQL, table, chart spec, diagram spec, as
    applicable).
  - `GET /api/schema` — optional direct schema-inspection endpoint, useful
    for debugging and for a frontend "database overview" affordance; always
    reflects the currently active database for the session.
  - `POST /api/database/upload` — accepts a SQLite file upload + session id,
    validates it, and makes it the session's active database (PRD §5.9,
    FR-14/FR-15).
  - `GET /api/database/current` — returns which database is currently active
    for the session (demo/default, or the uploaded filename), for the UI's
    active-database indicator.
  - `DELETE /api/database/current` — clears the session's uploaded database,
    reverting the session to the default/demo database.
  - `GET /api/health` — liveness/readiness check.
- **Session handling:** an in-memory session store keyed by a session id
  (UUID) issued to the frontend on first load, holding conversation history
  and the LangChain memory object. This is intentionally simple (no Redis,
  no database-backed sessions) — acceptable because the hackathon runs a
  single local/demo deployment (Rule 12: prefer simple implementations).
- **Concurrency:** FastAPI's async request handling is used for the chat
  endpoint so a single slow tool call does not block the whole server.
- **Configuration:** all environment-specific values are read from `.env`
  via Pydantic `BaseSettings` (or `pydantic-settings`) at startup; no
  connection strings, API keys, or model names are hardcoded anywhere in
  source.

---

## 4. LangChain Agent Requirements

- The agent is built as a LangChain tool-calling agent (function-calling
  style), **not** a prebuilt generic SQL agent (e.g., not
  `create_sql_agent`), because the hackathon mandates five *specific*,
  independently defined tools with structured contracts, not a black-box
  SQL toolkit.
- **Registered tools** (one-to-one with FR-2):

  | Tool | Responsibility |
  |---|---|
  | `get_schema` | Return the current database's tables, columns, types, and foreign-key relationships. |
  | `execute_query` | Execute a single read-only SQL statement and return rows + column metadata. |
  | `generate_chart` | Given tabular data and intent, choose a chart type and return a Plotly-compatible spec. |
  | `generate_flowchart` | Given intent (ER / process flow / decision tree) and, where relevant, schema data, return Mermaid syntax. |
  | `explain_data` | Given a result set (and/or chart spec) and the user's question, return a natural-language explanation. |

- Each tool is defined with an explicit Pydantic input schema and a
  structured JSON output, so the agent, the frontend, and any future
  automated tests can all reason about tool I/O without parsing free text.
- **Conversation memory:** LangChain conversation memory (buffer-based, with
  a bounded window if the context grows large) holds recent turns and the
  most recent result set(s), so references like "these products" or
  "the fastest one" resolve without requiring the user to restate context.
- **Error-correction loop:** on a tool failure (particularly
  `execute_query`), the agent receives the raw database error as a tool
  result, is prompted to reconsider the schema (re-invoking `get_schema` if
  needed) and correct the SQL, and is allowed exactly one automatic retry
  before falling back to a graceful, user-facing error message.
- **LLM provider abstraction:** the chat model is instantiated once, behind
  a small factory function, based on an `LLM_PROVIDER` environment variable
  (e.g., `openai`, `gemini`, `anthropic`); the agent and tools depend only on
  LangChain's provider-agnostic chat-model interface, never on a specific
  provider's SDK types.

---

## 5. Database Requirements

- **Default/sample database:** a seeded SQLite file, populated with a
  representative e-commerce schema (`customers`, `categories`, `products`,
  `orders`, `order_items`, `inventory`, `payments`, with realistic
  foreign-key relationships — see PRD §12 / Architecture for the ER
  diagram). This is used automatically whenever a session has no uploaded
  database, and remains the primary dataset for development, testing, and
  judging.
- **User-uploaded databases (primary MVP data-source capability, PRD
  §5.9):** a user can upload a `.db`/`.sqlite`/`.sqlite3` file through the
  frontend; once validated, it becomes the **active database** for that
  session. The agent and all five tools operate against the active
  database without knowing or caring whether it is the default demo
  database or a user upload.
- **Database Manager abstraction:** a small, dedicated module owns the
  active-database concept, separating the database *source* from the
  agent/tools. Conceptually:

  ```
  DatabaseManager
  ├── validate_upload(file)        # extension + genuine-SQLite check
  ├── register_database(session_id, file)  # store + record as active
  ├── get_active_database(session_id)      # demo DB if none uploaded
  ├── get_connection(session_id)           # hands a connection/engine to the Database Access Layer
  └── cleanup_session_database(session_id) # remove temp files where practical
  ```

  Exact function names may differ in implementation; the required property
  is the separation of responsibility — the Database Manager decides
  *which* database file is active for a session, the Database Access Layer
  (§ below) is the only thing that ever opens a SQLAlchemy connection to
  it, and the agent/tools never touch either concern directly.
- **Abstraction:** all access goes through a single database-access module
  wrapping SQLAlchemy's `create_engine` and `Inspector`, obtaining its
  target from the Database Manager's `get_connection(session_id)` rather
  than a single hardcoded engine. No other module opens its own database
  connection.
- **Dynamic schema discovery:** `get_schema` calls the Inspector at request
  time, against whichever database the Database Manager reports as active
  for the session (with light caching within a session, not hardcoded
  constants), so the agent never depends on a fixed table/column list. This
  is what lets a user-uploaded database — `sales.db`, `hospital.db`,
  anything — or, later, an organizer-provided database, become the active
  data source without any agent/tool code change.
- **Read-only enforcement (defense in depth):**
  1. The system prompt instructs the LLM to generate `SELECT`-only SQL.
  2. `execute_query` validates the statement before execution — rejecting
     any statement whose first keyword (or any statement in a multi-statement
     string) is `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, or `TRUNCATE`,
     and rejecting multiple statements in a single call. This validation
     remains a lightweight keyword/regex guard, not a full SQL parser, and it
     avoids false positives where a forbidden word occurs only inside a
     quoted string literal or a quoted identifier where practical (e.g.,
     `SELECT 'delete' AS status` must not be rejected merely because the
     literal contains the word `delete`).
  3. Where the driver supports it, the database connection itself is opened
     in a read-only mode/URI as an additional safeguard.
  4. This enforcement applies uniformly to the active database, whether it
     is the seeded demo database or a user upload — the SQL validator has
     no dataset-specific logic.
- **Configuration:** `DATABASE_URL` remains the single source of truth for
  the **default/sample database's** connection string (e.g.,
  `sqlite:///./data/ecommerce.db`), read from `.env`. It is not used for
  uploaded databases — those are resolved at runtime through the Database
  Manager (keyed by `session_id`), not forced into an environment variable.
- **Session isolation:** the Database Manager maps `session_id → active
  database file`, so one session's upload is never visible to, or queried
  by, another session (PRD FR-16). This is a simple in-process mapping —
  consistent with the Session Store's existing in-memory design
  (Architecture §7) — not a new distributed or authenticated system.

---

## 6. Visualization Requirements

- Chart specs are produced server-side (inside `generate_chart`) as Plotly
  figure JSON (`data` + `layout`), not as rendered images, so the frontend
  can render them responsively and interactively.
- **Chart-type selection logic** (deterministic rules, not left purely to
  LLM free-form choice, to guarantee consistency for scoring):
  - Two columns, one categorical + one numeric, few categories → **bar**.
  - A date/time column + one numeric column → **line**.
  - One categorical column + one numeric "share of total" framing → **pie**.
  - Two numeric columns, no explicit time/category axis, correlation intent
    → **scatter** (bonus).
- Every generated chart includes a title and axis labels derived from the
  query's column names/user intent — never left blank.
- Styling (colors, fonts) is kept consistent across chart types via a small
  shared Plotly layout template, addressing "aesthetically consistent"
  (NFR-6).

---

## 7. Diagram Requirements

- `generate_flowchart` returns raw Mermaid syntax as a string; the frontend
  is solely responsible for rendering it (Rule 10).
- **ER diagrams:** generated from the live schema returned by `get_schema`
  (tables, columns, foreign keys) using Mermaid's `erDiagram` syntax — never
  hand-written/hardcoded for a specific schema.
- **Process-flow diagrams:** the agent (not the tool) reasons about the
  requested process — using `get_schema`/session context when relevant — and
  derives a structured step sequence, which it passes to `generate_flowchart`
  as `context.steps`. The tool deterministically renders that step graph into
  Mermaid `flowchart` syntax. `generate_flowchart` holds no LLM call and no
  hardcoded default process (e.g., no built-in order-lifecycle template);
  process content always originates from agent-supplied structured steps, not
  a static fallback baked into the tool. This applies regardless of dataset —
  the tool must work the same way for a differently-shaped database.
- **Decision trees (bonus):** Mermaid `flowchart`/`graph` syntax expressing
  branching logic relevant to the user's question.

---

## 8. API & Integration Requirements

- All backend responses to the frontend follow one structured envelope
  (finalized in `03_ARCHITECTURE.md`) containing, as applicable: message
  text, generated SQL, result rows/columns, chart spec, diagram syntax, and
  an error object — so the frontend never needs to guess response shape.
- No direct frontend-to-database or frontend-to-LLM-provider calls; all
  external integration happens through the FastAPI backend.

---

## 9. Security Requirements

- SQL execution is **read-only by default**, enforced at the tool layer as
  described in §5, independent of what the LLM was asked or how it was
  prompted.
- No API keys, database credentials, or secrets are committed to source
  control; all are supplied via `.env` (with a checked-in `.env.example`
  documenting required variables).
- Basic input handling on the chat endpoint (message length limits,
  rejection of empty/malformed payloads via Pydantic validation) to avoid
  trivial misuse; full authentication/authorization is explicitly out of
  scope for this hackathon (PRD §12).
- Error messages returned to the frontend are sanitized/human-readable;
  raw stack traces or internal exception details are logged server-side
  only, never sent to the client.
- **Database upload safety** (PRD §5.9, NFR-9):
  - Only files with a supported extension (`.db`, `.sqlite`, `.sqlite3`)
    are accepted; the upload is additionally validated as a genuine SQLite
    file (e.g., checking the SQLite file header) before being registered,
    not merely trusted by extension.
  - Uploaded files are stored in a controlled, backend-owned application
    data directory — never a user-supplied path — with a generated,
    session-scoped filename so the original filename cannot be used to
    write outside that directory (path-traversal prevention).
  - Uploaded files are never executed as code or opened by anything other
    than the SQLite/SQLAlchemy connection path; they are treated purely as
    data.
  - The frontend and the LLM never receive the uploaded file's on-disk path
    or direct database credentials — only the FastAPI backend's Database
    Manager resolves and opens the file.
  - Uploading a new file never overwrites another session's active
    database file; each session's upload is stored and referenced
    independently, and temporary/session database files are cleaned up
    where practical (e.g., on session end), without building a persistent
    multi-file archive.
  - This remains a hackathon-appropriate safeguard set (basic validation +
    controlled storage + isolation), not an enterprise file-security
    architecture — no virus scanning, quarantine pipeline, or external
    storage service is introduced.

---

## 10. Environment Configuration

All configuration is environment-variable driven and documented in
`.env.example`. Indicative variables:

```
# LLM
LLM_PROVIDER=openai            # openai | gemini | anthropic
LLM_MODEL=<provider-specific model name>
LLM_API_KEY=<set locally, never committed>

# Database (default/sample dataset — see Section 5 for uploaded databases)
DATABASE_URL=sqlite:///./data/ecommerce.db

# Database uploads (PRD §5.9)
DATABASE_UPLOAD_DIR=./data/uploads      # controlled storage directory for uploaded SQLite files
DATABASE_UPLOAD_MAX_MB=50               # basic size guard on uploaded files

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

---

## 11. Testing Requirements

- **Unit tests (bonus, prioritized if time allows):** Pytest tests for each
  tool in isolation — e.g., `execute_query` rejects destructive statements,
  `get_schema` returns the seeded tables, `generate_chart` selects the
  expected chart type for representative inputs.
- **Manual integration testing (mandatory):** the four PRD user journeys
  (§8, including Journey D — database upload and switch) are run manually
  against the running application before code freeze, using at least two
  differently-shaped SQLite databases to confirm no schema is hardcoded
  (full test matrix in `06_TESTING_CHECKLIST.md`).
- **No end-to-end browser automation** is planned given the time budget;
  manual verification against the acceptance/success criteria in the PRD is
  sufficient for this hackathon.

---

## 12. Deployment Requirements

- **Docker:** separate `Dockerfile`s for frontend and backend; a
  `docker-compose.yml` bringing up both services plus a mounted volume
  covering both the default SQLite file and the `DATABASE_UPLOAD_DIR`
  (§10), so the demo database and any uploaded databases persist across
  container restarts during judging.
- **Local run without Docker** must also remain possible (`npm run dev` for
  the frontend, `uvicorn` for the backend) as a fallback, since Docker
  support is preferred, not mandatory, per the submission requirements.
- A single documented setup path (README) covers both options.

---

## 13. Technical Constraints

- Single LLM call per agent "step" — no multi-agent debate/voting patterns;
  keeps latency and cost predictable within a 3-day build.
- SQLite's single-writer concurrency model is acceptable because the
  application only performs reads at runtime (writes only happen at seed
  time, offline).
- No microservices, message queues, or container orchestration (Rule 11);
  the backend is one FastAPI process, the frontend is one static/dev-served
  React app.
- No RAG/document retrieval — the agent's only external knowledge source is
  the live database schema and query results.
- Context-window awareness: conversation memory is bounded (recent turns +
  the most recent result set(s), not the full session history verbatim) to
  keep prompts within provider context limits as the conversation grows.

---

## 14. Document Relationship

This TRD explains *how* the PRD's requirements are implemented at a
technology-choice level. `03_ARCHITECTURE.md` takes these same choices and
lays out the concrete component structure, data flow, and diagrams. Any
technology named here (LangChain, FastAPI, React, SQLAlchemy, SQLite,
Plotly, Mermaid.js, Docker) is used consistently in the architecture
document with no substitutions.
