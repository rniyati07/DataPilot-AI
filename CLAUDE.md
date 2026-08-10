# DataPilot AI — Claude Code Instructions

## 1. Project Overview

DataPilot AI is a conversational AI data analyst being developed for the
Sairam Hackathon 2026 / iTech AI Innovation Hackathon 2026.

The system allows users to upload a SQLite database and interact with its
data through natural language.

Core flow:

User
→ React Chat UI
→ FastAPI
→ Session-scoped Database Manager
→ LangChain Agent
→ Custom Agent Tools
→ Database / Visualization / Explanation
→ React

The five mandatory agent tools are:

- `get_schema`
- `execute_query`
- `generate_chart`
- `generate_flowchart`
- `explain_data`

The seeded e-commerce SQLite database is a sample/demo database.
The application must not assume that every database has the e-commerce schema.

---

## 2. Source of Truth

Before making architectural or implementation decisions, read the relevant
documents in:

`docs/`

The six documents are:

1. `docs/01_PRD.md` — Product requirements
2. `docs/02_TRD.md` — Technical requirements/design
3. `docs/03_ARCHITECTURE.md` — System architecture
4. `docs/04_AGENT_TOOLS.md` — Agent tool contracts
5. `docs/05_IMPLEMENTATION_PLAN.md` — Implementation phases
6. `docs/06_TESTING_CHECKLIST.md` — Testing and acceptance criteria

Treat these documents as the primary project specification.

Do not contradict them or introduce architectural changes without first
identifying the conflict.

---

## 3. Technology Stack

Use the stack defined by the project documentation:

- Frontend: React + Vite + Tailwind CSS
- Backend: Python + FastAPI + Pydantic
- Agent: LangChain
- Database: SQLite + SQLAlchemy
- Charts: Plotly / react-plotly.js
- Diagrams: Mermaid.js
- Testing: Pytest
- Deployment: Docker / Docker Compose

Do not introduce additional frameworks or infrastructure unless there is a
clear implementation requirement.

---

## 4. Database Architecture

The application supports user-uploaded SQLite databases.

The database flow is:

User uploads SQLite file
→ validate file
→ controlled storage
→ associate with current session
→ make it the active database
→ dynamically discover schema
→ agent queries the active database

Important:

- Never hardcode the e-commerce schema.
- `get_schema` must discover the currently active database dynamically.
- `execute_query` must execute against the current session's active database.
- The sample `ecommerce.db` is only the default/demo dataset.
- Database source management must remain separate from the agent logic.
- Session isolation must prevent one session from querying another session's
  database.
- Do not expose raw database paths to the frontend or LLM.

---

## 5. Agent and Tool Rules

The LangChain agent must use the five custom tools defined in
`docs/04_AGENT_TOOLS.md`.

Do not replace them with a generic SQL-agent abstraction if the documentation
requires the custom tool architecture.

Tools must:

- have structured inputs/outputs
- be independently testable
- return useful errors
- remain modular
- operate through the backend/database layer

### SQL Safety

`execute_query` must remain read-only.

Reject:

- INSERT
- UPDATE
- DELETE
- DROP
- ALTER
- TRUNCATE
- CREATE
- ATTACH
- PRAGMA
- multi-statement SQL

Do not falsely reject safe queries merely because forbidden words occur inside
quoted string literals.

Example:

`SELECT 'delete' AS status`

must remain valid.

### Process Flow

`generate_flowchart` must not contain a hardcoded e-commerce workflow.

The agent derives process steps and passes structured steps to the tool.

The tool deterministically generates Mermaid syntax.

The tool must not call the LLM internally.

### Charts

Do not force a chart for every query.

Use appropriate visualization rules based on the data.

### Large Results

Do not blindly send large database result sets to the LLM.

Use bounded/aggregated context where required.

---

## 6. Development Workflow

Follow `docs/05_IMPLEMENTATION_PLAN.md` phase by phase.

Do not jump ahead unnecessarily.

Use a vertical-slice approach:

Frontend
→ Backend
→ Database
→ Agent
→ Tools
→ Working end-to-end flow

Prioritize mandatory functionality before bonus features.

Do not implement bonus features while core functionality is unstable.

Prefer simple, reliable implementations over unnecessary complexity.

---

## 7. Scope Restrictions

Do NOT add unless explicitly requested or required by the documentation:

- RAG
- multi-agent architecture
- microservices
- Kubernetes
- unnecessary Redis usage
- authentication systems
- unnecessary cloud infrastructure
- PostgreSQL/MySQL/MongoDB implementation
- unrelated features

The current database MVP is user-uploaded SQLite.

---

## 8. Security and Configuration

- Never hardcode API keys.
- Use `.env`.
- Maintain `.env.example`.
- Never commit secrets.
- Validate uploaded database files.
- Protect against path traversal.
- Keep uploaded databases isolated by session.
- Do not expose internal filesystem paths to the frontend.

---

## 9. Code Quality

- Keep modules focused and maintainable.
- Follow existing project conventions.
- Use clear names and type hints where appropriate.
- Add tests for critical functionality.
- Do not modify unrelated files.
- Do not rewrite working code unnecessarily.
- Before adding a dependency, check whether the existing stack already
  provides the required functionality.

---

## 10. Important Implementation Rule

Before implementing a feature:

1. Identify the relevant phase in `docs/05_IMPLEMENTATION_PLAN.md`.
2. Read the corresponding requirements in the PRD/TRD.
3. Check the architecture and tool contracts.
4. Implement the smallest solution satisfying those requirements.
5. Run the relevant tests from `docs/06_TESTING_CHECKLIST.md`.
6. Do not move to the next major phase until the current phase is working.

If a requirement is ambiguous or conflicts with another project document,
STOP and explain the conflict before making an architectural decision.

---

## 11. Current Priority

The immediate goal is a reliable MVP:

SQLite upload
→ active session database
→ dynamic schema discovery
→ safe SQL execution
→ LangChain agent
→ React result display
→ charts / diagrams / explanations
→ testing
→ deployment readiness

Do not optimize or polish prematurely.

Functionality and reliability come before visual polish and bonus features.

---

## 12. Pending Documentation Corrections

There are two known documentation corrections that must be addressed when
the project reaches the relevant documentation/implementation stage:

1. In `docs/05_IMPLEMENTATION_PLAN.md`:
   - SQL transparency must be classified as MUST HAVE.
   - Phase 11 SQL Transparency must be classified as MUST.

2. In `docs/04_AGENT_TOOLS.md`:
   - Clarify how `session_id` reaches the Database Manager/tool execution
     context so the correct active database is resolved per session without
     exposing `session_id` as an LLM-facing tool argument.

Do not make these changes unless the user asks to apply the pending
documentation corrections at that stage.

---

## 13. Hackathon Deadline

The implementation is being developed with the goal of reaching code freeze
by August 11, 2026, leaving August 12 for submission-related work.

Prioritize completing the mandatory requirements over bonus features.

---

## Final Rule

When in doubt:

1. Follow the six documents in `docs/`.
2. Preserve the established architecture.
3. Prefer the simplest reliable implementation.
4. Do not expand scope without explicit approval.
5. Ask before making a significant architectural change.