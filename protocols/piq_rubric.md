# PIQ Rubric — Policy Injection Quality
## TCO-L2 Experiment · H5 Evaluation Instrument

**Version:** 1.0 — May 2026  
**Applies to:** Experimental group (TCO Dashboard condition)  
**Evaluator:** LLM-Judge (claude-sonnet-4-6 via OpenRouter) + 2 human annotators  
**Inter-rater target:** Cohen's κ ≥ 0.70  

---

## Conceptual grounding

In the CAL architecture (Chancay 2026, DOI: 10.5281/zenodo.20430343), Layer 2 (TCO-L2)
places the human orchestrator at the **Natural Cognitive Frontier**: the abstraction level
where cognitive demand is calibrated to human capacity, and decisions are expressible in
natural language that produces **policy** rather than artifact correction.

The PIQ rubric measures whether the participant's policy injection:
1. Leverages the compressed tensor state {Ω, Δ, Ρ, Ξ} — not just raw artifact reading
2. Is expressed at the correct NCF abstraction level (governance, not micromanagement)
3. Produces a `PolicyIntent` struct that is semantically conservative — capturing
   governance intent without information loss

A policy is evaluated at the `PolicyIntent` struct level extracted by the PolicyProcessor,
not on the raw text. This ensures evaluation targets governance semantics, not phrasing.

---

## PolicyIntent struct

```python
@dataclass
class PolicyIntent:
    target_agents: list[str]        # agents to direct
    action_type: str                # reprioritize | refactor | test | halt | escalate | monitor
    affected_dimensions: list[str]  # quality dimensions from V = (v1..v11)
    constraint: str                 # specific actionable constraint
    priority: str                   # critical | high | medium | low
    confidence: float               # PolicyProcessor self-assessment [0,1]
```

---

## Rubric: 5 dimensions × 3-point scale → PIQ ∈ [0, 1]

Each dimension is scored **0, 1, or 2**. Maximum raw score = 10.  
`PIQ_score = raw_score / 10`

### D1 — Root Cause Targeting (RCT)

*Does the policy address the actual fault signaled by {Ω, Δ, Ρ, Ξ}, not surface symptoms?*

