# CAL Benchmark v1.0 — Formal Annotation

**Role in the research program:**  
This document is the shared empirical anchor between Paper 1 (SID Study) and Paper 2 (TCO-L2 RCT).
S1–S5 appear identically in both papers. Paper 1 computes SID_C*(s) for each scenario.
Paper 2 measures ΔPIQ(s) from the n=40 experiment. The Spearman ρ between these two vectors
across the five scenarios is the cross-paper validation of H_cross.

**Date established:** 2026-06-01  
**Status:** Pre-registered before Paper 2 data collection.

---

## 1. Annotation vocabulary

Each scenario is annotated with `Y = (D, C)` where:

```
D = {T1_answer, T2_risk, T3_decision, T4_policy}
    — the correct supervisory decision for each task
    — source: GROUND_TRUTH in src/experiment/data_pipeline/accuracy_scorer.py

C = {dimensions, agents, time_indices, mechanism}
    — the causal structure that justifies D
    — expressed in the native vocabulary of T[d, i, j, k]
    — dimensions: quality vector dimension names (v1..v11)
    — agents: the agent(s) whose output carries the fault
    — time_indices: the cycle(s) where the fault is active
    — mechanism: element of Ω (causal ontology)
```

**Causal ontology Ω** (five mechanisms, one per benchmark scenario):

| Mechanism | Definition |
|---|---|
| `security_vulnerability` | Adversarial or unsafe pattern in a single agent's output, single cycle |
| `omission_failure` | Required configuration absent in a specific stage, single agent, single cycle |
| `structural_violation` | Architectural constraint violated by a specific agent, single cycle |
| `inter_agent_conflict` | Two agents produce outputs that are mutually incompatible on shared dimensions |
| `temporal_drift` | Quality degradation that only becomes visible through integration over multiple cycles |

---

## 2. CCI — Causal Complexity Index

**Formal definition:**

```
CCI(s) = |{ tensor indices required to read C(s) directly from T[d,i,j,k] }|
```

An index is "required" if omitting it makes C ambiguous or unrecoverable without external inference.
CCI is an objective property of the fault structure, determined by the fault injector design,
and can be computed before the experiment runs.

**Tensor operation taxonomy (maps to inference_engine.py):**

| CCI | Operation type | Description |
|---|---|---|
| 1 | Direct read | Single cell T[d,*,*,*] — dimension alone identifies the fault |
| 2 | Indexed read | Two indices required T[d,i,*,*] or T[d,*,j,*] |
| 3 | Pairwise comparison | Ρ operation — T[d,*,j₁,*] vs T[d,*,j₂,*] across agents |
| 4 | Trajectory integration | Δ operation — T[d,*,*,k] across multiple time indices |

---

## 3. Per-scenario annotation

---

### S1 — Authentication SQL Injection

**Fault:** String concatenation in SQL queries + MD5 password hashing.  
**Source:** `src/pipeline/scenarios/s1_auth.py`

**D (supervisory decisions):**

| Task | Correct answer |
|---|---|
| T1 — Fault detection | `sql_injection_and_md5_hash` |
| T2 — Risk level | `HIGH` |
| T3 — Deploy decision | `halt` |
| T4 — Re-orchestration policy | `parameterize_queries_replace_hash` |

**C (causal structure):**

```
dimensions:   [security_risk, anomaly_score]   — v4 drops 0.90→0.20; v11 signals anomaly
agents:       [code_agent]                     — single agent generates the auth module
time_indices: [k=0]                            — static fault, single cycle
mechanism:    security_vulnerability
```

**Tensor operation to expose C:**

```
Direct read: T[d=security_risk, i=build, j=code_agent, k=0]
Value: ~0.20 (vs. baseline ~0.90)
→ C is fully observable from a single tensor cell.
  No agent comparison, no temporal integration required.
```

**CCI: 1**  
Justification: the security_risk dimension alone identifies the fault type, the responsible agent,
and the affected cycle. No additional index is required to distinguish this fault from
other low-security-risk scenarios.

**Ω:** `security_vulnerability`

---

### S2 — Architectural Circular Dependency

**Fault:** Circular import between user and order modules (hexagonal architecture violation).  
**Source:** `src/pipeline/scenarios/s2_arch.py`

**D (supervisory decisions):**

| Task | Correct answer |
|---|---|
| T1 — Fault detection | `circular_dependency_user_order` |
| T2 — Risk level | `MEDIUM` |
| T3 — Deploy decision | `halt` |
| T4 — Re-orchestration policy | `break_circular_dependency` |

