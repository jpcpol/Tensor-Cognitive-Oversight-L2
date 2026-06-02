// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import type { EvaluationVector, DimName } from '../api/types'
import { DIM_LABELS, DIM_NAMES } from '../api/types'

const ANGLE_LABELS: Record<DimName, string> = {
  functional_correctness: 'v₁ Func', architectural_alignment: 'v₂ Arch',
  scalability_projection: 'v₃ Scale', security_risk: 'v₄ Sec',
  observability_coverage: 'v₅ Obs', testability: 'v₆ Test',
  maintainability: 'v₇ Maint', technical_debt: 'v₈ Debt',
  performance: 'v₉ Perf', confidence: 'v₁₀ Conf', anomaly_score: 'v₁₁ Anom',
}

interface VectorRadarProps {
  vector: EvaluationVector
  baseline?: EvaluationVector
  label?: string
}

export function VectorRadar({ vector, baseline, label }: VectorRadarProps) {
  const data = DIM_NAMES.map((key) => ({
    dim: ANGLE_LABELS[key],
    current: Math.round(vector[key] * 100),
    baseline: baseline ? Math.round(baseline[key] * 100) : undefined,
    label: DIM_LABELS[key],
  }))

  return (
    <div className="bg-gray-900 rounded border border-gray-700 p-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Quality Vector φ(A) ∈ [0,1]¹¹
        </span>
        {label && <span className="text-xs text-gray-500">{label}</span>}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={data}>
          <PolarGrid gridType="polygon" stroke="#374151" />
          <PolarAngleAxis dataKey="dim" tick={{ fill: '#9ca3af', fontSize: 10, fontFamily: 'monospace' }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 9 }} tickCount={5} />
          {baseline && (
            <Radar name="Baseline" dataKey="baseline" stroke="#374151" fill="#374151" fillOpacity={0.2} dot={false} />
          )}
          <Radar name="Current" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.35} dot={{ r: 3, fill: '#3b82f6' }} />
          <Tooltip
            contentStyle={{ background: '#1f2937', border: '1px solid #374151', fontSize: 11 }}
            formatter={(val: number, name: string, entry) => [`${val}%  (${entry.payload.label})`, name]}
          />
          {baseline && <Legend wrapperStyle={{ fontSize: 10 }} />}
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
