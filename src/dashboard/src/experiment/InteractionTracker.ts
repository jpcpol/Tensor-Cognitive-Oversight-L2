// SPDX-License-Identifier: AGPL-3.0
// Copyright (C) 2026 Juan Pablo Chancay
//
// InteractionTracker — NCF Proxy 4: Attention Fragmentation
// Records millisecond-precision events and computes time-to-first-correction
// per artifact. Uses performance.now() to avoid system clock drift.

import type { CorrectionInput, Severity } from '../api/types'

interface TrackedCorrection {
  artifactId: string
  severity: Severity
  description: string
  location: string
  presentedAt: number
  firstActionAt: number | null
}

export class InteractionTracker {
  private readonly sessionId: string
  private readonly taskId: string
  private readonly scenarioId: string
  private presentedAt: number | null = null
  private firstActionAt: number | null = null
  private readonly corrections: TrackedCorrection[] = []
  private taskStartedAt: number = performance.now()

  constructor(sessionId: string, taskId: string, scenarioId: string) {
    this.sessionId = sessionId
    this.taskId = taskId
    this.scenarioId = scenarioId
  }

  onArtifactView(_artifactId: string): void {
    this.presentedAt = performance.now()
    this.firstActionAt = null
  }

  onInteraction(): void {
    if (this.firstActionAt === null) {
      this.firstActionAt = performance.now()
    }
  }

  addCorrection(artifactId: string, severity: Severity, description: string, location: string): void {
    this.corrections.push({
      artifactId,
      severity,
      description,
      location,
      presentedAt: this.presentedAt ?? performance.now(),
      firstActionAt: this.firstActionAt,
    })
  }

  toCorrectionInputs(): CorrectionInput[] {
    return this.corrections.map((c) => ({
      artifact_id: c.artifactId,
      severity: c.severity,
      description: c.description,
      location: c.location,
      time_to_first_correction_s:
        c.firstActionAt !== null
          ? (c.firstActionAt - c.presentedAt) / 1000
          : undefined,
    }))
  }

  elapsedMs(): number {
    return performance.now() - this.taskStartedAt
  }

  getCorrectionCount(): number { return this.corrections.length }
  getSessionId(): string { return this.sessionId }
  getTaskId(): string { return this.taskId }
  getScenarioId(): string { return this.scenarioId }
}
