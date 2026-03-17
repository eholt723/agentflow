import { Link } from 'react-router-dom'

const pipeline = [
  {
    step: '1',
    title: 'Upload',
    desc: 'Drop a PDF, DOCX, spreadsheet, or image. The parser extracts text from any format — including scanned documents and handwritten notes via a vision model.',
  },
  {
    step: '2',
    title: 'Classify',
    desc: 'An LLM identifies the document type — resume, interview notes, scorecard, or cover letter — and returns a confidence score.',
  },
  {
    step: '3',
    title: 'Analyze',
    desc: 'The right analysis node runs: deep resume evaluation, interview signal extraction, or scorecard anomaly detection.',
  },
  {
    step: '4',
    title: 'Decision Memo',
    desc: 'A structured memo is assembled with a hiring recommendation, key findings, risk flags, and match score.',
  },
  {
    step: '5',
    title: 'Persist',
    desc: 'The session is saved to SQLite. Related documents — resume + interview for the same candidate — can be grouped under a shared session ID.',
  },
]

const achievements = [
  'Multi-format document parsing: PDF, DOCX, TXT, CSV, XLSX, and images',
  'Vision model fallback for scanned PDFs and handwritten notes (Groq llama-4-scout)',
  'LangGraph multi-step agent pipeline with typed state and conditional routing',
  'Groq free-tier inference — zero LLM hosting cost',
  'Tenacity retry with exponential backoff on 429 and 5xx responses',
  'SQLite session persistence with session grouping via X-Session-ID header',
  'Deterministic pre-check for cover letters fires before LLM (0.97 confidence)',
  'Pydantic Settings — zero hardcoded config, everything from environment',
  '40+ tests across 4 files: HTTP contract tests for all endpoints, Pydantic schema validation, async DB layer, and session grouping — all external calls mocked, no API keys needed',
  'Docker Compose multi-container setup with named volume for data',
  'Deployed to Hugging Face Spaces — free hosting, zero infrastructure cost',
]

const stack = [
  { name: 'FastAPI', role: 'API routing, file upload, schema validation' },
  { name: 'LangGraph', role: 'Multi-step agent pipeline and conditional routing' },
  { name: 'Groq', role: 'Free-tier hosted LLM inference (text + vision)' },
  { name: 'React + Vite', role: 'Frontend UI with dark mode' },
  { name: 'Tailwind CSS', role: 'Utility-first styling' },
  { name: 'SQLite + aiosqlite', role: 'Async session persistence' },
  { name: 'Docker Compose', role: 'Multi-container local and cloud orchestration' },
  { name: 'Hugging Face Spaces', role: 'Free cloud deployment' },
  { name: 'Pydantic', role: 'Request validation and settings management' },
  { name: 'pdfplumber + PyMuPDF', role: 'PDF parsing with fallback chain' },
]

export default function About() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">

      {/* Hero */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
          What is AgentFlow?
        </h2>
        <p className="text-base text-slate-600 dark:text-slate-400 leading-relaxed">
          AgentFlow is a document intelligence assistant built for HR and hiring workflows.
          Upload a resume, interview notes, or scorecard and it returns structured analysis —
          skills, risk flags, match scores, and a hiring memo — powered by a multi-step
          LangGraph agent pipeline running on Groq's free-tier LLM inference.
          The entire stack runs at zero cost.
        </p>
      </section>

      {/* How It Works */}
      <section className="mb-12">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">
          How It Works
        </h2>
        <div className="flex flex-col">
          {pipeline.map((item, i) => (
            <div key={item.step} className="flex gap-4">
              {/* Step indicator + connector */}
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full bg-cyan-600 text-white text-sm font-bold flex items-center justify-center shrink-0">
                  {item.step}
                </div>
                {i < pipeline.length - 1 && (
                  <div className="w-px flex-1 bg-slate-200 dark:bg-slate-700 my-1" />
                )}
              </div>
              {/* Content */}
              <div className="pb-8">
                <p className="text-sm font-semibold text-slate-900 dark:text-white mb-1">
                  {item.title}
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* What Was Built */}
      <section className="mb-12">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          What Was Built
        </h2>
        <ul className="space-y-2">
          {achievements.map(a => (
            <li key={a} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
              <span className="text-cyan-500 font-bold shrink-0 mt-0.5">✓</span>
              {a}
            </li>
          ))}
        </ul>
      </section>

      {/* Tech Stack */}
      <section className="mb-12">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Tech Stack
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {stack.map(t => (
            <div
              key={t.name}
              className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3"
            >
              <p className="text-sm font-semibold text-slate-900 dark:text-white">{t.name}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{t.role}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Links */}
      <section className="flex flex-wrap gap-3">
        <Link
          to="/"
          className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white text-sm font-semibold transition-colors"
        >
          Try the App
        </Link>
        <a
          href="https://github.com/eholt723/agentflow"
          target="_blank"
          rel="noopener noreferrer"
          className="px-5 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-sm font-semibold hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
        >
          View on GitHub
        </a>
      </section>

    </div>
  )
}
