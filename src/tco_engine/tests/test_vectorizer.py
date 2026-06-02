# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Tests for Vectorizer φ: Artifact → V ∈ [0,1]¹¹

All LLM calls, static analysis runners, and Redis cache are mocked
so tests run without API keys, installed tools, or network access.
"""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from tco_engine.core.vectorizer import Artifact, HistoricalBaseline, Vectorizer
from tco_engine.schemas.vector import EvaluationVector
from tco_engine.static_analysis.bandit_runner import SecurityMetrics
from tco_engine.static_analysis.radon_runner import RadonMetrics


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _radon(cc=0.2, halstead=0.3, debt=0.2, log=0.8, maintainability=0.75, testability=0.8, fc=1.0):
    return RadonMetrics(
        cyclomatic_complexity=cc,
        halstead_volume=halstead,
        debt_ratio=debt,
        log_coverage=log,
        maintainability=maintainability,
        testability=testability,
        functional_correctness=fc,
    )


def _bandit(severity=0.1):
    return SecurityMetrics(weighted_severity=severity, issue_count=0,
                           high_count=0, medium_count=0, low_count=0)


def _llm_metrics(**overrides):
    from tco_engine.core.qa_evaluator import EvaluationMetrics
    defaults = dict(
        functional_correctness=0.85, architectural_alignment=0.80,
        scalability_projection=0.75, performance_score=0.80,
        semantic_maintainability=0.82, semantic_testability=0.78,
        semantic_security=0.88, semantic_debt_assessment=0.83,
        reasoning="mock", confidence_self_assessment=0.9,
    )
    return EvaluationMetrics(**(defaults | overrides))


def _make_vectorizer(radon_m=None, bandit_m=None, llm_m=None, cache_value=None):
    """Return a Vectorizer with all dependencies mocked."""
    with patch("tco_engine.core.vectorizer.RadonRunner") as MockRadon, \
         patch("tco_engine.core.vectorizer.BanditRunner") as MockBandit, \
         patch("tco_engine.core.vectorizer.QAEvaluator") as MockQA, \
         patch("tco_engine.core.vectorizer.ArtifactCache") as MockCache:

        MockRadon.return_value.analyze.return_value = radon_m or _radon()
        MockBandit.return_value.scan.return_value = bandit_m or _bandit()
        MockQA.return_value.evaluate.return_value = llm_m or _llm_metrics()

        cache = MagicMock()
        cache.get.return_value = cache_value
        MockCache.return_value = cache

        v = Vectorizer()
    return v


def _artifact(code="x = 1") -> Artifact:
    return Artifact(artifact_id="test", agent_id="agent_0",
                    stage="build", cycle_k=0, code=code)


# ── All 11 dimensions present ─────────────────────────────────────────────────

def test_all_11_dimensions_present():
    v = _make_vectorizer()
    result = v.vectorize(_artifact())
    assert isinstance(result, EvaluationVector)
    fields = [
        "functional_correctness", "architectural_alignment", "scalability_projection",
        "security_risk", "observability_coverage", "testability", "maintainability",
        "technical_debt", "performance", "confidence", "anomaly_score",
    ]
    for f in fields:
        assert hasattr(result, f), f"Missing dimension: {f}"
        val = getattr(result, f)
        assert 0.0 <= val <= 1.0, f"{f}={val} outside [0,1]"


# ── Values are clipped ────────────────────────────────────────────────────────

def test_values_clipped_to_0_1():
    # Radon returns values that could produce > 1 after inversion
    v = _make_vectorizer(radon_m=_radon(cc=0.0, halstead=0.0, debt=0.0, log=1.0))
    result = v.vectorize(_artifact())
    for val in result.to_list():
        assert 0.0 <= val <= 1.0, f"value {val} outside [0, 1]"


# ── Security risk is inverted ─────────────────────────────────────────────────

def test_security_risk_inverted_from_bandit():
    # high bandit severity → low v4 (security_risk)
    v = _make_vectorizer(bandit_m=_bandit(severity=0.9))
    result = v.vectorize(_artifact())
    assert result.security_risk == pytest.approx(0.1, abs=1e-6)


def test_security_risk_zero_severity_gives_max():
    v = _make_vectorizer(bandit_m=_bandit(severity=0.0))
    result = v.vectorize(_artifact())
    assert result.security_risk == pytest.approx(1.0, abs=1e-6)


# ── Technical debt is inverted ────────────────────────────────────────────────

def test_technical_debt_inverted_from_radon():
    # high debt_ratio → low v8 (technical_debt)
    v = _make_vectorizer(radon_m=_radon(debt=0.8))
    result = v.vectorize(_artifact())
    assert result.technical_debt == pytest.approx(0.2, abs=1e-6)


# ── Cache ─────────────────────────────────────────────────────────────────────

def test_cache_hit_skips_llm():
    cached_vector = EvaluationVector(**{d: 0.7 for d in [
        "functional_correctness", "architectural_alignment", "scalability_projection",
        "security_risk", "observability_coverage", "testability", "maintainability",
        "technical_debt", "performance", "confidence", "anomaly_score",
    ]})

    with patch("tco_engine.core.vectorizer.RadonRunner") as MockRadon, \
         patch("tco_engine.core.vectorizer.BanditRunner") as MockBandit, \
         patch("tco_engine.core.vectorizer.QAEvaluator") as MockQA, \
         patch("tco_engine.core.vectorizer.ArtifactCache") as MockCache:

        MockRadon.return_value.analyze.return_value = _radon()
        MockBandit.return_value.scan.return_value = _bandit()
        MockQA.return_value.evaluate.return_value = _llm_metrics()

        cache = MagicMock()
        cache.get.return_value = cached_vector.model_dump()
        MockCache.return_value = cache

        v = Vectorizer()
        result = v.vectorize(_artifact())

        MockQA.return_value.evaluate.assert_not_called()
    assert all(val == pytest.approx(0.7, abs=1e-6) for val in result.to_list())


def test_cache_miss_calls_llm():
    with patch("tco_engine.core.vectorizer.RadonRunner") as MockRadon, \
         patch("tco_engine.core.vectorizer.BanditRunner") as MockBandit, \
         patch("tco_engine.core.vectorizer.QAEvaluator") as MockQA, \
         patch("tco_engine.core.vectorizer.ArtifactCache") as MockCache:

        MockRadon.return_value.analyze.return_value = _radon()
        MockBandit.return_value.scan.return_value = _bandit()
        MockQA.return_value.evaluate.return_value = _llm_metrics()

        cache = MagicMock()
        cache.get.return_value = None  # cache miss
        MockCache.return_value = cache

        v = Vectorizer()
        v.vectorize(_artifact())

        MockQA.return_value.evaluate.assert_called_once()


# ── Anomaly score ─────────────────────────────────────────────────────────────

def test_anomaly_zero_without_baseline():
    # No baseline → anomaly = 0.0 → anomaly_score = 1 - 0 = 1.0
    v = _make_vectorizer()
    result = v.vectorize(_artifact(), baseline=None)
    assert result.anomaly_score == pytest.approx(1.0, abs=1e-6)


def test_anomaly_nonzero_with_baseline():
    v = _make_vectorizer(radon_m=_radon(cc=0.9, halstead=0.9, debt=0.9))
    baseline = HistoricalBaseline(
        mean=np.array([0.2, 0.2, 0.2, 0.2, 0.2]),
        std=np.array([0.05, 0.05, 0.05, 0.05, 0.05]),
    )
    result = v.vectorize(_artifact(), baseline=baseline)
    assert result.anomaly_score < 1.0


# ── Confidence (v10) ──────────────────────────────────────────────────────────

def test_confidence_decreases_with_disagreement():
    # Perfect agreement: static and LLM agree on all overlap dims → high confidence
    # High disagreement: static says good, LLM says bad → lower confidence
    v_agree = _make_vectorizer(
        radon_m=_radon(cc=0.1, halstead=0.1, debt=0.1, maintainability=0.9, testability=0.9, fc=1.0),
        llm_m=_llm_metrics(functional_correctness=0.9, semantic_maintainability=0.9, semantic_testability=0.9),
    )
    v_disagree = _make_vectorizer(
        radon_m=_radon(cc=0.9, halstead=0.9, debt=0.9, maintainability=0.1, testability=0.1, fc=0.2),
        llm_m=_llm_metrics(functional_correctness=0.9, semantic_maintainability=0.9, semantic_testability=0.9),
    )
    r_agree = v_agree.vectorize(_artifact())
    r_disagree = v_disagree.vectorize(_artifact())
    assert r_agree.confidence > r_disagree.confidence
