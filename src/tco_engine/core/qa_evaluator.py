# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
QA LLM evaluation layer — v1 (functional_correctness), v2 (architectural_alignment),
v3 (scalability_projection), v9 (performance) + semantic proxies for consensus.

All scores are in [0,1] where 1 = best quality, including for dimensions that are
"inverted" in the final vector (v4, v8 are handled by static analysis, not here).
"""
import json
import logging
import os
from typing import Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ArtifactType = Literal["python_code", "yaml_config", "architecture_doc", "ci_cd_config", "generic"]

_SYSTEM_PROMPT = """\
You are a senior software quality analyst evaluating AI-generated software artifacts.
Your task is to assess the quality of the provided artifact across eight semantic dimensions.
Return ONLY valid JSON matching the exact schema described — no prose, no markdown.

DIMENSION DEFINITIONS:
- functional_correctness [0,1]: Does the logic correctly implement what the artifact is
  supposed to do? 1.0 = correct and complete, 0.0 = fundamentally broken or wrong.
- architectural_alignment [0,1]: Does the artifact follow sound architectural patterns
  (separation of concerns, no circular dependencies, proper layering)?
  1.0 = exemplary design, 0.0 = severe architectural violations.
- scalability_projection [0,1]: How well will this artifact perform under 10x load?
  1.0 = inherently scalable (stateless, async-ready, no N+1 issues),
  0.0 = will fail under modest load increase.
- performance_score [0,1]: Are there obvious performance problems (blocking I/O in hot
  paths, inefficient data structures, missing caching)?
  1.0 = performant, 0.0 = severe performance issues.
- semantic_maintainability [0,1]: How easy is it for another developer to understand,
  modify, and extend this artifact? Consider naming, structure, and complexity.
  1.0 = clean and self-documenting, 0.0 = opaque and fragile.
- semantic_testability [0,1]: How easy is this artifact to unit-test in isolation?
  Consider coupling, side effects, and dependency injection.
  1.0 = highly testable (pure functions, injected deps), 0.0 = hard to test.
- semantic_security [0,1]: How secure is the artifact against known vulnerability
  patterns (injection, broken auth, insecure deserialization, secrets in code)?
  1.0 = no detectable security issues, 0.0 = critical vulnerabilities present.
  Score what is visible; do not penalize for unknown runtime context.
- semantic_debt_assessment [0,1]: How much accumulated technical debt does this artifact
  represent? Consider: workarounds, TODO comments, duplicated logic, missing abstractions,
  known-bad patterns left in place. 1.0 = clean with no visible debt,
  0.0 = severe accumulated shortcuts that will compound.

