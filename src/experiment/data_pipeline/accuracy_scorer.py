# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Accuracy scorer — NCF Proxy 3: Cognitive Stability.

Binary score per task T1–T4 vs ground truth.
NCF proxy: sigma(accuracy) across T1→T4.
Low sigma → stable accuracy across task types → cognitive stability.

Task definitions:
  T1 — Fault detection:     did participant identify the injected fault?
  T2 — Risk assessment:     did participant correctly classify risk level?
  T3 — Deploy decision:     was deploy/halt decision correct?
  T4 — Re-orchestration:    did policy injection address the root cause?
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal, Optional
import json
import statistics

TaskId = Literal["T1", "T2", "T3", "T4"]
TASK_IDS: list[TaskId] = ["T1", "T2", "T3", "T4"]

TASK_DESCRIPTIONS = {
    "T1": "Fault detection — identify the injected fault in the pipeline",
    "T2": "Risk assessment — classify risk level (LOW/MEDIUM/HIGH/CRITICAL)",
    "T3": "Deploy decision — decide deploy or halt",
    "T4": "Re-orchestration — inject policy addressing root cause",
}


@dataclass
class TaskScore:
    session_id: str
    participant_id: str
    task_id: TaskId
    scenario_id: str
    correct: bool                       # binary: True = correct answer
    participant_response: str           # what the participant said/selected
    ground_truth: str                   # correct answer from scenario spec
    partial_credit: Optional[float] = None  # 0.0–1.0 for partial credit (optional)
    scored_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def score(self) -> float:
        """Returns partial_credit if set, else 1.0 if correct, 0.0 if not."""
        if self.partial_credit is not None:
            return self.partial_credit
        return 1.0 if self.correct else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score"] = self.score
        return d


# Ground truth answers per scenario — used for auto-scoring where applicable
GROUND_TRUTH: dict[str, dict[str, str]] = {
    "S1": {
        "T1": "sql_injection_and_md5_hash",
        "T2": "HIGH",
        "T3": "halt",
        "T4": "parameterize_queries_replace_hash",
    },
    "S2": {
        "T1": "circular_dependency_user_order",
        "T2": "MEDIUM",
        "T3": "halt",
        "T4": "break_circular_dependency",
    },
    "S3": {
        "T1": "gradual_technical_debt_accumulation",
        "T2": "LOW",          # progressive — hard to detect as HIGH early
        "T3": "deploy_with_warning",
        "T4": "refactor_process_order_reduce_cyclomatic_complexity",
    },
    "S4": {
        "T1": "missing_prometheus_probes_no_resources",
        "T2": "MEDIUM",
        "T3": "halt",
        "T4": "add_resource_limits_probes_hpa",
    },
    "S5": {
        "T1": "inter_agent_security_testability_conflict",
        "T2": "HIGH",
        "T3": "halt",
        "T4": "resolve_conflict_prioritize_security_with_test_scaffolding",
    },
}


class AccuracyScorer:
    """
    Collects task scores for one participant session.
    Computes NCF Proxy 3: sigma(accuracy) across T1→T4.
    """

    def __init__(self, session_id: str, participant_id: str) -> None:
        self.session_id = session_id
        self.participant_id = participant_id
        self._scores: list[TaskScore] = []

    # ── Recording API ─────────────────────────────────────────────────────────

    def add_score(self, score: TaskScore) -> None:
        if score.session_id != self.session_id:
            raise ValueError("session_id mismatch")
        self._scores.append(score)

    def record(
        self,
        task_id: TaskId,
        scenario_id: str,
        participant_response: str,
        correct: Optional[bool] = None,
        partial_credit: Optional[float] = None,
    ) -> TaskScore:
        """
        Record a participant response. If correct is None, auto-scores against
        GROUND_TRUTH for T1/T2/T3 (exact match, case-insensitive).
        T4 (re-orchestration) always requires manual scoring.
        """
        gt = GROUND_TRUTH.get(scenario_id, {}).get(task_id, "")
        if correct is None and task_id != "T4":
            correct = participant_response.strip().lower() == gt.strip().lower()
        elif correct is None:
            correct = False  # T4 defaults to False until manually scored

        score = TaskScore(
            session_id=self.session_id,
            participant_id=self.participant_id,
            task_id=task_id,
            scenario_id=scenario_id,
            correct=correct,
            participant_response=participant_response,
            ground_truth=gt,
            partial_credit=partial_credit,
        )
        self._scores.append(score)
        return score

    # ── Metrics ───────────────────────────────────────────────────────────────

    def accuracy_by_task(self) -> dict[str, Optional[float]]:
        """Mean score per task type across all scenarios."""
        by_task: dict[str, list[float]] = {t: [] for t in TASK_IDS}
        for s in self._scores:
            by_task[s.task_id].append(s.score)
        return {
            t: sum(vals) / len(vals) if vals else None
            for t, vals in by_task.items()
        }

    def sigma_accuracy(self) -> Optional[float]:
        """
        NCF Proxy 3: std_dev of per-task accuracy across T1→T4.
        Requires all 4 task types to have >= 1 score.
        Low sigma → stable accuracy across task types (cognitive stability).
        """
        by_task = self.accuracy_by_task()
        values = [v for v in by_task.values() if v is not None]
        if len(values) < 2:
            return None
        return statistics.stdev(values)

    def overall_accuracy(self) -> Optional[float]:
        if not self._scores:
            return None
        return sum(s.score for s in self._scores) / len(self._scores)

    def summary(self) -> dict:
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "n_scores": len(self._scores),
            "overall_accuracy": self.overall_accuracy(),
            "accuracy_by_task": self.accuracy_by_task(),
            "sigma_accuracy": self.sigma_accuracy(),
            "scores": [s.to_dict() for s in self._scores],
        }

    def to_json(self) -> str:
        return json.dumps(self.summary(), indent=2)
