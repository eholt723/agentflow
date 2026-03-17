---
title: AgentFlow
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# AgentFlow
### AI-Powered HR Document Intelligence

[![CI](https://github.com/eholt723/agentflow/actions/workflows/ci.yml/badge.svg)](https://github.com/eholt723/agentflow/actions/workflows/ci.yml)

AgentFlow accepts uploaded HR documents — resumes, cover letters, interview notes, scorecards, job descriptions — and runs them through a LangGraph agent pipeline powered by Groq LLM inference. It returns structured analytical output: document classification, skill extraction, risk flags, anomaly detection, hiring recommendations, and narrative decision memos.

Built as a portfolio demo targeting HR and hiring workflows.

---

## What It Does

Upload a document and the pipeline:

1. **Classifies** the document type (resume, cover letter, interview notes, scorecard, job description, policy doc, performance review)
2. **Routes** to the appropriate analysis node based on document type
3. **Analyzes** with a specialist LLM prompt — strengths, skill gaps, risk signals, seniority assessment, hiring recommendation
4. **Returns** a structured JSON response rendered in the UI

Supported file formats: PDF, DOCX, TXT, CSV, XLSX, JPG, PNG, WEBP (images processed via Groq vision model)

---

## Tech stack

| Layer | Technology |
|---|---|
| Agent pipeline | LangGraph 0.2 — compiled `StateGraph` with typed state and conditional routing |
| LLM | Groq — `llama-3.3-70b-versatile` (text), `llama-4-scout-17b-16e-instruct` (vision) |
| Document parsing | pdfplumber, PyMuPDF (fallback), python-docx, pandas |
| Backend | FastAPI, Python 3.12, Uvicorn |
| Validation | Pydantic v2 (schema-first) |
| Database | SQLite via aiosqlite |
| Frontend | React 19, Vite, Tailwind CSS |
| Hosting | Hugging Face Spaces (Docker) |
| Automation | n8n webhook stub (optional — `N8N_ENABLED=true`) |

---

## Architecture

```
File upload (PDF / DOCX / TXT / CSV / XLSX / image)
        │
  document_parser.py ── pdfplumber → PyMuPDF fallback → Groq vision (scanned PDFs / images)
        │
  classify_document.py ── filename pre-check (cover letters) → Groq LLM → doc_type + confidence
        │
  ┌─────┴──────────────────────────────────────┐
  │           route on doc_type                │
  └──┬──────────┬──────────┬───────────────────┘
     │          │          │
  resume  interview  scorecard / cover_letter
     │          │          │
     └──────────┴──────────┘
              LangGraph analysis nodes (Groq LLM)
                        │
              write_memo.py ── structured decision memo
                        │
              SQLite (aiosqlite) ── session persisted, grouped via X-Session-ID
```

| Layer | Responsibility |
|---|---|
| Parsing | Extract text from any supported format; vision transcription for images and scanned PDFs |
| Classification | LLM identifies document type and returns a confidence score; deterministic pre-check fires first for cover letters |
| Routing | LangGraph conditional edge directs to the appropriate analysis node |
| Analysis | Specialist LLM prompt per doc type: skills, risk flags, seniority assessment, hiring recommendation |
| Memo assembly | Structured decision memo with key fields, summary, and full action trail |
| Persistence | SQLite via aiosqlite; related documents grouped under a shared session ID via `X-Session-ID` header |
| Notification | n8n webhook stub fires after every analysis (opt-in via `N8N_ENABLED=true`) |

---

## Running Locally

### Prerequisites
- Python 3.12+
- Node 18+
- A free [Groq API key](https://console.groq.com)

### API

```bash
cp .env.example .env
# Add your GROQ_API_KEY to .env

pip install -r api/requirements.txt
uvicorn api.app.main:app --reload
```

### UI

```bash
cd ui
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The Vite dev server proxies `/agent` and `/sessions` to the API on port 8000.

### Docker

```bash
docker compose up -d
```

API available at [http://localhost:8000](http://localhost:8000).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agent/analyze` | Upload a document for analysis |
| `GET` | `/sessions` | List all analysis sessions |
| `GET` | `/sessions/{session_id}` | Get sessions by ID |
| `GET` | `/health` | Health check |

The `/agent/analyze` endpoint accepts `multipart/form-data` with a `file` field and an optional `context` field (plain text hint passed to the LLM). An optional `X-Session-ID` header groups related requests (e.g. resume + interview notes for the same candidate).

---

## n8n Webhook (Optional)

The pipeline includes a notification hook that fires after every analysis completes. To enable it, set two environment variables:

```env
N8N_ENABLED=true
N8N_WEBHOOK_URL=https://your-n8n-instance/webhook/your-trigger-id
```

When enabled, a POST is sent to the webhook with `request_id`, `filename`, `doc_type`, `recommendation`, and `summary`. When disabled (the default), the hook is a no-op and nothing is sent.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Required. Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Text inference model |
| `GROQ_VISION_MODEL` | `meta-llama/llama-4-scout-17b-16e-instruct` | Vision model for image uploads |
| `DB_PATH` | `agentflow.db` | SQLite database path |
| `N8N_ENABLED` | `false` | Enable n8n webhook notifications |
| `N8N_WEBHOOK_URL` | — | n8n webhook URL |

---

## Project structure

```
agentflow/
├── api/
│   └── app/
│       ├── graph/
│       │   ├── nodes/
│       │   │   ├── classify_document.py     # LLM doc-type classifier; deterministic filename pre-check for cover letters
│       │   │   ├── extract_inputs.py        # Intent classification via Groq LLM (anomaly_check, risk_flag, etc.)
│       │   │   ├── analyze_resume.py        # Resume deep analysis — skills, seniority, risk flags, recommendation
│       │   │   ├── analyze_interview.py     # Interview notes → structured hiring memo
│       │   │   ├── analyze_scorecard.py     # Scorecard stats + anomaly detection
│       │   │   ├── analyze_cover_letter.py  # Cover letter analysis node
│       │   │   ├── risk_flags.py            # Risk flag detection node
│       │   │   ├── score_alignment.py       # Match score calculation
│       │   │   └── write_memo.py            # Final decision memo assembly
│       │   ├── tools/
│       │   │   ├── analytics_tool.py        # Analytics query tool (mock)
│       │   │   ├── database_tool.py         # Database lookup tool (mock)
│       │   │   └── notification_tool.py     # n8n webhook stub — fires after every analysis
│       │   ├── analyze_graph.py             # Document analysis pipeline: classify → analyze → memo
│       │   └── decision_graph.py            # Core routing and tool execution (anomaly/intent)
│       ├── runner/
│       │   ├── agent_runner.py              # Async wrapper → decision graph
│       │   └── analyze_runner.py            # Async wrapper → analyze graph (+ vision transcription)
│       ├── parsers/
│       │   └── document_parser.py           # PDF/DOCX/TXT/CSV/XLSX/image extraction; pdfplumber → PyMuPDF → vision fallback
│       ├── clients/
│       │   └── inference_client.py          # Groq text + vision clients; tenacity retry on 429/5xx
│       ├── db/
│       │   ├── database.py                  # SQLite init (aiosqlite, lifespan)
│       │   └── repository.py               # save_analyze_session, save_agent_session, list_sessions
│       ├── schemas/
│       │   ├── agent.py                     # ToolAction, AgentRequest, AgentResponse
│       │   ├── analyze.py                   # AnalyzeState, AnalyzeResponse
│       │   ├── decision.py                  # Decision-related schemas
│       │   └── session.py                   # SessionRecord (history endpoint response)
│       ├── settings.py                      # Pydantic BaseSettings — all config from environment
│       └── main.py                          # FastAPI app: /agent, /agent/analyze, /sessions; serves React build
├── ui/
│   └── src/
│       ├── App.jsx                          # Router and route definitions
│       ├── components/
│       │   ├── Header.jsx                   # Nav, dark mode toggle
│       │   ├── UploadZone.jsx               # File upload drop zone
│       │   └── ResultCard.jsx              # Analysis result renderer
│       └── pages/
│           └── About.jsx                   # Project overview page
├── tests/
│   ├── conftest.py                         # Shared fixtures; mocks all external calls (no API keys needed)
│   ├── test_agent_contract.py              # HTTP contract tests for /agent
│   ├── test_analyze.py                     # HTTP contract tests for /agent/analyze
│   ├── test_schemas.py                     # Unit tests: Pydantic schemas, _normalize_actions, async DB layer
│   └── test_sessions.py                    # Tests for GET /sessions and GET /sessions/{session_id}
├── Dockerfile                              # Multi-stage: Node 20 builds React UI, Python 3.12 serves via FastAPI
├── docker-compose.yml                      # API service + db_data named volume
└── pyproject.toml                          # Project config, pytest settings, coverage config
```
