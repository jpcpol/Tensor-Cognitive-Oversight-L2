# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Interaction timer — NCF Proxy 4: Attention Fragmentation.

Records time-to-first-correction per artifact.
NCF proxy: IQR(time_to_first_correction_seconds) across artifacts.
High IQR → uneven attention → attention fragmentation.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import json
import statistics


@dataclass
class TimingEntry:
    artifact_id: str
    scenario_id: str
    task_id: str
    presentation_epoch: float           # time.time() when artifact shown
    first_correction_epoch: Optional[float] = None  # first user action
    completion_epoch: Optional[float] = None        # task completed

    @property
    def time_to_first_correction(self) -> Optional[float]:
        """Seconds from presentation to first correction. None if no correction made."""
        if self.first_correction_epoch is None:
            return None
        return self.first_correction_epoch - self.presentation_epoch

    @property
    def total_time(self) -> Optional[float]:
        if self.completion_epoch is None:
            return None
        return self.completion_epoch - self.presentation_epoch

    def to_dict(self) -> dict:
        d = asdict(self)
        d["time_to_first_correction_s"] = self.time_to_first_correction
        d["total_time_s"] = self.total_time
        return d


class InteractionTimer:
    """
    Records per-artifact interaction timing for one participant session.
    Computes IQR of time-to-first-correction as the NCF attention proxy.
    """

    def __init__(self, session_id: str, participant_id: str) -> None:
        self.session_id = session_id
        self.participant_id = participant_id
        self._entries: list[TimingEntry] = []
        self._active: Optional[TimingEntry] = None

    # ── Recording API ─────────────────────────────────────────────────────────

    def start_artifact(self, artifact_id: str, scenario_id: str,
                       task_id: str) -> None:
        """Call when an artifact is presented to the participant."""
        if self._active is not None:
            # Auto-close previous if not closed
            self._active.completion_epoch = time.time()
            self._entries.append(self._active)
        self._active = TimingEntry(
            artifact_id=artifact_id,
            scenario_id=scenario_id,
            task_id=task_id,
            presentation_epoch=time.time(),
        )

    def record_first_correction(self) -> None:
        """Call on participant's first interaction (click, keystroke) after presentation."""
        if self._active is not None and self._active.first_correction_epoch is None:
            self._active.first_correction_epoch = time.time()

    def end_artifact(self) -> None:
        """Call when participant submits their response for the current artifact."""
        if self._active is not None:
            self._active.completion_epoch = time.time()
            self._entries.append(self._active)
            self._active = None

    # ── Metrics ───────────────────────────────────────────────────────────────

    def times_to_first_correction(self) -> list[float]:
        """Returns list of time-to-first-correction (seconds) for entries where correction was made."""
        return [
            e.time_to_first_correction
            for e in self._entries
            if e.time_to_first_correction is not None
        ]

    def iqr_attention_fragmentation(self) -> Optional[float]:
        """
        NCF Proxy 4: IQR of time-to-first-correction across artifacts.
        Requires >= 4 entries with recorded corrections.
        Higher IQR indicates more uneven attention distribution.
        """
        times = self.times_to_first_correction()
        if len(times) < 4:
            return None
        times_sorted = sorted(times)
        n = len(times_sorted)
        q1 = statistics.median(times_sorted[: n // 2])
        q3 = statistics.median(times_sorted[(n + 1) // 2 :])
        return q3 - q1

    def mean_time_to_first_correction(self) -> Optional[float]:
        times = self.times_to_first_correction()
        return statistics.mean(times) if times else None

    def summary(self) -> dict:
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "n_artifacts_timed": len(self._entries),
            "n_with_correction": len(self.times_to_first_correction()),
            "mean_time_to_first_correction_s": self.mean_time_to_first_correction(),
            "iqr_attention_fragmentation_s": self.iqr_attention_fragmentation(),
            "entries": [e.to_dict() for e in self._entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.summary(), indent=2)
