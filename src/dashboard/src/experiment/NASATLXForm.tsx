// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// NASA Raw-TLX form — NCF Proxy 1: Working Memory Saturation
// 6 subscales, 0–100 scale. Raw-TLX: no pairwise weighting (Hart & Staveland 1988).

import { useState } from 'react'
import type { TLXCheckpoint } from '../api/types'

type Checkpoint = 'post_t2' | 'post_t4'
type Subscale = Exclude<keyof TLXCheckpoint, 'checkpoint'>

interface NASATLXFormProps {
  checkpoint: Checkpoint
  onSubmit: (data: TLXCheckpoint) => void
}

const SUBSCALES: Array<{ key: Subscale; label: string; description: string }> = [
  { key: 'mental_demand',   label: 'Mental Demand',   description: 'How mentally demanding was the task?' },
  { key: 'physical_demand', label: 'Physical Demand', description: 'How physically demanding was the task?' },
  { key: 'temporal_demand', label: 'Temporal Demand', description: 'How hurried or rushed was the pace?' },
  { key: 'performance',     label: 'Performance',     description: 'How successful were you? (0 = perfect, 100 = failure)' },
  { key: 'effort',          label: 'Effort',          description: 'How hard did you have to work to accomplish your performance?' },
  { key: 'frustration',     label: 'Frustration',     description: 'How insecure, discouraged, or stressed were you?' },
]

const INITIAL: Record<Subscale, number> = {
  mental_demand: 50, physical_demand: 50, temporal_demand: 50,
  performance: 50, effort: 50, frustration: 50,
}

export function NASATLXForm({ checkpoint, onSubmit }: NASATLXFormProps) {
  const [values, setValues] = useState<Record<Subscale, number>>(INITIAL)

  const set = (key: Subscale, val: number) =>
    setValues((prev) => ({ ...prev, [key]: val }))

  const rawTlx = Object.values(values).reduce((a, b) => a + b, 0) / 6

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-100 font-mono text-sm">
      <div className="px-6 py-3 bg-gray-900 border-b border-gray-700 shrink-0">
        <h1 className="text-base font-semibold text-white">
          NASA Raw-TLX —{' '}
          <span className="text-blue-400">
            {checkpoint === 'post_t2' ? 'Mid-session checkpoint' : 'End of session'}
          </span>
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Rate each dimension from 0 (very low) to 100 (very high).
        </p>
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); onSubmit({ checkpoint, ...values }) }}
        className="flex-1 overflow-auto p-6 space-y-6"
      >
        {SUBSCALES.map(({ key, label, description }) => (
          <div key={key}>
            <div className="flex items-baseline justify-between mb-1">
              <label htmlFor={key} className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                {label}
              </label>
              <span className="text-lg font-bold tabular-nums text-white w-10 text-right">{values[key]}</span>
            </div>
            <p className="text-xs text-gray-500 mb-2">{description}</p>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-600 w-8">Low</span>
              <input
                id={key}
                type="range"
                min={0} max={100} step={5}
                value={values[key]}
                onChange={(e) => set(key, parseInt(e.target.value, 10))}
                aria-label={`${label}: ${values[key]}`}
                className="flex-1 h-2 bg-gray-700 rounded appearance-none cursor-pointer accent-blue-500"
              />
              <span className="text-xs text-gray-600 w-8 text-right">High</span>
            </div>
          </div>
        ))}

        <div className="bg-gray-800 rounded p-3 border border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-400">Raw-TLX aggregate</span>
            <span className="text-xl font-bold tabular-nums text-white">{rawTlx.toFixed(1)}</span>
          </div>
        </div>

        <button
          type="submit"
          className="w-full py-3 text-sm font-semibold rounded bg-blue-700 hover:bg-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          Submit and continue →
        </button>
      </form>
    </div>
  )
}
