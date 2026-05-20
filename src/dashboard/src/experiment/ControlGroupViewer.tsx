// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// Control group interface: raw artifact viewer + structured correction form.
// Mirrors the TCO dashboard layout dimensions for between-subjects comparability.

import { useState, useEffect, useCallback } from 'react'

type ArtifactTab = 'code' | 'yaml' | 'architecture' | 'ci_cd'
type Severity = 'Low' | 'Medium' | 'High'

export interface RawArtifact {
  id: string
  type: ArtifactTab
  label: string
  content: string
  agent: string
  stage: string
}

export interface Correction {
  artifact_id: string
  description: string
  severity: Severity
  location: string
  submitted_at: number
}

export interface ControlGroupViewerProps {
  sessionId: string
  taskId: string
  artifacts: RawArtifact[]
  onTaskComplete: (corrections: Correction[], timeMs: number) => void
}

const TAB_LABELS: Record<ArtifactTab, string> = {
  code: 'Python Code',
  yaml: 'YAML Config',
  architecture: 'Architecture',
  ci_cd: 'CI/CD Logs',
}

const SEVERITY_BADGE: Record<Severity, string> = {
  Low: 'bg-yellow-900 text-yellow-300 border border-yellow-700',
  Medium: 'bg-orange-900 text-orange-300 border border-orange-700',
  High: 'bg-red-900 text-red-300 border border-red-700',
}

