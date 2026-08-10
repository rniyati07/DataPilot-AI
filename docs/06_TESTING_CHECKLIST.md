# Testing & Verification Checklist

**Project:** AI Data Analyst — Conversational Database Intelligence
**Companion documents:** `01_PRD.md`, `02_TRD.md`, `03_ARCHITECTURE.md`,
`04_AGENT_TOOLS.md`, `05_IMPLEMENTATION_PLAN.md`
**Purpose:** a practical checklist to run directly on **11 August 2026**,
before code freeze — and again, lightly, on 12 August before submission.
This is not a theoretical QA document; every item below is something a
team member actually clicks, types, or runs.

**Scope tags:** `[MUST]` items block freeze if failing. `[SHOULD]` items are
important but do not block freeze on their own if MUST items are solid.
`[BONUS]` items are checked only if implemented at all.

---

## 1. Environment `[MUST]`

- [ ] Python environment installs cleanly (`pip install -r requirements.txt`)
- [ ] Node environment installs cleanly (`npm install`)
- [ ] `.env` works when populated from `.env.example`
- [ ] `.env.example` exists and lists every variable the app actually reads
- [ ] No secrets (API keys, credentials) are committed anywhere in the repo
- [ ] `data/ecommerce.db` is committed and present immediately after a fresh clone (no seed step required to reproduce the demo)
- [ ] `*.db-wal`, `*.db-shm`, `*.db-journal` are git-ignored and not present in the repo
- [ ] The contents of `DATABASE_UPLOAD_DIR` (session-uploaded databases) are git-ignored; the directory itself exists (e.g., via `.gitkeep`) after a fresh clone

---

## 2. Database Upload & Management `[MUST]`

- [ ] Valid `.db` upload succeeds and becomes the active database
- [ ] Valid `.sqlite` upload succeeds and becomes the active database
- [ ] Valid `.sqlite3` upload succeeds and becomes the active database
- [ ] Invalid/corrupt file (wrong extension) is rejected with a clear error, not a crash
- [ ] Non-SQLite file with a spoofed `.db` extension is rejected (content validation, not extension-only)
- [ ] Missing/empty file upload is handled gracefully
- [ ] An oversized file (beyond `DATABASE_UPLOAD_MAX_MB`) is rejected gracefully, if a size limit is implemented
- [ ] A filename containing path-traversal characters (e.g., `../../etc/passwd`) cannot write outside the controlled upload directory
- [ ] After a successful upload, `GET /api/database/current` reports the uploaded file as active
- [ ] The frontend's active-database indicator updates immediately after a successful upload
- [ ] Uploading a second valid file replaces the active database (the session no longer queries the first uploaded file or the default database)
- [ ] `DELETE /api/database/current` reverts the session to the default/demo database
- [ ] An invalid upload does **not** replace a currently-working active database (the prior valid database, default or uploaded, remains active)
- [ ] The uploaded file is stored only in the backend's controlled data directory — never exposed to the frontend as a raw path or made directly downloadable
- [ ] The LLM/agent never receives the uploaded file's on-disk path or a raw connection string

**Dynamic schema across two databases** — test with at least two
differently-shaped SQLite files (e.g., the seeded `ecommerce.db` and a
simple `hospital.db`-style test file):
- [ ] `get_schema` discovers Database A's tables/columns correctly when A is active
- [ ] Queries against Database A return correct results
- [ ] Switching the active database to Database B updates `get_schema`'s output accordingly on the very next call
- [ ] Queries against Database B return correct results, using B's actual schema
- [ ] No hardcoded e-commerce table/column name (`customers`, `products`, etc.) is referenced anywhere in the agent's behavior while Database B is active

