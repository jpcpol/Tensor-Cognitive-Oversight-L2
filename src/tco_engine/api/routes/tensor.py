# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Tensor endpoints — f: {V} → T ∈ ℝⁿˣˢˣᵃˣᵗ.

POST /tensor/aggregate  → build T from a set of vectorized artifacts and
return the current snapshot T[:, :, :, -1]. Stateless: the caller supplies
the entries, keeping the engine free of per-session tensor state in Phase 1.
"""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, HTTPException

from tco_engine.core.aggregator import (
    DIM_NAMES, STAGE_INDEX, STAGES, TensorAggregator, VectorEntry,
)
from tco_engine.schemas.tensor import AggregateRequest, TensorSnapshotResponse

router = APIRouter()

_aggregator = TensorAggregator()


def build_tensor(req: AggregateRequest) -> np.ndarray:
    """Map request entries → VectorEntry list → aggregated tensor T."""
    if not req.entries:
        raise HTTPException(status_code=400, detail="No entries provided")
    entries: list[VectorEntry] = []
    for e in req.entries:
        if e.stage not in STAGE_INDEX:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown stage '{e.stage}' (expected one of {STAGES})",
            )
        entries.append(VectorEntry(
            vector=e.vector,
            stage_idx=STAGE_INDEX[e.stage],
            agent_idx=e.agent_idx,
            time_idx=e.time_idx,
        ))
    return _aggregator.aggregate(entries)


def _nan_to_none(arr: np.ndarray) -> list:
    return [[[None if np.isnan(v) else float(v) for v in agents]
             for agents in stages] for stages in arr]


@router.post("/aggregate", response_model=TensorSnapshotResponse)
def aggregate(req: AggregateRequest):
    T = build_tensor(req)
    snapshot = _aggregator.current_snapshot(T)   # [n_dims, n_stages, n_agents]
    return TensorSnapshotResponse(
        shape=list(T.shape),
        dim_names=DIM_NAMES,
        stages=STAGES,
        snapshot=_nan_to_none(snapshot),
    )