**C (causal structure):**

```
dimensions:   [architectural_alignment, maintainability]   — v2 drops 0.85→0.20; v7 drops ~0.26
agents:       [code_agent]                                 — agent that produced the circular import
time_indices: [k=0]                                        — static fault, single cycle
mechanism:    structural_violation
```

**Tensor operation to expose C:**

```
Indexed read: T[d=architectural_alignment, i=build, j=code_agent, k=0]
Value: ~0.20 (vs. baseline ~0.85)
→ Knowing the dimension alone (architectural_alignment low) does not uniquely
  identify which agent introduced the violation.
  The agent index j is required to attribute the structural fault.
```

**CCI: 2**  
Justification: requires d (architectural_alignment) and j (code_agent).
The stage index i disambiguates from deploy-time structural issues.
Temporal index k is not required — fault is static.

**Ω:** `structural_violation`

---

### S3 — Technical Debt Accumulation

**Fault:** Gradual cyclomatic complexity increase across 4 cycles.  
**Source:** `src/pipeline/scenarios/s3_debt.py` (N_CYCLES=4)

**D (supervisory decisions):**

| Task | Correct answer |
|---|---|
| T1 — Fault detection | `gradual_technical_debt_accumulation` |
| T2 — Risk level | `LOW` (correct — progressive, not yet critical at any single cycle) |
| T3 — Deploy decision | `deploy_with_warning` |
| T4 — Re-orchestration policy | `refactor_process_order_reduce_cyclomatic_complexity` |

**C (causal structure):**

```
dimensions:   [technical_debt, testability]   — v8 degrades 0.68→0.60→0.52→0.44 per cycle;
                                                v6 degrades as CC rises 2→5→8→12
agents:       [code_agent]                    — single agent, gradual pattern
time_indices: [k=0, k=1, k=2, k=3]           — ALL four cycles required for drift detection
mechanism:    temporal_drift
```

**Tensor operation to expose C:**

```
Δ (delta): T[d=technical_debt, i=build, j=code_agent, k] over k=0..3
Slope: approximately -0.08 per cycle (detectable with |slope| > 0.05 threshold in inference_engine.py)
→ At any single cycle k, the value of technical_debt is within normal range.
  The fault is ONLY visible through the temporal trajectory.
  Without the k index, this fault is not reliably detectable.
  Monte Carlo simulation (analysis/tensor_necessity.py): 32.3% detection raw vs 66.9% tensor Δ.
```

**CCI: 4**  
Justification: requires d (technical_debt), j (code_agent), and k=[0,1,2,3].
The four time indices are not redundant — each represents a distinct measurement in the
accumulation trajectory. Omitting any k reduces detection probability.
This is the maximum CCI in the benchmark.

**Ω:** `temporal_drift`  
**Note:** T2 answer is `LOW` (not HIGH) because no single cycle crosses the warning threshold.
The correct governance response is `deploy_with_warning` — TCO provides early warning
via Δ before the fault becomes critical. This is the central demonstration of TCO's
advantage over traditional HITL for temporal faults.

---

### S4 — K8s Observability Configuration

**Fault:** Missing Prometheus probes and resource limits in Kubernetes YAML.  
**Source:** `src/pipeline/scenarios/s4_deploy.py`

**D (supervisory decisions):**

| Task | Correct answer |
|---|---|
| T1 — Fault detection | `missing_prometheus_probes_no_resources` |
| T2 — Risk level | `MEDIUM` |
| T3 — Deploy decision | `halt` |
| T4 — Re-orchestration policy | `add_resource_limits_probes_hpa` |

**C (causal structure):**

```
dimensions:   [observability_coverage, performance]   — v5 drops 0.85→0.15; v9 drops ~0.26
agents:       [deploy_agent]                           — the agent producing the K8s config
time_indices: [k=0]                                    — static omission, single cycle
mechanism:    omission_failure
```

**Tensor operation to expose C:**

```
Indexed read: T[d=observability_coverage, i=deploy, j=deploy_agent, k=0]
Value: ~0.15 (vs. baseline ~0.85)
→ The stage index i=deploy is required to distinguish this from
  observability gaps at other pipeline stages (e.g., missing logs in build).
  The fault is specifically a deployment-configuration omission.
```

