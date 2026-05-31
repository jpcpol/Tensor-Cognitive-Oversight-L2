# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
NCF proxy computation from persisted session rows.

Reconstructs the four data_pipeline instruments (NASA-TLX, correction log,
accuracy scorer, interaction timer) from `cal_*` DB rows and delegates to
`experiment.data_pipeline.compute_ncf_proxies` — keeping that package the
single source of truth for the proxy formulas. Imported lazily so the API
process starts even when the `experiment` package is not on the path
(production image bundling is a Phase 3 deploy concern).
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# scenario → fault category (correction log grouping)
SCENARIO_CATEGORY = {
    "S1": "security",
    "S2": "architecture",
    "S3": "debt",
    "S4": "observability",
    "S5": "conflict",
}

# control-group severity label → 1–5 scale
SEVERITY_SCALE = {"Low": 2, "Medium": 3, "High": 5}


def compute_ncf_for_session(session) -> Optional[dict]:
    """
    Build the four instruments from a CalSession's related rows and return the
    NCFProxies dict (proxies + within_bounds + ncf_at_frontier). Returns None
    if the data_pipeline package is unavailable.
    """
    try:
        from experiment.data_pipeline.accuracy_scorer import AccuracyScorer, TaskScore
        from experiment.data_pipeline.correction_log import CorrectionLog
        from experiment.data_pipeline.interaction_timer import InteractionTimer, TimingEntry
        from experiment.data_pipeline.nasa_tlx_form import NASATLXResponse, NASATLXSession
        from experiment.data_pipeline.ncf_proxy import compute_ncf_proxies
    except ImportError as exc:
        logger.warning("data_pipeline unavailable — NCF compute skipped: %s", exc)
        return None

    sid, pid = session.id, session.participant_id

    # Proxy 1 — NASA-TLX working memory saturation
    tlx = NASATLXSession(session_id=sid, participant_id=pid)
    for m in session.tlx:
        task = "T2" if m.checkpoint == "post_t2" else "T4"
        tlx.add(NASATLXResponse(
            session_id=sid, participant_id=pid, task_id=task, scenario_id="",
            mental_demand=m.mental_demand or 0,
            physical_demand=m.physical_demand or 0,
            temporal_demand=m.temporal_demand or 0,
            effort=m.effort or 0,
            performance=m.performance or 0,
            frustration=m.frustration or 0,
        ))

    # Proxy 2 — correction log sigma severity (grouped by fault category)
    clog = CorrectionLog(sid, pid)
    for e in session.events:
        if e.event_type != "correction" or not e.payload:
            continue
        p = e.payload
        clog.add_correction(
            task_id=p.get("task", "?"),
            scenario_id=p.get("scenario", "?"),
            artifact_id=e.artifact_id or "",
            fault_category=p.get("fault_category", "other"),
            severity=int(p.get("severity", 3)),
            correction_text=p.get("description", ""),
            time_to_detect_s=p.get("time_to_first_correction_s"),
        )

    # Proxy 3 — accuracy scorer sigma across tasks
    acc = AccuracyScorer(sid, pid)
    for r in session.task_results:
        correct = bool(r.detected) if r.detected is not None else (r.accuracy or 0) >= 0.5
        acc.add_score(TaskScore(
            session_id=sid, participant_id=pid, task_id=r.task, scenario_id=r.scenario,
            correct=correct, participant_response="", ground_truth="",
            partial_credit=r.accuracy,
        ))

    # Proxy 4 — interaction timer IQR of time-to-first-correction
    timer = InteractionTimer(sid, pid)
    for r in session.task_results:
        if r.time_to_first_correction_s is None:
            continue
        timer._entries.append(TimingEntry(
            artifact_id=r.task, scenario_id=r.scenario, task_id=r.task,
            presentation_epoch=0.0,
            first_correction_epoch=r.time_to_first_correction_s,
            completion_epoch=r.time_to_first_correction_s,
        ))

    return compute_ncf_proxies(tlx, clog, acc, timer).to_dict()
