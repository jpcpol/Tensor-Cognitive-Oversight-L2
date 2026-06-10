# TENSOR-BASED COGNITIVE OVERSIGHT — TCO-L2
### A Framework for Human Orchestration of AI-Driven Software Systems
#### Layer 2 of the Cognitive Abstraction Layer (CAL) Architecture

**Working Paper — Confidential Draft for Peer Review**
**2026 · v3.1 — Includes Experimental Design, MVP Architecture & Software Implementation Plan**

> *This paper formalizes and empirically validates Layer 2 (L2) of the CAL architecture [Chancay 2026b]. The full five-level research agenda (L0–L4) — spanning L0 raw artifacts to L4 autonomous meta-inference — is described in the companion pre-paper, canonically at `CAL/CAL_PrePaper_v1.4.md` (DOI [10.5281/zenodo.20430343](https://doi.org/10.5281/zenodo.20430343)).*
>
> *Inter-layer status (June 2026): the L2 contribution below — the tensor framework, the NCF, and the n=40 RCT design — is unchanged. Since v3.0, the layers L2 feeds have advanced: **L3's characterization closed** (the composition operator C is characterized; causal conservation = structural sparsity preservation, not reconstruction fidelity) and **L4's gate-C is met** (κ(V)=1296 delivered; the κ vs n² cost contrast is active). These results validate, downstream, that the tensor representation L2 produces carries the causal structure higher layers need. See `CAL/L3/L3_CLOSURE.md` and the pre-paper §5.7. This is a v3.1 status note only; no L2 experimental claim is altered.*

---

> **Abstract**
>
> The rapid adoption of artificial intelligence in software development has shifted human roles from creators to supervisors of increasingly complex, AI-generated systems. This transition has introduced significant cognitive challenges — decision fatigue, reduced scalability of oversight, and difficulty validating high-complexity outputs — collectively referred to as *"brain fry"* in practitioner settings.
>
> This paper proposes **Tensor-based Cognitive Oversight (TCO)**, a novel framework that restructures human-AI interaction through a vector-based evaluation model and its aggregation into tensor representations. These structures enable system-level inference and facilitate human orchestration at a higher abstraction level.
>
> A central theoretical contribution of TCO is the **Natural Cognitive Frontier (NCF)**: the level of abstraction at which human cognitive demand is calibrated to human capacity — achievable through natural language policy injection without technical friction. The bidirectional architecture of TCO transforms the human role from output validator to system orchestrator, resolving automation bias through obligatory active judgment rather than passive acceptance.
>
> The paper includes a full experimental design with five controlled scenarios, a functional MVP specification, and a 10-week software implementation roadmap validated against five research hypotheses (H1–H5).
>
> A secondary but equally important contribution is a reframing of the human role in AI-supervised software systems. TCO does not argue that technical expertise becomes less valuable — it argues that expertise **shifts** from artifact manipulation to systemic orchestration. As AI system autonomy increases, the capacity for systemic supervision becomes more critical, not less: the engineer who once debugged lines of code must now debug emergent behaviors. The NCF is the design boundary that makes this shift tractable.
>
> **Keywords:** *cognitive oversight, tensor representation, multi-agent systems, human orchestration, Natural Cognitive Frontier, policy injection, software quality, AI supervision, controlled experiment, expertise shift, orchestration engineer*

---

## Table of Contents

1. Introduction
2. Related Work
3. Theoretical Framework
4. Problem Statement
5. The TCO Framework
6. Research Objectives and Hypotheses
7. Experimental Design and MVP — Phase 3
8. Software Architecture and Implementation Roadmap
9. Challenges and Open Problems
10. Expected Contributions
11. References
- Appendix A — Evaluation Vector JSON Schema
- Appendix B — Inference Layer Output Schema
- Appendix C — MVP Component Specifications

---

## 1. Introduction

Artificial intelligence systems are increasingly capable of generating complete software artifacts — code, configurations, architectural decisions, and deployment pipelines. While this capability enhances productivity at an unprecedented scale, it introduces a fundamental and underexplored bottleneck: humans are required to supervise outputs that systematically exceed their efficient cognitive processing capacity.

This bottleneck manifests as what practitioners describe as *"brain fry"* — a state of cognitive saturation produced by sustained exposure to high-volume, low-level, technically dense outputs. The phenomenon is well-documented in cognitive science: when working memory is saturated, error detection capability deteriorates, decision quality degrades, and the human agent begins to operate in a reactive, heuristic mode rather than a deliberate, analytical one [1, 2].

Traditional Human-in-the-Loop (HITL) models assume that human supervisors review discrete, bounded outputs and intervene at well-defined checkpoints. This assumption was reasonable when automated systems produced individual, interpretable decisions. In multi-agent AI-driven software development, it fails structurally: the volume of outputs is continuous, the complexity of each artifact is high, and the consequences of any single error propagate across interdependent system components.

This paper argues that the limitation is not human capability per se, but the **level of abstraction** at which humans interact with AI systems — and more fundamentally, a mismatch between that abstraction level and the **new role** that AI autonomy is creating for human engineers. The solution is not better tools for reviewing raw outputs. It is a recognition that the engineer's role has already shifted — from artifact author and validator to systemic orchestrator — and that current interfaces have not kept pace with that shift.

As AI systems take over the generation of code, configurations, and architectural decisions, the human's comparative advantage is no longer in producing those artifacts. It is in **supervising the behaviors and quality trajectories of the systems that produce them** — detecting drift, resolving inter-agent conflicts, enforcing architectural policy. This requires operating at a higher abstraction level: one where cognitive effort is directed at judgment about system direction rather than validation of technical detail. TCO is a framework for engineering that abstraction level deliberately.

We propose Tensor-based Cognitive Oversight (TCO), a framework that:

- Transforms AI-generated artifacts into structured, normalized **evaluation vectors** V ∈ [0,1]¹¹ capturing eleven quality dimensions
- Aggregates these vectors into a **cognitive tensor** T[dimension, stage, agent, time] representing the global state of the system
- Derives actionable **inferences** from the tensor — system state, trend analysis, risk detection, and prioritized recommendations
- Positions the human as a high-level orchestrator operating at the **Natural Cognitive Frontier (NCF)**: the level of abstraction where cognitive demand is calibrated to human capacity, expressible in natural language
- Implements a **bidirectional loop** in which human judgment, expressed as natural language policy injection, re-orchestrates the agent system

---

## 2. Related Work

### 2.1 Human-in-the-Loop Frameworks for Agentic AI Systems

The Human-in-the-Loop paradigm — embedding human decision-making at defined checkpoints within automated pipelines — has been studied across medical diagnosis, content moderation, autonomous vehicles, and scientific data analysis [8]. A 2025 systematic review of over 400 HITL implementations identifies a recurring structural pattern: HITL effectiveness degrades sharply as system output volume and artifact complexity increase, with cognitive load and trust calibration identified as the two persistently unsolved challenges in deployed systems [8].

The most directly related work is HULA (Human-In-the-Loop Software Development Agents), proposed by Takerngsaksiri et al. [19]. HULA integrates human review checkpoints into a multi-agent software development pipeline, routing artifacts to human reviewers at defined pipeline stages. TCO and HULA share the foundational recognition that unmediated agentic output is unmanageable for human supervisors; they differ on the architectural response. HULA preserves artifact-level intervention: humans review individual outputs at each checkpoint, and review effort scales with output volume. TCO proposes system-level orchestration: humans interact with a tensor-derived abstraction of system state, and cognitive effort is decoupled from output volume by design. This decoupling is TCO's central architectural claim.

Pareschi and Saghafian [20] develop a system-theoretic account of human-AI collaboration in agentic contexts, arguing for a shift from direct to delegated control as agent capability increases. Their framework supports TCO's architectural premise but does not specify a concrete abstraction mechanism. TCO operationalizes that delegation with a formal evaluation vector φ, a cognitive tensor T, and a bidirectional policy injection loop — the missing implementation layer.

### 2.2 Supervisory Control Theory and Levels of Automation

Parasuraman, Sheridan, and Wickens [25] establish a ten-level taxonomy of human-automation interaction — from fully manual to fully autonomous — with empirical evidence linking mismatched automation levels to both cognitive overload and automation complacency. Their model predicts that as AI system autonomy increases, supervisory interfaces must shift from monitoring individual actions to managing goal-level outcomes. Miller and Parasuraman [7] extend this with a delegation interface model: effective oversight requires interfaces calibrated to the decision horizon, not the operational detail.

Cummings [26] applies supervisory control theory to high-tempo, high-volume automated environments, demonstrating that human performance bottlenecks in complex automation arise from interface design failures, not human cognitive limits. Supervisors consistently perform better when given aggregated, decision-relevant displays than when given technical readouts. This directly motivates TCO's inference layer: the human-facing output is system state, trend, conflict, and recommendations — not metrics, logs, or raw evaluation scores.

Sheridan's foundational framework [6] provides the historical anchor: the evolution from direct control to supervisory oversight in aviation, nuclear operations, and telemedicine established that the correct response to overwhelming operational complexity is not better tools for direct review, but abstraction to a level where human judgment can operate with full deliberative capacity. TCO applies this pattern to the novel domain of multi-agent AI software development.

### 2.3 Observability and Monitoring Tools for AI Systems

Commercial observability platforms — Datadog, New Relic, Grafana — are the de facto standard for production system monitoring. Their cognitive model is diagnostic: they surface technical telemetry (latency, error rates, resource utilization) and rely on the operator to translate indicators into quality judgments. Applied to AI-generated software artifacts, this model has a structural limitation: the quality dimensions that matter to a human orchestrator — architectural alignment, security exposure, maintainability trajectory — are semantic properties not representable in infrastructure metrics.

The NIST AI Risk Management Framework [27] identifies continuous monitoring as a core governance obligation for deployed AI systems but frames it as a compliance and anomaly-detection activity. It does not address the cognitive interface through which human risk managers interact with monitoring outputs. This gap — between the requirement to monitor and the cognitive feasibility of monitoring — is precisely the problem TCO addresses.

Sculley et al. [28] document the hidden technical debt that accumulates in ML systems because existing monitoring captures operational health, not quality degradation. In multi-agent agentic systems, the equivalent phenomenon occurs at the semantic level: architectural alignment deteriorates, inter-agent conflicts accumulate, and technical debt compounds before any operational metric registers a signal. TCO's tensor T is designed to surface this pre-operational degradation — specifically through v₈ (technical_debt) and the Ρ (conflict) inference component — giving orchestrators an early warning window that reactive monitoring cannot provide.

### 2.4 Cognitive Load in Software Engineering

Research on cognitive load in software engineering identifies code review as the most cognitively demanding activity in the development workflow, with measurable quality degradation after 60–90 minutes of sustained review [2]. The introduction of AI-assisted development tools has redistributed, not reduced, this burden. Amershi et al. [29] document that practitioners adopting ML components face compound cognitive demands: conventional software quality concerns compounded by model behavior uncertainty. Agentic AI tools amplify this effect at scale.

Codebridge's analysis of 211 million changed lines of code over four years [12] provides quantitative evidence: repositories with high proportions of AI-generated code show increasing defect rates over time despite — or because of — higher output volume. The implication is that review throughput has not kept pace with generation throughput. TCO's core hypothesis is that this mismatch is not a resource problem solvable by adding reviewers, but an abstraction problem solvable by changing the level at which human judgment operates.

### 2.5 Multi-Agent Evaluation and LLM-as-Judge

The emergence of LLM-based multi-agent software development systems — SWE-agent [30], Devin, OpenHands, and related architectures — has introduced a new evaluation challenge: artifacts are semantically interdependent across agents and stages, and errors in one component propagate silently until a later integration failure. Evaluation methods designed for single-model outputs do not address this cross-agent dependency structure.

TCO's tensor indexing T[dimension, stage, agent, time] is designed for this structure: the Ρ (conflict) component of the inference layer computes cross-agent inconsistency at the dimension level, enabling detection of inter-agent disagreement before it produces downstream failures — a capability absent from per-artifact evaluation frameworks.

The LLM-as-Judge paradigm [22, 23, 24] provides the substrate for TCO's QA evaluation layer. Recent empirical studies show that LLM judges achieve inter-rater reliability of κ ≥ 0.70 with human experts when given structured rubrics [23, 24]. TCO uses this capability to automate vector generation φ without per-artifact human annotation, while the tensor aggregation and inference layers address the system-level synthesis that the LLM-as-Judge literature does not.

---

## 3. Theoretical Framework

TCO is grounded in four bodies of established theory, each contributing a distinct explanatory lens. The framework's originality lies in their integration within the specific domain of human orchestration of multi-agent AI software systems.

| Theory | Author | TCO Role | Core Contribution |
|--------|--------|----------|-------------------|
| **Cognitive Load Theory** | Sweller (1988) | Psychological basis of the problem | Formalizes why reviewing raw outputs causes overload. Distinguishes extraneous load (problem) from germane load (solution). TCO eliminates the former and maximizes the latter. |
| **Situation Awareness** | Endsley (1995) | Orchestration model | L1 (perception), L2 (comprehension), L3 (projection) map directly to TCO's vectorization, tensor, and inference layers. The orchestrator operates at L2/L3, not L1. |
| **Supervisory Control Theory** | Sheridan (1992) | Precedent in complex systems | LOA model and aviation precedent validate the shift from operator to orchestrator. TCO applies this proven pattern to multi-agent AI software. |
| **Hybrid Cognitive Alignment** | AMR (2025) | Human-AI collaboration framework | The tensor is the AI's representation of the system; policy injection is the human response in natural language — a formally aligned bidirectional interface. |

### 3.1 Cognitive Load Theory and the Root Cause of Brain Fry

Cognitive Load Theory (CLT), introduced by Sweller [1], formalizes the constraints of human working memory during complex cognitive tasks. The theory distinguishes three types of cognitive load: **intrinsic load** (inherent complexity of the material), **extraneous load** (unnecessary burden imposed by poor information presentation), and **germane load** (productive effort directed at schema construction and decision-making).

The critical insight for TCO is that intrinsic and extraneous loads compete with germane load for the same finite working memory capacity — estimated at 3 to 5 meaningful chunks in young adults [3]. When supervisors review raw AI-generated outputs, they face maximum intrinsic load (the artifact is complex) and maximum extraneous load (the presentation format — code, logs, configurations — is optimized for machine processing, not human cognition). The result is that germane load — the only type that produces real oversight value — is crowded out entirely.

> **CLT Applied to TCO:** The vector φ(A) eliminates extraneous cognitive load by pre-processing the artifact into a normalized, semantically interpretable representation. The tensor T eliminates the intrinsic load of cross-artifact, cross-agent, cross-time synthesis. What remains for the human is pure germane load: interpretation, judgment, and policy formulation — the cognitive work humans are uniquely equipped to perform.

### 3.2 Situation Awareness and the Three Levels of Orchestration

Endsley's model of Situation Awareness (SA) [4] describes the cognitive process by which operators of complex dynamic systems develop and maintain an accurate mental model of system state. The model specifies three hierarchical levels:

| SA Level | Corresponds to in TCO |
|----------|-----------------------|
| **L1 — Perception** | Vectorization layer φ: automated extraction of quality signals from artifacts |
| **L2 — Comprehension** | Tensor T + Inference layer: aggregated system state and pattern detection |
| **L3 — Projection** | Trend analysis Δ and risk detection Ρ: early warning before threshold breach |
| **Decision & Action** | NCF: human interprets L2/L3 output and formulates natural language policy P_new |

Research on SA failures in aviation shows that **76% of SA errors occur at Level 1** — failure to correctly perceive information [5]. This is the level at which HITL supervisors of AI systems currently operate: reading code, parsing logs, manually cross-referencing outputs. TCO is designed to shift human operation to Levels 2 and 3, where awareness is most valuable and cognitive efficiency is highest.

### 3.3 Supervisory Control Theory and the Historical Precedent

Sheridan's Supervisory Control Theory [6] describes the evolution of human roles in automated systems from direct operators to supervisors — and identifies the cognitive challenges this transition creates. The Level of Human Control Abstraction (LHCA) framework [7] extends this with five levels of decreasing control granularity: Direct, Augmented, Parametric, Goal-Oriented, and Mission-Capable.

The aviation industry resolved an analogous problem in the 1980s and 1990s: as aircraft became too complex for direct manual control, cockpit design shifted from physical controls to glass cockpits displaying aggregated system state, allowing pilots to operate at Goal-Oriented and Mission-Capable levels. **TCO proposes the equivalent shift for AI-driven software**: from reviewing code (Direct level) to orchestrating system state (Goal-Oriented level) through a structured, interpretable interface.

### 3.4 Gap in the Existing Literature

Despite the maturity of HITL research [8], the literature identifies a persistent gap: scalability. As AI systems become more agentic and continuous, manual oversight cannot keep pace [9]. Research surveys explicitly cite cognitive load and trust calibration as unsolved challenges in deployed HITL systems [8].

Existing approaches fail on two counts. First, they treat HITL as output-level intervention, not system-level orchestration. Second, they do not address the representation problem: raw outputs are not cognitively appropriate interfaces for human supervisors of complex multi-agent systems.

TCO is structurally distinct from existing observability platforms (Datadog, New Relic, NIST RMF monitoring) along **four dimensions**:

1. **Semantic quality vocabulary** normalized across agents and stages rather than technical metrics
2. **Multi-agent aggregation** with inter-agent conflict detection at the tensor level
3. **Cognitive interface** oriented toward decision rather than technical diagnosis
4. **Bidirectional policy loop** that returns human judgment to the system as structured re-orchestration instructions — absent from all existing monitoring platforms

---

## 4. Problem Statement

### 4.1 Central Problem: Cognitive Mismatch in AI Supervision

The supervision of AI-generated software systems presents a structural cognitive mismatch: the information format of system outputs (code, logs, configurations) is optimized for machine execution, not for human evaluation. Supervisors operating at this level face:

- High **intrinsic cognitive load** from artifact complexity
- Maximum **extraneous cognitive load** from format mismatch between output type and human cognition
- **Decision fatigue** from high volume and sustained context switching
- Deteriorating **error detection capability** as working memory saturates
- Susceptibility to **automation bias** — passive acceptance of AI outputs — as a cognitive defense mechanism against overload [10, 11]

> **The Brain Fry Problem — Empirical Evidence**
>
> Analysis of over 211 million changed lines of code between 2020 and 2024 documents a 60% decline in refactored code as developers increasingly favor velocity over health. Code churn — the proportion of code reverted within two weeks — has doubled. A 2025 METR study found a 39–44% perception gap: developers using AI tools felt 20% faster while measuring 19% slower in real-world codebases [12]. These findings indicate that cognitive saturation from AI-assisted workflows actively degrades both output quality and the human's ability to accurately assess their own performance — a compounding failure mode.

### 4.2 Structural Underlying Problem: Incorrect Abstraction Level

The root cause is not that humans lack the capability to supervise complex systems — it is that they are operating at the **wrong abstraction level**. Current HITL models position humans as:

- **Output validators**: reviewing individual artifacts for correctness
- **Manual debuggers**: tracing errors through system artifacts
- **Technical configurators**: adjusting system parameters directly

TCO proposes that humans should instead operate as:

- **System orchestrators**: governing the direction of the multi-agent system through policy
- **Strategic decision-makers**: interpreting aggregated state and formulating high-level responses
- **Policy designers**: expressing system constraints and priorities in **natural language**

The analogy from Site Reliability Engineering is direct. When production systems scaled beyond the capacity of operators to monitor individual servers, the field did not respond by hiring more operators — it invented observability platforms (Datadog, New Relic, Prometheus) that allowed one engineer to supervise aggregate system health across thousands of services. Engineers stopped debugging individual packets and started supervising state. The expertise did not disappear — it shifted to a higher abstraction level: from network configuration to reliability policy.

The same shift is underway in AI-driven software engineering. Engineers are increasingly unable to review the volume of AI-generated artifacts at artifact-level granularity. The correct response is not to slow down generation — it is to elevate the abstraction level of supervision. The difference between observability platforms and TCO is the nature of the signal: Datadog monitors *operational health* (latency, error rates, resource utilization), while TCO monitors *semantic health* (architectural alignment, security exposure, technical debt trajectory, inter-agent coherence). The human-facing output in both cases is state — not raw data — because state is what enables judgment.

This framing clarifies TCO's unique claim: it is not a cognitive load reduction tool but an **expertise relocation tool** — a system that moves the human's cognitive engagement from the level where AI already performs well (artifact production and review) to the level where human judgment remains irreplaceable (systemic direction, policy design, emergent behavior diagnosis).

### 4.3 The Automation Bias Risk and Its TCO Resolution

A critical secondary problem in AI supervision is automation bias: the tendency to over-rely on automated recommendations, accepting system outputs without sufficient scrutiny [10]. Standard dashboard-based oversight risks amplifying this bias by converting complex system state into simplified signals that invite passive acceptance.

**TCO resolves this structurally.** The inference layer produces not a decision but a state description — {Ω, Δ, Ρ, Ξ}. The human receives this state and is required to **interpret it, formulate a response, and inject that response as a new policy**. This is an inherently active cognitive process: the tensor does not tell the orchestrator what to do — it tells the orchestrator what is happening, so they can decide what to do. Automation bias is mitigated not by interface design but by architectural necessity.

---

## 5. The TCO Framework

### 5.1 Architectural Overview

TCO is structured as a six-layer architecture in which each layer transforms system information into progressively higher-abstraction representations, culminating in a natural language interface for the human orchestrator. The architecture is **bidirectional**: a downstream flow transforms artifacts into state, and an upstream flow returns human judgment as system policy.

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 6 — Human Orchestration (NCF)                                │
│  Reads {Ω,Δ,Ρ,Ξ} · Interprets in natural language · Policy P_new   │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 5 — Inference  I: T → {Ω, Δ, Ρ, Ξ}                          │
│  Global state · Trend analysis · Risk detection · Recommendations    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 4 — Tensor Aggregation  T[d, i, j, k]    ← TCO CORE         │
│  f: {V} → T ∈ ℝⁿˣˢˣᵃˣᵗ   ·   stage × agent × time                 │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 3 — Vectorization  φ: A → V ∈ [0,1]ⁿ                        │
│  V = (v₁...v₁₁) · Normalized · ~Orthogonal supervisory dimensions    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2 — QA Evaluation (Multi-agent)                              │
│  QA Agent · Security Agent · Perf Agent · Arch Agent                │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1 — AI Generation                                            │
│  Code Agent · Design Agent · Deploy Agent · Test Agent              │
└─────────────────────────────────────────────────────────────────────┘
         ↑ Policy P_new (upstream — natural language)
         ↓ Artifacts (downstream — machine outputs)
```

### 5.2 Layer 3 — The Evaluation Vector Model

#### 4.2.1 Formal Definition

Let `A` denote a software artifact. The vectorization function φ is defined as:

```
φ : A → V ∈ [0,1]ⁿ

V = (v₁, v₂, v₃, v₄, v₅, v₆, v₇, v₈, v₉, v₁₀, v₁₁)

where n = 11 for the base TCO specification (extensible to ℝⁿ)
```

Each dimension is computed as weighted aggregation of domain-specific metrics:

```
vᵢ = Σⱼ (wᵢⱼ · mᵢⱼ(A)) / Σⱼ wᵢⱼ

where:  wᵢⱼ = weight of metric j within pilar i  (calibrable by domain)
        mᵢⱼ = normalized value of metric j for artifact A
        ∀i,j: mᵢⱼ ∈ [0,1]  (min-max normalization against known bounds)
```

#### 4.2.2 The Eleven Quality Pillars

| Dim | Name | Operational Definition | Signal Source | Type |
|-----|------|----------------------|---------------|------|
| v₁ | `functional_correctness` | LLM-estimated degree to which the artifact fulfills specified functional requirements | LLM-QA semantic assessment | **SE** |
| v₂ | `architectural_alignment` | LLM-estimated coherence with defined architectural patterns and principles | LLM-QA semantic assessment | **SE** |
| v₃ | `scalability_projection` | LLM-estimated projected capacity to grow under incremental load | LLM-QA semantic assessment | **SE** |
| v₄ | `security_risk` ↓ | Detected vulnerability and attack surface — deterministic (inverted: 1=no risk) | Bandit static analysis | GT |
| v₅ | `observability_coverage` | Extent of log, metric, and trace coverage of the system | Radon log density | GT |
| v₆ | `testability` | Cyclomatic complexity — ease of automated validation (inverted) | Radon CC | GT |
| v₇ | `maintainability` | Halstead volume and MI index — ease of understanding and modifying | Radon Halstead/MI | GT |
| v₈ | `technical_debt` ↓ | Debt ratio — accumulation of shortcuts (inverted) | Radon MI | GT |
| v₉ | `performance` | LLM-estimated efficiency in resource use and response latency | LLM-QA semantic assessment | **SE** |
| v₁₀ | `confidence` | Certainty level of the QA evaluation — consensus between SE and GT signals | Consensus SE ↔ GT | — |
| v₁₁ | `anomaly_score` ↓ | Deviation from expected historical patterns (inverted: 1=no anomaly) | Z-score vs baseline | — |

> ↓ = inverted: higher raw score = worse quality → normalized as (1 − raw)  
> **SE** = *supervisory estimator* — heuristic semantic signal produced by LLM-QA assessment. Provides decision-relevant information to the orchestrator; does not constitute an objective quality certificate. No universal ground truth.  
> **GT** = *verifiable ground truth* — deterministic static analysis output (Bandit / Radon). Reproducible and objectively measurable.

> **Epistemological note — LLM-sourced dimensions (v₁, v₂, v₃, v₉):** These four dimensions are computed via LLM-QA evaluation and do not have strong universal ground truth. They should be understood as **supervisory estimators** — heuristic semantic signals that provide decision-relevant information to the orchestrator, not objective quality certificates. Their value lies in enabling rapid cross-artifact and cross-temporal comparison within the same pipeline context, not in absolute calibration. Static analysis dimensions (v₄, v₆, v₇, v₈) are grounded in deterministic computation and have verifiable ground truth; the LLM dimensions are explicitly distinct in epistemological status.

#### 4.2.3 Formal Properties of V

The vector V must satisfy four formal properties to function as a valid cognitive interface:

- **P1 — Normalization:** `∀i : vᵢ ∈ [0,1]`. Enables comparison across contexts without scale distortion.
- **P2 — Approximate orthogonality:** Pillars are *supervisoriamente distinguishable* — each captures a distinct oversight concern that provides non-redundant decision-relevant signal to the orchestrator, even when dimensions partially correlate empirically (e.g. maintainability ↔ technical_debt). An artifact may simultaneously have high `functional_correctness` and low `maintainability` — this is diagnostic information, not contradiction. Strict statistical independence is not claimed; supervisory distinguishability is. This framing is analogous to Multidimensional Quality Metrics (MQM) in machine translation evaluation [cite: Lommel 2014], where dimensions correlate but are maintained separately for their differential diagnostic value. (See Section 7.6.1 for inter-dimension Spearman ρ analysis on the calibration corpus; any pair with ρ > 0.90 will receive explicit justification.)
- **P3 — Comparability:** The same vector semantics apply across agents, stages, and time instants. V_{agent₁, stage₁, t₁} is directly comparable to V_{agent₂, stage₂, t₂}.
- **P4 — Extensibility:** The base specification uses n=11; domain-specific dimensions may be added without altering the aggregation or inference architecture.

### 5.3 Layer 4 — The Cognitive Tensor

#### 4.3.1 Formal Definition

Let S = {design, build, test, deploy}, A = {ag₁...agₘ}, T_idx = {t₁...tₜ}. The TCO tensor:

```
T ∈ ℝⁿ × |S| × |A| × |T_idx|

T[d, i, j, k]  =  f_d( V_{i,j,k} )

where:  d  ∈ {1...n}   indexes the quality dimension
        i  ∈ S          indexes the pipeline stage
        j  ∈ A          indexes the generating agent
        k  ∈ T_idx      indexes the time instant
        f_d             aggregation function for dimension d
```

#### 4.3.2 Aggregation Functions

```
f₁ — Weighted mean (recommended for MVP and baseline):
   T[d,i,j,k] = Σᵣ wᵣ · vᵣ(i,j,k) / Σᵣ wᵣ
   Use when: pillars have relatively uniform importance.

f₂ — L2-norm reduction (for degradation sensitivity):
   T[d,i,j,k] = ‖V_{i,j,k}‖₂ / √n
   Use when: simultaneous drops across multiple dimensions must be
   detected with higher sensitivity than f₁.

f₃ — CP decomposition (for advanced pattern analysis):
   T ≈ Σᵣ λᵣ · u_d^(r) ⊗ u_i^(r) ⊗ u_j^(r) ⊗ u_k^(r)
   Use when: latent degradation patterns across agents and stages
   are the primary analytical objective [15].
```

#### 4.3.3 Tensor Slicing for the Orchestrator

| Slice Operation | Orchestration Question Answered |
|----------------|----------------------------------|
| `T[:, :, :, k_now]` | What is the complete state of the system right now? |
| `T[:, i, :, :]` | How has quality evolved across stage i over time? |
| `T[:, :, j, :]` | What is the quality trajectory of agent j across all stages? |
| `T[d, :, :, :]` | How does dimension d (e.g., security_risk) behave across the entire system? |
| `T[:, :, j₁, k] vs T[:, :, j₂, k]` | Are two agents producing conflicting quality profiles for the same stage? |

#### 4.3.4 Tensor Necessity: Why Not a Relational Table?

A likely critical objection is that `T[d,i,j,k]` could be equivalently stored in a relational table with columns `(dimension, stage, agent, cycle, value)`. The objection is technically correct for *storage* but incorrect for *inference*.

The case rests on two scenarios that are not reliably detectable without joint 4D indexing:

**S3 — Accumulative technical debt** requires the operation:

```
Δ_debt = T[d₈, :, :, k] − T[d₈, :, :, k−3]
```

This retrieves the v₈ slice across all stages and agents for two time indices simultaneously and computes their element-wise difference. In a relational table, the equivalent is a self-join on `(dimension='technical_debt') WHERE cycle IN (k, k-3)`, followed by grouping by `(stage, agent)`. The S3 scenario involves a degradation of −0.08 per cycle — invisible in any single-cycle snapshot, below the noise floor of per-artifact review. Only the temporal accumulation over 3 cycles (−0.24 total) crosses the alert threshold. A monitoring system that processes artifacts individually — even one that stores results in a table — cannot surface this pattern without explicitly constructing the temporal join. The tensor makes this operation first-class: the k axis is always present, always comparable, and the delta is always computable.

**S5 — Inter-agent conflict** requires the operation:

```
Ρ = max_{d} | T[d, i, j₁, k] − T[d, i, j₂, k] | > 0.30
```

This computes the element-wise difference between two agent slices across all 11 quality dimensions simultaneously, at the same stage and cycle. The equivalent SQL is a self-join on `(stage, cycle)` with a `CASE` expression for each of the 11 dimensions. Beyond the query complexity, the structural problem is deeper: per-artifact review systems process outputs of agent j₁ and agent j₂ in separate review sessions, without any mechanism for cross-referencing their quality profiles at the same pipeline coordinate. The conflict in S5 — a code agent generating stateless services while the architecture agent enforces stateful session constraints — is invisible to any reviewer who does not have both agents' outputs in scope simultaneously, indexed by the same `[stage, cycle]` coordinate.

The tensor's contribution is therefore not storage efficiency but **inference first-classness**: the shared index structure `[d,i,j,k]` is what allows the inference engine to express Δ and Ρ as direct tensor operations rather than as application-level logic that must reconstruct the coordinate system from relational data. S3 and S5 are the empirical proof that this first-classness is operationally necessary for the detection objectives of TCO — not a representational convenience.

**Empirical validation (Monte Carlo, n=1000).** A simulation of the S3 detection problem (trajectory [0.68, 0.60, 0.52, 0.44], evaluator noise σ=0.07, SNR per cycle=1.14) yielded: artifact-level detection rate 32.3% (single-cycle threshold 0.20); tensor Δ detection rate 66.9% (cumulative 3-cycle threshold 0.20). The detection gap of +34.6 percentage points confirms that individual artifact review is unreliable at this noise level. For S5, tensor Ρ detected 2 conflicting dimensions (security_risk: Δ=0.65, testability: Δ=0.50, both exceeding threshold 0.30); per-artifact review requires the reviewer to hold both agent outputs in working memory simultaneously to perform the equivalent comparison. Analysis script: `analysis/tensor_necessity.py`; figure: `analysis/figures/tensor_necessity_combined.png`.

### 5.4 Layer 5 — The Inference Model

```
I : T → { Ω, Δ, Ρ, Ξ }

Ω — Global system state:
   Ω = classify( mean(T[:,:,:,k_now]), θ ) → { stable | warning | critical }
   θ: configurable thresholds per dimension and composite score

Δ — Temporal trend analysis:
   Δ[d,i,j] = T[d,i,j,k] − T[d,i,j,k−1]
   Sustained Δ < 0 on technical_debt predicts future failure
   even when Ω = stable. This is the primary early-warning mechanism.

Ρ — Systemic risk detection:
   Ρ = detect_conflicts( T[:,:,j₁,k], T[:,:,j₂,k] )  ∀ j₁≠j₂
   Identifies inter-agent quality conflicts and correlated failures.

Ξ — Actionable recommendations:
   Ξ = recommend(Ω, Δ, Ρ) → { action₁, action₂, ... }
   Ranked by estimated impact: ∂Ω/∂action (gradient-based prioritization)
```

The trend analysis output **Δ is the most strategically valuable component** of the inference layer. Because it detects directional change rather than threshold breach, it enables intervention before quality reaches critical levels — addressing hypothesis H4 and providing the orchestrator with predictive rather than reactive information.

### 5.5 The Natural Cognitive Frontier (NCF): TCO as a Cognitive Positioning System

> **Definition — Natural Cognitive Frontier (NCF)**
>
> The Natural Cognitive Frontier is the level of abstraction at which a human agent operates with maximum cognitive efficiency: demand sufficient to activate real judgment, expressible in the human's natural language, without exceeding the capacity of working memory.
>
> TCO is architecturally designed to maintain the human orchestrator at the NCF by: (1) pre-processing system complexity into semantically interpretable state representations; (2) requiring active interpretive judgment as the mechanism of closure of the bidirectional loop; and (3) accepting policy responses in natural language — the most cognitively accessible supervisory interface for policy-level orchestration.

The NCF is grounded in three convergent theoretical bases:

- From **CLT [1]**: the NCF corresponds to the point where extraneous load is minimized and germane load is maximized.
- From **Vygotsky's Zone of Proximal Development [16]**: the tensor and inference layer function as scaffolding that elevates the human to their potential development level — systemic judgment and strategic decision-making, rather than line-by-line validation.
- From **Hybrid Cognitive Alignment theory [17]**: the NCF is the operating point where human and AI representations are mutually interpretable and the interaction loop produces emergent intelligence greater than either party alone.

**NCF Cognitive Demand Spectrum:**

| Without AI (all manual) | HITL Traditional (raw outputs) | TCO — NCF (target zone) |
|------------------------|-------------------------------|-------------------------|
| Low demand but low productive capacity. Human carries all production complexity. | Cognitive overload. Maximum extraneous load. Brain fry. High error rate from fatigue. | Calibrated demand. Active germane load. Natural language judgment. Maximum cognitive efficiency. |

#### 4.5.0 NCF Operationalization — Observable Proxies

The NCF is a theoretical construct and must be operationalized with measurable proxies to avoid appearing purely philosophical. The following table maps each NCF property to an observable variable and a concrete measurement instrument used in the TCO experiment. The experimental prediction is that participants in the TCO condition will show better outcomes on all four proxies than the control group.

| NCF Property | Observable Variable | Operational Measure | Instrument |
|---|---|---|---|
| Working memory not saturated | Working memory saturation | NASA Raw-TLX subscales: mental demand + frustration (lower = better) | Post-task Raw-TLX questionnaire |
| Sustained supervisory coherence | Supervisory coherence | Consistency of correction severity across same-type faults: σ(severity) per fault category | Structured correction log |
| Stable quality judgment | Cognitive stability | Variance of detection accuracy across task cycles T1→T4: σ(accuracy) over time | Scored task outcomes |
| Undivided attention | Attention fragmentation | Inter-quartile range of time-to-first-correction within each scenario: IQR(latency) | Interaction timer |

These proxies transform NCF from a design concept into a testable claim: the TCO architecture should produce lower Raw-TLX, more consistent corrections, more stable accuracy, and tighter latency distributions than raw-output HITL. Each proxy is captured automatically by the experiment infrastructure (interaction logger + NASA-TLX form) without additional participant burden.

#### 4.5.1 Why Natural Language is the Correct Interface

The policy injection mechanism accepts natural language as the primary input format for three reasons:

**First**, natural language is the domain in which human judgment is maximally expressive. A product manager, solution architect, or technical lead can articulate system goals, quality trade-offs, and priority shifts with richness that technical configuration interfaces cannot capture.

**Second**, natural language eliminates the technical barrier of entry to the orchestrator role. Understanding the business domain, quality objectives, and system goals is sufficient — broadening the pool of effective orchestrators beyond software engineers to product, architecture, and business leadership roles.

**Third**, the act of formulating a natural language policy is itself a cognitive act that mitigates automation bias. The orchestrator cannot passively accept a tensor state — they must read it, interpret it, and compose a response. This composition requires working memory engagement, contextual reasoning, and domain judgment: precisely the cognitive activities that HITL models are designed to preserve but that raw-output supervision suppresses through fatigue.

### 5.6 Layer 6 — The Bidirectional Orchestration Loop

```
TCO Bidirectional Orchestration Cycle:

  A_gen(k)  →  φ(A)  →  V_{i,j,k}  →  f(V)  →  T
                                                   ↓
                                            I(T) → {Ω, Δ, Ρ, Ξ}
                                                   ↓
                                    Human reads state at NCF
                                                   ↓
                            P_new = Orchestrate(Ξ, judgment, context)
                                                   ↓
                                    Agents ← P_new  [policy injection]
                                                   ↓
                         A_gen(k+1) = Generate(P_new)  [cycle k+1]
```

| Step | Actor | Action |
|------|-------|--------|
| ① Generation | AI Agents | Generate software artifacts (code, configs, designs, pipelines) |
| ② QA Evaluation | QA Agents | Analyze each artifact and produce raw metrics per quality pilar |
| ③ Vectorization φ | Motor TCO | Transform raw metrics into V ∈ [0,1]¹¹, normalized and comparable |
| ④ Aggregation f | Motor TCO | Aggregate vectors into tensor T[d,i,j,k] |
| ⑤ Inference I | Motor TCO | Produce {Ω, Δ, Ρ, Ξ}: global state, trends, risks, and recommendations |
| ⑥ Human Orchestration | Human (NCF) | Read tensor state, interpret, decide, formulate P_new in natural language |
| ⑦ Policy Injection | System | Inject P_new to generating agents — cycle restarts from ① |

The variable `P_new` is a natural language policy reformulation. Examples: *"Prioritize observability instrumentation in the build stage before the next deploy cycle"* or *"The security agent is flagging false positives on the OAuth2 module — add context about the stateless implementation before re-evaluating."* These instructions carry semantic richness that no automated system can generate.

---

## 6. Research Objectives and Hypotheses

### 6.1 Theoretical Reframing: Causal Observability for Human Governance

TCO-L2 is grounded in a theory of **causal observability for human governance**: the tensor T[d,i,j,k] makes the causal structure of multi-agent faults directly observable, reducing the cognitive cost of causal recovery and extending the set of faults that can be effectively governed.

The central claim has evolved from "cognitive load reduction" (a consequence) to the deeper mechanism:

```
T[d,i,j,k]
  → C directly readable via indexed access (d, i, j, k)
  → lower cost of causal recovery (vs. inferential reconstruction from raw)
  → better governance decisions (H2, H5)
  → lower cognitive load (H1 — mediator, not primary phenomenon)
  → advantage grows with causal complexity of the scenario (H_OBS — primary claim)
```

This reframing is validated against the **CAL Benchmark v1.0** (`Documentacion/CAL_Benchmark_v1.md`), which defines the **Causal Complexity Index (CCI)** — an objective, pre-registrable measure of how many tensor indices are required to read the causal structure C of each scenario directly from T.

| Scenario | CCI | Required tensor operation | Ω mechanism |
|---|---|---|---|
| S1 — Auth | 1 | Direct read: T[d=security_risk] | security_vulnerability |
| S4 — Deploy | 2 | Indexed read: T[d=observability, i=deploy] | omission_failure |
| S2 — Arch | 2 | Indexed read: T[d=arch_alignment, j=code_agent] | structural_violation |
| S5 — Conflict | 3 | Ρ: \|T[d,j₁,k] − T[d,j₂,k]\| | inter_agent_conflict |
| S3 — Debt | 4 | Δ: T[d=tech_debt, k=0..3] over 4 cycles | temporal_drift |

S3 and S5 are **critical theory tests**: they are the only scenarios requiring tensor operations (Δ and Ρ) with no equivalent in per-artifact review. If TCO were merely a better-formatted display, improvement would be uniform. H_OBS predicts ΔPIQ(S3,S5) >> ΔPIQ(S1,S4) — a specific, falsifiable prediction that only a causal observability framework can make.

### 6.2 General Objective

To develop, formalize, and empirically validate a framework for **causal observability** in multi-agent AI systems that enables humans to govern complex pipelines through cognitively efficient, tensor-based representations — extending the space of governable faults beyond what is achievable through per-artifact review, while reducing cognitive load and improving decision quality.

### 6.3 Specific Objectives

1. Define a formal multidimensional evaluation vector φ that produces normalized, semantically comparable quality representations of AI-generated software artifacts.
2. Establish a tensor aggregation function f that captures causal structure across quality dimensions, pipeline stages, agents, and time in a form amenable to direct human observation.
3. Design an inference model I that derives actionable causal attribution from the tensor (Ω, Δ, Ρ, Ξ), making the causal ontology Ω directly readable without inferential reconstruction.
4. Formalize the Natural Cognitive Frontier (NCF) as the level of abstraction at which causal recovery cost is minimized while governance capacity is maximized.
5. Empirically validate H_OBS and secondary hypotheses through a controlled comparative study with a functional MVP and a cross-paper pre-registered prediction (H_cross).

### 6.4 Research Hypotheses

**Primary hypothesis:**

| H | Hypothesis | Primary Metric | Test |
|---|-----------|----------------|------|
| **H_OBS** | TCO governance advantage is proportional to scenario CCI: ΔPIQ(S3,S5) >> ΔPIQ(S1,S4) | ΔPIQ × CCI interaction | Mixed ANOVA: Group × CCI |

**Secondary hypotheses:**

| H | Hypothesis | Primary Metric | Test |
|---|-----------|----------------|------|
| **H1** | TCO reduces cognitive load vs. traditional HITL | NASA Raw-TLX | Mann-Whitney U |
| **H2** | TCO improves detection precision + recall | Error detection rate, decision accuracy | Cohen's d ≥ 0.50 |
| **H4** | Tensor inference detects systemic risks before critical thresholds | Lead time to detection, time-to-correct | Wilcoxon |
| **H5** | NL policy injection produces higher-quality re-orchestration | PIQ score (LLM-Judge, κ ≥ 0.70) | Spearman ρ |

> **Note on H3:** The original H3 (scalability via concurrent workflows) is replaced by H_OBS, which captures the same scalability intuition more precisely: TCO does not merely scale supervision uniformly — it extends governance to fault classes (high-CCI) that are not supervisable at all with traditional HITL.

**Cross-paper hypothesis (pre-registered before RCT data collection):**

| H | Hypothesis | Metric | Source |
|---|---|---|---|
| **H_cross** | SID_C*(s) predicts ΔPIQ(s) across S1–S5 | r_Spearman(SID_C*, ΔPIQ) > 0 | Paper 1 (SID Study) → Paper 2 (RCT) |

H_cross is computed from Paper 1 (SID Study on CAL Benchmark S1–S5) and pre-registered before Paper 2 data collection begins. This converts the two-paper program from parallel corroboration to sequential prediction-and-confirmation.

### 6.5 Statistical Analysis Plan

| Hypothesis | Test | Effect Size | Notes |
|------------|------|-------------|-------|
| H_OBS | Mixed ANOVA: Group × CCI | Partial η² (interaction) | Primary — H_OBS is the falsifying test |
| H1 | Mann-Whitney U (two-tailed) | Cohen's d | |
| H2 | Mann-Whitney U (two-tailed) | Cohen's d | |
| H4 | Wilcoxon signed-rank | Cohen's d | ARIMA on S3 temporal trajectory |
| H5 | Spearman ρ + linear regression | ρ + β | PIQ → Δ_vector |
| All | ANCOVA | Partial η² | Covariates: experience + pre-test + AI tool familiarity (0–4) |
| All | Bonferroni correction | α_eff = 0.01 | Applied uniformly across 5 hypotheses |
| H_cross | Spearman ρ across 5 scenarios | ρ coefficient | Pre-registered; computed after Paper 1 SID values are fixed |

---

## 7. Experimental Design and MVP — Phase 3

### 7.1 Experimental Design Overview

**Design:** Between-subjects controlled comparative study with single-blind randomization. Both groups supervise the same multi-agent pipeline in the same controlled environment. The only independent variable is the supervision interface.

**Participants:** Minimum n=40 software engineers with ≥2 years of code review experience, no prior exposure to TCO. Sample size calculated to detect medium effect (Cohen's d ≥ 0.5) with α = 0.05 and power = 0.80. Participants are randomly assigned to groups, stratified by experience level.

**Groups:**

| Group | Interface | Correction Mechanism |
|-------|-----------|---------------------|
| **Control — Traditional HITL** | Raw outputs: code, logs, configs, diagrams. No vector or tensor assistance. Standard IDE + terminal. | Direct artifact editing |
| **Experimental — TCO** | TCO dashboard: vector V, tensor slices, {Ω,Δ,Ρ,Ξ}. No access to raw outputs. | Natural language policy injection |

#### 7.1.1 Control Group Environment — Standardized Interface

To ensure that observed between-group differences reflect the supervision interface and not interface quality disparities, the control group environment is explicitly standardized as the **ControlGroupViewer**: a read-only multi-tab code viewer presenting artifacts (Python source, YAML configs, architecture markdown, CI/CD logs) with syntax highlighting but no editing capability, paired with a structured **correction form** containing a free-text field ("Describe the issue and your correction") and a severity classifier (Low / Medium / High). No direct artifact modification is permitted; corrections are recorded as text entries logged to the interaction database.

This design equalizes the input modality between groups — both write a text description of their response — while preserving the raw-output information format that defines the Traditional HITL condition. The ControlGroupViewer is implemented with identical layout dimensions, font size, and timer display as the TCO dashboard, eliminating interface ergonomics as a confound.

**Session Protocol per Participant:**

1. **Orientation (30 min):** Environment familiarization. Experimental group: TCO dashboard training. Control group: ControlGroupViewer navigation training.
2. **Warm-up (15 min):** Practice task on a separate warm-up pipeline (microservice with no injected faults) to eliminate novelty effect. Both groups use their assigned interface.
3. **Experimental block (90 min total, time-boxed per task):** T1: 25 min · T2: 20 min · T3: 15 min · T4: 30 min. Visible countdown timer displayed to all participants. Task closes automatically at time limit; partial responses are captured and scored with available data.
4. **Raw-TLX administration** immediately post-T2 (intra-session baseline) and immediately post-T4 (final). Six subscales reported individually and as unweighted composite.
5. **Semi-structured interview (15 min).**

> **Why Raw-TLX over standard NASA-TLX:** Recent literature indicates that global NASA-TLX scores calculated with the traditional pairwise weighting method may be mathematically problematic [Bolton et al., 2023]. Raw-TLX — without pairwise weighting — improves experimental validity for between-condition comparisons. The six subscales are reported individually and as an unweighted composite.

### 7.2 The Four Tasks

**T1 — Error Detection:** Three artifacts with planted faults of different type and severity. Participants must identify how many errors exist, locate them, and classify their severity. Scoring: number of errors detected, false positives generated, and time employed.

**T2 — Risk Assessment:** Pipeline in progressive degradation state (sustained negative Δ on three dimensions). Participants assess the current risk level on a 5-point scale and justify their evaluation. Measured: correlation between participant perception and real tensor state (ground truth).

**T3 — Deployment Decision:** High-pressure scenario: Ω = warning, two active inter-agent conflicts. Participants decide: proceed, block, or proceed with restrictions. Measured: accuracy against expert ground truth and justification quality.

**T3 expert panel protocol:** Ground truth for the deployment decision is established through a two-expert independent panel (n=2 senior software engineers with ≥5 years CI/CD experience, external to the study). Both experts evaluate each T3 scenario independently and produce a consensus decision with documented justification. In case of panel disagreement, a third expert arbiter resolves. Cohen's κ between the two primary experts must be ≥ 0.80 before use in the experiment; if κ < 0.80, the scenario is revised and re-evaluated. Expert panel convenes in Week 3 alongside scenario validation.

**T4 — Re-orchestration (H5 activation):** After identifying a fault in T1 or T2, participants formulate a correction instruction. Control group: writes directly in code/config using the ControlGroupViewer correction form. Experimental group: writes a natural language policy in the TCO injection field. The system applies the policy automatically and the vector delta is measured.

**T4 Δ_post measurement window:** Policy effect is measured across cycles k+1, k+2, and k+3 following injection (3-cycle window). The primary metric is the maximum Δ observed within the window per affected dimension. Mean Δ over the window is reported as a secondary metric. If no statistically significant change is detected within the 3-cycle window, the policy is recorded as ineffective (Δ_post = 0) for H5 scoring. The 3-cycle window is pre-validated in the pilot (Week 5) to confirm it captures the full policy propagation lag of the simulated pipeline.

### 7.3 The Five Experimental Scenarios — Ground Truth Definition

The fault injection methodology follows established software engineering research protocols [21]. Each scenario is constructed from anonymized real-world artifacts (Apache ecosystem open-source projects) with specifically introduced and documented faults.

| Scenario | Fault Type | Pillar Affected | Severity | GT Vector Delta | Detectable via |
|----------|-----------|-----------------|----------|-----------------|----------------|
| **S1 — Auth** | SQL injection in auth module | v₄ security_risk, v₁₁ anomaly | HIGH | v₄: 0.82→0.21, v₁₁: 0.90→0.31 | Raw: code reading · TCO: red radar + Ρ alert |
| **S2 — Arch** | Circular dependency violating hexagonal architecture | v₂ arch_alignment, v₇ maintainability | MEDIUM | v₂: 0.79→0.38, v₇: 0.71→0.45 | Raw: expert knowledge required · TCO: tensor slice T[:,i,:,:] |
| **S3 — Debt** | Three cycles of accumulating cyclomatic complexity | v₈ technical_debt, v₃ scalability | LOW (progressive) | v₈: 0.68→0.44 (Δ = −0.08/cycle) | Raw: not reliably detectable · TCO: Δ trend view (H4 test) |
| **S4 — Deploy** | Kubernetes config disabling Prometheus metric export | v₅ observability, v₉ performance | MEDIUM | v₅: 0.85→0.29, v₉: 0.77→0.51 | Raw: full YAML review · TCO: Ξ alert + recommendation |
| **S5 — Conflict** | Code agent (stateless auth) vs. Arch agent (stateful sessions) | v₂ inter-agent diff = 0.41 | HIGH | Ρ conflict active, Ω = warning | Raw: not reliably detectable in isolation · TCO only (exclusive H4 test) |

> **Note on S3 and S5:** These scenarios are not reliably detectable through individual artifact review. S3 requires cross-temporal correlation of three independent commits; S5 requires simultaneous comparison of two agent outputs on the same module. Both are naturally surfaced by the TCO tensor. This asymmetry is the most direct test of the framework's unique detection capabilities.

**S3 Session Pre-loading Protocol:** S3 requires three prior cycles of accumulated complexity degradation to be visible as a trend (Δ < 0 over three consecutive k values). The pipeline pre-runs S3 with the fault injected automatically before each participant session begins. The three pre-loaded cycles are executed by the real agent pipeline and stored in the database with timestamps set to t−90min, t−60min, and t−30min relative to session start, ensuring the Δ trend is visible in the temporal heatmap from session opening. Pre-loaded data are verified against ground truth delta (v₈: 0.68→0.44, Δ = −0.08/cycle) before each session via automated integrity check. This pre-loading procedure is applied identically to both groups; the control group sees the raw code artifacts from each pre-loaded cycle in their multi-tab viewer.

### 7.4 Policy Injection Quality (PIQ) Protocol — H5

The PIQ evaluation uses a triangulated approach validated by the LLM-as-a-judge literature [22, 23].

**PIQ Rubric — three dimensions, scale 1–5:**

| Dimension | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|-----------|----------|--------------|---------------|
| **Clarity** | Vague or contradictory with system state | Interpretable but imprecise | Unambiguous, specific component and constraint identified |
| **Systemic specificity** | Generic technical instruction disconnected from tensor state | References one system dimension | Explicitly cites vector dimensions, agents, or tensor conflicts |
| **Projected impact** | Policy would not produce measurable Δ | Partial improvement on target pillars | Correct delta on affected dimensions, no negative side effects |

**Three measurement instruments (triangulation):**

1. **Vector Δ (objective — automatic):** `Δ_post = V(k+1) − V(k)` measured per dimension affected by P_new. Ground truth comparison.
2. **PIQ-Rubric (subjective — 2 independent expert annotators):** Blind evaluation of 40 policy samples (20% of total). Inter-rater reliability: Cohen's κ target ≥ 0.70 per dimension [22].
3. **LLM-Judge (semi-automatic):** Claude evaluator with few-shot prompt including rubric + reference examples. Validated: κ ≥ 0.70 vs. human experts before deployment [23].

> **LLM-Judge validation note:** Recent research confirms that providing both reference answers and score descriptions is crucial for reliable LLM-based evaluation. Omitting either significantly degrades alignment with human judgment [24]. The PIQ prompt template includes all three rubric dimensions with calibrated examples for each score level.

### 7.5 Statistical Analysis Plan

| Hypothesis | Test | Justification | Effect Size |
|------------|------|---------------|-------------|
| H1–H4 | Mann-Whitney U (two-tailed) | Non-normal distribution expected in workload scores; n=20/group | Cohen's d, reported mandatory |
| H5 | Linear regression PIQ → Δ_vector | Continuous predictor and outcome; R² > 0.40 = support | Pearson r + β coefficient |
| All | ANCOVA | Control for years of experience + pre-test technical score | Reported as partial η² |
| Multiple comparison | Bonferroni correction | α_effective = 0.01 per comparison (5 hypotheses) | Applied uniformly |
| H4 (S3 scenario) | ARIMA time series | Detect degradation pattern pre-threshold in tensor Δ | Lead time Δ in cycles |

**Statistical significance:** p < 0.05 (Bonferroni-adjusted p < 0.01). Results reported with and without correction. Effect size is reported for all tests regardless of p-value.

### 7.6 Threats to Validity and Mitigations

| Threat | Type | Mitigation |
|--------|------|------------|
| **Hawthorne effect** | Internal | Single-blind design: participants don't know which group is "experimental" — both presented as "evaluation of two supervision interfaces" |
| **TCO learning curve** | Internal | 30-min training session before experiment. Intra-session learning tracked (T1 vs T4 time). 30-day voluntary follow-up in real environment for longitudinal data |
| **Ecological validity** | External | Scenarios constructed from anonymized real CI/CD pipelines. Fault types replicate real defect distributions documented in Apache ecosystem research |
| **H5 subjectivity** | Construct | Triangulation of three metrics (Vector Δ, PIQ-Rubric, LLM-Judge). κ < 0.60 for any dimension → excluded from main analysis, reported as limitation |
| **Experience confound** | Internal | ANCOVA controlling for years of experience + pre-test score. Stratified randomization at assignment |
| **QA evaluation circularity** | Construct | The vector φ produced by the QA LLM agent is the basis of both the experimental instrument (dashboard) and the dependent variable (vector Δ). Agent inconsistency contaminates both simultaneously. Mitigation: pre-experiment validation of QA agent output against static analysis ground truth across all 5 scenarios (Week 3). Required threshold: Spearman ρ ≥ 0.75 between QA-LLM and static metrics for dimensions v₄, v₆, v₇, v₈. If ρ < 0.75 for any dimension, QA agent prompt is revised before proceeding. Validation report archived as Open Science artifact. |
| **Task order fatigue asymmetry** | Internal | Fixed T1→T4 ordering means control group participants arrive at T4 with higher cumulative cognitive load from raw output review in T1/T2, biasing H5 in favor of TCO. Mitigation: (a) time-boxing prevents runaway time on early tasks; (b) Raw-TLX is administered post-T2 and post-T4 independently to quantify intra-session fatigue trajectory; (c) T4 results are analyzed controlling for T1+T2 combined completion time as a fatigue proxy covariate in ANCOVA. |

#### 7.6.1 φ Calibration Protocol — Formal No-Go Gate

The QA evaluation circularity threat (see table above) is the single highest-risk validity issue in the TCO experimental design, because a low-quality vectorizer φ simultaneously degrades the experimental instrument (the dashboard) and the dependent variable (vector Δ). To ensure this risk is managed with quantitative rigor, φ validation is formalized here as a **pre-pilot no-go gate** that must be passed before Week 5 (pilot) begins.

**Calibration corpus:** 12 synthetic artifacts with known ground-truth quality values, constructed to cover all five experimental scenarios (S1–S5) with their documented ground-truth vectors. The corpus is generated by `src/pipeline/scenario_preloader.py` and stored at `src/experiment/phi_calibration/corpus/corpus.json` (generated 2026-05-20). Each entry contains: `artifact_id`, `scenario`, `cycle`, `artifact_type`, raw `code`, `context`, `fault_present`, and `ground_truth` metadata.

| Scenario | Artifacts | Ground Truth Vectors |
| --- | --- | --- |
| S1 — SQL injection | 2 (clean + faulty) | v₄_clean ≈ 0.90, v₄_faulty ≈ 0.20 (bandit B608+B324) |
| S2 — Circular dependency | 2 (clean + faulty) | v₂_clean ≈ 0.85, v₂_faulty ≈ 0.20 (LLM-scored arch violation) |
| S3 — 4-cycle debt | 4 (k=0..3) | v₈ ∈ {0.68, 0.60, 0.52, 0.44} per cycle (−0.08/cycle, CC: 2→5→8→12) |
| S4 — Missing Prometheus | 2 (clean + faulty) | v₅_clean ≈ 0.85, v₅_faulty ≈ 0.15 |
| S5 — Inter-agent conflict | 2 (security_agent vs. code_agent) | v₄Δ ≈ 0.65, v₆Δ ≈ 0.50 (exceeds Ρ threshold of 0.30) |

Of the 12 artifacts, 8 are `python_code` and are eligible for Spearman ρ computation against radon/bandit ground truth. The 4 YAML artifacts (S2, S4) contribute to LLM calibration on v₂ and v₅ only. Clean artifacts (fault_present = false) serve as positive controls to prevent calibration bias toward failure cases.

**Validation procedure:** For each artifact in the corpus, run both φ's static analysis pipeline (radon + bandit) and the LLM-QA evaluator independently. Compute Spearman ρ between the two sources for each of the four comparable dimensions:

| Dimension | LLM Field | Static Source | No-Go Threshold |
|-----------|-----------|---------------|-----------------|
| v₄ `security_risk` | `semantic_security` | Bandit `weighted_severity` | ρ < 0.75 |
| v₆ `testability` | `semantic_testability` | Radon `1 − cyclomatic_norm` | ρ < 0.75 |
| v₇ `maintainability` | `semantic_maintainability` | Radon `maintainability_index` | ρ < 0.75 |
| v₈ `technical_debt` | `semantic_debt_assessment` | Radon `debt_ratio` | ρ < 0.75 |

**Go/no-go decision rule:** If Spearman ρ ≥ 0.75 for all four dimensions → **GO** (proceed to Week 5 pilot). If ρ < 0.75 for any dimension → **NO-GO**: suspend experiment execution, revise the QA agent prompt for the failing dimension(s), expand the normalization bounds in `radon_runner.py` or `bandit_runner.py` if the static analysis source is at fault, and re-run calibration within one week.

**Archival:** The calibration report (ρ per dimension with 95% confidence intervals, scatter plots, outlier artifacts) is archived as an Open Science artifact and cited in the paper's Methods section. This documentation is required for CHI submission under the Reproducibility Appendix.

**Implementation:** The calibration is executed by `src/experiment/phi_calibration/phi_calibration.py` (see DT-021). The no-go decision is computed automatically and logged with a `PASS`/`FAIL` verdict per dimension.

**Inter-dimension correlation analysis (DT-025):** In addition to the Spearman ρ no-go gate, `phi_calibration.py` computes pairwise Spearman ρ between all static quality dimensions (v₄, v₆, v₇, v₈) on the corpus. The top-3 most correlated pairs are reported. Any pair with ρ > 0.90 requires explicit justification in the paper that supervisory distinguishability is maintained despite empirical correlation (see Section 4.2.3, P2). The MQM analogy applies: as in machine translation evaluation [cite: Lommel 2014], correlated dimensions may be retained when they serve distinct diagnostic functions for the orchestrator. Results will be included in the Methods section upon φ calibration execution (pending ANTHROPIC_API_KEY for static analysis pipeline).

**LLM-QA Evaluator Reliability Results (DT-024 — 2026-05-28):** The evaluator variance analysis was executed on the calibration corpus using `analysis/evaluator_reliability.py`. All 8 `python_code` artifacts in the corpus were evaluated n=10 times each (80 API calls total) via OpenRouter (claude-sonnet-4-6, max_tokens=2048). Results:

| Artifact | max σ (SE dims) | Verdict |
|----------|----------------|---------|
| s1_auth_clean | 0.036 | PASS |
| s1_auth_faulty | 0.050 | PASS |
| s3_processor_k0 | 0.026 | PASS |
| s3_processor_k1 | 0.021 | PASS |
| s3_processor_k2 | 0.031 | PASS |
| s3_processor_k3 | 0.028 | PASS |
| s5_auth_security_agent | 0.044 | PASS |
| s5_auth_code_agent | — | PASS |

All SE dimensions (v₁, v₂, v₃, v₉) satisfy σ < 0.05 across all artifacts. **The LLM-QA evaluator is confirmed reliable for use in the experiment.** Note: an earlier run with max_tokens=1024 produced spurious failures due to JSON truncation in the `reasoning` field — not evaluator instability. The entropy analysis (H > 0.8 nats for all dimensions) is an expected result given the corpus design: clean vs. faulty artifact pairs span the full quality range by construction, producing high score variance across artifacts (not within the same artifact). Full report: `analysis/figures/evaluator_reliability_report.json`.

> **Implementation status (2026-05-20):** Corpus generated and available. Pipeline (`src/pipeline/graph.py`), fault injector, and all five scenario modules (S1–S5) are fully implemented. `phi_calibration.py` requires `ANTHROPIC_API_KEY` to score LLM dimensions — ready for execution in Week 3.

### 7.7 10-Week Experiment Timeline

| Week | Phase | Activity | Deliverable |
|------|-------|----------|-------------|
| 1–2 | Build | TCO engine: φ (static analysis + LLM-QA), f₁ (weighted mean), I (threshold + trend detection) | REST API functional: `/vector`, `/tensor`, `/inference`, `/policy/inject` |
| 3 | Build + Validate | Simulated pipeline: 4 LLM agents + 1 QA agent. 5 scenarios with planted faults. **QA agent validation**: Spearman ρ ≥ 0.75 between QA-LLM and static analysis ground truth for v₄, v₆, v₇, v₈. **T3 expert panel**: 2 external senior engineers establish deployment decision ground truth (κ ≥ 0.80). Scenario ground truth documentation validated. *(Pipeline + scenarios + corpus.json implemented 2026-05-20. φ calibration run pending ANTHROPIC_API_KEY.)* | Validated pipeline + scenarios. QA agent accuracy report. T3 expert panel agreement record. |
| 4 | Build | Orchestration dashboard: radar chart, tensor heatmap, inference panel, policy injection field | MVP complete |
| 5 | Pilot | Internal pilot (n=4, 2 per group). Usability issues detected and protocol adjusted | Final experimental protocol |
| 6 | Calibration | LLM-Judge calibration for H5. κ validation against 2 human expert annotators | PIQ rubric validated (κ ≥ 0.70) |
| 7–8 | Experiment | Full experiment execution (n=40). Raw-TLX + interaction logs + interview recordings | Raw data + complete logs |
| 9 | Analysis | Statistical analysis (Mann-Whitney, ANCOVA, ARIMA, PIQ regression) | Preliminary results |
| 10 | Writing | Results section + Discussion section + paper finalization | Section 7 (Results) complete |

---

## 8. Software Architecture and Implementation Roadmap

### 8.1 System Overview

The MVP implements the complete TCO bidirectional loop as three decoupled services communicating via REST API. The architecture is designed for observability, reproducibility, and incremental deployment.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TCO MVP — Component Map                      │
├──────────────────┬──────────────────┬───────────────────────────────┤
│  COMPONENT A     │  COMPONENT B     │  COMPONENT C                  │
│  Simulated       │  TCO Engine      │  Orchestration                │
│  Pipeline        │  (Core)          │  Dashboard                    │
│                  │                  │                               │
│  4 LLM Agents    │  φ Vectorizer    │  Radar Chart (V)              │
│  1 QA Agent      │  f Aggregator    │  Tensor Heatmap               │
│  5 Scenarios     │  I Inference     │  Inference Panel              │
│  Fault Injector  │  REST API        │  Policy Injection             │
│                  │  TimescaleDB     │  History Log                  │
└──────────────────┴──────────────────┴───────────────────────────────┘
         ↓ artifacts + metrics          ↑ policy P_new (NL)
              REST API (JSON)                REST API (JSON)
```

### 8.2 Component A — Simulated Pipeline

**Technology stack:** Python 3.11 + LangGraph for agent orchestration + Claude API (claude-sonnet-4-6)

**Agent definitions:**

```python
# agents/code_agent.py
class CodeAgent:
    """Generates Python microservice code from specifications."""
    role = "code_generator"
    model = "claude-sonnet-4-6"
    system_prompt = """You are a Python microservice developer.
    Generate production-quality code following the specifications provided.
    Apply the active policy P_new if present in context."""

# agents/arch_agent.py  
class ArchAgent:
    """Designs system architecture and produces ADR documents."""
    role = "architecture_designer"
    model = "claude-sonnet-4-6"

# agents/deploy_agent.py
class DeployAgent:
    """Generates Kubernetes manifests and CI/CD pipeline configs."""
    role = "deployment_configurator"
    model = "claude-sonnet-4-6"

# agents/test_agent.py
class TestAgent:
    """Generates pytest test suites and coverage configurations."""
    role = "test_generator"
    model = "claude-sonnet-4-6"

# agents/qa_agent.py
class QAAgent:
    """Evaluates artifacts and produces raw quality metrics per pilar."""
    role = "quality_evaluator"
    model = "claude-sonnet-4-6"
    output_schema = "EvaluationMetrics"  # structured output
```

**Fault injector:**

```python
# pipeline/fault_injector.py
SCENARIOS = {
    "S1_auth": {
        "target_agent": "code_agent",
        "target_artifact": "auth_module.py",
        "fault_type": "sql_injection",
        "injection": "query = f\"SELECT * FROM users WHERE id = {user_input}\"",
        "gt_vector_delta": {"security_risk": -0.61, "anomaly_score": -0.59}
    },
    "S2_arch": {
        "target_agent": "arch_agent",
        "target_artifact": "architecture.md",
        "fault_type": "circular_dependency",
        "injection": "OrderService → PaymentService → OrderService (circular)",
        "gt_vector_delta": {"architectural_alignment": -0.41, "maintainability": -0.26}
    },
    "S3_debt": {
        "target_agent": "code_agent",
        "cycles": 3,
        "fault_type": "complexity_accumulation",
        "delta_per_cycle": {"technical_debt": -0.08, "scalability_projection": -0.04}
    },
    "S4_deploy": {
        "target_agent": "deploy_agent",
        "target_artifact": "k8s-deployment.yaml",
        "fault_type": "missing_metrics_export",
        "injection": "# prometheus.io/scrape: 'true'  ← commented out",
        "gt_vector_delta": {"observability_coverage": -0.56, "performance": -0.26}
    },
    "S5_conflict": {
        "agents": ["code_agent", "arch_agent"],
        "fault_type": "inter_agent_conflict",
        "conflict": "code=stateless_auth vs arch=stateful_sessions",
        "gt_rho_delta": 0.41
    }
}
```

**LangGraph orchestration:**

```python
# pipeline/graph.py
from langgraph.graph import StateGraph

def build_pipeline(scenario_id: str, policy: str = None):
    graph = StateGraph(PipelineState)
    
    graph.add_node("code_gen", CodeAgent(policy=policy).run)
    graph.add_node("arch_design", ArchAgent(policy=policy).run)
    graph.add_node("deploy_config", DeployAgent(policy=policy).run)
    graph.add_node("test_gen", TestAgent(policy=policy).run)
    graph.add_node("qa_eval", QAAgent().run)
    graph.add_node("fault_inject", FaultInjector(scenario_id).run)
    
    graph.add_edge("code_gen", "fault_inject")
    graph.add_edge("arch_design", "fault_inject")
    graph.add_edge("fault_inject", "qa_eval")
    graph.add_edge("qa_eval", END)
    
    return graph.compile()
```

### 8.3 Component B — TCO Engine (Core)

**Technology stack:** Python 3.11 + FastAPI + PostgreSQL 16 + Redis (tensor cache) + radon + pylint + Bandit + Coverage.py

> **Stack decision rationale:** SonarQube Community Edition requires a dedicated Docker server with ~2 days of setup overhead. For the MVP and experiment (n=40), radon provides equivalent cyclomatic complexity and Halstead metrics natively in Python without a server. TimescaleDB is the upgrade path for production deployment after the experiment; the schema is designed for zero-destructive migration (`SELECT create_hypertable(...)` on existing tables). Redis caches `/tensor/current` responses with a 30-second TTL, eliminating redundant aggregation recomputation across concurrent dashboard views. Artifact evaluations are also cached by SHA-256 hash of the artifact content — identical code is not re-evaluated, reducing Claude API costs by an estimated 40–60% in repeated cycle scenarios.

**Project structure:**

```
tco_engine/
├── api/
│   ├── routes/
│   │   ├── vector.py          # POST /vector/compute
│   │   ├── tensor.py          # GET /tensor/current, GET /tensor/slice
│   │   ├── inference.py       # GET /inference/latest
│   │   └── policy.py          # POST /policy/inject
│   └── main.py                # FastAPI app + CORS + logging
├── core/
│   ├── vectorizer.py          # φ: Artifact → V
│   ├── aggregator.py          # f: {V} → T
│   ├── inference_engine.py    # I: T → {Ω, Δ, Ρ, Ξ}
│   └── policy_processor.py   # P_new → agent instructions
├── db/
│   ├── models.py              # SQLAlchemy models + Redis cache helpers
│   ├── queries.py             # Time-indexed DB operations
│   └── migrations/
├── static_analysis/
│   ├── radon_runner.py        # v₆, v₇, v₈: cyclomatic complexity, Halstead, debt ratio
│   ├── bandit_runner.py       # v₄ security_risk: CVSS-equivalent vulnerability scan
│   └── coverage_runner.py    # v₆ testability: branch + line coverage ratio
└── tests/
    ├── test_vectorizer.py
    ├── test_aggregator.py
    └── test_inference.py
```

**Vectorizer — φ implementation:**

```python
# core/vectorizer.py
from dataclasses import dataclass
from typing import Dict
import numpy as np

@dataclass
class EvaluationVector:
    functional_correctness: float    # v₁
    architectural_alignment: float   # v₂
    scalability_projection: float    # v₃
    security_risk: float             # v₄ (inverted)
    observability_coverage: float    # v₅
    testability: float               # v₆
    maintainability: float           # v₇
    technical_debt: float            # v₈ (inverted)
    performance: float               # v₉
    confidence: float                # v₁₀
    anomaly_score: float             # v₁₁ (inverted)
    
    def to_array(self) -> np.ndarray:
        return np.array([
            self.functional_correctness, self.architectural_alignment,
            self.scalability_projection, self.security_risk,
            self.observability_coverage, self.testability,
            self.maintainability, self.technical_debt,
            self.performance, self.confidence, self.anomaly_score
        ])

class Vectorizer:
    """φ: Artifact → V ∈ [0,1]¹¹"""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {k: 1.0 for k in range(11)}
        self.radon  = RadonRunner()      # cyclomatic complexity, Halstead, debt ratio
        self.bandit = BanditRunner()     # security vulnerability scan
        self.qa_llm = QAAgent()          # LLM-based evaluation for semantic pillars
        self.cache  = ArtifactCache()    # Redis: keyed by SHA-256 of artifact content
    
    def vectorize(self, artifact: Artifact, historical_baseline: np.ndarray = None) -> EvaluationVector:
        # Cache check: identical artifact content → return cached vector
        cache_key = artifact.content_hash()  # SHA-256
        if cached := self.cache.get(cache_key):
            return cached
        
        # Static analysis metrics (objective — radon + bandit)
        radon_metrics   = self.radon.analyze(artifact)   # cyclomatic, Halstead, debt
        security_metrics = self.bandit.scan(artifact)    # vulnerability count, severity
        
        # LLM-QA evaluation (semantic pillars)
        llm_eval = self.qa_llm.evaluate(artifact)
        
        # Confidence: consensus between static analysis and LLM-QA
        confidence = self._compute_consensus(radon_metrics, llm_eval)
        
        # Anomaly: Z-score vs historical baseline
        anomaly = self._compute_anomaly(artifact, historical_baseline)
        
        vector = EvaluationVector(
            functional_correctness  = self._normalize(llm_eval.test_pass_rate),
            architectural_alignment = self._normalize(llm_eval.pattern_compliance),
            scalability_projection  = self._normalize(llm_eval.scalability_score),
            security_risk           = 1 - self._normalize(security_metrics.weighted_severity),
            observability_coverage  = self._normalize(radon_metrics.log_coverage),
            testability             = self._normalize(radon_metrics.cyclomatic_complexity, invert=True),
            maintainability         = self._normalize(radon_metrics.halstead_volume, invert=True),
            technical_debt          = 1 - self._normalize(radon_metrics.debt_ratio),
            performance             = self._normalize(llm_eval.performance_score),
            confidence              = confidence,
            anomaly_score           = 1 - anomaly
        )
        self.cache.set(cache_key, vector)
        return vector
    
    def _normalize(self, value: float, invert: bool = False) -> float:
        """Min-max normalization to [0,1]"""
        normalized = max(0.0, min(1.0, value))
        return 1 - normalized if invert else normalized
    
    def _compute_consensus(self, static, llm) -> float:
        """Inter-rater agreement between static analysis and LLM-QA"""
        overlap_dims = ['functional_correctness', 'maintainability', 'testability']
        agreements = [abs(getattr(static, d) - getattr(llm, d)) for d in overlap_dims]
        return 1 - np.mean(agreements)
    
    def _compute_anomaly(self, artifact, baseline) -> float:
        """Z-score of current vector vs historical baseline"""
        if baseline is None:
            return 0.0
        current = np.array(artifact.raw_metrics)
        z_scores = np.abs((current - baseline.mean) / (baseline.std + 1e-8))
        return float(np.clip(np.mean(z_scores) / 3.0, 0, 1))
```

**Aggregator — f implementation:**

```python
# core/aggregator.py
import numpy as np
from typing import List

class TensorAggregator:
    """f: {V_{i,j,k}} → T ∈ ℝⁿˣˢˣᵃˣᵗ"""
    
    STAGES = ["design", "build", "test", "deploy"]
    N_DIMS = 11
    
    def __init__(self, aggregation_fn: str = "f1_weighted_mean"):
        self.fn = aggregation_fn
    
    def aggregate(self, vectors: List[VectorEntry]) -> np.ndarray:
        """Build or update tensor from incoming vector batch."""
        n_stages = len(self.STAGES)
        n_agents = max(v.agent_idx for v in vectors) + 1
        n_time   = max(v.time_idx for v in vectors) + 1
        
        T = np.zeros((self.N_DIMS, n_stages, n_agents, n_time))
        
        for v in vectors:
            d_slice = v.vector.to_array()
            i, j, k = v.stage_idx, v.agent_idx, v.time_idx
            T[:, i, j, k] = self._apply_fn(d_slice)
        
        return T
    
    def _apply_fn(self, v: np.ndarray) -> np.ndarray:
        if self.fn == "f1_weighted_mean":
            return v  # weights are applied at vectorization level
        elif self.fn == "f2_l2_norm":
            return np.full(self.N_DIMS, np.linalg.norm(v) / np.sqrt(self.N_DIMS))
        else:
            return v
    
    def slice(self, T: np.ndarray, **kwargs) -> np.ndarray:
        """
        Named slicing operations:
        - current_snapshot(k):  T[:,:,:,k]
        - stage_evolution(i):   T[:,i,:,:]
        - agent_trajectory(j):  T[:,:,j,:]
        - dimension_global(d):  T[d,:,:,:]
        """
        slices = {k: (slice(None) if v is None else v) for k, v in kwargs.items()}
        return T[slices.get('d'), slices.get('i'), slices.get('j'), slices.get('k')]
```

**Inference Engine — I implementation:**

```python
# core/inference_engine.py
from dataclasses import dataclass
from typing import List, Literal
import numpy as np

@dataclass
class InferenceResult:
    omega: Literal["stable", "warning", "critical"]
    omega_score: float
    delta: List[TrendEntry]       # Δ per dimension
    rho: List[ConflictEntry]      # Inter-agent conflicts
    xi: List[RecommendationEntry] # Prioritized actions

class InferenceEngine:
    """I: T → {Ω, Δ, Ρ, Ξ}"""
    
    THRESHOLDS = {
        "stable":   0.70,
        "warning":  0.50,
        "critical": 0.00   # below warning = critical
    }
    
    def infer(self, T: np.ndarray, k_now: int) -> InferenceResult:
        omega, omega_score = self._compute_omega(T, k_now)
        delta              = self._compute_delta(T, k_now)
        rho                = self._compute_rho(T, k_now)
        xi                 = self._generate_recommendations(omega, delta, rho)
        
        return InferenceResult(omega, omega_score, delta, rho, xi)
    
    def _compute_omega(self, T, k):
        snapshot = T[:, :, :, k]
        score = float(np.nanmean(snapshot))
        
        if score >= self.THRESHOLDS["stable"]:
            state = "stable"
        elif score >= self.THRESHOLDS["warning"]:
            state = "warning"
        else:
            state = "critical"
        
        return state, score
    
    def _compute_delta(self, T, k) -> List[TrendEntry]:
        """Δ[d,i,j] = T[d,i,j,k] - T[d,i,j,k-1]"""
        if k == 0:
            return []
        
        delta_tensor = T[:, :, :, k] - T[:, :, :, k-1]
        trends = []
        
        for d in range(T.shape[0]):
            for i in range(T.shape[1]):
                for j in range(T.shape[2]):
                    slope = float(delta_tensor[d, i, j])
                    if abs(slope) > 0.05:  # significance threshold
                        trends.append(TrendEntry(
                            dimension=DIM_NAMES[d],
                            stage=STAGE_NAMES[i],
                            agent=f"agent_{j}",
                            slope=slope,
                            direction="improving" if slope > 0 else "degrading"
                        ))
        
        return sorted(trends, key=lambda x: abs(x.slope), reverse=True)
    
    def _compute_rho(self, T, k) -> List[ConflictEntry]:
        """Detect inter-agent conflicts at stage level."""
        conflicts = []
        n_agents = T.shape[2]
        
        for i in range(T.shape[1]):
            for j1 in range(n_agents):
                for j2 in range(j1+1, n_agents):
                    diff = np.abs(T[:, i, j1, k] - T[:, i, j2, k])
                    for d, delta_d in enumerate(diff):
                        if delta_d > 0.30:  # conflict threshold
                            severity = "high" if delta_d > 0.40 else "medium"
                            conflicts.append(ConflictEntry(
                                agents=[f"agent_{j1}", f"agent_{j2}"],
                                stage=STAGE_NAMES[i],
                                dimension=DIM_NAMES[d],
                                delta_score=float(delta_d),
                                severity=severity
                            ))
        
        return conflicts
    
    def _generate_recommendations(self, omega, delta, rho) -> List[RecommendationEntry]:
        """Ξ: prioritized recommendations based on Ω + Δ + Ρ."""
        recs = []
        
        # From Δ: degrading trends above threshold
        for trend in [t for t in delta if t.direction == "degrading"][:3]:
            recs.append(RecommendationEntry(
                action=f"Address {trend.direction} {trend.dimension} in {trend.stage} stage",
                target=trend.stage,
                estimated_impact=abs(trend.slope),
                urgency="high" if abs(trend.slope) > 0.15 else "medium"
            ))
        
        # From Ρ: active conflicts
        for conflict in rho[:2]:
            recs.append(RecommendationEntry(
                action=f"Resolve {conflict.dimension} conflict between {conflict.agents[0]} and {conflict.agents[1]}",
                target=conflict.stage,
                estimated_impact=conflict.delta_score,
                urgency=conflict.severity
            ))
        
        # Sort by estimated_impact descending
        return sorted(recs, key=lambda x: x.estimated_impact, reverse=True)
```

**REST API — FastAPI routes:**

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TCO Engine API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.post("/vector/compute")
async def compute_vector(artifact: ArtifactPayload) -> VectorResponse:
    """φ: Compute evaluation vector from artifact."""
    vector = vectorizer.vectorize(artifact.to_artifact())
    db.store_vector(vector, artifact.metadata)
    return VectorResponse(vector=vector, metadata=artifact.metadata)

@app.get("/tensor/current")
async def get_current_tensor() -> TensorResponse:
    """Get current tensor snapshot T[:,:,:,k_now]."""
    vectors = db.get_recent_vectors(limit=200)
    T = aggregator.aggregate(vectors)
    return TensorResponse(tensor=T.tolist(), shape=T.shape)

@app.get("/tensor/slice")
async def get_tensor_slice(d: int = None, i: int = None, j: int = None, k: int = None):
    """Named tensor slicing for dashboard views."""
    T = aggregator.get_full_tensor()
    sliced = aggregator.slice(T, d=d, i=i, j=j, k=k)
    return {"slice": sliced.tolist(), "shape": sliced.shape}

@app.get("/inference/latest")
async def get_latest_inference() -> InferenceResponse:
    """I: Get current {Ω, Δ, Ρ, Ξ} inference."""
    T = aggregator.get_full_tensor()
    k_now = db.get_latest_time_index()
    result = engine.infer(T, k_now)
    return InferenceResponse(**result.__dict__)

@app.post("/policy/inject")
async def inject_policy(payload: PolicyPayload) -> PolicyResponse:
    """Receive natural language policy P_new and re-orchestrate agents."""
    # Structured extraction: NL → PolicyIntent struct
    instructions = policy_processor.parse(payload.policy_text, context=payload.tensor_state)
    
    # Store full struct for H5 evaluation (PIQ scored on struct, not only on raw text)
    policy_id = db.store_policy(payload.policy_text, instructions, payload.participant_id)
    
    # Inject struct as system prompt patch per target agent
    pipeline.update_context(instructions)
    
    return PolicyResponse(policy_id=policy_id, instructions=instructions, status="injected")
```

**Policy Processor — Structured Extraction Architecture:**

The `policy_processor` implements a **hybrid structured extraction** pattern. This architecture was selected over direct prompt injection because the extracted struct provides a fully auditable record for H5 scoring: PIQ evaluation can be applied to the intent struct, not only to the raw natural language text.

```python
# core/policy_processor.py
from dataclasses import dataclass
from typing import Literal

@dataclass
class PolicyIntent:
    """Structured representation of a natural language policy P_new."""
    target_agents:       list[str]                          # e.g. ["code_agent", "arch_agent"]
    action_type:         Literal["prioritize","restrict","focus","resolve"]
    affected_dimensions: list[str]                          # e.g. ["security_risk", "v4"]
    constraint:          str                                # e.g. "use parameterized queries"
    priority:            Literal["high","medium","low"]

class PolicyProcessor:
    """P_new (NL) → PolicyIntent → agent system prompt patch."""
    
    def parse(self, policy_text: str, context: dict) -> PolicyIntent:
        # Step 1: LLM extracts structured intent from NL + current tensor state
        intent = self._extract_intent(policy_text, context)
        
        # Step 2: Validate intent references real agents and dimensions
        self._validate(intent)
        return intent
    
    def to_agent_patch(self, intent: PolicyIntent) -> dict[str, str]:
        """Convert PolicyIntent to per-agent system prompt addendum."""
        patch = {}
        for agent_id in intent.target_agents:
            patch[agent_id] = (
                f"ACTIVE POLICY [{intent.priority.upper()}]: "
                f"{intent.action_type} {', '.join(intent.affected_dimensions)}. "
                f"Constraint: {intent.constraint}. Apply to next generation cycle."
            )
        return patch
    
    def _extract_intent(self, policy_text: str, context: dict) -> PolicyIntent:
        """LLM-based extraction with structured output via Pydantic."""
        # Uses claude-sonnet-4-6 with few-shot examples
        # Fallback: if extraction confidence < 0.7, returns direct-injection mode
        ...
```

> **Fallback behavior:** If intent extraction produces confidence < 0.70 (measured by LLM self-assessment), the system falls back to direct injection: the full policy text is appended as a free-text addendum to all agent system prompts. The fallback event is logged and counted in the H5 analysis as a degraded policy case.

**Database schema — PostgreSQL 16:**

```sql
-- Evaluation vectors (time-series hypertable)
CREATE TABLE evaluation_vectors (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL,
    agent_id    VARCHAR(50) NOT NULL,
    stage       VARCHAR(20) NOT NULL CHECK (stage IN ('design','build','test','deploy')),
    cycle_k     INTEGER NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Vector dimensions
    v1_functional_correctness  FLOAT CHECK (v1_functional_correctness BETWEEN 0 AND 1),
    v2_architectural_alignment FLOAT CHECK (v2_architectural_alignment BETWEEN 0 AND 1),
    v3_scalability_projection  FLOAT CHECK (v3_scalability_projection  BETWEEN 0 AND 1),
    v4_security_risk           FLOAT CHECK (v4_security_risk           BETWEEN 0 AND 1),
    v5_observability_coverage  FLOAT CHECK (v5_observability_coverage  BETWEEN 0 AND 1),
    v6_testability             FLOAT CHECK (v6_testability             BETWEEN 0 AND 1),
    v7_maintainability         FLOAT CHECK (v7_maintainability         BETWEEN 0 AND 1),
    v8_technical_debt          FLOAT CHECK (v8_technical_debt          BETWEEN 0 AND 1),
    v9_performance             FLOAT CHECK (v9_performance             BETWEEN 0 AND 1),
    v10_confidence             FLOAT CHECK (v10_confidence             BETWEEN 0 AND 1),
    v11_anomaly_score          FLOAT CHECK (v11_anomaly_score          BETWEEN 0 AND 1),
    
    -- Metadata
    scenario_id VARCHAR(20),
    fault_injected BOOLEAN DEFAULT FALSE,
    participant_id VARCHAR(50)  -- for experiment tracking
);

SELECT create_hypertable('evaluation_vectors', 'created_at');
CREATE INDEX ON evaluation_vectors (agent_id, cycle_k, stage);

-- Policy injection log (for H5 evaluation)
CREATE TABLE policy_injections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id  VARCHAR(50) NOT NULL,
    group_type      VARCHAR(20) NOT NULL CHECK (group_type IN ('control','experimental')),
    cycle_k_pre     INTEGER NOT NULL,
    cycle_k_post    INTEGER,
    policy_text     TEXT,          -- NL policy (experimental group)
    raw_edit        TEXT,          -- Code/config edit (control group)
    piq_rubric_1    INTEGER,       -- Clarity (1-5, human annotator)
    piq_rubric_2    INTEGER,       -- Systemic specificity (1-5)
    piq_rubric_3    INTEGER,       -- Projected impact (1-5)
    piq_llm_judge   FLOAT,         -- LLM-Judge composite score
    vector_delta    JSONB,         -- Actual Δ_post measured
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Experiment interaction log (for H1 NASA-TLX objective metrics)
CREATE TABLE interaction_log (
    id             BIGSERIAL PRIMARY KEY,
    participant_id VARCHAR(50) NOT NULL,
    group_type     VARCHAR(20) NOT NULL,
    task_id        VARCHAR(5) NOT NULL,   -- T1,T2,T3,T4
    event_type     VARCHAR(30) NOT NULL,  -- click, scroll, keypress, context_switch
    element_id     VARCHAR(100),
    timestamp_ms   BIGINT NOT NULL,       -- milliseconds since task start
    payload        JSONB
);
```

### 8.4 Component C — Orchestration Dashboard

**Technology stack:** React 18 + Recharts + TailwindCSS + Axios

**Four views, single screen — no navigation to minimize context switches:**

```
┌──────────────────────────────────────────────────────────────────────────┐
│  TCO Dashboard  ·  System: WARNING  ·  Last update: 2 min ago            │
├─────────────────────────┬────────────────────────┬───────────────────────┤
│  VIEW 1                 │  VIEW 2                │  VIEW 3               │
│  Vector Radar           │  Temporal Heatmap      │  Inference Panel      │
│  (current cycle)        │  (Δ by dimension/time) │  {Ω, Δ, Ρ, Ξ}        │
│                         │                        │                       │
│  ◉ Agent 1  ◉ Agent 2  │  [dim×time grid,       │  ⚠ WARNING            │
│  [spider chart,         │   color = vᵢ value,    │  ─────────────────    │
│   11 axes,              │   arrows = Δ trend]    │  📉 security_risk     │
│   color-coded]          │                        │     degrading −0.61   │
│                         │                        │  ⚡ CONFLICT: ag1/ag2 │
│                         │                        │     arch_alignment    │
│                         │                        │  ────────────────     │
│                         │                        │  1. Fix auth vuln     │
│                         │                        │  2. Resolve conflict  │
├─────────────────────────┴────────────────────────┴───────────────────────┤
│  VIEW 4 — Policy Injection (Natural Language)                             │
│                                                                           │
│  [ The security agent detected SQL injection in auth_module.py.           │
│    Prioritize parameterized queries before next build cycle.    ▶ INJECT ]│
│                                                                           │
│  History: [P_new_001: +0.41 v₄] [P_new_002: +0.18 v₂] [P_new_003: ...]  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Key React components:**

```jsx
// components/VectorRadar.jsx
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';

const PILLAR_LABELS = {
  v1: 'Correctness', v2: 'Architecture', v3: 'Scalability',
  v4: 'Security', v5: 'Observability', v6: 'Testability',
  v7: 'Maintainability', v8: 'Debt', v9: 'Performance'
};

export function VectorRadar({ vectors, agentIds }) {
  const data = Object.entries(PILLAR_LABELS).map(([key, label]) => {
    const entry = { subject: label };
    agentIds.forEach(id => {
      entry[id] = vectors[id]?.[key] ?? 0;
    });
    return entry;
  });

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
        {agentIds.map((id, i) => (
          <Radar key={id} name={id} dataKey={id}
            stroke={AGENT_COLORS[i]} fill={AGENT_COLORS[i]}
            fillOpacity={0.15} dot={false} />
        ))}
      </RadarChart>
    </ResponsiveContainer>
  );
}

// components/TensorHeatmap.jsx
export function TensorHeatmap({ tensorSlice, dimensions, timeLabels }) {
  // tensorSlice: T[:,j,:] — agent trajectory
  // Color scale: red (0) → yellow (0.5) → green (1)
  const getColor = (val) => {
    if (val >= 0.75) return '#22c55e';  // green
    if (val >= 0.50) return '#eab308';  // yellow
    return '#ef4444';                    // red
  };

  return (
    <div className="grid" style={{ gridTemplateColumns: `auto repeat(${timeLabels.length}, 1fr)` }}>
      {dimensions.map(dim => (
        <React.Fragment key={dim}>
          <span className="text-xs text-gray-500 pr-2">{dim}</span>
          {timeLabels.map((t, k) => {
            const val = tensorSlice[dim]?.[k] ?? 0;
            const trend = k > 0 ? val - (tensorSlice[dim]?.[k-1] ?? val) : 0;
            return (
              <div key={t} className="h-8 flex items-center justify-center text-xs rounded"
                   style={{ backgroundColor: getColor(val) }}>
                {val.toFixed(2)}
                {Math.abs(trend) > 0.05 && (
                  <span className="ml-1">{trend > 0 ? '↑' : '↓'}</span>
                )}
              </div>
            );
          })}
        </React.Fragment>
      ))}
    </div>
  );
}

// components/PolicyInjection.jsx
export function PolicyInjection({ onInject, history }) {
  const [policy, setPolicy] = useState('');
  const [loading, setLoading] = useState(false);

  const handleInject = async () => {
    setLoading(true);
    const result = await api.post('/policy/inject', {
      policy_text: policy,
      tensor_state: getCurrentTensorState()
    });
    onInject(result.data);
    setPolicy('');
    setLoading(false);
  };

  return (
    <div className="border-t pt-4">
      <label className="text-sm font-medium text-gray-700 mb-2 block">
        Policy Injection — Natural Language
      </label>
      <div className="flex gap-2">
        <textarea
          value={policy}
          onChange={e => setPolicy(e.target.value)}
          className="flex-1 border rounded p-2 text-sm resize-none h-16"
          placeholder="Describe what the system should change in the next cycle..."
        />
        <button onClick={handleInject} disabled={!policy || loading}
          className="px-4 bg-blue-600 text-white rounded text-sm font-medium disabled:opacity-50">
          {loading ? 'Injecting...' : '▶ Inject'}
        </button>
      </div>
      
      {/* Policy history with delta feedback */}
      <div className="mt-2 flex gap-2 flex-wrap">
        {history.map(p => (
          <span key={p.id} className="text-xs bg-gray-100 rounded px-2 py-1">
            {p.policy_text.slice(0, 40)}...
            <span className={`ml-1 font-mono ${p.delta > 0 ? 'text-green-600' : 'text-red-500'}`}>
              {p.delta > 0 ? '+' : ''}{p.delta.toFixed(2)}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
```

### 8.5 Interaction Logger — Experiment Support

```python
# logging/interaction_logger.py
class InteractionLogger:
    """Records all participant interactions for H1 objective metrics."""
    
    def __init__(self, participant_id: str, group: str, task_id: str):
        self.participant_id = participant_id
        self.group = group
        self.task_id = task_id
        self.task_start_ms = time.time() * 1000
    
    def log(self, event_type: str, element_id: str = None, payload: dict = None):
        db.insert("interaction_log", {
            "participant_id": self.participant_id,
            "group_type": self.group,
            "task_id": self.task_id,
            "event_type": event_type,
            "element_id": element_id,
            "timestamp_ms": int(time.time() * 1000 - self.task_start_ms),
            "payload": json.dumps(payload or {})
        })
    
    def compute_metrics(self) -> TaskMetrics:
        events = db.query("interaction_log", participant_id=self.participant_id, task_id=self.task_id)
        return TaskMetrics(
            time_on_task_sec = events[-1]["timestamp_ms"] / 1000 if events else 0,
            context_switches = len([e for e in events if e["event_type"] == "context_switch"]),
            total_clicks     = len([e for e in events if e["event_type"] == "click"]),
            raw_output_reads = len([e for e in events if e["event_type"] == "file_open"]),  # control group
            dashboard_reads  = len([e for e in events if e["event_type"] == "view_change"]) # experimental
        )
```

### 8.6 Docker Compose — Full Stack

```yaml
# docker-compose.yml — 5 services, no external analysis server required
version: '3.9'

services:
  tco_engine:
    build: ./src/tco_engine
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://tco:tco@postgres:5432/tco_experiment
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - POLICY_WINDOW_CYCLES=3
    depends_on: [postgres, redis]
    volumes:
      - ./src/tco_engine:/app

  pipeline:
    build: ./src/pipeline
    environment:
      - TCO_ENGINE_URL=http://tco_engine:8000
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on: [tco_engine]

  dashboard:
    build: ./src/dashboard
    ports: ["3000:3000"]
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on: [tco_engine]

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=tco_experiment
      - POSTGRES_USER=tco
      - POSTGRES_PASSWORD=tco
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./src/tco_engine/db/migrations/001_initial.sql:/docker-entrypoint-initdb.d/001_initial.sql

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 9. Challenges and Open Problems

### 9.1 Vector Calibration

The quality and reliability of TCO depend critically on the calibration of the weight vectors wᵢⱼ for each pilar. The initial specification proposes equal weights as a baseline, with domain-specific calibration as a research deliverable. The MVP must include a calibration protocol using expert annotation and inter-rater reliability measures [18].

### 9.2 Tensor Interpretability

A tensor of dimension n × |S| × |A| × |T| grows rapidly with system scale. For large multi-agent systems, CP decomposition and Tucker decomposition [15] are proposed as inference-layer preprocessing steps, but their output interpretability in this domain requires empirical validation.

### 9.3 Multi-Agent Bias

Agents operating in parallel may develop systematic biases in their quality evaluations. The tensor's inter-agent comparison capability (Ρ) is designed to surface these discrepancies, but the inference model must be robust to systematic agent bias rather than treating all vectors as equally reliable. The confidence dimension v₁₀ partially addresses this but requires further formalization.

### 9.4 Policy Injection Semantics

Natural language policy injection is the most expressive and least constrained component of the TCO cycle. A structured natural language schema — analogous to prompt engineering frameworks — may be necessary to ensure policy injection produces reliable re-orchestration. This is an open design problem with implications for both usability and system reliability.

---

## 10. Expected Contributions

### 10.1 Theoretical Contributions

- The **Natural Cognitive Frontier (NCF)**: a formally defined HCI design construct identifying the optimal abstraction level for human-AI collaboration in complex system oversight. The NCF is not merely an analytical concept — it is an engineering target: a system is well-designed when it positions the human operator at the NCF, rather than above or below it.
- The **expertise shift thesis**: as AI system autonomy increases, human expertise does not become less valuable — it migrates from artifact-level manipulation to systemic orchestration. The correct comparison is not "expert engineer vs. vibe coder" but "artifact validator vs. orchestration engineer." TCO is the first framework to operationalize this shift with a formal interface architecture.
- The **TCO bidirectional loop model**: a formalized architecture for human-AI orchestration that resolves automation bias through structural active judgment rather than interface design.
- Application of tensor-based state representation to the domain of **human cognitive oversight of software quality** — a novel combination of multi-agent representation theory and human factors engineering.
- The **orchestration engineer** as an emerging professional role: a practitioner whose core competency is systemic supervision, policy design, and emergent behavior diagnosis — not artifact production. TCO provides the first formal specification of the interface requirements for this role.

### 10.2 Practical Contributions

- A replicable framework for AI-driven software development teams to implement structured human oversight at scale, with defined interfaces at each layer.
- Reduction of brain fry and cognitive fatigue in AI supervision roles, with measurable impact on decision quality and operator wellbeing.
- Expanded access to the orchestrator role: by requiring only natural language competency rather than technical expertise, TCO enables product, architecture, and business leadership to participate meaningfully in AI system governance.
- A foundation for next-generation DevOps tooling integrating quality vector dashboards, tensor visualization, and natural language policy interfaces.

### 10.3 Future Work

- **Replication and scope extension:** The n=40 between-subjects experiment reported here is designed as preliminary evidence suitable for a CHI workshop or FSE short paper. Claims about cognition, expertise transition, and multi-agent oversight should not be generalized beyond this scope. Future work requires: (a) replication with independent participant pools, (b) multi-site studies across organizational contexts, and (c) longitudinal observation to distinguish learning effects from sustained NCF operation. The current study establishes proof-of-concept, not universal theory.
- **Real-world deployment validation** across multiple organizational contexts and AI development stacks beyond the simulated pipeline used in this study.
- **Adaptive vector learning:** automated recalibration of wᵢⱼ weights based on observed correlations between vector values and deployment outcomes.
- **Integration with observability platforms:** mapping TCO quality dimensions to existing metric streams (Prometheus, OpenTelemetry) to reduce instrumentation overhead.
- **Autonomous policy suggestion:** training a policy generation model on historical P_new entries and their system impact to provide policy drafts for orchestrator review.

- **Hierarchical Abstraction Pyramid: TCO as Level 2 of a multi-tier cognitive compression architecture.** The present work formalizes a single abstraction step: φ maps raw artifacts to quality vectors V ∈ [0,1]¹¹, and f aggregates vectors into a cognitive tensor T[d,i,j,k]. Human oversight at this level is validated by the experiment, but the theoretical contribution extends further. TCO is best understood as the empirical validation of **Level 2** in a four-level abstraction hierarchy:

  | Level | Representation | Operation | Supervisor |
  |-------|---------------|-----------|------------|
  | L0 | Tokens / raw artifacts | Generation | AI agents |
  | L1 | Embeddings / semantic features | Local LLM inference | — |
  | **L2** | **Cognitive tensor T[d,i,j,k]** | **φ + f + I: T → {Ω,Δ,Ρ,Ξ}** | **Human (NCF) — TCO** |
  | L3 | Tensor volume V(T₁, T₂, ..., Tₙ) | Cross-session composition, temporal evolution | Automated inference |
  | L4 | Meta-inference output M(V) | Higher-order reasoning on compressed state | Automated / hybrid |

  The critical observation is that the TCO experiment does not only test whether the dashboard reduces cognitive load. It tests whether **tensor representation is semantically conservative** — whether T[d,i,j,k] preserves sufficient structure for effective high-stakes reasoning. A positive experimental result (H2, H3) constitutes empirical evidence that the abstraction does not destroy decision-relevant information. That evidence is the theoretical foundation for Levels 3 and 4: if a human orchestrator can reason effectively from a tensor representation, an automated inference layer operating on tensor volumes can do so without the human as an intermediary.

  The central open problem at Level 3 is the composition of tensors across time and across pipeline sessions into a stable **tensor volume** V(T₁...Tₙ). The key research questions are: (a) what composition operator preserves causal relationships across T instances while reducing dimensionality; (b) whether the resulting volume exhibits stable attractor states or phase transitions analogous to semantic regime shifts; and (c) whether inference cost on V scales with *structural complexity of the compressed representation* rather than raw artifact count — the hypothesis that would decouple context capacity from computational cost. This connects to active research in State Space Models [Gu & Dao, 2023], hierarchical coarse-graining in physics (renormalization group theory), and tensor decomposition methods [Kolda & Bader, 2009]. The central metric to develop is **Semantic Information Density**: not the quantity of tokens processed but the quantity of decision-relevant cognitive structure preserved per unit of representation. TCO's quality vector V and inference outputs {Ω,Δ,Ρ,Ξ} provide a concrete starting point for operationalizing this metric.

---

## 11. References

[1] Sweller, J. (1988). Cognitive load during problem solving: Effects on learning. *Cognitive Science, 12*(2), 257–285. https://doi.org/10.1207/s15516709cog1202_4

[2] Sweller, J., Ayres, P., & Kalyuga, S. (2011). Cognitive Load Theory. *Psychology of Learning and Motivation, 55*, 37–76.

[3] Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration of mental storage capacity. *Behavioral and Brain Sciences, 24*(1), 87–114.

[4] Endsley, M. R. (1995). Toward a theory of situation awareness in dynamic systems. *Human Factors, 37*(1), 32–64.

[5] Endsley, M. R., & Garland, D. J. (Eds.). (2000). *Situation Awareness Analysis and Measurement*. Lawrence Erlbaum Associates.

[6] Sheridan, T. B. (1992). *Telerobotics, Automation, and Human Supervisory Control*. MIT Press.

[7] Miller, C. A., & Parasuraman, R. (2007). Designing for flexible interaction between humans and automation: Delegation interfaces for supervisory control. *Human Factors, 49*(1), 57–75.

[8] Human-in-the-Loop AI: A Systematic Review of Concepts, Methods, and Applications. (2025). *Entropy, 28*(4), 377. https://doi.org/10.3390/e28040377

[9] Human-in-the-loop has hit the wall: It's time for AI to oversee AI. (2026, January). SiliconANGLE.

[10] Parasuraman, R., & Manzey, D. H. (2010). Complacency and bias in human use of automation: An attentional integration. *Human Factors, 52*(3), 381–410.

[11] Kücking, F., et al. (2024). Automation Bias in AI-Decision Support: Results from an Empirical Study. *Studies in Health Technology and Informatics, 317*, 298–304.

[12] Codebridge. (2025). The Hidden Costs of AI-Generated Code: Analysis of 211M changed lines of code, 2020–2024. https://www.codebridge.tech

[13] Chen, B., et al. (2021). Tensor decomposition for multi-agent predictive state representation. *Expert Systems with Applications, 183*. https://doi.org/10.1016/j.eswa.2021.115413

[14] Mahajan, A., et al. (2021). TESSERACT: Tensorised actors for multi-agent reinforcement learning. *Proceedings of ICML 2021*.

[15] Van Der Vaart, P., et al. (2021). Model-based multi-agent reinforcement learning with tensor decompositions. arXiv:2110.14524.

[16] Vygotsky, L. S. (1978). *Mind in Society: The Development of Higher Psychological Processes*. Harvard University Press.

[17] Syncing Minds and Machines: Hybrid Cognitive Alignment as an Emergent Coordination Mechanism in Human–AI Collaboration. (2025). *Academy of Management Review*. https://doi.org/10.5465/amr.2024.0546

[18] Lommel, A., Burchardt, A., & Uszkoreit, H. (2014). Multidimensional Quality Metrics (MQM): A framework for declaring and describing translation quality metrics. *Tradumàtica, 0*, 455–463.

[19] Takerngsaksiri, W., et al. (2024). Human-In-the-Loop Software Development Agents (HULA). arXiv:2411.12924.

[20] Pareschi, R., & Saghafian, S. (2024). Human-artificial interaction in the age of agentic AI: A system-theoretical approach. *Frontiers in Human Dynamics*.

[21] Zhang, Z., et al. (2022). FixReverter: Bug injection by reverting CVE-related fixes for fuzz testing. In *USENIX Security Symposium 2022*.

[22] LLMs-as-Judges in Automatic Evaluation of Free-Form QA. (2025). *WiNLP Workshop, ACL 2025*. https://aclanthology.org/2025.winlp-main.37

[23] Inter-Rater Reliability between Large Language Models and Human Raters in Qualitative Analysis. (2025). arXiv:2508.14764.

[24] An Empirical Study of LLM-as-a-Judge: How Design Choices Impact Evaluation Reliability. (2025). arXiv:2506.13639.

[25] Parasuraman, R., Sheridan, T. B., & Wickens, C. D. (2000). A model for types and levels of human interaction with automation. *IEEE Transactions on Systems, Man, and Cybernetics — Part A, 30*(3), 286–297. <https://doi.org/10.1109/3468.844354>

[26] Cummings, M. L. (2014). Man versus machine or man + machine? *IEEE Intelligent Systems, 29*(5), 62–69. <https://doi.org/10.1109/MIS.2014.87>

[27] National Institute of Standards and Technology. (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*. NIST AI 100-1. <https://doi.org/10.6028/NIST.AI.100-1>

[28] Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J.-F., & Dennison, D. (2015). Hidden technical debt in machine learning systems. In *Advances in Neural Information Processing Systems 28 (NeurIPS 2015)*, 2503–2511.

[29] Amershi, S., Begel, A., Bird, C., DeLine, R., Gall, H., Kamar, E., Nagappan, N., Nushi, B., & Zimmermann, T. (2019). Software engineering for machine learning: A case study. In *Proceedings of ICSE-SEIP 2019*, 291–300. IEEE. <https://doi.org/10.1109/ICSE-SEIP.2019.00042>

[30] Yang, J., Carlos, E. J., Yao, K., Hu, S., Schafer, M., Prabhu, R., Ramakrishnan, K., Chen, F., Awasthi, K., Bhatt, N., & Narayanan, S. (2024). SWE-agent: Agent-computer interfaces enable automated software engineering. arXiv:2405.15793.

---

## Appendix A — Evaluation Vector JSON Schema

```json
{
  "artifact_id":   "string (UUID)",
  "agent_id":      "string",
  "stage":         "design | build | test | deploy",
  "cycle_k":       "integer",
  "timestamp":     "ISO 8601",
  "scenario_id":   "string (optional, for experiment)",
  "vector": {
    "functional_correctness":  "float ∈ [0,1]",
    "architectural_alignment": "float ∈ [0,1]",
    "scalability_projection":  "float ∈ [0,1]",
    "security_risk":           "float ∈ [0,1]  (1 = no risk)",
    "observability_coverage":  "float ∈ [0,1]",
    "testability":             "float ∈ [0,1]",
    "maintainability":         "float ∈ [0,1]",
    "technical_debt":          "float ∈ [0,1]  (1 = no debt)",
    "performance":             "float ∈ [0,1]",
    "confidence":              "float ∈ [0,1]",
    "anomaly_score":           "float ∈ [0,1]  (1 = no anomaly)"
  },
  "weights":   "object (optional: wᵢⱼ calibration map)",
  "metadata":  {
    "qa_agent":      "string",
    "model_version": "string",
    "analysis_tools": ["sonarqube", "bandit", "coverage"]
  }
}
```

---

## Appendix B — Inference Layer Output Schema

```json
{
  "tensor_snapshot_id": "string (UUID)",
  "cycle_k":            "integer",
  "evaluated_at":       "ISO 8601",
  "Omega": {
    "global_state":   "stable | warning | critical",
    "composite_score": "float ∈ [0,1]",
    "pillar_scores":   "{ dimension: score, ... }"
  },
  "Delta": {
    "trends": [{
      "dimension":  "string",
      "stage":      "string",
      "agent":      "string",
      "direction":  "improving | stable | degrading",
      "slope":      "float",
      "cycles_sustained": "integer"
    }]
  },
  "Rho": {
    "conflicts": [{
      "agents":      ["string", "string"],
      "stage":       "string",
      "dimension":   "string",
      "delta_score": "float",
      "severity":    "low | medium | high"
    }],
    "correlated_failures": [{
      "dimensions":  ["string"],
      "correlation": "float",
      "pattern":     "string"
    }]
  },
  "Xi": {
    "recommendations": [{
      "rank":             "integer",
      "action":           "string (natural language)",
      "target":           "stage | agent | dimension",
      "estimated_impact": "float",
      "urgency":          "low | medium | high"
    }]
  }
}
```

---

## Appendix C — MVP Component Specifications

### C.1 Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| TCO Engine API | FastAPI | 0.115+ | REST API, vectorization, inference |
| Agent Orchestration | LangGraph | 0.2+ | Multi-agent pipeline control |
| LLM (all agents) | Claude API | claude-sonnet-4-6 | Generation, QA evaluation, policy processing |
| Database | PostgreSQL 16 | 16-alpine | Vector + interaction + policy persistence |
| Cache | Redis | 7-alpine | Tensor cache (TTL 30s) + artifact hash cache |
| Static Analysis | radon + pylint | 6.0 + 3.1 | v₆, v₇, v₈: complexity, Halstead, debt ratio |
| Security Scan | Bandit | 1.8+ | v₄: vulnerability scan |
| Test Coverage | Coverage.py | 7.0+ | v₆: branch + line coverage ratio |
| Dashboard | React 18 + Recharts + TypeScript | 18 + 2.x + 5.x | 4-view orchestration UI + experiment UI |
| Container | Docker Compose | 3.9 | 5-service full-stack (no external analysis server) |

### C.2 API Endpoint Reference

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/vector/compute` | POST | Compute V from artifact | `ArtifactPayload` | `VectorResponse` |
| `/tensor/current` | GET | Full tensor snapshot | — | `TensorResponse` |
| `/tensor/slice` | GET | Named tensor slice | `?d=&i=&j=&k=` | `SliceResponse` |
| `/inference/latest` | GET | Current {Ω,Δ,Ρ,Ξ} | — | `InferenceResponse` |
| `/policy/inject` | POST | Inject P_new, re-orchestrate | `PolicyPayload` | `PolicyResponse` |
| `/experiment/log` | POST | Log participant interaction | `InteractionEvent` | `{status: "ok"}` |
| `/experiment/metrics/{id}` | GET | Compute task metrics | — | `TaskMetrics` |

### C.3 Environment Variables

```bash
# .env — copy from .env.example, never commit
ANTHROPIC_API_KEY=sk-ant-...          # Required: Claude API
DATABASE_URL=postgresql://...          # Required: PostgreSQL 16
REDIS_URL=redis://localhost:6379/0    # Required: tensor + artifact cache

# Experiment configuration
EXPERIMENT_MODE=development           # development | pilot | full
POLICY_WINDOW_CYCLES=3               # Δ_post measurement window (H5)
TENSOR_CACHE_TTL=30                  # Redis TTL in seconds

# TCO thresholds (configurable per domain)
TCO_THRESHOLD_STABLE=0.70            # Ω = stable if score ≥ this
TCO_THRESHOLD_WARNING=0.50           # Ω = warning if score ≥ this
TCO_CONFLICT_THRESHOLD=0.30          # Ρ detection threshold
TCO_TREND_SIGNIFICANCE=0.05          # Δ minimum significance
```

---

*Document version: 2.0 — Phases 1, 2 and 3 complete*
*Next milestone: Implementation Sprint 1 (Weeks 1–2) — TCO Engine API*
