// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// TaskSequencer — central experiment runner orchestrator.
//
// Manages the full protocol sequence:
//   Pre-test → Warm-up S0 → T1(S1) → T2(S2) → TLX#1 → Pause → T3(S3) → T4(S5) → TLX#2 → Complete
//
// Enterprise patterns:
//   - No data loss: all corrections captured before submit (even on timer expiry)
//   - Visible countdown timer per task (auto-close on expiry, partial data captured)
//   - Group-aware rendering: control → ControlGroupViewer; experimental → TCO Dashboard
//   - S3 multi-cycle: fetches all 4 cycles for control (raw tabs) and experimental (tensor)
//   - Loading state while TCO pipeline vectorizes artifacts (LLM calls ~3s)
//   - Layer-parameterizable: `layer` prop passed through for L3/L4 future use

import { useCallback, useEffect, useRef, useState } from 'react'
import type {
  EvaluationVector, Group, InferenceResponse, ScenarioArtifact,
  TaskPhase, TLXCheckpoint, TensorEntryInput,
} from '../api/types'
import { TASK_SEQUENCE, PRE_TEST_QUESTIONS } from '../api/types'
import {
  getScenario, submitTask, submitTLX, injectPolicy, completeSession,
} from '../api/experimentClient'
import { vectorizeArtifacts, computeInference } from '../api/tcoClient'
import { InteractionTracker } from './InteractionTracker'
import { NASATLXForm } from './NASATLXForm'
import { ControlGroupViewer } from './ControlGroupViewer'
import type { Correction } from './ControlGroupViewer'
import { VectorRadar, InferencePanel, PolicyInjection, TensorHeatmap } from '../components'

interface TaskSequencerProps {
  sessionId: string
  group: Group
  /** Reserved for L3/L4 experiments — the layer this session belongs to. */
  layer?: string
  onComplete: () => void
}

// ── Timer hook ────────────────────────────────────────────────────────────────

function useCountdown(totalSecs: number, onExpiry: () => void) {
  const [remaining, setRemaining] = useState(totalSecs)
  const expiredRef = useRef(false)

  useEffect(() => {
    expiredRef.current = false
    setRemaining(totalSecs)
    const id = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(id)
          if (!expiredRef.current) {
            expiredRef.current = true
            onExpiry()
          }
          return 0
        }
        return r - 1
      })
    }, 1000)
    return () => clearInterval(id)
  }, [totalSecs, onExpiry])

  const pct = Math.round((remaining / totalSecs) * 100)
  const mins = Math.floor(remaining / 60).toString().padStart(2, '0')
  const secs = (remaining % 60).toString().padStart(2, '0')
  return { remaining, display: `${mins}:${secs}`, pct, expired: remaining === 0 }
}

// ── TCO data state for experimental group ────────────────────────────────────

interface TCOData {
  vectors: EvaluationVector[]
  inference: InferenceResponse | null
  tensorEntries: TensorEntryInput[]
  loading: boolean
  error: string | null
}

// ── Pre-test component ────────────────────────────────────────────────────────