**Isolation:**
- [ ] Switching the active database changes the query target for that session only
- [ ] A second session's active database is not accidentally queried after a first session uploads or switches its own database
- [ ] An invalid upload attempt does not replace the current valid active database (duplicate of the Database Upload check above, verified specifically from the session-isolation angle — i.e., session A's failed upload does not affect session B either)

---

## 3. Frontend `[MUST]`

- [ ] Application loads without console errors
- [ ] Chat input accepts and submits text
- [ ] Messages render for both user and agent turns
- [ ] Loading state appears while a request is in flight
- [ ] Errors render through `ErrorBanner`, never as a raw stack trace or blank screen
- [ ] `SqlPanel` expands/collapses and shows the generated SQL
- [ ] `ResultTable` renders tabular results correctly
- [ ] `ChartRenderer` renders Plotly charts inline
- [ ] `DiagramRenderer` renders Mermaid diagrams inline
- [ ] `DatabaseUpload` accepts a file selection and shows upload progress/result
- [ ] The active-database indicator is visible and always reflects the current session state (default vs. uploaded filename)
- [ ] Layout remains usable at common desktop and tablet breakpoints `[SHOULD]`

---

## 4. Backend `[MUST]`

- [ ] `GET /api/health` returns `200`
- [ ] `POST /api/chat` returns a correctly-shaped response envelope
- [ ] `GET /api/schema` returns the live schema of the currently active database
- [ ] `POST /api/database/upload` returns a correctly-shaped response envelope (accepted or rejected)
- [ ] `GET /api/database/current` returns the correct active-database identity for the session
- [ ] `DELETE /api/database/current` correctly reverts the session to the default database
- [ ] An invalid/malformed request payload is rejected with a clean `4xx`, not a `500`
- [ ] An LLM provider failure is caught and returns a structured error, not a crash
- [ ] A database failure is caught and returns a structured error, not a crash

---

## 5. Tool: `get_schema` `[MUST]`

- [ ] Tables are detected correctly for the default/demo database
- [ ] Columns are detected correctly
- [ ] Data types are detected correctly
- [ ] Foreign keys are detected correctly
- [ ] Output is structured (matches `04_AGENT_TOOLS.md` Tool 1 §6), not free text
- [ ] An empty or unreachable database is handled gracefully (no crash)
- [ ] No table/column name is hardcoded anywhere in the tool's source — verify by uploading a differently-shaped test database (or pointing `DATABASE_URL` at one, for the default) and confirming the output changes accordingly
- [ ] After a session uploads a new database, `get_schema` reflects the newly active database on the very next call (no stale cache from the previous active database)

---

## 6. Tool: `execute_query` `[MUST]`

- [ ] A valid `SELECT` executes and returns rows
- [ ] Aggregation (`SUM`/`COUNT`/`AVG`/etc.) works
- [ ] `JOIN` works
- [ ] `ORDER BY` works
- [ ] `LIMIT` works
- [ ] An empty result set is handled gracefully (`rows: []`, not an error)
- [ ] Invalid SQL returns a structured `sql_error`, not a crash
- [ ] `INSERT` is rejected
- [ ] `UPDATE` is rejected
- [ ] `DELETE` is rejected
- [ ] `DROP` is rejected
- [ ] `ALTER` is rejected
- [ ] `TRUNCATE` is rejected
- [ ] Multi-statement input (e.g., `SELECT 1; DROP TABLE x;`) is rejected
- [ ] A column/table name that merely *contains* a forbidden keyword as a substring (e.g., `updated_at`) is **not** falsely rejected
- [ ] A forbidden keyword occurring only inside a quoted string literal (e.g., `SELECT 'delete' AS status`) is **not** falsely rejected
- [ ] An excessively large result set is capped/truncated safely, with `truncated: true`, never sent unbounded
- [ ] All of the above behave identically when the active database is a session upload rather than the default database

---

## 7. Tool: `generate_chart` `[MUST bar/line/pie, BONUS scatter]`

- [ ] Bar chart renders for categorical + numeric data
- [ ] Line chart renders for date/time + numeric data
- [ ] Pie chart renders for share/proportion framing
- [ ] Scatter chart renders for two-numeric correlation data, if implemented `[BONUS]`
- [ ] The correct chart type is selected deterministically for each representative shape
- [ ] Every chart has a non-blank title
- [ ] Every chart has labeled axes
- [ ] Charts render responsively (no overflow/clipping in the chat pane)
- [ ] Empty data is handled without crashing (`chart_type: "none"`)
- [ ] Genuinely unchartable data (e.g., all-text, single scalar) is handled without crashing
- [ ] No chart is forced when a chart is not meaningful (e.g., "how many customers do we have?" → table + explanation only)

---

## 8. Tool: `generate_flowchart` `[MUST ER + process, BONUS decision tree]`

- [ ] ER diagram renders correctly
- [ ] Process-flow diagram renders correctly
- [ ] Decision tree renders correctly, if implemented `[BONUS]`
- [ ] Generated Mermaid syntax is always valid (frontend never receives broken syntax)
- [ ] ER diagram is built from the **live** schema of the currently active database, not hardcoded — verify by altering the test database's schema (or uploading a differently-shaped database) and confirming the diagram changes accordingly
- [ ] Process-flow diagram is built from an agent-supplied/derived `context.steps` graph, **not** a hardcoded e-commerce diagram — verify by requesting a process-flow diagram for a different process (or against a differently-shaped test database) and confirming the diagram reflects the supplied steps rather than a fixed order-lifecycle sequence
- [ ] A process-flow request with no `context.steps` supplied is handled gracefully (`generation_failed` / insufficient-context response), not by silently emitting a default order-lifecycle diagram
- [ ] Rendering works reliably in the chat pane
- [ ] An invalid/insufficient diagram request (e.g., decision tree with no context) is handled gracefully, not with a crash or a nonsensical diagram

---

## 9. Tool: `explain_data` `[MUST]`

- [ ] An explanation is generated for a non-empty result
- [ ] Trends are identified correctly on representative data
- [ ] Comparisons are explained correctly
- [ ] Highest/lowest values are identified correctly
- [ ] The explanation contains no claims unsupported by the actual data (spot-check against a fixed test dataset)
- [ ] An empty result produces an appropriate, friendly explanation (not an LLM hallucination, not a crash)
- [ ] A large result set is handled safely — verify the raw row count sent into the LLM prompt stays under the configured summarization threshold (Clarification 3)

---

## 10. Agent `[MUST]`

- [ ] The correct tool (or tool sequence) is selected for a given request type
- [ ] Tools can be chained within a single turn (e.g., `execute_query → generate_chart → explain_data`)
- [ ] Schema context is retained within a session (no redundant `get_schema` calls once cached)
- [ ] Schema context is correctly invalidated/refreshed when the session's active database changes mid-session (no stale schema served after an upload)
- [ ] Multi-turn references ("these products", "the fastest one") resolve correctly
- [ ] SQL transparency works — generated SQL is visible for every data-producing turn
- [ ] Exactly **one** automatic retry occurs on a query failure
- [ ] No infinite retry loop is possible — verify with an intentionally-unfixable query and confirm the agent stops after one retry
- [ ] A graceful, human-readable fallback message is shown when the retry also fails

---

## 11. Required End-to-End Demo Tests `[MUST]`

These four journeys, from `01_PRD.md` §8 (Journeys A–D), must run cleanly,
in order, without a crash or an unhandled error, before code freeze.

### Test 1 — Sales Analysis

**"Show me the top 5 products by revenue."**
- [ ] Generated SQL is shown
- [ ] Results table is shown
- [ ] Bar chart is shown
- [ ] Explanation is shown

**Then: "Now show me the trend for these products over the last year."**
- [ ] Prior context (the same products) is retained
- [ ] The correct products are used in the follow-up query
- [ ] Line chart is shown

**Then: "Which one grew the fastest?"**
- [ ] The question is correctly interpreted against the trend data
- [ ] The correct product/result is identified
- [ ] An explanation is given

### Test 2 — Database Understanding

**"Draw me the ER diagram for this database."**
- [ ] Schema is discovered (via `get_schema`)
- [ ] Mermaid ER syntax is generated
- [ ] Relationships shown are correct against the live schema
- [ ] Diagram renders correctly in the chat pane

**Then: "Which tables are related to customers?"**
- [ ] The agent reasons correctly over schema data
- [ ] The relationships named are correct

### Test 3 — Process Visualization

**"Create a flowchart showing how orders flow through our system."**
- [ ] The process is correctly understood/mapped to steps
- [ ] The step sequence is derived by the **agent** and passed as `context.steps` — not returned by a hardcoded default inside `generate_flowchart`
- [ ] Mermaid flowchart syntax is generated
- [ ] Diagram renders correctly in the chat pane

### Test 4 — Database Upload and Switch

**Upload `sales.db` (or equivalent test file) through the chat application.**
- [ ] The file is validated and accepted
- [ ] The active-database indicator updates to show the uploaded file
- [ ] `get_schema` reflects the uploaded database's actual schema, not the e-commerce schema

**Then: "Which product generated the highest revenue?"**
- [ ] Generated SQL is shown, referencing the uploaded database's real column/table names
- [ ] Results table is shown
- [ ] An appropriate chart is shown
- [ ] Explanation is shown, grounded in the uploaded database's data

**Then: upload `hospital.db` (or equivalent second test file), replacing the active database.**
- [ ] The active-database indicator updates to show the second uploaded file
- [ ] `get_schema` reflects the second database's schema

**Then: "Which department has the most patients?" (or an equivalent question suited to the second file's schema)**
- [ ] The agent answers correctly using only the second database's actual schema
- [ ] No trace of the first uploaded database or the e-commerce schema appears in the response

---

## 12. Error / Edge Case Testing `[MUST]`

- [ ] Empty question (blank submit) is handled gracefully
- [ ] Nonsense/unrelated question is handled gracefully (no crash, a sensible response)
- [ ] Reference to an unknown table is handled gracefully
- [ ] Reference to an unknown column is handled gracefully (Journey C style correction)
- [ ] A query with no matching records is handled gracefully
- [ ] Invalid SQL from the agent is caught and does not crash the app
- [ ] Database unavailable is handled gracefully
- [ ] LLM provider unavailable is handled gracefully
- [ ] A slow/timed-out API call is handled gracefully (no indefinite spinner)
- [ ] A visualization failure falls back to table + explanation rather than crashing
- [ ] An implied write request (e.g., "delete that order") is declined with a clear, friendly message
- [ ] A very large result set is handled without freezing the UI or overflowing the LLM context
- [ ] Asking a data question before any database is active/available (should never actually occur, since the default database is always active, but verify the fallback if the default fails to load) is handled gracefully, not with a crash
- [ ] Uploading a corrupt/invalid file mid-session does not disrupt the currently active (valid) database or the current conversation

**The application must never expose a raw stack trace to the user, under
any of the above conditions.**

---

## 13. Security Checklist `[MUST]`

- [ ] No API keys anywhere in source
- [ ] `.env` is git-ignored
- [ ] `.env.example` is included and accurate
- [ ] The frontend holds no database credentials
- [ ] The frontend holds no LLM API key
- [ ] The LLM cannot directly access the database — it can only request tool calls
- [ ] SQL is validated before execution, at the tool/database layer (not only via LLM prompting)
- [ ] Destructive SQL is rejected
- [ ] Multi-statement SQL is rejected
- [ ] Internal error details are sanitized before reaching the client
- [ ] Uploaded files are validated as genuine SQLite databases before being registered (not trusted by extension alone)
- [ ] Uploaded files are stored only under the controlled `DATABASE_UPLOAD_DIR`, with generated filenames — the original filename cannot be used for path traversal
- [ ] Uploaded files are never executed as code or opened by anything other than the SQLite/SQLAlchemy connection path
- [ ] The uploaded database's on-disk path is never exposed to the frontend or the LLM
- [ ] One session's uploaded database cannot be reached from another session's requests

---

## 14. Performance / Reliability Checklist `[SHOULD]`

- [ ] A normal query completes reliably within a reasonable time
- [ ] A loading indicator appears during slower operations
- [ ] The agent never retries indefinitely
- [ ] A large result set does not overwhelm the LLM's context window (aggregation path verified — see §9)
- [ ] Chart rendering does not freeze the UI
- [ ] Mermaid rendering does not break the surrounding chat thread
- [ ] The application recovers cleanly from a failed query on the very next turn

---

## 15. Deployment Checklist `[SHOULD, Docker preferred not mandatory]`

- [ ] Local frontend run works (`npm run dev`)
- [ ] Local backend run works (`uvicorn ...`)
- [ ] `docker build` succeeds for both services, if Docker is in scope
- [ ] `docker compose up` works end-to-end, if Docker is in scope
- [ ] The SQLite database file is available/persists correctly in both run modes
- [ ] All environment variables are documented in `.env.example` and the README
- [ ] A genuinely clean clone (fresh directory, no leftover local state) works
- [ ] README setup instructions have been followed literally, start to finish, by someone other than the author

---

## 16. Final Hackathon Submission Checklist `[MUST]`

**FUNCTIONALITY**
- [ ] All 5 tools working
- [ ] Natural language queries working
- [ ] Multi-turn working
- [ ] Charts working
- [ ] Diagrams working
- [ ] Explanations working
- [ ] SQLite database upload/switch working, with the seeded database as default

**ARCHITECTURE**
- [ ] Modular tools
- [ ] Structured tool schemas
- [ ] Dynamic schema discovery
- [ ] Safe (read-only, code-enforced) SQL execution
- [ ] Clear separation of concerns
- [ ] Database source (Database Manager) separated from the agent and tools

**UX**
- [ ] Chat interface
- [ ] Loading states
- [ ] Error states
- [ ] SQL transparency
- [ ] Embedded visualizations
- [ ] Active-database indicator, with upload/replace working from the UI

**VISUALIZATION**
- [ ] Bar
- [ ] Line
- [ ] Pie
- [ ] ER diagram
- [ ] Process-flow diagram
- [ ] Scatter, if implemented `[BONUS]`

**SUBMISSION**
- [ ] GitHub repository accessible
- [ ] README complete
- [ ] Team information complete
- [ ] `.env.example` included
- [ ] No secrets committed
- [ ] Demo video recorded
- [ ] Live/local demo verified end-to-end one final time
- [ ] Final GitHub link submitted

---

## 17. Scope Discipline Reminder

Per `01_PRD.md` and `05_IMPLEMENTATION_PLAN.md`, bonus items (scatter charts,
decision trees, query history, CSV/PNG/PDF export, a non-SQLite backend
configurability demonstration) are checked **only after** every `[MUST]`
and `[SHOULD]` item above is confirmed passing. A bonus feature failing
this checklist is not a freeze blocker; a `[MUST]` item failing is. Note
that SQLite database upload/switch (§2) is **not** a bonus item — it is
part of the MVP (PRD §5.9) and must pass before freeze.

---

## 18. Document Relationship

This checklist verifies, item by item, the requirements defined in
`01_PRD.md` (functional/non-functional requirements, user journeys, success
criteria), the guarantees specified in `02_TRD.md`/`03_ARCHITECTURE.md`
(security boundaries, error-recovery flow, chart/diagram determinism), and
the per-tool contracts in `04_AGENT_TOOLS.md`. It introduces no new
requirement of its own — every checked item traces back to one of those four
documents.