**CCI: 2**  
Justification: requires d (observability_coverage) and i (deploy).
The agent index j confirms attribution but is not strictly required for identification
(only the deploy agent produces deploy-stage configs).
Temporal index k is not required — fault is static.

**Ω:** `omission_failure`

---

### S5 — Inter-Agent Security/Testability Conflict

**Fault:** security_agent prioritizes security (stateless design) while code_agent
prioritizes testability (stateful design). The conflict is in the disagreement, not in either artifact individually.  
**Source:** `src/pipeline/scenarios/s5_conflict.py`

**D (supervisory decisions):**

| Task | Correct answer |
|---|---|
| T1 — Fault detection | `inter_agent_security_testability_conflict` |
| T2 — Risk level | `HIGH` |
| T3 — Deploy decision | `halt` |
| T4 — Re-orchestration policy | `resolve_conflict_prioritize_security_with_test_scaffolding` |

**C (causal structure):**

```
dimensions:   [security_risk, testability]                     — v4 gap Δ≈0.65; v6 gap Δ≈0.50
agents:       [security_agent, code_agent]                     — BOTH agents, simultaneously
time_indices: [k=0]                                            — single cycle, simultaneous conflict
mechanism:    inter_agent_conflict
```

**Tensor operation to expose C:**

```
Ρ (rho):
  |T[d=security_risk, i=build, j=security_agent, k=0] - T[d=security_risk, i=build, j=code_agent, k=0]| ≈ 0.65
  |T[d=testability,   i=build, j=security_agent, k=0] - T[d=testability,   i=build, j=code_agent, k=0]| ≈ 0.50

→ Inspecting either artifact individually shows no fault.
  The fault is ONLY visible as the DIFFERENCE between agents on shared dimensions.
  Requires simultaneous access to j₁=security_agent and j₂=code_agent.
  Without the agent index (and two agents simultaneously), this fault is not detectable.
```

**CCI: 3**  
Justification: requires d=[security_risk, testability] (two dimensions), j₁=security_agent,
and j₂=code_agent. Three distinct index specifications are necessary.
This is the Ρ operation — the most structurally complex readable in a single cycle.
Note: higher than S2/S4 (CCI=2) because the conflict requires cross-agent comparison,
not just locating a specific agent's fault.

**Ω:** `inter_agent_conflict`  
**Note:** S5 cannot be detected by inspecting individual artifacts — a fact confirmed
by design. The fault exists only in the relationship between agent outputs.
This is the central demonstration of why the agent index j is not optional in the tensor.

---

## 4. CCI ordering and pre-registered prediction

```
CCI ranking (ascending):
  S1 (CCI=1) < S4 (CCI=2) = S2 (CCI=2) < S5 (CCI=3) < S3 (CCI=4)

Tensor operation progression:
  S1: direct read (d only)
  S4: indexed read (d + i)
  S2: indexed read (d + j)
  S5: Ρ — pairwise comparison (d + j₁ + j₂)
  S3: Δ — trajectory integration (d + j + k[0..3])
```

**H_cross (pre-registered prediction):**

```
r_Spearman(SID_C*(s), ΔPIQ(s)) > 0   for s ∈ {S1, S2, S3, S4, S5}

Specific ordering prediction (Paper 1 → Paper 2):
  SID_C*(S3) ≥ SID_C*(S5) > SID_C*(S2) ≈ SID_C*(S4) > SID_C*(S1)
  ΔPIQ(S3)   ≥ ΔPIQ(S5)   > ΔPIQ(S2)   ≈ ΔPIQ(S4)   > ΔPIQ(S1)

This prediction must be made using Paper 1 SID values
BEFORE Paper 2 data collection begins.
If computed after, H_cross becomes a post-hoc correlation and loses pre-registered status.
```

---

## 5. What this benchmark does NOT claim

- **It does not claim S1–S5 are the only causal mechanisms in AI pipelines.** They are the minimum sufficient set to demonstrate that the tensor is qualitatively superior across the CCI spectrum. Level 2 scenarios (S6–S8) in the SID Study add generalization.

- **It does not claim CCI is the only moderator of TCO's advantage.** It is the theoretically motivated moderator. Other moderators (participant experience, AI familiarity) are ANCOVA covariates in Paper 2.

- **It does not claim the D annotation is exhaustive.** T4 (re-orchestration policy) has multiple acceptable responses. The GROUND_TRUTH represents the canonical correct policy, not the only correct policy.
