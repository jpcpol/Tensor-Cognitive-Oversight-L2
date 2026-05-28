# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Correction log — NCF Proxy 2: Supervisory Coherence.

Records participant corrections with fault_category.
NCF proxy: sigma_severity = std_dev(severity) grouped by fault_category.
Low sigma → consistent severity judgments → supervisory coherence.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal, Optional
import json
import statistics

FaultCategory = Literal[
    "security",       # S1 — SQL injection, credential exposure
    "architecture",   # S2 — circular dependency, design violation
    "debt",           # S3 — technical debt accumulation
    "observability",  # S4 — missing metrics, probes
    "conflict",       # S5 — inter-agent quality conflict
    "other",
]

FAULT_CATEGORIES: list[FaultCategory] = [
    "security", "architecture", "debt", "observability", "conflict", "other"
]


@dataclass
class CorrectionEntry:
    session_id: str
    participant_id: str
    task_id: str                        # T1 | T2 | T3 | T4
    scenario_id: str                    # S1–S5
    artifact_id: str
    fault_category: FaultCategory
    severity: int                       # 1 (low) – 5 (critical)
    correction_text: str                # free-text description of the correction
    time_to_detect_s: Optional[float] = None  # seconds from artifact presentation
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not (1 <= self.severity <= 5):
            raise ValueError(f"severity must be in [1, 5], got {self.severity}")
        if self.fault_category not in FAULT_CATEGORIES:
            raise ValueError(f"Unknown fault_category: {self.fault_category}")

    def to_dict(self) -> dict:
        return asdict(self)


class CorrectionLog:
    """
    Collects all corrections for one participant session.
    Computes NCF Proxy 2: sigma(severity) per fault_category.
    """

    def __init__(self, session_id: str, participant_id: str) -> None:
        self.session_id = session_id
        self.participant_id = participant_id
        self._entries: list[CorrectionEntry] = []

    # ── Recording API ─────────────────────────────────────────────────────────

    def add(self, entry: CorrectionEntry) -> None:
        if entry.session_id != self.session_id:
            raise ValueError("session_id mismatch")
        self._entries.append(entry)

    def add_correction(
        self,
        task_id: str,
        scenario_id: str,
        artifact_id: str,
        fault_category: FaultCategory,
        severity: int,
        correction_text: str,
        time_to_detect_s: Optional[float] = None,
    ) -> CorrectionEntry:
        entry = CorrectionEntry(
            session_id=self.session_id,
            participant_id=self.participant_id,
            task_id=task_id,
            scenario_id=scenario_id,
            artifact_id=artifact_id,
            fault_category=fault_category,
            severity=severity,
            correction_text=correction_text,
            time_to_detect_s=time_to_detect_s,
        )
        self._entries.append(entry)
        return entry

    # ── Metrics ───────────────────────────────────────────────────────────────

    def severities_by_category(self) -> dict[str, list[int]]:
        """Group severity scores by fault_category."""
        result: dict[str, list[int]] = {cat: [] for cat in FAULT_CATEGORIES}
        for e in self._entries:
            result[e.fault_category].append(e.severity)
        return {cat: vals for cat, vals in result.items() if vals}

    def sigma_severity_per_category(self) -> dict[str, Optional[float]]:
        """
        NCF Proxy 2: std_dev(severity) per fault_category.
        Requires >= 2 entries per category. None if insufficient data.
        Low sigma → consistent severity judgments (supervisory coherence).
        """
        by_cat = self.severities_by_category()
        return {
            cat: statistics.stdev(vals) if len(vals) >= 2 else None
            for cat, vals in by_cat.items()
        }

    def mean_sigma_severity(self) -> Optional[float]:
        """Mean of sigma_severity across categories with >= 2 entries."""
        sigmas = [
            v for v in self.sigma_severity_per_category().values()
            if v is not None
        ]
        return statistics.mean(sigmas) if sigmas else None

    def detection_rate(self) -> float:
        """Fraction of entries where time_to_detect_s is recorded."""
        if not self._entries:
            return 0.0
        detected = sum(1 for e in self._entries if e.time_to_detect_s is not None)
        return detected / len(self._entries)

    def summary(self) -> dict:
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "n_corrections": len(self._entries),
            "sigma_severity_per_category": self.sigma_severity_per_category(),
            "mean_sigma_severity": self.mean_sigma_severity(),
            "detection_rate": self.detection_rate(),
            "entries": [e.to_dict() for e in self._entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.summary(), indent=2)
