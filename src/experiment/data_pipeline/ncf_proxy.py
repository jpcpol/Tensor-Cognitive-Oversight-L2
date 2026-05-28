# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
NCF Proxy Aggregator — combines the 4 observable proxies into a
composite Natural Cognitive Frontier measurement for one session.

NCF is at the natural frontier when all 4 proxies are within bounds.
Any proxy exceeding its threshold signals NCF violation (saturation,
incoherence, instability, or fragmentation).

Thresholds (calibrated for pilot, adjustable):
  working_memory_saturation  < 50   (0–100, experimental group target)
  mean_sigma_severity        < 1.0  (severity scale 1–5)
  sigma_accuracy             < 0.20 (accuracy scale 0–1)
  iqr_attention_fragmentation < 30  (seconds)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import json

from .nasa_tlx_form import NASATLXSession
from .correction_log import CorrectionLog
from .accuracy_scorer import AccuracyScorer
from .interaction_timer import InteractionTimer

# Default NCF thresholds — override via NCFThresholds
_DEFAULT_THRESHOLDS = {
    "working_memory_saturation": 50.0,
    "mean_sigma_severity": 1.0,
    "sigma_accuracy": 0.20,
    "iqr_attention_fragmentation_s": 30.0,
}


@dataclass
class NCFProxies:
    """All 4 NCF proxy measurements for one session."""
    session_id: str
    participant_id: str
    working_memory_saturation: Optional[float]      # Proxy 1 — NASA-TLX
    mean_sigma_severity: Optional[float]             # Proxy 2 — Correction log
    sigma_accuracy: Optional[float]                  # Proxy 3 — Accuracy scorer
    iqr_attention_fragmentation_s: Optional[float]   # Proxy 4 — Interaction timer

    def within_bounds(
        self,
        thresholds: Optional[dict] = None,
    ) -> dict[str, Optional[bool]]:
        """
        Returns per-proxy bool: True = within NCF bounds, False = exceeded,
        None = insufficient data to evaluate.
        """
        t = thresholds or _DEFAULT_THRESHOLDS
        return {
            "working_memory_saturation": (
                self.working_memory_saturation < t["working_memory_saturation"]
                if self.working_memory_saturation is not None else None
            ),
            "mean_sigma_severity": (
                self.mean_sigma_severity < t["mean_sigma_severity"]
                if self.mean_sigma_severity is not None else None
            ),
            "sigma_accuracy": (
                self.sigma_accuracy < t["sigma_accuracy"]
                if self.sigma_accuracy is not None else None
            ),
            "iqr_attention_fragmentation_s": (
                self.iqr_attention_fragmentation_s < t["iqr_attention_fragmentation_s"]
                if self.iqr_attention_fragmentation_s is not None else None
            ),
        }

    def ncf_at_frontier(self, thresholds: Optional[dict] = None) -> Optional[bool]:
        """
        True if all evaluable proxies are within bounds (NCF operational).
        None if any proxy has insufficient data.
        False if any proxy exceeds its threshold (NCF violated).
        """
        bounds = self.within_bounds(thresholds)
        values = list(bounds.values())
        if any(v is None for v in values):
            return None
        return all(v is True for v in values)

    def to_dict(self, thresholds: Optional[dict] = None) -> dict:
        bounds = self.within_bounds(thresholds)
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "proxies": {
                "working_memory_saturation": self.working_memory_saturation,
                "mean_sigma_severity": self.mean_sigma_severity,
                "sigma_accuracy": self.sigma_accuracy,
                "iqr_attention_fragmentation_s": self.iqr_attention_fragmentation_s,
            },
            "within_bounds": bounds,
            "ncf_at_frontier": self.ncf_at_frontier(thresholds),
            "thresholds": thresholds or _DEFAULT_THRESHOLDS,
        }

    def to_json(self, thresholds: Optional[dict] = None) -> str:
        return json.dumps(self.to_dict(thresholds), indent=2)


def compute_ncf_proxies(
    tlx_session: NASATLXSession,
    correction_log: CorrectionLog,
    accuracy_scorer: AccuracyScorer,
    interaction_timer: InteractionTimer,
) -> NCFProxies:
    """Aggregate all 4 instruments into a single NCFProxies snapshot."""
    return NCFProxies(
        session_id=tlx_session.session_id,
        participant_id=tlx_session.participant_id,
        working_memory_saturation=tlx_session.mean_working_memory_saturation(),
        mean_sigma_severity=correction_log.mean_sigma_severity(),
        sigma_accuracy=accuracy_scorer.sigma_accuracy(),
        iqr_attention_fragmentation_s=interaction_timer.iqr_attention_fragmentation(),
    )
