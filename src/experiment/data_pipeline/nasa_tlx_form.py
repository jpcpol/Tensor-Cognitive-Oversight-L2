# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
NASA Raw-TLX form — NCF Proxy 1: Working Memory Saturation.

Raw-TLX (no weights): 6 subscales on 0-100 scale.
NCF proxy: working_memory_saturation = mean(mental_demand, frustration).

Reference: Hart, S.G., & Staveland, L.E. (1988). Development of NASA-TLX.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import json


SUBSCALES = [
    "mental_demand",
    "physical_demand",
    "temporal_demand",
    "effort",
    "performance",
    "frustration",
]

SUBSCALE_DESCRIPTIONS = {
    "mental_demand":  "How mentally demanding was the task?",
    "physical_demand": "How physically demanding was the task?",
    "temporal_demand": "How hurried or rushed was the pace?",
    "effort":         "How hard did you have to work to accomplish your level of performance?",
    "performance":    "How successful were you in accomplishing the task? (0=perfect, 100=failure)",
    "frustration":    "How insecure, discouraged, irritated, stressed or annoyed were you?",
}


@dataclass
class NASATLXResponse:
    session_id: str
    participant_id: str
    task_id: str                    # T1 | T2 | T3 | T4
    scenario_id: str                # S1 | S2 | S3 | S4 | S5
    mental_demand: int              # 0–100
    physical_demand: int            # 0–100
    temporal_demand: int            # 0–100
    effort: int                     # 0–100
    performance: int                # 0–100  (inverted: 0=perfect)
    frustration: int                # 0–100
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        for s in SUBSCALES:
            v = getattr(self, s)
            if not (0 <= v <= 100):
                raise ValueError(f"Subscale '{s}' must be in [0, 100], got {v}")

    # ── Derived proxies ───────────────────────────────────────────────────────

    @property
    def working_memory_saturation(self) -> float:
        """NCF Proxy 1 — mean(mental_demand, frustration). Higher = more saturated."""
        return (self.mental_demand + self.frustration) / 2.0

    @property
    def raw_tlx_score(self) -> float:
        """Unweighted mean of all 6 subscales (Raw-TLX aggregate)."""
        return sum(getattr(self, s) for s in SUBSCALES) / len(SUBSCALES)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["working_memory_saturation"] = self.working_memory_saturation
        d["raw_tlx_score"] = self.raw_tlx_score
        return d


@dataclass
class NASATLXSession:
    """Collects all Raw-TLX responses for one participant across tasks."""
    session_id: str
    participant_id: str
    responses: list[NASATLXResponse] = field(default_factory=list)

    def add(self, response: NASATLXResponse) -> None:
        if response.session_id != self.session_id:
            raise ValueError("session_id mismatch")
        self.responses.append(response)

    def mean_working_memory_saturation(self) -> Optional[float]:
        if not self.responses:
            return None
        return sum(r.working_memory_saturation for r in self.responses) / len(self.responses)

    def mean_raw_tlx(self) -> Optional[float]:
        if not self.responses:
            return None
        return sum(r.raw_tlx_score for r in self.responses) / len(self.responses)

    def summary(self) -> dict:
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "n_responses": len(self.responses),
            "mean_working_memory_saturation": self.mean_working_memory_saturation(),
            "mean_raw_tlx_score": self.mean_raw_tlx(),
            "responses": [r.to_dict() for r in self.responses],
        }

    def to_json(self) -> str:
        return json.dumps(self.summary(), indent=2)


def collect_cli(session_id: str, participant_id: str,
                task_id: str, scenario_id: str) -> NASATLXResponse:
    """Interactive CLI collector for use during in-person sessions."""
    print(f"\nNASA Raw-TLX — Task {task_id} / Scenario {scenario_id}")
    print("Rate each item from 0 (very low) to 100 (very high).\n")
    scores: dict[str, int] = {}
    for s in SUBSCALES:
        desc = SUBSCALE_DESCRIPTIONS[s]
        while True:
            try:
                val = int(input(f"  {s} — {desc}\n  [0-100]: ").strip())
                if 0 <= val <= 100:
                    scores[s] = val
                    break
                print("  Please enter a value between 0 and 100.")
            except ValueError:
                print("  Invalid input.")
    return NASATLXResponse(
        session_id=session_id,
        participant_id=participant_id,
        task_id=task_id,
        scenario_id=scenario_id,
        **scores,
    )
