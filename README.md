# AgentFlow
### AI-Powered HR Document Intelligence

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

## Stack

| Layer | Technology |
|-------|-----------|
| UI | React + Vite + Tailwind CSS |
| API | FastAPI + Uvicorn |
| Agent | LangGraph (compiled StateGraph) |
| Inference | Groq free tier — `llama-3.3-70b-versatile` (text), `llama-4-scout` (vision) |
| Persistence | SQLite via aiosqlite |
| Deployment | Docker Compose |
| Automation | n8n webhook stub (optional, see below) |

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

## Project Structure

```
api/
  app/
    graph/
      nodes/          — LangGraph node implementations (classify, analyze_*)
      tools/          — notification_tool (n8n webhook stub)
      analyze_graph.py — compiled StateGraph pipeline
    parsers/          — PDF/DOCX/CSV/image extraction
    clients/          — Groq inference client with retry logic
    db/               — SQLite init and session repository
    schemas/          — Pydantic models
    settings.py       — Environment config via pydantic-settings
    main.py           — FastAPI app
ui/
  src/
    components/       — Header, UploadZone, ResultCard
    App.jsx
```
