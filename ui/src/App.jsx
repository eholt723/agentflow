import { useState, useEffect } from 'react'
import Header from './components/Header'
import UploadZone from './components/UploadZone'
import ResultCard from './components/ResultCard'

export default function App() {
  const [dark, setDark] = useState(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches
  )
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  async function handleSubmit(file, context) {
    setLoading(true)
    setResult(null)
    setError(null)

    const body = new FormData()
    body.append('file', file)
    if (context) body.append('context', context)

    try {
      const res = await fetch('/agent/analyze', { method: 'POST', body })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors">
      <Header dark={dark} onToggle={() => setDark(d => !d)} />

      <main className="max-w-5xl mx-auto px-4 py-10 grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">

        {/* Left — upload panel */}
        <div className="rounded-2xl bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-5 uppercase tracking-wider">
            Upload Document
          </h2>
          <UploadZone onSubmit={handleSubmit} loading={loading} />
        </div>

        {/* Right — results panel */}
        <div className="rounded-2xl bg-white dark:bg-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 p-6 min-h-64">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-5 uppercase tracking-wider">
            Analysis Results
          </h2>

          {!result && !error && !loading && (
            <div className="flex flex-col items-center justify-center h-48 text-slate-400 dark:text-slate-600 gap-3">
              <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
              </svg>
              <p className="text-sm">Results will appear here</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center h-48 gap-4">
              <svg className="w-8 h-8 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p className="text-sm text-slate-500 dark:text-slate-400">Running analysis pipeline…</p>
            </div>
          )}

          {error && (
            <div className="rounded-lg bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 px-4 py-3">
              <p className="text-sm text-rose-700 dark:text-rose-400">{error}</p>
            </div>
          )}

          {result && <ResultCard result={result} />}
        </div>
      </main>

      <footer className="max-w-5xl mx-auto px-4 pb-6 flex justify-end">
        <div className="text-right">
          <p className="text-xs text-slate-400 dark:text-slate-600">Created by</p>
          <p className="text-xs font-medium text-slate-500 dark:text-slate-500">Eric Holt</p>
        </div>
      </footer>
    </div>
  )
}
