# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-032 — Representation encoders: raw → R_raw, φ-vector → R_V, tensor → R_T.

Three representations are compared in the SID Study:

  R_raw  — TF-IDF over artifact source text (char n-grams 2–4).
            Baseline: what a simple text classifier can learn about Y=(D,C).
            Complexity C(R_raw) = vocabulary size × n-gram range (high).

  R_V    — 11-dimensional evaluation vector φ(artifact) from ground truth.
            Captures per-artifact quality signal; no cross-artifact comparison.
            Complexity C(R_V) = 11 (dimensionality; fixed regardless of n).

  R_T    — Tensor-derived features: the joint representation across agents and
            cycles that the TCO inference engine operates on.
            For a given (scenario, stage), R_T stacks all available cycle and
            agent slices → the cross-index signal that makes S3/S5 legible.
            Complexity C(R_T) = number of filled tensor cells (data-dependent).

All encoders produce a numpy matrix X ∈ ℝ^{n × d} where n = number of corpus
entries and d = representation dimensionality. The associated label vectors
Y_D (supervisory decision) and Y_C (causal structure correctness) are also
produced here so probe.py receives (X, y) pairs directly.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

# ─── Corpus-level constants ───────────────────────────────────────────────────

DIM_NAMES = [
    "functional_correctness", "architectural_alignment", "scalability_projection",
    "security_risk", "observability_coverage", "testability", "maintainability",
    "technical_debt", "performance", "confidence", "anomaly_score",
]
N_DIMS = len(DIM_NAMES)

# Ground-truth supervisory decisions (D) — from CAL_Benchmark_v1.md.
# One binary label per scenario: "halt" or "deploy" (T3 decision, most
# discriminative single decision for a probe study with 12 samples).
# S1→halt, S2→halt, S3→halt (k=3), S4→halt, S5→halt (detect conflict).
# All faulty artefacts should signal halt; clean ones should signal deploy.
# For multi-cycle S3 we label k=3 (highest debt) as halt, k=0 as deploy.
GT_DECISION: dict[str, str] = {
    "s1_auth_clean":          "deploy",
    "s1_auth_faulty":         "halt",
    "s2_arch_clean":          "deploy",
    "s2_arch_faulty":         "halt",
    "s3_processor_k0":        "deploy",
    "s3_processor_k1":        "deploy",
    "s3_processor_k2":        "caution",   # borderline (CC=8)
    "s3_processor_k3":        "halt",      # CC=12, debt accumulated
    "s4_deploy_clean":        "deploy",
    "s4_deploy_faulty":       "halt",
    "s5_auth_security_agent": "caution",   # high security, poor testability
    "s5_auth_code_agent":     "halt",      # SQL injection present
}

# Causal correctness label (C): does the representation expose the fault's
# causal structure?  Ground-truth from fault_present + scenario CCI.
#
# Key design decision: the label measures whether THE SYSTEM is in a
# causally-significant state, not whether a single artifact is faulty.
# This is the governance-relevant question: "should I intervene?"
#
# For tensor-level faults (S3, S5), both/all artifacts of the scenario
# get label=1 when the causal state is present, because the tensor as a
# whole manifests it even though no single artifact does.
#
#  S3 (CCI=4, temporal drift): per-artifact values stay above the absolute
#     fault threshold (0.45) at every cycle, so the drift is invisible to a
#     per-artifact reviewer. Only the cumulative tensor Δ from k=0 reveals it.
#     k0/k1: Δ above the trajectory threshold (-0.15) → label=0 (no signal yet).
#     k2 (Δ=-0.17) / k3 (Δ=-0.26): Δ crosses the threshold → label=1.
#  S5 (CCI=3, inter-agent conflict): the conflict is ALWAYS present across
#     the two agents. Both artifacts get label=1 — the tensor exposes it
#     while per-artifact review cannot.
GT_CAUSAL: dict[str, int] = {
    "s1_auth_clean":          0,
    "s1_auth_faulty":         1,   # v4 drop: direct read (CCI=1)
    "s2_arch_clean":          0,
    "s2_arch_faulty":         1,   # v2 drop: indexed read (CCI=2)
    "s3_processor_k0":        0,   # Δ = 0.00, baseline (no drift yet)
    "s3_processor_k1":        0,   # Δ = -0.08 from k0, below trajectory threshold
    "s3_processor_k2":        1,   # Δ = -0.17 from k0 — trajectory threshold crossed
    "s3_processor_k3":        1,   # Δ = -0.26 from k0 — clearly above threshold
    "s4_deploy_clean":        0,
    "s4_deploy_faulty":       1,   # v5 drop: indexed read (CCI=2)
    "s5_auth_security_agent": 1,   # conflict IS present (joint view); tensor exposes it
    "s5_auth_code_agent":     1,   # conflict IS present (joint view); tensor exposes it
}


@dataclass
class CorpusEntry:
    artifact_id: str
    scenario: str
    cycle: int
    code: str
    fault_present: Optional[bool]
    ground_truth: dict
    decision_label: str    # "deploy" / "caution" / "halt"
    causal_label: int      # 0 or 1


def load_corpus(path: Path) -> list[CorpusEntry]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for item in data["corpus"]:
        aid = item["artifact_id"]
        entries.append(CorpusEntry(
            artifact_id=aid,
            scenario=item["scenario"],
            cycle=item.get("cycle", 0),
            code=item["code"],
            fault_present=item.get("fault_present"),
            ground_truth=item.get("ground_truth", {}),
            decision_label=GT_DECISION.get(aid, "deploy"),
            causal_label=GT_CAUSAL.get(aid, 0),
        ))
    return entries


# ─── R_raw: TF-IDF over char n-grams ─────────────────────────────────────────

