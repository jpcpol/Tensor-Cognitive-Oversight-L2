# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Tests for InferenceEngine I: T → {Ω, Δ, Ρ, Ξ}

Critical tests (marked with S3/S5) directly validate the CAL Benchmark v1.0
predictions: S3 requires temporal trajectory detection (Δ), S5 requires
inter-agent conflict detection (Ρ). These are the CCI=4 and CCI=3 scenarios
that form the basis of H_OBS.
"""
import numpy as np
import pytest

from tco_engine.core.aggregator import N_DIMS, STAGES, TensorAggregator, VectorEntry
from tco_engine.core.inference_engine import (
    InferenceEngine,
    _CONFLICT_HIGH,
    _CONFLICT_THRESHOLD,
    _THRESHOLD_STABLE,
    _THRESHOLD_WARNING,
    _TREND_MIN_SLOPE,
)
from tco_engine.schemas.vector import EvaluationVector

_DIMS = [
    "functional_correctness", "architectural_alignment", "scalability_projection",
    "security_risk", "observability_coverage", "testability", "maintainability",
    "technical_debt", "performance", "confidence", "anomaly_score",
]


def make_vector(**overrides) -> EvaluationVector:
    return EvaluationVector(**({d: 0.8 for d in _DIMS} | overrides))


def build_tensor(*entries) -> np.ndarray:
    return TensorAggregator().aggregate(list(entries))


def entry(agent_idx=0, time_idx=0, stage_idx=1, **dims) -> VectorEntry:
    return VectorEntry(vector=make_vector(**dims), stage_idx=stage_idx,
                       agent_idx=agent_idx, time_idx=time_idx)


@pytest.fixture
def engine():
    return InferenceEngine()


# ── Omega ─────────────────────────────────────────────────────────────────────

def test_omega_stable(engine):
    T = build_tensor(entry())
    r = engine.infer(T, k_now=0)
    assert r.omega == "stable"
    assert r.omega_score >= _THRESHOLD_STABLE


def test_omega_warning(engine):
    T = build_tensor(entry(**{d: 0.60 for d in _DIMS}))
    r = engine.infer(T, k_now=0)
    assert r.omega == "warning"
    assert _THRESHOLD_WARNING <= r.omega_score < _THRESHOLD_STABLE


def test_omega_critical(engine):
    T = build_tensor(entry(**{d: 0.30 for d in _DIMS}))
    r = engine.infer(T, k_now=0)
    assert r.omega == "critical"
    assert r.omega_score < _THRESHOLD_WARNING


def test_omega_at_stable_boundary(engine):
    T = build_tensor(entry(**{d: _THRESHOLD_STABLE for d in _DIMS}))
    assert engine.infer(T, k_now=0).omega == "stable"


def test_omega_just_below_warning_is_critical(engine):
    val = _THRESHOLD_WARNING - 0.01
    T = build_tensor(entry(**{d: val for d in _DIMS}))
    assert engine.infer(T, k_now=0).omega == "critical"


def test_omega_ignores_nan(engine):
    T = np.full((N_DIMS, len(STAGES), 1, 1), np.nan)
    T[:, 1, 0, 0] = 0.75
    r = engine.infer(T, k_now=0)
    assert r.omega == "stable"
    assert r.omega_score == pytest.approx(0.75, abs=1e-6)


# ── Delta ─────────────────────────────────────────────────────────────────────

def test_delta_empty_at_k0(engine):
    T = build_tensor(entry())
    assert engine.infer(T, k_now=0).delta == []


def test_delta_detects_degrading(engine):
    T = build_tensor(entry(time_idx=0, technical_debt=0.80),
                     entry(time_idx=1, technical_debt=0.60))
    td = [t for t in engine.infer(T, k_now=1).delta if t.dimension == "technical_debt"]
    assert len(td) == 1
    assert td[0].direction == "degrading"
    assert td[0].slope == pytest.approx(-0.20, abs=1e-6)


def test_delta_detects_improving(engine):
    T = build_tensor(entry(time_idx=0, security_risk=0.40),
                     entry(time_idx=1, security_risk=0.75))
    sec = [t for t in engine.infer(T, k_now=1).delta if t.dimension == "security_risk"]
    assert len(sec) == 1
    assert sec[0].direction == "improving"


def test_delta_ignores_small_slope(engine):
    # slope = 0.02, below _TREND_MIN_SLOPE (0.05) → not reported
    T = build_tensor(entry(time_idx=0, technical_debt=0.80),
                     entry(time_idx=1, technical_debt=0.78))
    td = [t for t in engine.infer(T, k_now=1).delta if t.dimension == "technical_debt"]
    assert len(td) == 0


def test_delta_sorted_by_abs_slope_descending(engine):
    T = build_tensor(entry(time_idx=0, technical_debt=0.80, security_risk=0.80),
                     entry(time_idx=1, technical_debt=0.60, security_risk=0.72))
    slopes = [abs(t.slope) for t in engine.infer(T, k_now=1).delta]
    assert slopes == sorted(slopes, reverse=True)


# ── S3 CRITICAL THEORY TEST — temporal_drift CCI=4 ───────────────────────────

def test_delta_s3_simulation(engine):
    """
    CAL Benchmark S3: technical_debt degrades -0.08/cycle over 4 cycles.
    v8: 0.68 → 0.60 → 0.52 → 0.44.

    H_OBS prediction: Δ detects the degrading trend at each k ≥ 1.
    At k=0, no previous cycle exists so no trend. At k=1..3 the slope
    is ≈ -0.08 per cycle, above _TREND_MIN_SLOPE.

    CCI=4: all four time indices are required to observe this pattern.
    Raw review of any single artifact shows values in normal range.
    """
    values = [0.68, 0.60, 0.52, 0.44]
    entries = [entry(time_idx=k, technical_debt=v) for k, v in enumerate(values)]
    T = TensorAggregator().aggregate(entries)

    # k=0 → no Δ
    td_k0 = [t for t in engine.infer(T, k_now=0).delta if t.dimension == "technical_debt"]
    assert td_k0 == [], "No Δ at k=0 — no previous cycle to compare"

    # k=1,2,3 → degrading Δ ≈ -0.08 detected
    for k in range(1, 4):
        r = engine.infer(T, k_now=k)
        td = [t for t in r.delta if t.dimension == "technical_debt"]
        assert len(td) == 1, f"Δ must detect technical_debt at k={k} (S3 CCI=4)"
        assert td[0].direction == "degrading", f"Expected degrading at k={k}"
        assert abs(td[0].slope) == pytest.approx(0.08, abs=1e-6), (
            f"S3 slope should be 0.08 at k={k}, got {td[0].slope:.4f}"
        )


# ── Rho ───────────────────────────────────────────────────────────────────────

def test_rho_empty_single_agent(engine):
    T = build_tensor(entry())
    assert engine.infer(T, k_now=0).rho == []


def test_rho_no_conflict_below_threshold(engine):
    # |0.8 - 0.6| = 0.2 < _CONFLICT_THRESHOLD (0.30)
    T = build_tensor(entry(agent_idx=0, security_risk=0.80),
                     entry(agent_idx=1, security_risk=0.60))
    assert engine.infer(T, k_now=0).rho == []


def test_rho_detects_medium_conflict(engine):
    # |0.80 - 0.45| = 0.35 → medium
    T = build_tensor(entry(agent_idx=0, security_risk=0.80),
                     entry(agent_idx=1, security_risk=0.45))
    sec = [c for c in engine.infer(T, k_now=0).rho if c.dimension == "security_risk"]
    assert len(sec) == 1
    assert sec[0].severity == "medium"
    assert sec[0].delta_score == pytest.approx(0.35, abs=1e-6)


def test_rho_detects_high_conflict(engine):
    # |0.85 - 0.40| = 0.45 > _CONFLICT_HIGH (0.40)
    T = build_tensor(entry(agent_idx=0, security_risk=0.85),
                     entry(agent_idx=1, security_risk=0.40))
    sec = [c for c in engine.infer(T, k_now=0).rho if c.dimension == "security_risk"]
    assert len(sec) == 1
    assert sec[0].severity == "high"


def test_rho_sorted_by_delta_descending(engine):
    # security conflict (Δ=0.65) should rank before testability (Δ=0.35)
    T = build_tensor(entry(agent_idx=0, security_risk=0.85, testability=0.80),
                     entry(agent_idx=1, security_risk=0.20, testability=0.45))
    deltas = [c.delta_score for c in engine.infer(T, k_now=0).rho]
    assert deltas == sorted(deltas, reverse=True)


# ── S5 CRITICAL THEORY TEST — inter_agent_conflict CCI=3 ─────────────────────

def test_rho_s5_simulation(engine):
    """
    CAL Benchmark S5: security_agent vs code_agent conflict.
    security_risk:  j=0 (security_agent) = 0.85, j=1 (code_agent) = 0.20 → Δ=0.65 HIGH
    testability:    j=0 (security_agent) = 0.25, j=1 (code_agent) = 0.80 → Δ=0.55 HIGH

    H_OBS prediction: Ρ detects both conflicts. Neither is detectable
    from inspecting either artifact in isolation — the fault IS the disagreement.
    CCI=3: requires d=[security_risk, testability] + j₁ + j₂.
    """
    e0 = entry(agent_idx=0, security_risk=0.85, testability=0.25)  # security_agent
    e1 = entry(agent_idx=1, security_risk=0.20, testability=0.80)  # code_agent
    T = build_tensor(e0, e1)
    result = engine.infer(T, k_now=0)

    dims_in_conflict = {c.dimension for c in result.rho}

    assert "security_risk" in dims_in_conflict, (
        "S5: security_risk conflict (Δ=0.65) not detected — Ρ failed on CCI=3 scenario"
    )
    assert "testability" in dims_in_conflict, (
        "S5: testability conflict (Δ=0.55) not detected — Ρ failed on CCI=3 scenario"
    )

    sec = next(c for c in result.rho if c.dimension == "security_risk")
    assert sec.delta_score == pytest.approx(0.65, abs=1e-6)
    assert sec.severity == "high"

    tst = next(c for c in result.rho if c.dimension == "testability")
    assert tst.delta_score == pytest.approx(0.55, abs=1e-6)
    assert tst.severity == "high"


# ── Xi (recommendations) ──────────────────────────────────────────────────────

def test_xi_includes_degrading_trends(engine):
    T = build_tensor(entry(time_idx=0, security_risk=0.80),
                     entry(time_idx=1, security_risk=0.50))
    xi = engine.infer(T, k_now=1).xi
    assert any("security_risk" in r.action for r in xi)


def test_xi_includes_rho_conflicts(engine):
    T = build_tensor(entry(agent_idx=0, security_risk=0.85),
                     entry(agent_idx=1, security_risk=0.20))
    xi = engine.infer(T, k_now=0).xi
    assert any("security_risk" in r.action for r in xi)


def test_xi_sorted_by_impact_descending(engine):
    T = build_tensor(entry(agent_idx=0, security_risk=0.85, technical_debt=0.80),
                     entry(agent_idx=1, security_risk=0.20, technical_debt=0.60))
    impacts = [r.estimated_impact for r in engine.infer(T, k_now=0).xi]
    assert impacts == sorted(impacts, reverse=True)


def test_xi_critical_fallback(engine):
    # critical omega, single cycle (no Δ), single agent (no Ρ) → fallback rec
    T = build_tensor(entry(**{d: 0.30 for d in _DIMS}))
    r = engine.infer(T, k_now=0)
    assert r.omega == "critical"
    assert len(r.xi) >= 1
    assert r.xi[0].urgency == "high"


def test_xi_trend_urgency_high_for_large_slope(engine):
    # slope = 0.20 > 0.15 → urgency=high
    T = build_tensor(entry(time_idx=0, security_risk=0.80),
                     entry(time_idx=1, security_risk=0.60))
    sec_recs = [r for r in engine.infer(T, k_now=1).xi if "security_risk" in r.action]
    assert len(sec_recs) == 1
    assert sec_recs[0].urgency == "high"