function formatTime(secs: number): string {
  const m = Math.floor(secs / 60).toString().padStart(2, '0')
  const s = (secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

export function ControlGroupViewer({
  sessionId,
  taskId,
  artifacts,
  onTaskComplete,
}: ControlGroupViewerProps) {
  const [activeTab, setActiveTab] = useState<ArtifactTab>('code')
  const [activeArtifactIdx, setActiveArtifactIdx] = useState(0)
  const [corrections, setCorrections] = useState<Correction[]>([])
  const [description, setDescription] = useState('')
  const [severity, setSeverity] = useState<Severity>('Medium')
  const [location, setLocation] = useState('')
  const [startTime] = useState(() => Date.now())
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - startTime) / 1000)), 1000)
    return () => clearInterval(id)
  }, [startTime])

  const artifactsOfTab = useCallback(
    (tab: ArtifactTab) => artifacts.filter((a) => a.type === tab),
    [artifacts],
  )

  const visibleArtifacts = artifactsOfTab(activeTab)
  const currentArtifact = visibleArtifacts[activeArtifactIdx] ?? null

  const handleTabChange = (tab: ArtifactTab) => {
    setActiveTab(tab)
    setActiveArtifactIdx(0)
  }

  const submitCorrection = () => {
    if (!currentArtifact || !description.trim()) return
    setCorrections((prev) => [
      ...prev,
      {
        artifact_id: currentArtifact.id,
        description: description.trim(),
        severity,
        location: location.trim(),
        submitted_at: Date.now(),
      },
    ])
    setDescription('')
    setLocation('')
    setSeverity('Medium')
  }

  const handleComplete = () => {
    onTaskComplete(corrections, Date.now() - startTime)
  }

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100 font-mono text-sm select-none">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700 shrink-0">
        <span className="text-gray-500 text-xs">
          CONTROL · Task <span className="text-gray-300">{taskId}</span> · Session{' '}
          <span className="text-gray-300">{sessionId}</span>
        </span>
        <span className="tabular-nums text-white font-semibold tracking-widest text-base">
          {formatTime(elapsed)}
        </span>
        <span className="text-gray-500 text-xs">
          {corrections.length} correction{corrections.length !== 1 ? 's' : ''} logged
        </span>
      </div>

      <div className="flex flex-1 overflow-hidden">

        {/* ── LEFT: Artifact viewer (2/3 width) ── */}
        <div className="flex flex-col w-2/3 border-r border-gray-700 overflow-hidden">

          {/* Artifact type tabs */}
          <div className="flex shrink-0 border-b border-gray-700 bg-gray-900">
            {(Object.keys(TAB_LABELS) as ArtifactTab[]).map((tab) => {
              const count = artifactsOfTab(tab).length
              return (
                <button
                  key={tab}
                  onClick={() => count > 0 && handleTabChange(tab)}
                  className={[
                    'px-4 py-2 text-xs font-medium transition-colors',
                    activeTab === tab
                      ? 'bg-gray-800 text-white border-b-2 border-blue-400'
                      : 'text-gray-400 hover:text-gray-200',
                    count === 0 ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer',
                  ].join(' ')}
                >
                  {TAB_LABELS[tab]}
                  {count > 0 && <span className="ml-1 text-gray-600">({count})</span>}
                </button>
              )
            })}
          </div>

          {/* Sub-selector when multiple artifacts of same type */}
          {visibleArtifacts.length > 1 && (
            <div className="flex gap-1 px-3 py-1.5 bg-gray-900 border-b border-gray-700 shrink-0">
              {visibleArtifacts.map((a, idx) => (
                <button
                  key={a.id}
                  onClick={() => setActiveArtifactIdx(idx)}
                  className={[
                    'px-2 py-0.5 text-xs rounded transition-colors',
                    idx === activeArtifactIdx
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600',
                  ].join(' ')}
                >
                  {a.label}
                </button>
              ))}
            </div>
          )}

          {/* Artifact metadata strip */}
          {currentArtifact && (
            <div className="px-3 py-1 bg-gray-900 border-b border-gray-700 text-xs text-gray-500 shrink-0">
              Agent: <span className="text-gray-300">{currentArtifact.agent}</span>
              {' · '}
              Stage: <span className="text-gray-300">{currentArtifact.stage}</span>
              {' · '}
              ID: <span className="text-gray-400">{currentArtifact.id}</span>
            </div>
          )}

          {/* Content area */}
          <div className="flex-1 overflow-auto p-4 bg-gray-950">
            {currentArtifact ? (
              <pre className="whitespace-pre-wrap text-xs text-gray-200 leading-relaxed">
                {currentArtifact.content}
              </pre>
            ) : (
              <p className="text-gray-600 italic text-xs mt-4">
                No artifacts of this type in the current scenario.
              </p>
            )}
          </div>
        </div>

        {/* ── RIGHT: Correction form + log (1/3 width) ── */}
        <div className="flex flex-col w-1/3 bg-gray-900 overflow-hidden">

          {/* Correction form */}
          <div className="p-4 border-b border-gray-700 shrink-0">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Log Correction
            </h2>

            <label className="block text-xs text-gray-500 mb-1">Location / line reference</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. line 42, function authenticate"
              className="w-full mb-2 bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-xs text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500"
            />

            <label className="block text-xs text-gray-500 mb-1">Severity</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as Severity)}
              className="w-full mb-2 bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-xs text-gray-100 focus:outline-none focus:border-blue-500"
            >
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
            </select>

            <label className="block text-xs text-gray-500 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={5}
              placeholder="Describe the issue found and the correction needed..."
              className="w-full mb-3 bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-xs text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none"
            />

            <button
              onClick={submitCorrection}
              disabled={!description.trim() || !currentArtifact}
              className="w-full py-1.5 text-xs font-semibold rounded bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
            >
              Submit Correction
            </button>
          </div>

          {/* Corrections log */}
          <div className="flex-1 overflow-auto p-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              Submitted ({corrections.length})
            </h2>
            {corrections.length === 0 ? (
              <p className="text-xs text-gray-600 italic">No corrections logged yet.</p>
            ) : (
              <div className="space-y-2">
                {corrections.map((c, i) => (
                  <div key={i} className="bg-gray-800 rounded p-2 border border-gray-700">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${SEVERITY_BADGE[c.severity]}`}>
                        {c.severity}
                      </span>
                      <span className="text-xs text-gray-500 truncate">{c.artifact_id}</span>
                    </div>
                    {c.location && (
                      <p className="text-xs text-gray-500 mb-0.5">@ {c.location}</p>
                    )}
                    <p className="text-xs text-gray-200 leading-snug">{c.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Complete task */}
          <div className="p-4 border-t border-gray-700 shrink-0">
            <button
              onClick={handleComplete}
              className="w-full py-2 text-sm font-semibold rounded bg-green-800 hover:bg-green-700 transition-colors"
            >
              Complete Task →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
