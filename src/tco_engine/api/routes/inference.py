# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Inference endpoint — I: T → {Ω, Δ, Ρ, Ξ}.

POST /inference/compute  → build T from the supplied entries and run the
InferenceEngine, returning global state Ω, trends Δ, conflicts Ρ and
prioritised recommendations Ξ.
"""
from __future__ import annotations

from fastapi import APIRouter

from tco_engine.api.routes.tensor import build_tensor
from tco_engine.core.inference_engine import InferenceEngine
from tco_engine.schemas.inference import (
    ConflictOut, InferenceRequest, InferenceResponse, RecommendationOut, TrendOut,
)
from tco_engine.schemas.tensor import AggregateRequest

router = APIRouter()

_engine = InferenceEngine()


@router.post("/compute", response_model=InferenceResponse)
def compute_inference(req: InferenceRequest):
    T = build_tensor(AggregateRequest(entries=req.entries))
    k_now = req.k_now if req.k_now is not None else T.shape[3] - 1
    result = _engine.infer(T, k_now)

    return InferenceResponse(
        omega=result.omega,
        omega_score=result.omega_score,
        delta=[TrendOut(**vars(t)) for t in result.delta],
        rho=[ConflictOut(**vars(c)) for c in result.rho],
        xi=[RecommendationOut(**vars(x)) for x in result.xi],
    )