| Score | Criterion |
|-------|-----------|
| **2** | Policy directly addresses the primary fault identified by the inference outputs. The root cause is correctly named in `constraint` or `action_type`. For S3: addresses temporal debt pattern (not single commit). For S5: addresses the inter-agent conflict (not one agent's output). |
| **1** | Policy addresses a symptom or secondary effect of the fault. Partially relevant but misses the systemic root cause. Example: "fix the SQL query" instead of "enforce parameterized queries across auth_agent". |
| **0** | Policy is unrelated to the actual fault, or addresses a fault from a different scenario. No evidence of using {Ω, Δ, Ρ, Ξ} outputs. |

### D2 — Agent Precision (AP)

*Are `target_agents` the agents causally responsible for the fault in T[d,i,j,k]?*

| Score | Criterion |
|-------|-----------|
| **2** | `target_agents` correctly identifies the agent(s) responsible for the degraded quality dimension(s). For S5: identifies BOTH conflicting agents. For S1/S2/S4: correctly targets the single responsible agent. |
| **1** | `target_agents` partially correct: includes the responsible agent plus irrelevant agents, or targets a proxy agent instead of the root cause agent. |
| **0** | `target_agents` is empty, targets wrong agents entirely, or names agents not present in the scenario. |

### D3 — Dimension Relevance (DR)

*Do `affected_dimensions` correspond to the actually degraded dimensions visible in the tensor?*

| Score | Criterion |
|-------|-----------|
| **2** | `affected_dimensions` matches the primary degraded dimensions from the scenario's ground truth. Acceptable: names 1–3 dimensions that include the primary degraded dimension. Example for S1: includes `security_risk` (v4). For S5: includes both `security_risk` (v4) and `testability` (v6). |
| **1** | `affected_dimensions` includes the degraded dimension among others, but primary degradation is not the most prominent, or relevant dimensions are mixed with irrelevant ones. |
| **0** | `affected_dimensions` does not include the primary degraded dimension(s), or lists all 11 dimensions without selectivity. |

### D4 — Constraint Specificity (CS)

*Is `constraint` actionable and expressed at the correct NCF abstraction level?*

| Score | Criterion |
|-------|-----------|
| **2** | `constraint` is specific, actionable, and expressed at governance level — neither too abstract ("improve security") nor too microscopic (dictating specific code lines). The constraint is something an agent can act on directly. Example: "enforce parameterized queries and replace MD5 with SHA-256 in all auth endpoints". |
| **1** | `constraint` is vague ("improve security") OR overly microscopic ("change line 47 to use cursor.execute(query, params)"). Partially actionable but requires significant interpretation by the receiving agent. |
| **0** | `constraint` is absent, empty, or contradicts the fault (e.g., "allow direct queries for performance"). |

### D5 — Systemic Scope (SS)

*Does the policy demonstrate awareness of cascade effects visible only in the tensor?*

| Score | Criterion |
|-------|-----------|
| **2** | Policy accounts for cross-agent or cross-temporal effects that are visible in {Δ, Ρ} but not in individual artifact review. Example for S3: policy references the progressive degradation pattern or prevents future cycles. Example for S5: policy includes a coordination mechanism between conflicting agents. Example for S4: policy mentions monitoring continuity, not just current fix. |
| **1** | Policy addresses the immediate fault but ignores cascades. Correct for the current snapshot but would miss recurrence (S3) or ongoing conflict (S5). |
| **0** | Policy would actively worsen cascade risk (e.g., introducing new dependencies while fixing S2 circular dependency). |

---

## Scenario-specific ground truth anchors

Used by the LLM-Judge to anchor scoring per scenario.

| Scenario | Primary fault | Key dimensions | Ideal `action_type` | Ideal `constraint` (abbreviated) |
|----------|--------------|----------------|--------------------|------------------------------------|
| S1 — Auth | SQL injection + MD5 | v4 (security) | `refactor` | parameterize queries, replace MD5 with SHA-256 |
| S2 — Arch | Circular dependency | v2 (arch), v7 (maintainability) | `refactor` | break user_service ↔ order_service cycle, introduce event bus |
| S3 — Debt | Gradual CC accumulation | v8 (technical_debt) | `refactor` | refactor process_order to CC < 5, enforce complexity gate |
| S4 — Deploy | Missing Prometheus + resources | v5 (observability), v9 (performance) | `monitor` | add resource limits, probes, Prometheus annotations before deploy |
| S5 — Conflict | Security vs testability tradeoff | v4 + v6 | `reprioritize` | coordinate security_agent + code_agent: prioritize v4 while adding test scaffolding |

---

## Scoring procedure

1. PolicyProcessor extracts `PolicyIntent` from participant's raw text injection
2. If `confidence < 0.70`, flag as degraded case (count separately in H5 analysis)
3. LLM-Judge receives: scenario_id, inference outputs {Ω,Δ,Ρ,Ξ}, PolicyIntent struct
4. LLM-Judge scores D1–D5 independently per rubric above
5. Two human annotators score a random 20% subsample → compute κ
6. If κ < 0.70: revisit rubric wording, recalibrate LLM-Judge prompt
7. Final PIQ_score = raw_score / 10

---

## PIQ interpretation

| PIQ range | Interpretation |
|-----------|---------------|
| 0.80–1.00 | Expert-level governance: correctly identifies root cause, targets the right agents, demonstrates systemic awareness |
| 0.60–0.79 | Competent governance: correct intent but some imprecision in targeting or scope |
| 0.40–0.59 | Partial governance: addresses symptoms rather than root cause, or misses systemic effects |
| 0.20–0.39 | Minimal governance: policy is present but largely irrelevant or ineffective |
| 0.00–0.19 | No governance signal: policy injection did not demonstrate use of {Ω,Δ,Ρ,Ξ} |

---

## H5 hypothesis connection

**H5**: Participants in the experimental group (TCO Dashboard) inject policies of
significantly higher quality than control group participants (raw output view),
as measured by PIQ score (Spearman ρ between PIQ and condition, p < 0.05).

The rubric is designed so that:
- A participant reading raw artifacts (control) can at best score ~D4 (if they write a specific constraint)
- But D5 (systemic scope) and D3 (dimension relevance) require the tensor view ({Ω,Δ,Ρ,Ξ})
- D1 for S3/S5 requires the temporal/conflict view only available at L2

This asymmetry between conditions is the empirical test of whether the NCF abstraction
level (L2 tensor view) enables qualitatively different governance than artifact-level review.
