// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// Axios client for the CAL experiment platform (/cal/api).
// Enterprise patterns:
//  - Auth interceptor: auto-inject Bearer token from sessionStorage
//  - 401 interceptor: clear session + trigger logout callback
//  - Retry on network failures (exponential backoff, 3 attempts)
//  - Typed error normalization — never expose raw stack traces
//  - Layer-agnostic: all endpoints carry a `layer` field (L2/L3/L4)

import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  AdminParticipant,
  ConsentRequest,
  GroupOverrideRequest,
  InviteRequest,
  InviteResponse,
  LoginRequest,
  MeResponse,
  PolicyInjectRequest,
  RegisterRequest,
  ResultsResponse,
  ScenarioArtifact,
  StartSessionRequest,
  TLXCheckpoint,
  TaskSubmitRequest,
  TokenResponse,
  ApiError,
} from './types'

const TOKEN_KEY = 'cal_token'

// ── Token helpers (sessionStorage — cleared on tab close, XSS-safer than localStorage) ──

export const tokenStore = {
  get: (): string | null => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string): void => { sessionStorage.setItem(TOKEN_KEY, token) },
  clear: (): void => { sessionStorage.removeItem(TOKEN_KEY) },
}

// ── Error normalization ───────────────────────────────────────────────────────

function normalizeError(err: unknown): ApiError {
  if (axios.isAxiosError(err)) {
    const ae = err as AxiosError<{ detail?: string }>
    return {
      status: ae.response?.status ?? 0,
      detail: ae.response?.data?.detail ?? ae.message ?? 'Network error',
    }
  }
  return { status: 0, detail: 'Unknown error' }
}

export class ApiException extends Error {
  constructor(public readonly error: ApiError) {
    super(error.detail)
  }
}

// ── Retry helper (exponential backoff, network errors only) ───────────────────

async function withRetry<T>(fn: () => Promise<T>, maxAttempts = 3): Promise<T> {
  let attempt = 0
  while (true) {
    try {
      return await fn()
    } catch (err) {
      attempt++
      const ae = normalizeError(err)
      // Only retry on network errors or 5xx, not on auth/validation errors
      const shouldRetry = attempt < maxAttempts && (ae.status === 0 || ae.status >= 500)
      if (!shouldRetry) throw new ApiException(ae)
      await new Promise((r) => setTimeout(r, 2 ** attempt * 300))
    }
  }
}

// ── Axios instance ────────────────────────────────────────────────────────────

let _logoutCallback: (() => void) | null = null

export function setLogoutCallback(cb: () => void): void {
  _logoutCallback = cb
}

function createClient(): AxiosInstance {
  const client = axios.create({
    baseURL: '/cal/api',
    timeout: 15_000,
    headers: { 'Content-Type': 'application/json' },
  })

  client.interceptors.request.use((config) => {
    const token = tokenStore.get()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })

  client.interceptors.response.use(
    (res) => res,
    (err: AxiosError) => {
      if (err.response?.status === 401) {
        tokenStore.clear()
        _logoutCallback?.()
      }
      return Promise.reject(err)
    }
  )

  return client
}

const http = createClient()

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function register(req: RegisterRequest): Promise<TokenResponse> {
  return withRetry(() =>
    http.post<TokenResponse>('/auth/register', req).then((r) => r.data)
  )
}

export async function login(req: LoginRequest): Promise<TokenResponse> {
  return withRetry(() =>
    http.post<TokenResponse>('/auth/login', req).then((r) => r.data)
  )
}

export async function recordConsent(req: ConsentRequest): Promise<void> {
  return withRetry(() => http.post('/auth/consent', req).then(() => undefined))
}

export async function getMe(): Promise<MeResponse> {
  return withRetry(() => http.get<MeResponse>('/me').then((r) => r.data))
}

// ── Session lifecycle ─────────────────────────────────────────────────────────

export async function getScenario(
  scenarioId: string,
  cycleK = 0
): Promise<ScenarioArtifact[]> {
  return withRetry(() =>
    http
      .get<ScenarioArtifact[]>(`/scenario/${scenarioId}`, { params: { cycle_k: cycleK } })
      .then((r) => r.data)
  )
}

export async function startSession(req: StartSessionRequest): Promise<{ session_id: string }> {
  return withRetry(() =>
    http.post<{ ok: boolean; session_id: string; status: string }>('/session/start', req)
      .then((r) => ({ session_id: r.data.session_id }))
  )
}

export async function submitTask(
  sessionId: string,
  req: TaskSubmitRequest
): Promise<void> {
  return withRetry(() =>
    http.post(`/session/${sessionId}/task`, req).then(() => undefined)
  )
}

export async function submitTLX(
  sessionId: string,
  req: TLXCheckpoint
): Promise<void> {
  return withRetry(() =>
    http.post(`/session/${sessionId}/tlx`, req).then(() => undefined)
  )
}

export async function injectPolicy(
  sessionId: string,
  req: PolicyInjectRequest
): Promise<{ policy_id: string }> {
  return withRetry(() =>
    http
      .post<{ ok: boolean; policy_id: string }>(`/session/${sessionId}/policy`, req)
      .then((r) => ({ policy_id: r.data.policy_id }))
  )
}

export async function completeSession(sessionId: string): Promise<void> {
  return withRetry(() =>
    http.post(`/session/${sessionId}/complete`).then(() => undefined)
  )
}

export async function getSessionResults(sessionId: string): Promise<ResultsResponse> {
  return withRetry(() =>
    http.get<ResultsResponse>(`/session/${sessionId}/results`).then((r) => r.data)
  )
}

// ── Admin ─────────────────────────────────────────────────────────────────────

export async function adminListParticipants(): Promise<AdminParticipant[]> {
  return withRetry(() =>
    http.get<AdminParticipant[]>('/admin/participants').then((r) => r.data)
  )
}

export async function adminOverrideGroup(
  participantId: string,
  req: GroupOverrideRequest
): Promise<void> {
  return withRetry(() =>
    http.post(`/admin/participant/${participantId}/group`, req).then(() => undefined)
  )
}

export async function adminInvite(req: InviteRequest): Promise<InviteResponse> {
  return withRetry(() =>
    http.post<InviteResponse>('/admin/invite', req).then((r) => r.data)
  )
}
