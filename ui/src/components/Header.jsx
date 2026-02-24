export default function Header({ dark, onToggle }) {
  return (
    <header className="grid grid-cols-3 items-center px-6 py-4 border-b border-slate-200 dark:border-slate-700">
      {/* Left — spacer to balance the toggle */}
      <div />

      {/* Center — title */}
      <div className="text-center">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
          AgentFlow
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          AI-Powered Document Intelligence
        </p>
      </div>

      {/* Right — dark mode toggle */}
      <div className="flex justify-end">
      <button
        onClick={onToggle}
        className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-700 transition-colors"
        aria-label="Toggle dark mode"
      >
        {dark ? (
          // Sun icon
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 3v1m0 16v1m8.66-9h-1M4.34 12h-1m15.07-6.07-.71.71M6.34 17.66l-.71.71m12.73 0-.71-.71M6.34 6.34l-.71-.71M12 7a5 5 0 1 0 0 10A5 5 0 0 0 12 7z" />
          </svg>
        ) : (
          // Moon icon
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        )}
      </button>
      </div>
    </header>
  )
}
