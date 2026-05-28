# PIQ Rubric — LLM-Judge Quick Reference

Scores PolicyIntent structs on 5 dimensions × 0-2 points.
PIQ_score = raw_score / 10 ∈ [0, 1]. See protocols/piq_rubric.md for full rubric.

## Dimensions

| ID | Name | 2 (correct) | 1 (partial) | 0 (absent/wrong) |
|----|------|------------|-------------|-----------------|
| D1 | Root Cause Targeting | Addresses actual fault in {Ω,Δ,Ρ,Ξ} | Addresses symptom | Unrelated to fault |
| D2 | Agent Precision | Correct agent(s) targeted | Partially correct | Wrong/empty |
| D3 | Dimension Relevance | Matches degraded dimensions | Degraded dim present but mixed | Missing primary dim |
| D4 | Constraint Specificity | Specific + governance-level | Vague or microscopic | Absent/contradicts |
| D5 | Systemic Scope | Accounts for tensor-visible cascades | Fixes immediate, misses cascade | Worsens cascade |

## Scenario anchors

| Scenario | Key fault | Primary dim(s) | Expected action |
|----------|-----------|----------------|----------------|
| S1 | SQL injection + MD5 | v4 (security) | refactor |
| S2 | Circular dependency | v2 + v7 | refactor |
| S3 | Gradual CC debt | v8 (tech_debt) | refactor |
| S4 | Missing probes/resources | v5 + v9 | monitor |
| S5 | Security ↔ testability conflict | v4 + v6 | reprioritize |

## CAL-L2 alignment note

D5 (Systemic Scope) and D1 for S3/S5 are only achievable by participants using the
tensor view {Ω,Δ,Ρ,Ξ}. This asymmetry is the empirical test of H5: NCF abstraction
enables qualitatively different governance than artifact-level review.
