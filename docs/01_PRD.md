# Product Requirements Document (PRD)

**Project:** AI Data Analyst — Conversational Database Intelligence
**Event:** iTech AI Innovation Hackathon 2026 (Sairam Hackathon 2026)
**Document status:** Foundational — source of truth for product scope
**Team size:** 3–5
**Submission deadline:** 12 August 2026 (feature-complete/code-frozen by 11 August 2026)

---

## 1. Product Vision

Build an **AI Data Analyst**: a conversational system that lets a non-technical
person ask questions about a structured database in plain English and receive
back a correct answer, a well-chosen visualization or diagram, and a clear
explanation — without ever needing to know SQL, the schema, table
relationships, or which charting library to use.

The structured database itself is not fixed to one dataset: a user can
upload their own SQLite database and immediately start asking questions
about it, or use the application's built-in seeded e-commerce database as
a ready-made demo/sample dataset. Either way, the same conversational
experience and the same five agent tools apply.

The product is deliberately **not** framed as a "natural-language-to-SQL
chatbot." SQL generation is one internal capability among several. The product
is the combination of:

```
Natural Language + Database Intelligence + LLM Agent
+ SQL Generation + Visualization + Diagram Generation + AI Insights
```

**Value proposition:** *A non-technical user can explore, understand,
visualize, and reason about structured database information using natural
language, without needing to know SQL or database internals.*

---

## 2. Problem Statement

Structured business data (sales, customers, orders, inventory) is usually
locked behind SQL and BI tooling that requires technical skill to query and
visualize. Non-technical stakeholders must wait on analysts or engineers for
even simple questions ("what were our top products last quarter?"). This
creates friction, delay, and underuse of available data.

The hackathon problem statement asks for a system that removes this friction
by combining an LLM agent, dynamic schema discovery, safe query execution,
and intelligent visualization/diagram generation behind a single chat
interface.

---

## 3. Target Users

| User | Context | Need |
|---|---|---|
| Non-technical business user (primary persona) | Wants answers from data, does not know SQL | Ask questions in plain English, get answers with visuals and explanations |
| Hackathon judge (evaluation persona) | Time-boxed demo/review | A working, coherent, trustworthy chat experience that clearly satisfies all mandatory criteria |
| Data-literate user (secondary persona) | Wants speed and trust | Wants to see the generated SQL and verify correctness (SQL transparency) |

---

## 4. Solution Overview

A single web application with:

1. A **ChatGPT-style chat interface** (React) as the only surface the user
   interacts with, including a lightweight database upload/selection
   affordance (see item 2).
2. A **Database Manager** that lets the user upload a SQLite database
   (`.db` / `.sqlite` / `.sqlite3`) and makes it the **active database for
   that session**, falling back to the seeded e-commerce database as the
   default/sample dataset whenever nothing has been uploaded.
3. An **LLM-powered agent** (LangChain orchestration layer) that interprets
   user intent and calls a fixed set of **five custom tools**.
4. A **database abstraction layer** that discovers the schema of whichever
   database is currently active dynamically (no hardcoded table/column
   names) and executes **read-only** SQL against it.
5. A **visualization layer** that renders bar/line/pie/scatter charts chosen
   based on data shape and user intent.
6. A **diagram layer** that renders ER diagrams and process-flow diagrams
   (and, as a bonus, decision trees) using Mermaid.js.
7. **Session-scoped conversational memory**, so follow-up questions like
   "now show their trend" or "which one grew fastest" resolve correctly
   against prior turns, within the same session that owns the active
   database (see item 2).

The system is positioned as a single AI Data Analyst persona — the user
should never feel like they are talking to five separate backend tools.

---

## 5. Core Features

### 5.1 Conversational Interface
- Chat UI with real-time message display and streaming/progressive responses
  where practical.
- Message history retained for the duration of the session.
- Visible loading/processing indicators and clear signaling of agent/tool
  activity (e.g., "Checking schema…", "Running query…", "Building chart…").

### 5.2 Natural-Language Database Interaction
- Understands user intent without the user specifying tables, columns, or
  SQL.
- Discovers schema dynamically via the `get_schema` tool, always against
  whichever database is currently **active** for the session — the default
  demo database, or a database the user has uploaded (see §5.9).
- Generates and executes SQL via the `execute_query` tool (read-only),
  against that same active database.

### 5.3 Intelligent Visualization
- `generate_chart` tool selects an appropriate chart type based on data
  shape and intent:
  - Categorical comparison → Bar chart
  - Time-series trend → Line chart
  - Proportional distribution → Pie chart
  - Correlation between two numeric variables → Scatter chart (bonus)
