# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
LLM-Judge for PIQ (Policy Injection Quality) scoring — H5 instrument.

Scores PolicyIntent structs against the PIQ rubric (protocols/piq_rubric.md).
5 dimensions × 0-2 points each → PIQ_score ∈ [0, 1].

Uses QAEvaluator-compatible Anthropic client (supports OpenRouter via
LLM_PROVIDER env var). Requires LLM_PROVIDER and OPENROUTER_API_KEY or
ANTHROPIC_API_KEY in environment.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

# ── PIQ rubric embedded for LLM-Judge ─────────────────────────────────────────

_RUBRIC_PROMPT = """
You are an expert evaluator scoring a policy injection in the TCO-L2 experiment.

CONTEXT:
A participant is supervising an AI software pipeline using the TCO Dashboard.
They observe inference outputs {Omega (system state), Delta (trend), Rho (conflict),
Xi (recommendations)} derived from the cognitive tensor T[d,i,j,k], and inject
a natural language policy. The PolicyProcessor extracted a PolicyIntent struct
from their text. You score the PolicyIntent struct quality on 5 dimensions.

SCORING SCALE per dimension: 0 (absent/wrong) | 1 (partial) | 2 (precise/correct)

DIMENSIONS:

D1 - Root Cause Targeting (RCT):
  2 = Policy directly addresses the actual fault in {Omega,Delta,Rho,Xi}, root cause named.
      For S3: addresses temporal debt pattern (not single commit).
      For S5: addresses the inter-agent conflict (not one agent).
  1 = Addresses a symptom or secondary effect, misses systemic root cause.
  0 = Unrelated to actual fault, no evidence of using inference outputs.

D2 - Agent Precision (AP):
  2 = target_agents correctly identifies responsible agent(s). For S5: both conflicting agents.
  1 = Partially correct: includes responsible agent plus irrelevant agents.
  0 = Empty, wrong agents, or agents not present in scenario.

D3 - Dimension Relevance (DR):
  2 = affected_dimensions matches primary degraded dimensions from scenario ground truth.
  1 = Degraded dimension present but mixed with irrelevant ones, not prominent.
  0 = Missing primary degraded dimension(s), or all 11 listed without selectivity.

D4 - Constraint Specificity (CS):
  2 = constraint is specific, actionable, governance-level (not vague, not microscopic code).
  1 = Vague ("improve security") OR microscopic ("change line 47"). Partially actionable.
  0 = Absent, empty, or contradicts the fault.

D5 - Systemic Scope (SS):
  2 = Policy accounts for cascade effects visible only in tensor (Δ trend, Ρ conflicts).
      S3: references progressive pattern or prevents future degradation.
      S5: includes coordination between conflicting agents.
  1 = Addresses immediate fault, ignores cascades. Would miss recurrence.
  0 = Policy worsens cascade risk.

SCENARIO GROUND TRUTH ANCHORS:
S1: fault=sql_injection+MD5, dim=v4(security), action=refactor, constraint=parameterize+SHA256
S2: fault=circular_dependency, dim=v2(arch)+v7(maint), action=refactor, constraint=break_cycle
S3: fault=gradual_debt_CC, dim=v8(tech_debt), action=refactor, constraint=CC<5+complexity_gate
S4: fault=missing_probes+resources, dim=v5(obs)+v9(perf), action=monitor, constraint=limits+probes
S5: fault=security_testability_conflict, dim=v4+v6, action=reprioritize, constraint=coordinate_agents
"""

_TOOL_SCHEMA = {
    "name": "score_piq",
    "description": "Score a PolicyIntent struct on 5 PIQ dimensions",
    "input_schema": {
        "type": "object",
        "properties": {
            "d1_root_cause_targeting": {
                "type": "integer", "enum": [0, 1, 2],
                "description": "D1: Root Cause Targeting score"
            },
            "d2_agent_precision": {
                "type": "integer", "enum": [0, 1, 2],
                "description": "D2: Agent Precision score"
            },
            "d3_dimension_relevance": {
                "type": "integer", "enum": [0, 1, 2],
                "description": "D3: Dimension Relevance score"
            },
            "d4_constraint_specificity": {
                "type": "integer", "enum": [0, 1, 2],
                "description": "D4: Constraint Specificity score"
            },
            "d5_systemic_scope": {
                "type": "integer", "enum": [0, 1, 2],
                "description": "D5: Systemic Scope score"
            },
            "rationale": {
                "type": "string",
                "description": "One sentence per dimension explaining the score"
            },
        },
        "required": [
            "d1_root_cause_targeting", "d2_agent_precision",
            "d3_dimension_relevance", "d4_constraint_specificity",
            "d5_systemic_scope", "rationale"
        ],
    },
}


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class PolicyIntent:
    """Extracted struct from participant's natural language policy injection."""
    target_agents: list[str]
    action_type: str
    affected_dimensions: list[str]
    constraint: str
    priority: str
    confidence: float = 1.0
    raw_text: str = ""


