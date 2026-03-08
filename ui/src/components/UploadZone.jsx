import { useRef, useState } from 'react'

const ACCEPTED = '.pdf,.docx,.txt,.csv,.xlsx,.jpg,.jpeg,.png,.webp'
const ACCEPT_LABEL = 'PDF · DOCX · TXT · CSV · XLSX · JPG · PNG · WEBP'

export default function UploadZone({ onSubmit, loading }) {
  const [file, setFile] = useState(null)
  const [context, setContext] = useState('')
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    onSubmit(file, context)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current.click()}
        className={[
          'flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed cursor-pointer transition-colors px-6 py-12',
          dragging
            ? 'border-cyan-400 bg-cyan-50 dark:bg-cyan-950/30'
            : 'border-slate-300 dark:border-slate-600 hover:border-cyan-400 dark:hover:border-cyan-500 bg-slate-50 dark:bg-slate-800/50',
        ].join(' ')}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          className="hidden"
          onChange={(e) => setFile(e.target.files[0] || null)}
        />

        {file ? (
          <>
            <FileIcon />
            <div className="text-center">
              <p className="font-medium text-slate-800 dark:text-slate-100">{file.name}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                {(file.size / 1024).toFixed(1)} KB · click to change
              </p>
            </div>
          </>
        ) : (
          <>
            <UploadIcon />
            <div className="text-center">
              <p className="font-medium text-slate-700 dark:text-slate-300">
                Drop a file here, or click to browse
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{ACCEPT_LABEL}</p>
            </div>
          </>
        )}
      </div>

      {/* Context field */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Context <span className="font-normal text-slate-400">(optional)</span>
        </label>
        <input
          type="text"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder='e.g. "Backend engineer role, 5 years exp required"'
          className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2.5 text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition"
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={!file || loading}
        className="flex items-center justify-center gap-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-300 dark:disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium py-2.5 text-sm transition-colors"
      >
        {loading ? (
          <>
            <Spinner />
            Analyzing…
          </>
        ) : (
          'Analyze Document'
        )}
      </button>
    </form>
  )
}

function UploadIcon() {
  return (
    <svg className="w-10 h-10 text-slate-400 dark:text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
    </svg>
  )
}

function FileIcon() {
  return (
    <svg className="w-10 h-10 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
  )
}

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}