- Charts are embedded inline in the conversation with titles and labeled
  axes.

### 5.4 Diagram Generation
- `generate_flowchart` tool produces Mermaid-based diagrams:
  - Entity-Relationship (ER) diagrams of the discovered schema.
  - Process-flow diagrams (e.g., how an order moves through the system).
  - Decision trees (bonus, time permitting).

### 5.5 Conversational Explanation of Results
- `explain_data` tool produces a plain-language interpretation of a query
  result or chart (trends, standout values, comparisons).

### 5.6 SQL Transparency
- Every data-producing turn shows the generated SQL in a collapsible
  "Generated SQL" section, followed by the query result table, the
  visualization, and the AI's explanation, in that order.

### 5.7 Multi-Turn Context
- The agent retains conversation state within a session so pronouns and
  implicit references ("their", "that", "the fastest one") resolve to
  entities established earlier in the conversation.

### 5.8 Error Handling & Self-Correction
- On an invalid/failing query, the agent reads the database error, re-checks
  the schema if needed, corrects the SQL, retries once, and either returns a
  successful result (with a short note on the correction) or a graceful,
  human-readable failure message. The user is never shown a raw stack trace
  or an unrecoverable crash.
- Empty results, missing tables/columns, and unsupported requests are all
  handled with clear, friendly messaging rather than errors.

### 5.9 Dynamic Database Upload & Session-Scoped Selection
- The user can upload a SQLite database file (`.db`, `.sqlite`, or
  `.sqlite3`) directly through the chat application; once accepted, it
  becomes the **active database** for that user's session.
- The application ships with a seeded e-commerce SQLite database that
  remains available as the **default/demo/sample dataset** — used
  automatically when no database has been uploaded, and always available
  for development, testing, and judging.
