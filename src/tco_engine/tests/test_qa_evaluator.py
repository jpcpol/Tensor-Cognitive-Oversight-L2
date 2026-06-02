# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Tests for QAEvaluator — LLM-based semantic quality assessment.

All network calls are mocked. Tests cover:
- Happy-path JSON parsing (Anthropic + OpenRouter paths)
- Regex fallback for truncated JSON (DT-024 fix)
- Neutral fallback on any exception
- EvaluationMetrics property aliases
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from tco_engine.core.qa_evaluator import EvaluationMetrics, QAEvaluator, _fallback_metrics


# ── Helpers ───────────────────────────────────────────────────────────────────

_GOOD_PAYLOAD = {
    "functional_correctness": 0.85,
    "architectural_alignment": 0.80,
    "scalability_projection": 0.75,
    "performance_score": 0.80,
    "semantic_maintainability": 0.82,
    "semantic_testability": 0.78,
    "semantic_security": 0.88,
    "semantic_debt_assessment": 0.83,
    "reasoning": "Clean code, good practices.",
    "confidence_self_assessment": 0.90,
}


def _make_anthropic_evaluator():
    """QAEvaluator configured for Anthropic SDK (mocked).

    The SDK is imported lazily inside QAEvaluator.__init__, so we patch at the
    source module (anthropic.Anthropic) rather than at tco_engine.core.qa_evaluator.
    ev._client holds the MagicMock instance after the with-block exits.
    """
    with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test"}):
        with patch("anthropic.Anthropic"):
            ev = QAEvaluator()
    return ev


def _make_openrouter_evaluator():
    """QAEvaluator configured for OpenRouter via OpenAI SDK (mocked).

    openai is not a hard dependency of the venv (only used when LLM_PROVIDER=openrouter),
    so we inject a fake module into sys.modules before QAEvaluator.__init__ runs its
    lazy `from openai import OpenAI` import.
    """
    import sys
    fake_openai = MagicMock()
    env = {
        "LLM_PROVIDER": "openrouter",
        "OPENROUTER_API_KEY": "test",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
    }
    with patch.dict(sys.modules, {"openai": fake_openai}):
        with patch.dict(os.environ, env):
            ev = QAEvaluator()
    # ev._client is fake_openai.OpenAI.return_value (MagicMock) — lives beyond the with-block
    return ev


# ── Fallback ──────────────────────────────────────────────────────────────────

def test_fallback_metrics_are_neutral():
    m = _fallback_metrics()
    assert m.functional_correctness == pytest.approx(0.5)
    assert m.confidence_self_assessment == pytest.approx(0.0)
    assert "fallback" in m.reasoning.lower()


def test_fallback_on_llm_exception():
    ev = _make_anthropic_evaluator()
    ev._client.messages.create.side_effect = RuntimeError("connection refused")
    result = ev.evaluate("x = 1")
    assert result.confidence_self_assessment == pytest.approx(0.0)
    assert result.functional_correctness == pytest.approx(0.5)


# ── Anthropic path ────────────────────────────────────────────────────────────

def test_anthropic_parses_tool_use_block():
    ev = _make_anthropic_evaluator()
    block = MagicMock()
    block.type = "tool_use"
    block.name = "evaluate_artifact"
    block.input = _GOOD_PAYLOAD
    ev._client.messages.create.return_value.content = [block]

    result = ev.evaluate("def foo(): pass")
    assert isinstance(result, EvaluationMetrics)
    assert result.functional_correctness == pytest.approx(0.85)
    assert result.architectural_alignment == pytest.approx(0.80)


def test_anthropic_fallback_when_no_tool_use_block():
    ev = _make_anthropic_evaluator()
    non_tool_block = MagicMock()
    non_tool_block.type = "text"
    ev._client.messages.create.return_value.content = [non_tool_block]

    result = ev.evaluate("x = 1")
    # ValueError from "No tool_use block" → caught → fallback
    assert result.confidence_self_assessment == pytest.approx(0.0)


# ── OpenRouter path ───────────────────────────────────────────────────────────

def _openai_response(arguments: str):
    tc = MagicMock()
    tc.function.name = "evaluate_artifact"
    tc.function.arguments = arguments
    msg = MagicMock()
    msg.tool_calls = [tc]
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_openrouter_parses_valid_json():
    ev = _make_openrouter_evaluator()
    ev._client.chat.completions.create.return_value = _openai_response(
        json.dumps(_GOOD_PAYLOAD)
    )
    result = ev.evaluate("def foo(): pass")
    assert result.functional_correctness == pytest.approx(0.85)
    assert result.confidence_self_assessment == pytest.approx(0.90)


def test_openrouter_regex_fallback_on_truncated_json():
    """
    DT-024: when JSON is truncated mid-reasoning field, regex extraction
    should recover all numeric fields and still return valid EvaluationMetrics.
    """
    truncated = (
        '{"functional_correctness": 0.85, "architectural_alignment": 0.80, '
        '"scalability_projection": 0.75, "performance_score": 0.80, '
        '"semantic_maintainability": 0.82, "semantic_testability": 0.78, '
        '"semantic_security": 0.88, "semantic_debt_assessment": 0.83, '
        '"confidence_self_assessment": 0.90, "reasoning": "Clean code — trun'  # truncated!
    )
    ev = _make_openrouter_evaluator()
    ev._client.chat.completions.create.return_value = _openai_response(truncated)
    result = ev.evaluate("x = 1")
    # Should not fall back to neutral; should parse the numeric fields
    assert result.functional_correctness == pytest.approx(0.85, abs=1e-3)
    assert result.semantic_security == pytest.approx(0.88, abs=1e-3)


def test_openrouter_full_fallback_on_unparseable():
    """When JSON is completely malformed and regex finds < 8 fields → fallback."""
    ev = _make_openrouter_evaluator()
    ev._client.chat.completions.create.return_value = _openai_response("not json at all")
    result = ev.evaluate("x = 1")
    assert result.confidence_self_assessment == pytest.approx(0.0)


def test_openrouter_fallback_when_no_tool_call():
    ev = _make_openrouter_evaluator()
    msg = MagicMock()
    msg.tool_calls = []
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    ev._client.chat.completions.create.return_value = resp
    result = ev.evaluate("x = 1")
    assert result.confidence_self_assessment == pytest.approx(0.0)


# ── EvaluationMetrics property aliases ───────────────────────────────────────

def test_evaluation_metrics_property_aliases():
    m = EvaluationMetrics(**_GOOD_PAYLOAD)
    assert m.test_pass_rate == m.functional_correctness
    assert m.pattern_compliance == m.architectural_alignment
    assert m.scalability_score == m.scalability_projection
    assert m.maintainability == m.semantic_maintainability
    assert m.testability == m.semantic_testability


# ── Variance test (DT-024) ────────────────────────────────────────────────────

def test_run_variance_test_structure():
    """run_variance_test returns the expected keys with correct types."""
    ev = _make_anthropic_evaluator()
    block = MagicMock()
    block.type = "tool_use"
    block.name = "evaluate_artifact"
    block.input = _GOOD_PAYLOAD
    ev._client.messages.create.return_value.content = [block]

    result = ev.run_variance_test("x = 1", n=3)
    assert "sigma_per_dim" in result
    assert "max_se_sigma" in result
    assert "passed" in result
    assert result["n_runs"] == 3
    # All 3 runs return identical values → sigma = 0 → passed
    assert result["passed"] is True
    assert result["max_se_sigma"] == pytest.approx(0.0)
