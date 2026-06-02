// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
// Security: policy text is plain text only — never rendered as HTML.
import { useState } from 'react'

interface PolicyInjectionProps {
  scenarioId: string
  onSubmit: (policy: string) => Promise<void>
  disabled?: boolean
}

const MIN_CHARS = 10
const MAX_CHARS = 500

export function PolicyInjection({ scenarioId, onSubmit, disabled }: PolicyInjectionProps) {
  const [policy, setPolicy] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = policy.trim().length >= MIN_CHARS && !submitting && !disabled

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    setSubmitting(true)
    setError(null)
    try {
      await onSubmit(policy.trim())
      setSubmitted(true)
    } catch {
      setError('Could not submit policy. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div className="bg-green-900 border border-green-700 rounded p-3" role="status">
        <p className="text-xs font-semibold text-green-300">✓ Policy submitted for {scenarioId}</p>
        <button onClick={() => { setSubmitted(false); setPolicy('') }} className="mt-2 text-xs text-green-400 underline">
          Submit another
        </button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} aria-label="Policy injection">
      <div className="flex items-baseline justify-between mb-1.5">
        <label htmlFor="policy-input" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Policy Injection — {scenarioId}
        </label>
        <span className={`text-xs tabular-nums ${MAX_CHARS - policy.length < 50 ? 'text-yellow-400' : 'text-gray-600'}`}>
          {MAX_CHARS - policy.length}
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-2">
        Write a natural language re-orchestration instruction based on the system state above.
      </p>
      <textarea
        id="policy-input"
        value={policy}
        onChange={(e) => setPolicy(e.target.value.slice(0, MAX_CHARS))}
        disabled={disabled || submitting}
        rows={5}
        placeholder="e.g. Prioritize security hardening in the build stage — the security_risk dimension shows critical degradation…"
        className="w-full bg-gray-800 border border-gray-600 rounded px-2.5 py-2 text-xs text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none disabled:opacity-50"
      />
      {policy.trim().length > 0 && policy.trim().length < MIN_CHARS && (
        <p className="text-xs text-yellow-500 mt-1">Minimum {MIN_CHARS} characters required.</p>
      )}
      {error && <p role="alert" className="text-xs text-red-400 mt-1">{error}</p>}
      <button
        type="submit"
        disabled={!canSubmit}
        className="mt-2 w-full py-1.5 text-xs font-semibold rounded bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
      >
        {submitting ? 'Submitting…' : 'Inject Policy →'}
      </button>
    </form>
  )
}