- The active database is clearly indicated in the UI (e.g., "Active
  database: sales.db" vs. "Active database: demo e-commerce dataset").
- The user can replace the active database at any time by uploading a
  different SQLite file; the new file becomes active for that session
  going forward.
- Every uploaded file is validated (supported extension, genuine SQLite
  file) before being accepted; invalid files are rejected with a clear,
  friendly message and never replace a currently-working active database.
- The active database is **scoped to the requesting session**, so one
  user's uploaded database is never visible to, or queried by, another
  user's session.
- All five agent tools (`get_schema`, `execute_query`, `generate_chart`,
  `generate_flowchart`, `explain_data`) operate against whichever database
  is active — the agent and tools never assume the seeded e-commerce
  schema.

---

## 6. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | The system MUST provide a chat interface for natural-language input and output. |
| FR-2 | The system MUST implement exactly five agent tools: `get_schema`, `execute_query`, `generate_chart`, `generate_flowchart`, `explain_data`. |
| FR-3 | The system MUST discover the schema of whichever database is currently active for the session dynamically at runtime; no table/column name may be hardcoded into agent logic. |
| FR-4 | The system MUST restrict `execute_query` to read-only statements (`SELECT` only); it MUST reject `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`. |
| FR-5 | The system MUST support at minimum bar, line, and pie charts, and SHOULD support scatter plots. |
| FR-6 | The system MUST select chart type based on the semantic shape of the query/result, not a fixed default. |
| FR-7 | The system MUST support at minimum ER diagrams and process-flow diagrams via Mermaid.js, and MAY support decision trees. |
| FR-8 | The system MUST retain conversational context within a session so follow-up questions resolve correctly. |
| FR-9 | The system MUST display the generated SQL for each data-producing response in an expandable section. |
| FR-10 | The system MUST attempt automatic correction and one retry when a generated query fails, before surfacing a graceful error. |
| FR-11 | The system MUST handle empty results, missing tables/columns, database connection failures, LLM failures, and visualization failures without crashing. |
| FR-12 | The system MUST accept database connection configuration via environment variables (no hardcoded connection details). |
| FR-13 | The system MUST accept LLM provider/model configuration via environment variables. |
| FR-14 | The system MUST allow a user to upload a SQLite database file (`.db`/`.sqlite`/`.sqlite3`) through the chat application, which becomes the active database for that session. |
| FR-15 | The system MUST validate every uploaded file (supported extension and a genuine SQLite database) before accepting it, and MUST reject invalid or unreadable files with a clear, graceful error rather than a crash. |
| FR-16 | The system MUST scope the active database to the requesting session, so that one session's active database is never queried by another session. |
| FR-17 | The system MUST allow the user to replace/switch the active database by uploading a new SQLite file at any point in the session. |
| FR-18 | The system MUST provide the seeded e-commerce SQLite database as the default/sample active database whenever no file has been uploaded for a session. |

---

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | **Reliability** — All five tools must work reliably end-to-end for the demo dataset (weighted 30% of scoring). |
| NFR-2 | **Modularity** — Tools, agent orchestration, database access, and visualization must be independently modifiable (separation of concerns, weighted 25% of scoring). |
| NFR-3 | **Extensibility** — A new tool, a new chart type, or a new database backend can be added without rewriting existing components. |
| NFR-4 | **Security** — SQL execution is read-only by default; no destructive statement can reach the database from the LLM path. |
| NFR-5 | **Usability** — Loading states, error states, and responsive layout across common screen sizes (weighted 15% of scoring). |
| NFR-6 | **Visualization quality** — Charts must have clear titles, readable axis labels, consistent styling, and be embedded naturally in chat (weighted 20% of scoring). |
| NFR-7 | **Portability** — The system must run locally from a clean clone using documented setup steps, and Docker support is preferred. |
| NFR-8 | **Time-to-value** — Architecture favors implementation speed and reliability over completeness, given the 3-day build window. |
| NFR-9 | **Upload safety** — Uploaded files are restricted to supported SQLite extensions, validated as genuine SQLite databases, stored in a controlled application data directory (never executed as arbitrary files), and protected against path traversal; the frontend never receives direct file-system or database credentials for the uploaded file. |

---

## 8. Example User Journeys

### Journey A — Exploratory analysis with follow-up
1. User: *"Show me the top 5 products by revenue this quarter."*
   → Agent calls `get_schema` (if not cached) → `execute_query` → returns a
   ranked table + bar chart + short explanation. Generated SQL is visible in
   a collapsible panel.
2. User: *"Now show the trend for these products over the last year."*
   → Agent resolves "these products" from the prior turn's result set, calls
   `execute_query` again, and `generate_chart` returns a line chart.
3. User: *"Which one grew the fastest?"*
   → Agent reasons over the already-retrieved trend data (or issues a
   follow-up query) and calls `explain_data` to answer directly, referencing
   the specific product.

### Journey B — Schema and process understanding
1. User: *"Draw the ER diagram for this database."*
   → Agent calls `get_schema`, then `generate_flowchart` with diagram
   type = ER, rendered via Mermaid.
2. User: *"Create a flowchart showing how orders move through the system."*
   → Agent calls `generate_flowchart` with diagram type = process flow.

### Journey C — Self-correcting error
1. User: *"Show me sales by revenues."* (ambiguous/incorrect column)
2. Agent generates SQL referencing a non-existent `revenues` column, the
   database returns `no such column: revenues`, the agent re-checks the
   schema, corrects to the real column (e.g., `revenue`), retries, returns
   the correct result, and briefly notes that it corrected the field name.

### Journey D — Database upload and switch
1. User uploads `sales.db` through the chat application's upload
   affordance.
   → The Database Manager validates the file, stores it, and marks it as
   the active database for the session; the UI shows "Active database:
   sales.db".
2. User: *"Which product generated the highest revenue?"*
   → Agent calls `get_schema` against the newly active database (not the
   seeded e-commerce dataset), generates and executes SQL, and returns a
   result, an appropriate chart, and an explanation grounded in `sales.db`'s
   actual schema.
3. User uploads `hospital.db`, replacing the active database.
   → The UI updates to show "Active database: hospital.db".
4. User: *"Which department has the most patients?"*
   → The same application, with no code changes, discovers `hospital.db`'s
   schema and answers correctly — demonstrating that the agent and tools
   carry no assumptions about the e-commerce schema.

---

## 9. Hackathon Requirement Mapping

| Hackathon Evaluation Criterion | Weight | Primary PRD Coverage |
|---|---|---|
| Functionality | 30% | §5.1–5.6, §5.9, §6 (FR-1 to FR-11, FR-14 to FR-17) — all five tools, accurate NL→SQL, dynamic database upload |
| Tool Design & Architecture | 25% | §6 (FR-2, FR-3, FR-12 to FR-18), §7 (NFR-2, NFR-3, NFR-9) — see `02_TRD.md` and `03_ARCHITECTURE.md` |
| Visualization Quality | 20% | §5.3, §6 (FR-5, FR-6), §7 (NFR-6) |
| User Experience | 15% | §5.1, §5.6, §5.7, §7 (NFR-5) |
| Innovation & Creativity | 10% | §11 Bonus Scope |

---

## 10. Scope

### 10.1 MVP Scope (mandatory, must be stable before anything else)
- Chat interface with message history and loading indicators.
- All five tools implemented and reliable: `get_schema`, `execute_query`,
  `generate_chart`, `generate_flowchart`, `explain_data`.
- Bar, line, and pie charts, selected intelligently.
- ER diagrams and process-flow diagrams via Mermaid.
- Multi-turn context retention within a session.
- SQL transparency panel.
- Automatic error interpretation, schema re-check, correction, and one retry.
- Graceful handling of empty results, invalid questions, missing
  tables/columns, connection failures, LLM failures, visualization failures.
- Read-only query enforcement.
- Environment-variable-based configuration for the default database and
  LLM provider.
- User-uploaded SQLite database (`.db`/`.sqlite`/`.sqlite3`) support:
  upload, validation, and becoming the session's active database
  (FR-14–FR-17).
- Active-database indicator in the UI, with the ability to replace the
  active database by uploading a new file.
- Session-scoped active-database isolation (FR-16).
- Representative SQLite e-commerce database (own dataset — see §12),
  available as the default/sample dataset whenever no database has been
  uploaded.

### 10.1.1 Deferred to Day 3 (polish, still mandatory before freeze)
- Responsive layout, refined loading/error states, Docker packaging, README,
  setup verification from a clean clone.

### 11. Bonus Scope (only after MVP is stable — Day 3, time-permitting)
- Scatter plot support (correlation questions).
- Decision-tree diagrams.
- Query history within a session.
- CSV export of results.
- PNG/PDF export of charts.
- Unit tests for critical tools (pytest).
- Basic non-SQLite configurability demonstration (showing that
  `DATABASE_URL` could point at a different backend, e.g., Postgres, and
  that the Database Access Layer's Inspector-based discovery would still
  apply in principle) — distinct from the MVP's SQLite upload feature
  (§5.9), which already demonstrates swapping between SQLite databases at
  runtime; no actual non-SQLite connector is implemented.

Explicitly **not** planned for this hackathon window (higher effort, lower
scoring weight): voice input, collaborative visualization sharing, custom
dashboard builder.

---

## 12. Out of Scope

- Any destructive database operation (`INSERT`/`UPDATE`/`DELETE`/`DDL`)
  through the natural-language path.
- User authentication / multi-tenant access control.
- Simultaneous multi-database querying.
- Microservices, message queues, or distributed infrastructure.
- Retrieval-augmented generation (RAG) over unstructured documents.
- Implementing PostgreSQL, MySQL, MongoDB, or any other non-SQLite database
  connector in this pass — the architecture should allow adding them later
  (see `02_TRD.md`/`03_ARCHITECTURE.md`), but only SQLite (the default demo
  database or a user-uploaded file) is implemented now.
- Executing an uploaded file as anything other than a validated SQLite
  database (no arbitrary file execution).
- A persistent, multi-file database library across sessions — the active
  database is a simple, session-scoped concept (one active file at a time),
  not a saved collection of past uploads.
- An organizer-provided database — none exists yet; the team builds and
  ships its own representative SQLite e-commerce dataset
  (`customers`, `categories`, `products`, `orders`, `order_items`,
  `inventory`, `payments`) as the **default/sample database**, while
  keeping the database connection, schema discovery, and the Database
  Manager (§5.9) generic enough that a user-uploaded SQLite database — or,
  later, an organizer-provided database or non-SQLite backend — can become
  active without rewriting the agent or frontend.

---

## 13. Success Criteria

The project is considered successful for this hackathon if, by the freeze
date (11 August 2026):

1. All five tools function reliably against the active database — the
   seeded demo database by default, or a database the user has uploaded —
   end to end, from the chat UI.
2. A judge can run the three example journeys in §8 (Journeys A–C) without
   the application crashing or returning an unhandled error.
3. Every data-producing answer shows generated SQL, a result table, an
   appropriately chosen chart (where relevant), and a natural-language
   explanation.
4. At least ER and process-flow diagrams render correctly on request.
5. A fresh clone of the repository can be brought up locally using only the
   documented setup steps and a `.env` file.
6. The submission package (README, setup instructions, architecture
   overview, tool documentation, team information, demo video) is complete
   by 12 August 2026.
7. A user can upload a supported SQLite database, see it become the active
   data source, ask natural-language questions against it via all five
   tools, and later replace it with a different SQLite database (Journey D
   in §8) — all without any code change, using the same chat interface and
   tool set.

---

## 14. Document Relationship

This PRD defines *what* the product must do and *why*. Technology choices
and *how* it is built are defined in `02_TRD.md`; system structure and data
flow are defined in `03_ARCHITECTURE.md`. All three documents are kept
mutually consistent — features named here map 1:1 to tools and components
named in the other two documents.
