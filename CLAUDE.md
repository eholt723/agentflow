# AgentFlow — Claude Code Instructions

## Git Commit & Push Rules

- **Small, focused commits** — one logical change per commit. Do not bundle unrelated
  changes (e.g. a bug fix and a new feature) into the same commit.
- **Commit before starting a new task** — never carry uncommitted changes across phases.
- **Commit messages** must follow this format:
  ```
  <type>: <short description>

  <optional body explaining why, not what>
  ```
  Types: `fix`, `feat`, `refactor`, `test`, `chore`, `docs`
  Examples:
  - `fix: remove circular import in notification_tool`
  - `feat: add Pydantic Settings and populate .env.example`
  - `refactor: emit ToolAction objects directly from decision_graph`
- **Push after each phase completes**, or after any group of related commits.
- Never force-push to `main`.

---

## Session Start Protocol

At the beginning of every work session, check the dev board before doing anything else:

```bash
gh project item-list 3 --owner eholt723 --format json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data['items']:
    print(f\"{item['status']:<15} {item.get('layer',''):<22} {item['title']}\")
"
```

Use the board state to determine what is In Progress, what is Ready to pick up next,
and what phase the project is currently in. Cross-reference with the Phase Roadmap
section below before proposing or starting any work.

---

## Project Overview

AgentFlow is a **Decision Intelligence Business Assistant** for small business operations.
It combines a FastAPI inference layer, LangGraph agent reasoning, n8n workflow automation,
and a multi-container deployment strategy. The goal is end-to-end agent orchestration —
not a simple chat interface.

---

## Architecture Layers

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI + Uvicorn | Endpoint routing, schema validation, error handling |
| Agent | LangGraph | Multi-step reasoning, tool orchestration, conditional routing |
| Inference | Local LLM (OpenAI-compatible) | Language model serving on :8080 |
| Automation | n8n | Slack notifications, webhooks, scheduled workflows |
| Deployment | Docker Compose | Multi-container orchestration |

---

## Key File Paths

```
api/app/main.py                        — FastAPI app, /agent and /agent/analyze endpoints
api/app/runner/agent_runner.py         — Async orchestration wrapper → run_graph()
api/app/graph/decision_graph.py        — Core routing and tool execution logic
api/app/graph/tools/analytics_tool.py  — Analytics tool (mock → real in Phase 3)
api/app/graph/tools/database_tool.py   — Database lookup tool (mock → real in Phase 3)
api/app/graph/tools/notification_tool.py — Notification tool (→ n8n in Phase 5)
api/app/graph/nodes/                   — LangGraph node implementations (Phase 2)
api/app/schemas/agent.py               — ToolAction, AgentRequest, AgentResponse
api/app/schemas/decision.py            — DecisionContext (graph state carrier)
api/app/schemas/tools/                 — Per-tool Pydantic input/output models
api/app/clients/inference_client.py    — Async HTTP client for LLM service (Phase 3)
api/app/settings.py                    — Pydantic BaseSettings (reads from .env)
tests/test_agent_contract.py           — Contract tests (must always pass)
```

---

## Development Workflow

### Run tests
```bash
python -m pytest tests/ -v
```
Always run tests after any change. All tests must pass before moving a board item to Done.

### Environment setup
```bash
cp .env.example .env
# edit .env as needed
pip install -r api/requirements.txt
```

### Start the API (dev)
```bash
uvicorn api.app.main:app --reload
```

---

## Coding Conventions

### ToolAction objects — never strings
All actions emitted inside `decision_graph.py` and any future graph nodes must use
`ToolAction` objects directly. Never append raw strings or dicts to `actions_taken`.

```python
# correct
actions_taken.append(ToolAction(kind="tool", name="analytics_query", ok=True, ms=elapsed_ms, details={"date": target_date}))

# wrong — do not do this
actions_taken.append(f"tool:analytics_query ok ms={elapsed_ms}")
```

The `_normalize_actions()` helper in `main.py` exists only as a safety net for
external/legacy callers — internal graph code should never rely on it.

### Pydantic Settings
All configuration comes from `api/app/settings.py` via `pydantic-settings`.
Access config as `from api.app.settings import settings` then `settings.inference_base_url`.
Never hardcode URLs, model names, or feature flags inline.