@dataclass
class PIQScores:
    """Raw dimension scores + derived PIQ from LLM-Judge."""
    session_id: str
    participant_id: str
    scenario_id: str
    task_id: str
    d1_root_cause_targeting: int
    d2_agent_precision: int
    d3_dimension_relevance: int
    d4_constraint_specificity: int
    d5_systemic_scope: int
    rationale: str
    policy_intent: dict
    degraded: bool = False      # True if PolicyProcessor confidence < 0.70

    @property
    def raw_score(self) -> int:
        return (self.d1_root_cause_targeting + self.d2_agent_precision
                + self.d3_dimension_relevance + self.d4_constraint_specificity
                + self.d5_systemic_scope)

    @property
    def piq_score(self) -> float:
        """Normalized PIQ ∈ [0, 1]. Max raw = 10."""
        return self.raw_score / 10.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["raw_score"] = self.raw_score
        d["piq_score"] = self.piq_score
        return d


# ── LLM-Judge ─────────────────────────────────────────────────────────────────

class PIQLLMJudge:
    """
    Scores PolicyIntent structs using an LLM as judge.
    Compatible with OpenRouter (LLM_PROVIDER=openrouter) and direct Anthropic.
    """

    _CONFIDENCE_THRESHOLD = 0.70

    def __init__(self, model: str | None = None) -> None:
        from anthropic import Anthropic
        provider = os.environ.get("LLM_PROVIDER", "anthropic")
        if provider == "openrouter":
            self._client = Anthropic(
                api_key=os.environ["OPENROUTER_API_KEY"],
                base_url=os.environ.get("OPENROUTER_BASE_URL",
                                        "https://openrouter.ai/api/v1"),
            )
            self._model = model or os.environ.get("LLM_MODEL",
                                                   "anthropic/claude-sonnet-4-6")
        else:
            self._client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            self._model = model or os.environ.get("LLM_MODEL", "claude-sonnet-4-6")

    def score(
        self,
        session_id: str,
        participant_id: str,
        scenario_id: str,
        task_id: str,
        policy_intent: PolicyIntent,
        inference_outputs: Optional[dict] = None,
    ) -> PIQScores:
        """
        Score one PolicyIntent struct. Returns PIQScores with all dimensions.
        If policy_intent.confidence < threshold, marks as degraded and scores anyway.
        """
        degraded = policy_intent.confidence < self._CONFIDENCE_THRESHOLD

        user_content = self._build_user_message(
            scenario_id, policy_intent, inference_outputs
        )

        response = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=_RUBRIC_PROMPT,
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "score_piq"},
            messages=[{"role": "user", "content": user_content}],
        )

        tool_input = next(
            b.input for b in response.content if b.type == "tool_use"
        )

        return PIQScores(
            session_id=session_id,
            participant_id=participant_id,
            scenario_id=scenario_id,
            task_id=task_id,
            d1_root_cause_targeting=tool_input["d1_root_cause_targeting"],
            d2_agent_precision=tool_input["d2_agent_precision"],
            d3_dimension_relevance=tool_input["d3_dimension_relevance"],
            d4_constraint_specificity=tool_input["d4_constraint_specificity"],
            d5_systemic_scope=tool_input["d5_systemic_scope"],
            rationale=tool_input["rationale"],
            policy_intent=asdict(policy_intent),
            degraded=degraded,
        )

    @staticmethod
    def _build_user_message(
        scenario_id: str,
        policy_intent: PolicyIntent,
        inference_outputs: Optional[dict],
    ) -> str:
        lines = [f"SCENARIO: {scenario_id}"]
        if inference_outputs:
            lines.append(f"INFERENCE OUTPUTS: {json.dumps(inference_outputs, indent=2)}")
        lines.append("POLICY INTENT STRUCT:")
        lines.append(f"  target_agents:       {policy_intent.target_agents}")
        lines.append(f"  action_type:         {policy_intent.action_type}")
        lines.append(f"  affected_dimensions: {policy_intent.affected_dimensions}")
        lines.append(f"  constraint:          {policy_intent.constraint}")
        lines.append(f"  priority:            {policy_intent.priority}")
        lines.append(f"  confidence:          {policy_intent.confidence:.2f}")
        if policy_intent.raw_text:
            lines.append(f"ORIGINAL TEXT: {policy_intent.raw_text}")
        lines.append("\nScore the PolicyIntent on D1–D5.")
        return "\n".join(lines)


# ── Batch scorer ──────────────────────────────────────────────────────────────

def score_session_policies(
    session_id: str,
    participant_id: str,
    policies: list[dict],
    judge: Optional[PIQLLMJudge] = None,
) -> list[PIQScores]:
    """
    Score all policy injections from one session.
    Each entry in `policies` must have keys:
      scenario_id, task_id, policy_intent (dict), inference_outputs (optional).
    """
    judge = judge or PIQLLMJudge()
    results = []
    for p in policies:
        intent = PolicyIntent(**p["policy_intent"])
        scores = judge.score(
            session_id=session_id,
            participant_id=participant_id,
            scenario_id=p["scenario_id"],
            task_id=p["task_id"],
            policy_intent=intent,
            inference_outputs=p.get("inference_outputs"),
        )
        results.append(scores)
    return results
