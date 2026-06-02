// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
import type { InferenceResponse, OmegaState } from '../api/types'

const OMEGA_CFG: Record<OmegaState, { label: string; bg: string; text: string; ring: string }> = {
  stable:   { label: 'STABLE',   bg: 'bg-green-900',  text: 'text-green-300',  ring: 'ring-green-700' },
  warning:  { label: 'WARNING',  bg: 'bg-yellow-900', text: 'text-yellow-300', ring: 'ring-yellow-700' },
  critical: { label: 'CRITICAL', bg: 'bg-red-900',    text: 'text-red-300',    ring: 'ring-red-700' },
}
const URGENCY: Record<string, string> = { high: 'bg-red-900 text-red-300', medium: 'bg-orange-900 text-orange-300', low: 'bg-gray-700 text-gray-300' }
const SEVERITY: Record<string, string> = { high: 'bg-red-900 text-red-300', medium: 'bg-yellow-900 text-yellow-300' }

export function InferencePanel({ result }: { result: InferenceResponse }) {
  const omega = OMEGA_CFG[result.omega]
  const degrading = result.delta.filter((t) => t.direction === 'degrading').slice(0, 4)
  const improving = result.delta.filter((t) => t.direction === 'improving').slice(0, 2)

  return (
    <div className="space-y-3">
      {/* Ω */}
      <div className={`flex items-center justify-between rounded p-3 ${omega.bg} ring-1 ${omega.ring}`} aria-label="System state">
        <div>
          <div className={`text-xs font-bold uppercase tracking-widest ${omega.text}`}>Ω System State</div>
          <div className={`text-2xl font-black tracking-wide mt-0.5 ${omega.text}`}>{omega.label}</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500">Score</div>
          <div className={`text-xl font-mono font-bold ${omega.text}`}>{(result.omega_score * 100).toFixed(1)}</div>
        </div>
      </div>

      {/* Δ */}
      {(degrading.length > 0 || improving.length > 0) && (
        <section>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Δ Trends</h3>
          <div className="space-y-1">
            {degrading.map((t, i) => (
              <div key={i} className="flex items-center justify-between bg-gray-800 rounded px-2.5 py-1.5 border border-gray-700">
                <div className="flex items-center gap-2">
                  <span className="text-red-400 text-base leading-none">↓</span>
                  <span className="text-xs text-gray-200 font-mono">{t.dimension.replace(/_/g, ' ')}</span>
                  <span className="text-xs text-gray-600">{t.stage}</span>
                </div>
                <span className="text-xs font-mono text-red-400">{t.slope.toFixed(3)}</span>
              </div>
            ))}
            {improving.map((t, i) => (
              <div key={i} className="flex items-center justify-between bg-gray-800 rounded px-2.5 py-1.5 border border-gray-700 opacity-70">
                <div className="flex items-center gap-2">
                  <span className="text-green-400 text-base leading-none">↑</span>
                  <span className="text-xs text-gray-300 font-mono">{t.dimension.replace(/_/g, ' ')}</span>
                </div>
                <span className="text-xs font-mono text-green-400">+{t.slope.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Ρ */}
      {result.rho.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Ρ Conflicts</h3>
          <div className="space-y-1">
            {result.rho.slice(0, 3).map((c, i) => (
              <div key={i} className="bg-gray-800 rounded px-2.5 py-1.5 border border-gray-700">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-xs font-mono text-gray-200">{c.dimension.replace(/_/g, ' ')}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${SEVERITY[c.severity]}`}>
                    {c.severity.toUpperCase()} Δ={c.delta_score.toFixed(2)}
                  </span>
                </div>
                <span className="text-xs text-gray-500">{c.agents.join(' vs ')} · {c.stage}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Ξ */}
      {result.xi.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Ξ Recommendations</h3>
          <div className="space-y-1">
            {result.xi.slice(0, 3).map((r, i) => (
              <div key={i} className="bg-gray-800 rounded px-2.5 py-1.5 border border-gray-700">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs text-gray-200 leading-snug flex-1">{r.action}</p>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium shrink-0 ${URGENCY[r.urgency]}`}>{r.urgency}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {result.delta.length === 0 && result.rho.length === 0 && (
        <p className="text-xs text-gray-600 italic">No active trends or conflicts detected.</p>
      )}
    </div>
  )
}
