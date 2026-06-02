// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// Canonical TypeScript types for the TCO Engine API.
// Mirrors the Pydantic schemas in src/tco_engine/schemas/*.py
// and src/tco_engine/schemas/cal.py exactly — keep in sync.

// ── Auth / Registration ──────────────────────────────────────────────────────

export type Role = 'participant' | 'admin'
export type Group = 'control' | 'experimental'
export type ExperienceStratum = 'junior' | 'mid' | 'senior'
export type EducationLevel = 'undergraduate' | 'graduate' | 'other'

export interface RegisterRequest {
  email: string
  password: string
  name: string
  country?: string
  years_experience: number
  education_level?: EducationLevel
  institution?: string
  languages?: string
  ai_familiarity?: number   // 0–4, ANCOVA covariate
  prior_tco_exposure: boolean
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  role: Role
  participant_id: string
}

export interface ConsentRequest {
  consent: boolean
}

// ── Participant self-view ─────────────────────────────────────────────────────

export interface SessionSummary {
  id: string
  layer: string
  status: SessionStatus
  is_pilot: boolean
  scheduled_at: string | null
}

export interface MeResponse {
  participant_id: string
  email: string
  name: string
  role: Role
  group: Group | null
  experience_stratum: ExperienceStratum | null
  consent_given: boolean
  current_session: SessionSummary | null
}

// ── Session lifecycle ─────────────────────────────────────────────────────────

export type SessionStatus = 'invited' | 'in_progress' | 'completed' | 'aborted'

export interface StartSessionRequest {
  session_id?: string
}

export type ArtifactTab = 'code' | 'yaml' | 'architecture' | 'ci_cd'

export interface ScenarioArtifact {
  id: string
  type: ArtifactTab
  label: string
  content: string
  agent: string
  stage: string
}

export type Severity = 'Low' | 'Medium' | 'High'

export interface CorrectionInput {
  artifact_id: string
  severity: Severity
  description: string
  location: string
  time_to_first_correction_s?: number
}

export interface TaskSubmitRequest {
  task: string        // T1..T4
  scenario: string    // S1..S5
  response?: string
  detected?: boolean
  time_to_first_correction_s?: number
  corrections: CorrectionInput[]
}

export interface TLXCheckpoint {
  checkpoint: 'post_t2' | 'post_t4'
  mental_demand: number     // 0–100
  physical_demand: number
  temporal_demand: number
  performance: number
  effort: number
  frustration: number
}

export interface PolicyInjectRequest {
  scenario: string
  raw_policy: string
}

export interface TaskResultOut {
  task: string
  scenario: string
  accuracy: number | null
  detected: boolean | null
}

export interface NCFProxy {
  working_memory_saturation: number | null
  mean_sigma_severity: number | null
  sigma_accuracy: number | null
  iqr_attention_fragmentation_s: number | null
  ncf_at_frontier: boolean | null
}

export interface ResultsResponse {
  session_id: string
  group: Group | null
  status: SessionStatus
  task_results: TaskResultOut[]
  ncf: NCFProxy | null
}

// ── Admin ─────────────────────────────────────────────────────────────────────

export interface AdminParticipant {
  participant_id: string
  name: string
  email: string
  years_experience: number
  experience_stratum: ExperienceStratum | null
  group: Group | null
  ai_familiarity: number | null
  prior_tco_exposure: boolean
  consent_given: boolean
  session_status: SessionStatus | null
  created_at: string
}

export interface GroupOverrideRequest {
  group: Group
}

export interface InviteRequest {
  participant_id: string
  scheduled_at: string  // ISO datetime
  layer: string
  is_pilot: boolean
}

export interface InviteResponse {
  ok: boolean
  session_id: string
  invitation_status: string
  email_sent: boolean
}

// ── TCO Core: Vector ──────────────────────────────────────────────────────────

export interface EvaluationVector {
  functional_correctness: number
  architectural_alignment: number
  scalability_projection: number
  security_risk: number
  observability_coverage: number
  testability: number
  maintainability: number
  technical_debt: number
  performance: number
  confidence: number
  anomaly_score: number
}

export type DimName = keyof EvaluationVector

export const DIM_LABELS: Record<DimName, string> = {
  functional_correctness: 'Functional',
  architectural_alignment: 'Architecture',
  scalability_projection: 'Scalability',
  security_risk: 'Security',
  observability_coverage: 'Observability',
  testability: 'Testability',
  maintainability: 'Maintainability',
  technical_debt: 'Tech Debt',
  performance: 'Performance',
  confidence: 'Confidence',
  anomaly_score: 'Anomaly',
}

export const DIM_NAMES: DimName[] = [
  'functional_correctness', 'architectural_alignment', 'scalability_projection',
  'security_risk', 'observability_coverage', 'testability', 'maintainability',
  'technical_debt', 'performance', 'confidence', 'anomaly_score',
]