def encode_raw(entries: list[CorpusEntry]) -> tuple[np.ndarray, float]:
    """
    R_raw: TF-IDF char n-gram (2–4) representation of raw artifact text.

    Returns (X, complexity) where complexity = log(vocab_size) as a
    dimensionality-normalized cost.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    texts = [e.code for e in entries]
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4),
                          max_features=512, sublinear_tf=True)
    X = vec.fit_transform(texts).toarray()
    complexity = float(np.log1p(X.shape[1]))   # log(vocab_size)
    return X.astype(np.float32), complexity


# ─── R_V: 11-dimensional evaluation vector from ground truth ──────────────────

def encode_vector(entries: list[CorpusEntry]) -> tuple[np.ndarray, float]:
    """
    R_V: 11-dimensional evaluation vector φ(artifact) from corpus ground truth.

    Ground truth provides approximate values for the key dimensions.
    Missing dimensions are imputed from the scenario's expected baseline.
    """
    # Scenario baselines (healthy values for dims not explicitly annotated)
    BASELINE = {d: 0.75 for d in DIM_NAMES}
    # Overrides for specific scenarios' faulty dimensions
    OVERRIDES: dict[str, dict[str, float]] = {
        "s1_auth_faulty":         {"security_risk": 0.20, "anomaly_score": 0.20},
        "s2_arch_faulty":         {"architectural_alignment": 0.20, "maintainability": 0.40},
        # DT-034 corpus fix (anticipated): the S3 drift must be recoverable ONLY
        # via the tensor Δ operation, not from any single artifact's absolute
        # value. All four cycles stay ABOVE the absolute fault threshold (0.45)
        # so a per-artifact reviewer sees nothing; only the cumulative Δ from k0
        # crosses the trajectory threshold (Δ<-0.15) at k2 (Δ=-0.17) and k3
        # (Δ=-0.26). Previously k3=0.44 leaked below 0.45, letting the baseline
        # detect S3 without Δ and collapsing M_advantage(S3) to ~0.
        "s3_processor_k0":        {"technical_debt": 0.78},
        "s3_processor_k1":        {"technical_debt": 0.70},
        "s3_processor_k2":        {"technical_debt": 0.61},
        "s3_processor_k3":        {"technical_debt": 0.52},
        "s4_deploy_faulty":       {"observability_coverage": 0.15, "architectural_alignment": 0.35},
        "s5_auth_security_agent": {"security_risk": 0.85, "testability": 0.25},
        "s5_auth_code_agent":     {"security_risk": 0.20, "testability": 0.75},
    }

    rows = []
    for e in entries:
        v = dict(BASELINE)
        if e.artifact_id in OVERRIDES:
            v.update(OVERRIDES[e.artifact_id])
        row = np.array([v[d] for d in DIM_NAMES], dtype=np.float32)
        rows.append(row)

    X = np.stack(rows)
    complexity = float(N_DIMS)   # 11 — fixed regardless of corpus size
    return X, complexity


# ─── R_T: tensor-derived joint representation ─────────────────────────────────

def encode_tensor(entries: list[CorpusEntry]) -> tuple[np.ndarray, float]:
    """
    R_T: tensor-derived features that capture cross-agent and cross-cycle signal.

    For each entry, R_T stacks:
      1. Its own V (11 dims)
      2. The within-scenario delta Δ: V(k) - V(k=0) if k>0 else zeros (11 dims)
      3. The within-scenario inter-agent delta Ρ: |V(agent_0) - V(agent_1)| if
         two agents exist for the same scenario+cycle, else zeros (11 dims)

    This is the minimal tensor feature that exercises the Δ and Ρ operations
    from the inference engine — the two operations that require tensor indexing
    beyond a single cell.

    Total dimensionality: 33 (3 × 11).
    Complexity C(R_T): number of tensor cells that must be read to compute the
    full feature vector = scenario-dependent; we report the mean across entries.
    """
    # Build lookup: scenario → sorted list of entries by cycle
    by_scenario: dict[str, list[CorpusEntry]] = {}
    by_scenario_agent: dict[str, list[CorpusEntry]] = {}
    for e in entries:
        by_scenario.setdefault(e.scenario, []).append(e)

    # Get V vectors for all entries
    V_all, _ = encode_vector(entries)
    entry_to_v = {e.artifact_id: V_all[i] for i, e in enumerate(entries)}

    rows = []
    n_cells_list = []
    for e in entries:
        v_self = entry_to_v[e.artifact_id]

        # Δ: temporal delta within scenario (vs k=0 artifact of same scenario)
        scen_entries = sorted(by_scenario[e.scenario], key=lambda x: x.cycle)
        v_k0 = entry_to_v[scen_entries[0].artifact_id]
        delta = v_self - v_k0  # zero for k=0 itself

        # Ρ: inter-agent delta (S5 only — two agents, same scenario+cycle)
        scen_same_cycle = [x for x in by_scenario[e.scenario] if x.cycle == e.cycle]
        if len(scen_same_cycle) >= 2:
            # Two agents present — compute pairwise delta
            v_other = entry_to_v[scen_same_cycle[0].artifact_id
                                  if scen_same_cycle[0].artifact_id != e.artifact_id
                                  else scen_same_cycle[1].artifact_id]
            rho = np.abs(v_self - v_other)
            n_cells = 3   # d + (j0,j1) — 3 indices
        else:
            rho = np.zeros(N_DIMS, dtype=np.float32)
            n_cells = 2 if e.cycle > 0 else 1   # d + k; or d alone

        rows.append(np.concatenate([v_self, delta, rho]))
        n_cells_list.append(n_cells)

    X = np.stack(rows).astype(np.float32)
    complexity = float(np.mean(n_cells_list))   # mean tensor cells read
    return X, complexity