### Schema-first
Every tool must have matching Pydantic models in `api/app/schemas/tools/`.
Define input and result models before implementing a new tool.

---

## GitHub Project Board

**Project:** AgentFlow (project #3, owner: eholt723)
**Project ID:** `PVT_kwHODHNqr84BPKhj`

**Key field IDs:**
- Status field: `PVTSSF_lAHODHNqr84BPKhjzg9p2oc`
- Layer field: `PVTSSF_lAHODHNqr84BPKhjzg9p4Rw`

**Status option IDs:**
| Status | ID |
|--------|-----|
| Backlog | `f75ad846` |
| Ready | `98236657` |
| In Progress | `47fc9ee4` |
| Review / Test | `8fa26714` |
| Done | `eb01e0dd` |

**Move a card example:**
```bash
gh project item-edit --project-id PVT_kwHODHNqr84BPKhj \
  --id <ITEM_ID> \
  --field-id PVTSSF_lAHODHNqr84BPKhjzg9p2oc \
  --single-select-option-id <STATUS_OPTION_ID>
```

Claude Code should update the board whenever a task is completed or begins active work.

---

## Phase Roadmap

### Phase 1 — Fix & Stabilize ✅ Complete
- Fixed circular import in `notification_tool.py`
- Added Pydantic `BaseSettings` in `settings.py`
- Populated `.env.example`
- Added `pydantic-settings` to `requirements.txt`
- Defined tool schemas: `analytics.py`, `database.py`, `notification.py`, `decision.py`
- Refactored `decision_graph.py` to emit `ToolAction` objects directly

### Phase 2 — Real LangGraph Integration
- Implement empty graph nodes: `extract_inputs`, `risk_flags`, `score_alignment`, `write_memo`
- Refactor `decision_graph.py` to use LangGraph compiled graph (nodes + edges + typed state)
- Replace if/else routing with LangGraph conditional edges

### Phase 3 — LLM Inference
- Implement inference service (`inference/Dockerfile`, `entrypoint.sh`) — local model (Ollama or llama.cpp)
- Wire `inference_client.py` into the decision graph for actual LLM reasoning

### Phase 4 — Data & Persistence
- Replace mock tools with real DB/analytics backends
- Add conversational state / session management
- Populate `data/context.json` and `data/metrics.json` with seed data

### Phase 5 — Automation & Deployment
- Wire `notification_tool.py` to n8n webhook
- Write all Dockerfiles and `docker-compose.yml`
- Expand test coverage (unit tests per tool, error path tests)
- Implement `/agent/analyze` file analysis endpoint (PDF/CSV parsing)

---

## Board Item IDs (for reference)

| Item | ID |
|------|----|
| End-to-end anomaly workflow test | `PVTI_lAHODHNqr84BPKhjzglkNaI` |
| Define LangGraph planner node | `PVTI_lAHODHNqr84BPKhjzgldxq4` |
| Implement AnalyticsQueryTool (mock) | `PVTI_lAHODHNqr84BPKhjzglkNVQ` |
| Implement DatabaseLookupTool (mock) | `PVTI_lAHODHNqr84BPKhjzglkNX8` |
| retry/fallback logic in LangGraph | `PVTI_lAHODHNqr84BPKhjzgldwrc` |
| Structured tool execution logging | `PVTI_lAHODHNqr84BPKhjzgldwoQ` |
| Initialize inference service container | `PVTI_lAHODHNqr84BPKhjzgldxpA` |
| Implement NotificationTool (Slack/n8n) | `PVTI_lAHODHNqr84BPKhjzgldwqM` |
| conversational memory persistence | `PVTI_lAHODHNqr84BPKhjzgldwkA` |
| Create docker-compose.yml | `PVTI_lAHODHNqr84BPKhjzgldxxo` |
| Cloud deployment | `PVTI_lAHODHNqr84BPKhjzgldwtE` |
| Initialize GitHub Project board | `PVTI_lAHODHNqr84BPKhjzgldx0U` |
| Define MVP Workflow Contract | `PVTI_lAHODHNqr84BPKhjzglkMbo` |
| Implement /agent endpoint | `PVTI_lAHODHNqr84BPKhjzgldxpk` |
