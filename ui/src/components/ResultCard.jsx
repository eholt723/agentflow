import { useState } from 'react'

const DOC_TYPE_COLORS = {
  resume:          'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  cover_letter:    'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300',
  interview_notes: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  scorecard:       'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  job_desc:        'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
  unknown:         'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
}

const RECOMMENDATION_STYLES = {
  strong_hire: { pill: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300', label: 'Strong Hire' },
  hire:        { pill: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',   label: 'Hire' },
  consider:    { pill: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',   label: 'Consider' },
  follow_up:   { pill: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300',           label: 'Follow Up' },
  pass:        { pill: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',       label: 'Pass' },
}

export default function ResultCard({ result }) {
  const [trailOpen, setTrailOpen] = useState(false)

  const docType = result.doc_type || 'unknown'
  const docTypeLabel = docType.replace('_', ' ')
  const confidence = Math.round((result.doc_type_confidence || 0) * 100)
  const analysis = result.analysis || {}
  const rec = analysis.recommendation
  const recStyle = RECOMMENDATION_STYLES[rec]
  const keyFields = result.key_fields || {}

  return (
    <div className="flex flex-col gap-5">
      {/* Top row: doc type + recommendation */}
      <div className="flex flex-wrap items-center gap-3">
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${DOC_TYPE_COLORS[docType] || DOC_TYPE_COLORS.unknown}`}>
          {docTypeLabel}
        </span>
        <span className="text-xs text-slate-400 dark:text-slate-500">{confidence}% confidence</span>
        {recStyle && (
          <span className={`ml-auto text-xs font-semibold px-3 py-1 rounded-full ${recStyle.pill}`}>
            {recStyle.label}
          </span>
        )}
      </div>

      {/* Key fields */}
      {Object.keys(keyFields).length > 0 && (
        <Section title="Key Fields">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-2">
            {Object.entries(keyFields).map(([k, v]) => {
              if (!v || (Array.isArray(v) && v.length === 0)) return null
              return (
                <div key={k}>
                  <dt className="text-xs text-slate-400 dark:text-slate-500 capitalize">{k.replace(/_/g, ' ')}</dt>
                  <dd className="text-sm text-slate-800 dark:text-slate-100 mt-0.5">
                    {Array.isArray(v) ? v.join(', ') : String(v)}
                  </dd>
                </div>
              )
            })}
          </dl>
        </Section>
      )}

      {/* Analysis detail fields */}
      <AnalysisDetail analysis={analysis} docType={docType} />

      {/* Summary / narrative */}
      {result.summary && (
        <Section title="Summary">
          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{result.summary}</p>
        </Section>
      )}

      {/* Warnings */}
      {result.warnings?.length > 0 && (
        <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 px-4 py-3">
          {result.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-700 dark:text-amber-400">{w}</p>
          ))}
        </div>
      )}

      {/* Action trail — collapsible */}
      <div>
        <button
          onClick={() => setTrailOpen(o => !o)}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
        >
          <svg className={`w-3.5 h-3.5 transition-transform ${trailOpen ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          {result.actions_taken?.length || 0} pipeline steps
        </button>
        {trailOpen && (
          <div className="mt-2 flex flex-col gap-1.5">
            {(result.actions_taken || []).map((a, i) => (
              <div key={i} className="flex items-start gap-3 text-xs font-mono">
                <span className={`mt-0.5 shrink-0 w-1.5 h-1.5 rounded-full ${a.ok ? 'bg-emerald-400' : 'bg-rose-400'}`} />
                <span className="text-slate-500 dark:text-slate-400 w-10 shrink-0">{a.kind}</span>
                <span className="text-slate-700 dark:text-slate-200">{a.name}</span>
                <span className="ml-auto text-slate-400">{a.ms}ms</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">{title}</h3>
      {children}
    </div>
  )
}

function AnalysisDetail({ analysis, docType }) {
  if (!analysis || Object.keys(analysis).length === 0) return null

  const items = []

  if (docType === 'resume') {
    if (analysis.strengths?.length)
      items.push({ label: 'Strengths', value: analysis.strengths.join(' · ') })
    if (analysis.skill_gaps?.length)
      items.push({ label: 'Skill Gaps', value: analysis.skill_gaps.join(' · ') })
    if (analysis.seniority_assessment)
      items.push({ label: 'Seniority', value: analysis.seniority_assessment })
    if (analysis.risk_signals?.length) {
      items.push({
        label: 'Risk Signals',
        value: analysis.risk_signals.map(r => `${r.flag} (${r.severity})`).join(' · '),
      })
    }
  }

  if (docType === 'cover_letter') {
    if (analysis.first_impression)
      items.push({ label: 'First Impression', value: analysis.first_impression })
    if (analysis.motivation_clarity)
      items.push({ label: 'Motivation Clarity', value: analysis.motivation_clarity })
    if (analysis.communication_quality)
      items.push({ label: 'Communication Quality', value: analysis.communication_quality })
    if (analysis.role_fit_signals?.length)
      items.push({ label: 'Role Fit Signals', value: analysis.role_fit_signals.join(' · ') })
    if (analysis.red_flags?.length)
      items.push({ label: 'Red Flags', value: analysis.red_flags.join(' · ') })
  }

  if (docType === 'interview_notes') {
    const ts = analysis.technical_signals || {}
    if (ts.strengths?.length)
      items.push({ label: 'Technical Strengths', value: ts.strengths.join(' · ') })
    if (ts.gaps?.length)
      items.push({ label: 'Technical Gaps', value: ts.gaps.join(' · ') })
    const bs = analysis.behavioral_signals || {}
    if (bs.concerns?.length)
      items.push({ label: 'Behavioral Concerns', value: bs.concerns.join(' · ') })
    if (analysis.inconsistencies?.length)
      items.push({ label: 'Inconsistencies', value: analysis.inconsistencies.join(' · ') })
  }

  if (docType === 'scorecard') {
    if (analysis.high_variance_candidates?.length)
      items.push({ label: 'High Variance Candidates', value: analysis.high_variance_candidates.join(', ') })
    if (analysis.outlier_evaluators?.length)
      items.push({ label: 'Outlier Evaluators', value: analysis.outlier_evaluators.join(', ') })
  }

  if (items.length === 0) return null

  return (
    <Section title="Analysis">
      <dl className="flex flex-col gap-2">
        {items.map(({ label, value }) => (
          <div key={label}>
            <dt className="text-xs text-slate-400 dark:text-slate-500">{label}</dt>
            <dd className="text-sm text-slate-800 dark:text-slate-100 mt-0.5">{value}</dd>
          </div>
        ))}
      </dl>
    </Section>
  )
}