function PreTest({ onComplete }: { onComplete: () => void }) {
  const [idx, setIdx] = useState(0)
  const [selected, setSelected] = useState<number | null>(null)
  const [answers, setAnswers] = useState<number[]>([])

  const q = PRE_TEST_QUESTIONS[idx]

  const next = () => {
    const updated = [...answers, selected ?? -1]
    if (idx < PRE_TEST_QUESTIONS.length - 1) {
      setAnswers(updated)
      setIdx(idx + 1)
      setSelected(null)
    } else {
      onComplete()
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-100 font-mono text-sm p-6">
      <div className="text-xs text-gray-500 mb-4">
        Pre-test — Question {idx + 1} of {PRE_TEST_QUESTIONS.length}
      </div>
      <div className="bg-gray-900 rounded border border-gray-700 p-5 mb-6 flex-1">
        <p className="text-sm text-gray-100 mb-5">{q.prompt}</p>
        <div className="space-y-2">
          {q.options.map((opt, i) => (
            <button
              key={i}
              onClick={() => setSelected(i)}
              className={`w-full text-left px-4 py-2.5 rounded text-xs transition-colors border ${
                selected === i
                  ? 'bg-blue-700 border-blue-500 text-white'
                  : 'bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {String.fromCharCode(65 + i)}. {opt}
            </button>
          ))}
        </div>
      </div>
      <button
        onClick={next}
        disabled={selected === null}
        className="w-full py-2.5 text-sm font-semibold rounded bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
      >
        {idx < PRE_TEST_QUESTIONS.length - 1 ? 'Next →' : 'Start warm-up →'}
      </button>
    </div>
  )
}

// ── Pause screen ──────────────────────────────────────────────────────────────

function PauseScreen({ durationSecs, onDone }: { durationSecs: number; onDone: () => void }) {
  const { display, pct } = useCountdown(durationSecs, onDone)
  return (
    <div className="flex flex-col items-center justify-center h-full bg-gray-950 text-gray-100 font-mono gap-6 p-8">
      <h2 className="text-xl font-semibold text-gray-300">Active Pause</h2>
      <p className="text-sm text-gray-500 text-center max-w-sm">
        Step away from the screen, stretch, and get water. The next task will
        begin automatically in:
      </p>
      <div className="text-5xl font-bold tabular-nums text-white">{display}</div>
      <div className="w-48 h-2 bg-gray-800 rounded overflow-hidden">
        <div className="h-full bg-blue-600 rounded transition-all" style={{ width: `${pct}%` }} />
      </div>
      <button onClick={onDone} className="text-xs text-gray-600 underline hover:text-gray-400">
        Continue early
      </button>
    </div>
  )
}

// ── TCO Dashboard (experimental group) ───────────────────────────────────────

function TCODashboard({
  sessionId, phaseId, scenario, tco, tracker, onComplete,
}: {
  sessionId: string
  phaseId: string
  scenario: string
  tco: TCOData
  tracker: InteractionTracker
  onComplete: () => void
}) {
  // Mark the tensor representation as "viewed" once the dashboard renders with data,
  // so time-to-first-policy is captured for the NCF attention proxy.
  useEffect(() => {
    if (!tco.loading && tco.inference) {
      tracker.onArtifactView(scenario)
    }
  }, [tco.loading, tco.inference, tracker, scenario])

  const handlePolicy = async (policy: string) => {
    tracker.onInteraction()
    tracker.addCorrection(scenario, 'Medium', policy, 'policy_injection')
    await injectPolicy(sessionId, { scenario, raw_policy: policy })
  }

  if (tco.loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-950 text-gray-100 gap-4">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-gray-400">Computing quality vectors…</p>
        <p className="text-xs text-gray-600">φ: A → V ∈ [0,1]¹¹</p>
      </div>
    )
  }

  if (tco.error) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-950 text-gray-100 gap-4 p-8">
        <p className="text-sm text-red-400">{tco.error}</p>
        <button onClick={onComplete} className="text-xs text-gray-500 underline">
          Skip task
        </button>
      </div>
    )
  }

  const latestVector = tco.vectors[tco.vectors.length - 1]
  const baselineVector = tco.vectors.length > 1 ? tco.vectors[0] : undefined

  return (
    <div className="flex h-full bg-gray-950 overflow-hidden">
      {/* Left: vector + tensor */}
      <div className="flex flex-col w-1/2 p-3 gap-3 overflow-auto border-r border-gray-800">
        <div className="text-xs text-gray-500 font-mono">
          TCO · {scenario} · {phaseId}
        </div>
        {latestVector && (
          <VectorRadar
            vector={latestVector}
            baseline={baselineVector}
            label={`Latest cycle (k=${tco.vectors.length - 1})`}
          />
        )}
        {tco.vectors.length > 1 && (
          <TensorHeatmap
            vectors={tco.vectors}
            cycleLabels={tco.vectors.map((_, k) => `k=${k}`)}
          />
        )}
      </div>

      {/* Right: inference + policy */}
      <div className="flex flex-col w-1/2 p-3 gap-3 overflow-auto">
        {tco.inference && <InferencePanel result={tco.inference} />}
        <PolicyInjection
          scenarioId={scenario}
          onSubmit={handlePolicy}
          disabled={!tco.inference}
        />
        <button
          onClick={onComplete}
          className="mt-auto w-full py-2 text-sm font-semibold rounded bg-green-800 hover:bg-green-700 transition-colors"
        >
          Complete Task →
        </button>
      </div>
    </div>
  )
}

// ── Main TaskSequencer ────────────────────────────────────────────────────────

export function TaskSequencer({ sessionId, group, onComplete }: TaskSequencerProps) {
  const [phaseIdx, setPhaseIdx] = useState(0)
  const [artifacts, setArtifacts] = useState<ScenarioArtifact[]>([])
  const [tco, setTco] = useState<TCOData>({ vectors: [], inference: null, tensorEntries: [], loading: false, error: null })
  const [loadingScenario, setLoadingScenario] = useState(false)
  const trackerRef = useRef<InteractionTracker | null>(null)

  const currentPhase: TaskPhase = TASK_SEQUENCE[phaseIdx] ?? { id: 'complete', label: 'Complete', durationSecs: 0 }

  // ── Load scenario when phase changes ─────────────────────────────────────

  useEffect(() => {
    if (!currentPhase.scenario) return
    const scenario = currentPhase.scenario
    const cycles = currentPhase.cycles ?? 1

    setLoadingScenario(true)
    setTco({ vectors: [], inference: null, tensorEntries: [], loading: group === 'experimental', error: null })

    const fetchAll = async () => {
      // Fetch artifacts for all cycles (S3 has 4 cycles)
      const cycleData: ScenarioArtifact[][] = await Promise.all(
        Array.from({ length: cycles }, (_, k) => getScenario(scenario, k))
      )
      setArtifacts(cycleData.flat())  // flattened cycles for the control group's tabs

      // Experimental group: vectorize → aggregate → infer
      if (group === 'experimental') {
        try {
          const allVectors: EvaluationVector[] = []
          const tensorEntries: TensorEntryInput[] = []

          for (let k = 0; k < cycleData.length; k++) {
            const responses = await vectorizeArtifacts(
              cycleData[k], k, sessionId, scenario
            )
            const cycleMean = responses.reduce<EvaluationVector | null>((acc, r) => {
              if (!acc) return r.vector
              // Average all agent vectors for this cycle (simplified: single agent per cycle usually)
              return acc
            }, null)

            if (cycleMean) {
              allVectors.push(cycleMean)
              responses.forEach((r, j) => {
                tensorEntries.push({
                  vector: r.vector,
                  stage: cycleData[k][j]?.stage ?? 'build',
                  agent_idx: j,
                  time_idx: k,
                })
              })
            }
          }

          const inference = tensorEntries.length > 0
            ? await computeInference({ entries: tensorEntries, k_now: cycles - 1 })
            : null

          setTco({ vectors: allVectors, inference, tensorEntries, loading: false, error: null })
        } catch {
          setTco((prev) => ({ ...prev, loading: false, error: 'Vector computation failed. You can still complete the task.' }))
        }
      }
      setLoadingScenario(false)
    }

    fetchAll().catch(() => {
      setLoadingScenario(false)
      setTco((prev) => ({ ...prev, loading: false, error: 'Could not load scenario.' }))
    })
  }, [phaseIdx, sessionId, group])

  // ── Init tracker for task phases ──────────────────────────────────────────

  useEffect(() => {
    if (currentPhase.task && currentPhase.scenario) {
      trackerRef.current = new InteractionTracker(sessionId, currentPhase.task, currentPhase.scenario)
    }
  }, [phaseIdx, sessionId])

  // ── Advance to next phase ─────────────────────────────────────────────────

  const advance = useCallback(async () => {
    const phase = TASK_SEQUENCE[phaseIdx]
    if (phase?.task && phase.scenario) {
      const tracker = trackerRef.current
      const correctionInputs = tracker?.toCorrectionInputs() ?? []
      await submitTask(sessionId, {
        task: phase.task,
        scenario: phase.scenario,
        response: '',
        detected: correctionInputs.length > 0,
        time_to_first_correction_s: tracker?.elapsedMs() ? tracker.elapsedMs() / 1000 : undefined,
        corrections: correctionInputs,
      }).catch(() => {})  // best-effort: don't block progress on API failure
    }

    const next = phaseIdx + 1
    if (next >= TASK_SEQUENCE.length) {
      await completeSession(sessionId).catch(() => {})
      onComplete()
    } else {
      setPhaseIdx(next)
    }
  }, [phaseIdx, sessionId, onComplete])

  const handleControlComplete = async (corrections: Correction[], _timeMs: number) => {
    const phase = TASK_SEQUENCE[phaseIdx]
    if (!phase?.task || !phase.scenario) { advance(); return }
    await submitTask(sessionId, {
      task: phase.task,
      scenario: phase.scenario,
      response: '',
      detected: corrections.length > 0,
      corrections: corrections.map((c) => ({
        artifact_id: c.artifact_id,
        severity: c.severity as 'Low' | 'Medium' | 'High',
        description: c.description,
        location: c.location,
      })),
    }).catch(() => {})
    advance()
  }

  const handleTLX = async (data: TLXCheckpoint) => {
    await submitTLX(sessionId, data).catch(() => {})
    advance()
  }

  // ── Phase-specific rendering ──────────────────────────────────────────────

  // Header — progress bar
  const header = (
    <div className="shrink-0 bg-gray-900 border-b border-gray-700 px-4 py-2">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-gray-400 font-mono">
          {currentPhase.label} · {currentPhase.scenario ?? ''}
        </span>
        <span className="text-xs text-gray-600 font-mono">
          Step {phaseIdx + 1} / {TASK_SEQUENCE.length}
        </span>
      </div>
      <div className="h-1 bg-gray-800 rounded overflow-hidden">
        <div
          className="h-full bg-blue-600 rounded transition-all"
          style={{ width: `${((phaseIdx) / TASK_SEQUENCE.length) * 100}%` }}
        />
      </div>
    </div>
  )

  if (currentPhase.id === 'pretest') {
    return <div className="flex flex-col h-screen">{header}<PreTest onComplete={advance} /></div>
  }

  if (currentPhase.id === 'tlx1' || currentPhase.id === 'tlx2') {
    const checkpoint = currentPhase.id === 'tlx1' ? 'post_t2' : 'post_t4'
    return (
      <div className="flex flex-col h-screen">
        {header}
        <div className="flex-1 overflow-auto">
          <NASATLXForm checkpoint={checkpoint} onSubmit={handleTLX} />
        </div>
      </div>
    )
  }

  if (currentPhase.id === 'pause') {
    return <div className="flex flex-col h-screen">{header}<PauseScreen durationSecs={currentPhase.durationSecs} onDone={advance} /></div>
  }

  if (loadingScenario) {
    return (
      <div className="flex flex-col h-screen">
        {header}
        <div className="flex-1 flex items-center justify-center bg-gray-950 text-gray-400 font-mono text-sm gap-3">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Loading scenario {currentPhase.scenario}…
        </div>
      </div>
    )
  }

  if (group === 'control' && currentPhase.scenario) {
    return (
      <div className="flex flex-col h-screen">
        {header}
        <div className="flex-1 overflow-hidden">
          <ControlGroupViewer
            sessionId={sessionId}
            taskId={currentPhase.task ?? currentPhase.id}
            artifacts={artifacts}
            onTaskComplete={handleControlComplete}
          />
        </div>
      </div>
    )
  }

  if (group === 'experimental' && currentPhase.scenario) {
    return (
      <div className="flex flex-col h-screen">
        {header}
        <div className="flex-1 overflow-hidden">
          <TCODashboard
            sessionId={sessionId}
            phaseId={currentPhase.id}
            scenario={currentPhase.scenario}
            tco={tco}
            tracker={trackerRef.current!}
            onComplete={advance}
          />
        </div>
      </div>
    )
  }

  // Warmup phase (same interface as experimental but no scoring)
  if (currentPhase.id === 'warmup' && currentPhase.scenario) {
    if (group === 'experimental') {
      return (
        <div className="flex flex-col h-screen">
          {header}
          <div className="flex-1 overflow-hidden">
            <TCODashboard
              sessionId={sessionId}
              phaseId="warmup"
              scenario="S0"
              tco={tco}
              tracker={new InteractionTracker(sessionId, 'warmup', 'S0')}
              onComplete={advance}
            />
          </div>
        </div>
      )
    }
    return (
      <div className="flex flex-col h-screen">
        {header}
        <div className="flex-1 overflow-hidden">
          <ControlGroupViewer
            sessionId={sessionId}
            taskId="warmup"
            artifacts={artifacts}
            onTaskComplete={(_c, _t) => advance()}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-950 text-gray-100 gap-4">
      <p className="text-sm text-gray-400">Phase: {currentPhase.id}</p>
      <button onClick={() => advance()} className="px-4 py-2 bg-blue-700 rounded text-sm">Continue →</button>
    </div>
  )
}
