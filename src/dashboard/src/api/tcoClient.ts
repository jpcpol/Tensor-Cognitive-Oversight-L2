// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// Axios client for the TCO Engine core API (/vector, /tensor, /inference).
// These endpoints are compute-heavy (LLM calls, numpy). The client:
//   - Uses generous timeouts (60s for vectorization)
//   - Is layer-agnostic: works for L2, L3, L4 (same tensor operations)

import axios from 'axios'
import { tokenStore } from './experimentClient'
import type {
  AggregateRequest, InferenceRequest, InferenceResponse,
  ScenarioArtifact, TensorSnapshotResponse, VectorRequest, VectorResponse,
} from './types'

const core = axios.create({
  baseURL: '/',
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

core.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function computeVector(req: VectorRequest): Promise<VectorResponse> {
  const { data } = await core.post<VectorResponse>('/vector/compute', req)
  return data
}

/** Vectorize all artifacts of a cycle in parallel — used by the experimental group. */
export async function vectorizeArtifacts(
  artifacts: ScenarioArtifact[],
  cycleK: number,
  sessionId?: string,
  scenarioId?: string
): Promise<VectorResponse[]> {
  return Promise.all(
    artifacts.map((a) =>
      computeVector({
        artifact_id: a.id,
        agent_id: a.agent,
        stage: a.stage,
        cycle_k: cycleK,
        artifact_code: a.content,
        scenario_id: scenarioId,
        session_id: sessionId,
      })
    )
  )
}

export async function aggregateTensor(req: AggregateRequest): Promise<TensorSnapshotResponse> {
  const { data } = await core.post<TensorSnapshotResponse>('/tensor/aggregate', req)
  return data
}

export async function computeInference(req: InferenceRequest): Promise<InferenceResponse> {
  const { data } = await core.post<InferenceResponse>('/inference/compute', req)
  return data
}
