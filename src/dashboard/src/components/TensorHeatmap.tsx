// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// TensorHeatmap — T[d, k]: quality dimension × time cycle grid.
// Critical for S3 (CCI=4): the temporal drift of technical_debt is visible
// only when multiple cycles are laid out as columns in this grid.

import type { EvaluationVector, DimName } from '../api/types'
import { DIM_NAMES, DIM_LABELS } from '../api/types'

function cellBg(v: number): string {
  if (v >= 0.70) return 'bg-green-700'
  if (v >= 0.55) return 'bg-green-900'
  if (v >= 0.45) return 'bg-gray-700'
  if (v >= 0.30) return 'bg-red-900'
  return 'bg-red-700'
}
function cellText(v: number): string {
  return v >= 0.45 ? 'text-gray-200' : 'text-red-100'
}

export function TensorHeatmap({ vectors, cycleLabels }: { vectors: EvaluationVector[]; cycleLabels?: string[] }) {
  if (vectors.length === 0) return null
  const labels = cycleLabels ?? vectors.map((_, k) => `k=${k}`)

  return (
    <div className="bg-gray-900 rounded border border-gray-700 p-3 overflow-auto">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">T[d, k] — Dimensions × Cycles</span>
        <span className="text-xs text-gray-600">{vectors.length} cycle{vectors.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="min-w-max">
        <div className="flex mb-1" style={{ marginLeft: 96 }}>
          {labels.map((lbl, k) => (
            <div key={k} className="w-12 text-center text-xs text-gray-500 font-mono">{lbl}</div>
          ))}
        </div>
        {DIM_NAMES.map((dim: DimName) => (
          <div key={dim} className="flex items-center mb-0.5">
            <div className="w-24 text-right pr-2 text-xs text-gray-500 font-mono shrink-0 truncate">{DIM_LABELS[dim]}</div>
            {vectors.map((vec, k) => {
              const val = vec[dim]
              return (
                <div key={k} title={`${DIM_LABELS[dim]} k=${k}: ${val.toFixed(3)}`}
                  className={`w-12 h-7 mx-px flex items-center justify-center rounded-sm ${cellBg(val)}`}>
                  <span className={`text-xs font-mono ${cellText(val)}`}>{(val * 100).toFixed(0)}</span>
                </div>
              )
            })}
          </div>
        ))}
        <div className="flex items-center gap-3 mt-3 justify-end">
          <span className="text-xs text-gray-600">Low</span>
          {['bg-red-700', 'bg-red-900', 'bg-gray-700', 'bg-green-900', 'bg-green-700'].map((c, i) => (
            <div key={i} className={`w-5 h-3 rounded-sm ${c}`} />
          ))}
          <span className="text-xs text-gray-600">High</span>
        </div>
      </div>
    </div>
  )
}