IMPORTANT: Score what is present, not what is absent. A YAML config cannot be scored
on Python testability — use 0.5 as a neutral value for dimensions not applicable to
the artifact type. Justify each score briefly in the reasoning field.
"""

_FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": (
            "Artifact type: python_code\n\n"
            "```python\n"
            "import logging\nfrom sqlalchemy.orm import Session\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "def get_user(db: Session, user_id: int):\n"
            "    logger.info('Fetching user %s', user_id)\n"
            "    user = db.query(User).filter(User.id == user_id).first()\n"
            "    if not user:\n"
            "        raise HTTPException(status_code=404, detail='User not found')\n"
            "    return user\n"
            "```"
        ),
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "functional_correctness": 0.85,
            "architectural_alignment": 0.80,
            "scalability_projection": 0.75,
            "performance_score": 0.80,
            "semantic_maintainability": 0.82,
            "semantic_testability": 0.78,
            "semantic_security": 0.88,
            "semantic_debt_assessment": 0.83,
            "reasoning": (
                "Clean repository pattern with proper type hints and logging. "
                "Missing input validation (user_id type guard) and the db dependency "
                "is injected which aids testability. Parameterized query via ORM is "
                "safe from injection. No obvious debt."
            ),
            "confidence_self_assessment": 0.88,
        }),
    },
    {
        "role": "user",
        "content": (
            "Artifact type: python_code\n\n"
            "```python\n"
            "def get_user(db, user_id):\n"
            "    query = f'SELECT * FROM users WHERE id = {user_id}'\n"
            "    result = db.execute(query)\n"
            "    return result.fetchone()\n"
            "```"
        ),
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "functional_correctness": 0.45,
            "architectural_alignment": 0.20,
            "scalability_projection": 0.40,
            "performance_score": 0.50,
            "semantic_maintainability": 0.30,
            "semantic_testability": 0.35,
            "semantic_security": 0.05,
            "semantic_debt_assessment": 0.20,
            "reasoning": (
                "Critical SQL injection via f-string interpolation of user_id. "
                "No type hints, no logging, raw db reference instead of ORM. "
                "Returns raw tuple instead of domain object. Architecture bypasses "
                "the ORM layer entirely. Security score near zero: direct string "
                "interpolation into SQL is a textbook injection vector."
            ),
            "confidence_self_assessment": 0.95,
        }),
    },
    {
        "role": "user",
        "content": (
            "Artifact type: architecture_doc\n\n"
            "```yaml\n"
            "services:\n"
            "  order-service:\n"
            "    depends_on: [payment-service]\n"
            "  payment-service:\n"
            "    depends_on: [order-service]\n"
            "```"
        ),
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "functional_correctness": 0.50,
            "architectural_alignment": 0.15,
            "scalability_projection": 0.30,
            "performance_score": 0.50,
            "semantic_maintainability": 0.20,
            "semantic_testability": 0.50,
            "semantic_security": 0.70,
            "semantic_debt_assessment": 0.15,
            "reasoning": (
                "Explicit circular dependency between order-service and payment-service. "
                "This will cause initialization deadlock and prevents independent deployment. "
                "The circular reference makes the system impossible to scale independently "
                "and very difficult to maintain. Testability is neutral (N/A for YAML). "
                "Security: no obvious credentials or injection. Debt: the circular dep "
                "itself is severe accumulated structural debt."
            ),
            "confidence_self_assessment": 0.92,
        }),
    },
]

_OUTPUT_SCHEMA = {
    "name": "evaluate_artifact",
    "description": "Return quality scores for the artifact across eight semantic dimensions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "functional_correctness":     {"type": "number", "minimum": 0, "maximum": 1},
            "architectural_alignment":    {"type": "number", "minimum": 0, "maximum": 1},
            "scalability_projection":     {"type": "number", "minimum": 0, "maximum": 1},
            "performance_score":          {"type": "number", "minimum": 0, "maximum": 1},
            "semantic_maintainability":   {"type": "number", "minimum": 0, "maximum": 1},
            "semantic_testability":       {"type": "number", "minimum": 0, "maximum": 1},
            "semantic_security":          {"type": "number", "minimum": 0, "maximum": 1},
            "semantic_debt_assessment":   {"type": "number", "minimum": 0, "maximum": 1},
            "reasoning":                  {"type": "string"},
            "confidence_self_assessment": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": [
            "functional_correctness", "architectural_alignment", "scalability_projection",
            "performance_score", "semantic_maintainability", "semantic_testability",
            "semantic_security", "semantic_debt_assessment",
            "reasoning", "confidence_self_assessment",
        ],
    },
}


class EvaluationMetrics(BaseModel):
    """Structured output from LLM quality evaluation — maps to v1, v2, v3, v9 + calibration fields."""
    functional_correctness:   float = Field(ge=0.0, le=1.0)
    architectural_alignment:  float = Field(ge=0.0, le=1.0)
    scalability_projection:   float = Field(ge=0.0, le=1.0)
    performance_score:        float = Field(ge=0.0, le=1.0)
    semantic_maintainability: float = Field(ge=0.0, le=1.0)
    semantic_testability:     float = Field(ge=0.0, le=1.0)
    # Calibration fields — compared against bandit/radon in phi_calibration.py
    semantic_security:        float = Field(ge=0.0, le=1.0)
    semantic_debt_assessment: float = Field(ge=0.0, le=1.0)
    reasoning:                str
    confidence_self_assessment: float = Field(ge=0.0, le=1.0)

    @property
    def test_pass_rate(self) -> float:
        return self.functional_correctness

    @property
    def pattern_compliance(self) -> float:
        return self.architectural_alignment

    @property
    def scalability_score(self) -> float:
        return self.scalability_projection

    @property
    def maintainability(self) -> float:
        return self.semantic_maintainability

    @property
    def testability(self) -> float:
        return self.semantic_testability


def _fallback_metrics() -> EvaluationMetrics:
    """Neutral fallback when LLM evaluation fails."""
    return EvaluationMetrics(
        functional_correctness=0.5,
        architectural_alignment=0.5,
        scalability_projection=0.5,
        performance_score=0.5,
        semantic_maintainability=0.5,
        semantic_testability=0.5,
        semantic_security=0.5,
        semantic_debt_assessment=0.5,
        reasoning="LLM evaluation unavailable — neutral fallback applied.",
        confidence_self_assessment=0.0,
    )


class QAEvaluator:
    """
    LLM-based evaluator for semantic quality dimensions (v1, v2, v3, v9).
    Uses few-shot prompting and tool_use structured output via the Anthropic API.
    """

    def __init__(self, model: str = "claude-sonnet-4-6"):
        from anthropic import Anthropic
        self._client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._model = model

    def evaluate(
        self,
        artifact_content: str,
        artifact_type: ArtifactType = "python_code",
        context: str = "",
    ) -> EvaluationMetrics:
        user_content = f"Artifact type: {artifact_type}\n"
        if context:
            user_content += f"Context: {context}\n"
        user_content += f"\n```\n{artifact_content[:6000]}\n```"  # token guard

        messages = list(_FEW_SHOT_EXAMPLES) + [{"role": "user", "content": user_content}]

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                tools=[_OUTPUT_SCHEMA],
                tool_choice={"type": "tool", "name": "evaluate_artifact"},
                messages=messages,
            )
            for block in response.content:
                if block.type == "tool_use" and block.name == "evaluate_artifact":
                    return EvaluationMetrics(**block.input)
        except Exception as exc:
            logger.warning("QA evaluation failed: %s — using fallback", exc)

        return _fallback_metrics()
