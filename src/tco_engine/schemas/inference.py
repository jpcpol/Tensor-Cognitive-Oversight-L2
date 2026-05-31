# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""Schemas for the inference endpoint I: T → {Ω, Δ, Ρ, Ξ}."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from tco_engine.schemas.tensor import TensorEntryInput


class InferenceRequest(BaseModel):
    entries: list[TensorEntryInput]
    k_now: int | None = None   # default: latest time index


class TrendOut(BaseModel):
    dimension: str
    stage: str
    agent: str
    slope: float
    direction: Literal["improving", "degrading"]


class ConflictOut(BaseModel):
    agents: list[str]
    stage: str
    dimension: str
    delta_score: float
    severity: Literal["high", "medium"]


class RecommendationOut(BaseModel):
    action: str
    target: str
    estimated_impact: float
    urgency: Literal["high", "medium", "low"]


class InferenceResponse(BaseModel):
    omega: Literal["stable", "warning", "critical"]
    omega_score: float
    delta: list[TrendOut]
    rho: list[ConflictOut]
    xi: list[RecommendationOut]
