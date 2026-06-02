# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""Tests for TensorAggregator f: {V} → T ∈ ℝ^(n×s×a×t)"""
import numpy as np
import pytest

from tco_engine.core.aggregator import (
    N_DIMS, STAGE_INDEX, STAGES, TensorAggregator, VectorEntry,
)
from tco_engine.schemas.vector import EvaluationVector

_DIMS = [
    "functional_correctness", "architectural_alignment", "scalability_projection",
    "security_risk", "observability_coverage", "testability", "maintainability",
    "technical_debt", "performance", "confidence", "anomaly_score",
]


def make_vector(val: float = 0.8, **overrides) -> EvaluationVector:
    return EvaluationVector(**({d: val for d in _DIMS} | overrides))


def entry(stage="build", agent_idx=0, time_idx=0, val=0.8, **overrides) -> VectorEntry:
    return VectorEntry(
        vector=make_vector(val, **overrides),
        stage_idx=STAGE_INDEX[stage],
        agent_idx=agent_idx,
        time_idx=time_idx,
    )


@pytest.fixture
def agg():
    return TensorAggregator()


# ── Shape ─────────────────────────────────────────────────────────────────────

def test_empty_returns_zeros(agg):
    T = agg.aggregate([])
    assert T.shape == (N_DIMS, len(STAGES), 1, 1)
    assert np.all(T == 0.0)


def test_single_entry_shape(agg):
    T = agg.aggregate([entry()])
    assert T.shape == (N_DIMS, len(STAGES), 1, 1)


def test_two_agents_shape(agg):
    T = agg.aggregate([entry(agent_idx=0), entry(agent_idx=1)])
    assert T.shape == (N_DIMS, len(STAGES), 2, 1)


def test_two_cycles_shape(agg):
    T = agg.aggregate([entry(time_idx=0), entry(time_idx=1)])
    assert T.shape == (N_DIMS, len(STAGES), 1, 2)


def test_multi_stage_shape(agg):
    T = agg.aggregate([entry(stage="design"), entry(stage="deploy")])
    assert T.shape[1] == len(STAGES)


# ── Values ────────────────────────────────────────────────────────────────────

def test_single_entry_values_correct(agg):
    T = agg.aggregate([entry(val=0.7)])
    build_idx = STAGE_INDEX["build"]
    assert np.allclose(T[:, build_idx, 0, 0], 0.7)


def test_unfilled_positions_are_nan(agg):
    # Only build stage filled — design/test/deploy should be NaN
    T = agg.aggregate([entry(stage="build")])
    build_idx = STAGE_INDEX["build"]
    for stage, idx in STAGE_INDEX.items():
        if stage != "build":
            assert np.all(np.isnan(T[:, idx, 0, 0])), (
                f"Stage {stage} should be NaN but got values"
            )


def test_same_position_averages(agg):
    # Two entries at same (stage, agent, time) → averaged
    e0 = entry(val=0.6)
    e1 = entry(val=0.4)
    T = agg.aggregate([e0, e1])
    build_idx = STAGE_INDEX["build"]
    assert np.allclose(T[:, build_idx, 0, 0], 0.5)


def test_different_agents_independent(agg):
    e0 = entry(agent_idx=0, security_risk=0.9)
    e1 = entry(agent_idx=1, security_risk=0.2)
    T = agg.aggregate([e0, e1])
    build_idx = STAGE_INDEX["build"]
    sec_idx = _DIMS.index("security_risk")
    assert T[sec_idx, build_idx, 0, 0] == pytest.approx(0.9, abs=1e-6)
    assert T[sec_idx, build_idx, 1, 0] == pytest.approx(0.2, abs=1e-6)


def test_different_cycles_independent(agg):
    e0 = entry(time_idx=0, technical_debt=0.8)
    e1 = entry(time_idx=1, technical_debt=0.5)
    T = agg.aggregate([e0, e1])
    build_idx = STAGE_INDEX["build"]
    td_idx = _DIMS.index("technical_debt")
    assert T[td_idx, build_idx, 0, 0] == pytest.approx(0.8, abs=1e-6)
    assert T[td_idx, build_idx, 0, 1] == pytest.approx(0.5, abs=1e-6)


# ── Slice ─────────────────────────────────────────────────────────────────────

def test_slice_by_dim(agg):
    T = agg.aggregate([entry()])
    sec_idx = _DIMS.index("security_risk")
    sliced = agg.slice(T, d=sec_idx)
    assert sliced.shape == (len(STAGES), 1, 1)


def test_slice_by_time(agg):
    T = agg.aggregate([entry(time_idx=0), entry(time_idx=1)])
    sliced = agg.slice(T, k=0)
    assert sliced.shape == (N_DIMS, len(STAGES), 1)


def test_slice_by_agent(agg):
    T = agg.aggregate([entry(agent_idx=0), entry(agent_idx=1)])
    sliced = agg.slice(T, j=0)
    assert sliced.shape == (N_DIMS, len(STAGES), 1)


def test_slice_none_means_all(agg):
    T = agg.aggregate([entry()])
    assert agg.slice(T).shape == T.shape


# ── Named operations ──────────────────────────────────────────────────────────

def test_current_snapshot_is_last_k(agg):
    T = agg.aggregate([entry(time_idx=0, val=0.8), entry(time_idx=1, val=0.5)])
    snap = agg.current_snapshot(T)
    assert snap.shape == (N_DIMS, len(STAGES), 1)
    build_idx = STAGE_INDEX["build"]
    assert np.allclose(snap[:, build_idx, 0], 0.5)


def test_dimension_trajectory(agg):
    T = agg.aggregate([entry(time_idx=0), entry(time_idx=1)])
    td_idx = _DIMS.index("technical_debt")
    traj = agg.dimension_trajectory(T, dim=td_idx)
    assert traj.shape == (len(STAGES), 1, 2)


def test_stage_profile(agg):
    T = agg.aggregate([entry(stage="build")])
    prof = agg.stage_profile(T, stage="build")
    assert prof.shape == (N_DIMS, 1)
    assert np.allclose(prof[:, 0], 0.8)


def test_stage_profile_unknown_defaults_to_design(agg):
    T = agg.aggregate([entry(stage="design")])
    prof = agg.stage_profile(T, stage="unknown_stage")
    assert prof.shape == (N_DIMS, 1)
