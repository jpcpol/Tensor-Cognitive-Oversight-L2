# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""Schemas for tensor aggregation endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field

from tco_engine.schemas.vector import EvaluationVector


class TensorEntryInput(BaseModel):
    """One vectorized artifact placed at a tensor coordinate (i, j, k)."""
    vector: EvaluationVector
    stage: str = Field(description="design | build | test | deploy")
    agent_idx: int = Field(ge=0)
    time_idx: int = Field(ge=0)


class AggregateRequest(BaseModel):
    entries: list[TensorEntryInput]


class TensorSnapshotResponse(BaseModel):
    shape: list[int]          # [n_dims, n_stages, n_agents, n_time]
    dim_names: list[str]
    stages: list[str]
    snapshot: list            # T[:, :, :, -1] as nested lists (NaN → null)
