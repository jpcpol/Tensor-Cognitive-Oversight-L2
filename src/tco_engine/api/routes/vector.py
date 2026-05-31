# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Vector endpoint — φ: A → V ∈ [0,1]¹¹.

POST /vector/compute  → vectorize a single artifact via the Vectorizer
(radon + bandit + LLM-QA). The Vectorizer is instantiated lazily so the API
process starts even when no LLM credentials are configured (the dependency is
only required when a vectorization is actually requested).
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from tco_engine.core.vectorizer import Artifact, Vectorizer
from tco_engine.schemas.vector import VectorRequest, VectorResponse

router = APIRouter()


@lru_cache(maxsize=1)
def _vectorizer() -> Vectorizer:
    return Vectorizer()


@router.post("/compute", response_model=VectorResponse)
def compute_vector(req: VectorRequest):
    artifact = Artifact(
        artifact_id=req.artifact_id,
        agent_id=req.agent_id,
        stage=req.stage,
        cycle_k=req.cycle_k,
        code=req.artifact_code,
    )
    try:
        vector = _vectorizer().vectorize(artifact)
    except Exception as exc:  # noqa: BLE001 — surface backend/LLM failures as 502
        raise HTTPException(status_code=502, detail=f"Vectorization failed: {exc}")

    return VectorResponse(
        artifact_id=req.artifact_id,
        agent_id=req.agent_id,
        stage=req.stage,
        cycle_k=req.cycle_k,
        vector=vector,
    )