export interface VectorRequest {
  artifact_id: string
  agent_id: string
  stage: string
  cycle_k: number
  artifact_code: string
  scenario_id?: string
  participant_id?: string
  session_id?: string
}

export interface VectorResponse {
  artifact_id: string
  agent_id: string
  stage: string
  cycle_k: number
  vector: EvaluationVector
}

// ── TCO Core: Tensor ──────────────────────────────────────────────────────────

export interface TensorEntryInput {
  vector: EvaluationVector
  stage: string
  agent_idx: number
  time_idx: number
}

export interface AggregateRequest {
  entries: TensorEntryInput[]
}

export interface TensorSnapshotResponse {
  shape: number[]
  dim_names: string[]
  stages: string[]
  snapshot: (number | null)[][][]  // [dim][stage][agent]
}

// ── TCO Core: Inference ───────────────────────────────────────────────────────

export type OmegaState = 'stable' | 'warning' | 'critical'

export interface TrendOut {
  dimension: string
  stage: string
  agent: string
  slope: number
  direction: 'improving' | 'degrading'
}

export interface ConflictOut {
  agents: string[]
  stage: string
  dimension: string
  delta_score: number
  severity: 'high' | 'medium'
}

export interface RecommendationOut {
  action: string
  target: string
  estimated_impact: number
  urgency: 'high' | 'medium' | 'low'
}

export interface InferenceResponse {
  omega: OmegaState
  omega_score: number
  delta: TrendOut[]
  rho: ConflictOut[]
  xi: RecommendationOut[]
}

export interface InferenceRequest {
  entries: TensorEntryInput[]
  k_now?: number
}

// ── API error envelope ────────────────────────────────────────────────────────

export interface ApiError {
  status: number
  detail: string
}

// ── Experiment task sequence ──────────────────────────────────────────────────

export type PhaseId =
  | 'pretest'
  | 'warmup'
  | 'T1' | 'T2' | 'tlx1' | 'pause' | 'T3' | 'T4' | 'tlx2'
  | 'complete'

export interface TaskPhase {
  id: PhaseId
  label: string
  durationSecs: number
  task?: string     // T1..T4
  scenario?: string // S1..S5
  cycles?: number   // S3 needs 4 cycles
}

export const TASK_SEQUENCE: TaskPhase[] = [
  { id: 'pretest', label: 'Pre-test',      durationSecs: 600  },
  { id: 'warmup',  label: 'Warm-up (S0)',  durationSecs: 900,  scenario: 'S0' },
  { id: 'T1',      label: 'Task 1',        durationSecs: 1500, task: 'T1', scenario: 'S1' },
  { id: 'T2',      label: 'Task 2',        durationSecs: 1200, task: 'T2', scenario: 'S2' },
  { id: 'tlx1',    label: 'NASA-TLX #1',  durationSecs: 300  },
  { id: 'pause',   label: 'Active Pause', durationSecs: 600  },
  { id: 'T3',      label: 'Task 3',        durationSecs: 900,  task: 'T3', scenario: 'S3', cycles: 4 },
  { id: 'T4',      label: 'Task 4',        durationSecs: 1800, task: 'T4', scenario: 'S5' },
  { id: 'tlx2',    label: 'NASA-TLX #2',  durationSecs: 300  },
]

// Pre-test questions (static — no API required)
export interface PreTestQuestion {
  id: string
  prompt: string
  options: string[]
  correct: number  // index
}

export const PRE_TEST_QUESTIONS: PreTestQuestion[] = [
  {
    id: 'q1',
    prompt: 'Which of these is a SQL injection vulnerability?',
    options: [
      'Using parameterized queries',
      'Using f-string interpolation in a WHERE clause',
      'Using an ORM',
      'Using prepared statements',
    ],
    correct: 1,
  },
  {
    id: 'q2',
    prompt: 'A circular dependency between modules is best described as:',
    options: [
      'Module A imports from Module B, which imports from Module A',
      'A module that imports too many external libraries',
      'A module with high cyclomatic complexity',
      'A module that is not covered by unit tests',
    ],
    correct: 0,
  },
  {
    id: 'q3',
    prompt: 'Cyclomatic complexity measures:',
    options: [
      'Memory consumption of a function',
      'Number of external API calls',
      'Number of linearly independent paths through code',
      'Number of lines of code',
    ],
    correct: 2,
  },
  {
    id: 'q4',
    prompt: 'Which K8s configuration is required for Prometheus scraping?',
    options: [
      'resource.limits.cpu',
      'prometheus.io/scrape: "true" annotation',
      'readinessProbe path',
      'spec.selector.matchLabels',
    ],
    correct: 1,
  },
  {
    id: 'q5',
    prompt: 'Technical debt accumulates when:',
    options: [
      'A service depends on an external API',
      'Shortcuts are taken during development that must be addressed later',
      'Unit test coverage exceeds 80%',
      'Functions have fewer than 10 lines of code',
    ],
    correct: 1,
  },
]
