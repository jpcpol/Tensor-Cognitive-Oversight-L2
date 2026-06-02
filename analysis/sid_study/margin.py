# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-032 — Continuous detection-margin metric over a heterogeneous-basal ensemble.

Motivation
----------
The accuracy-based MI estimator (mi_estimator.py) saturates: P_structural=1.0 in
every scenario drives the Fano lower bound to I(R;Y)=H(Y), so SID_C*(R_T) differs
across scenarios ONLY through H(Y) and H_noise — numerical-sample artefacts at
n=2–4, not causal-information signal (audit, 2026-06-02).

A naive *static* detection margin does not fix this either: for S3 the tensor Δ
operation (V(k) − V(k0)) is an affine function of the per-artifact value V(k),
so on a single 4-point co-linear scenario it separates the causal classes
IDENTICALLY to an absolute V threshold. The tensor's real advantage in S3 is
OPERATIONAL: a relative threshold (Δ < −0.15) generalizes across projects whose
*healthy baseline* differs, whereas a fixed absolute threshold (V < 0.45) does
not. That advantage is only observable across HETEROGENEOUS baselines.

Heterogeneous-basal ensemble
----------------------------
Each scenario's healthy baseline is unknown and varies project-to-project. We
generate K replicas by shifting the whole scenario's operative dimension by
b ∈ BASAL_SHIFTS (progressively "healthier" projects). The fault structure is
relative to each replica's own baseline. Two detectors are scored on every
replica with balanced accuracy:

  Tensor (relative):   Δ = V − (scenario reference k0 / clean), fault if Δ < −0.15
                       (S5: inter-agent Ρ spread > 0.30 — basal-invariant).
                       Invariant to the basal shift → robust across replicas.

  Baseline (absolute): fault if V < 0.45 (fixed governance threshold).
                       Degrades as the basal rises: a relative fault no longer
                       falls below 0.45, and clean artifacts on a low basal fire
                       false positives. Non-robust across replicas.

Margins (mean balanced accuracy over the ensemble):

  M_tensor(s)    — tensor detector robustness (ordering tie-breaker, non-saturating)
  M_baseline(s)  — absolute detector robustness
  M_advantage(s) = M_tensor − M_baseline — the H_cross ordering statistic.

Empirically (corpus v1.0 + S3 fix): M_advantage = {S1:0, S2:0, S3:0.50,
S4:0, S5:0.30}, order S3 > S5 > {S1,S2,S4}, Spearman ρ(M_advantage, CCI) ≈ +0.92.
Direct faults (low CCI) give advantage 0 — the absolute detector handles large
drops even under basal variation; only the tensor-level faults (S3 Δ, S5 Ρ)
defeat it. This is the CCI hypothesis made numeric.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from probe import (
    OPERATIVE_DIM, DIM_IDX,
    FAULT_THRESHOLD,
)
from representations import encode_vector

# Structural decision thresholds (match probe.py).
S3_DELTA_THRESHOLD = -0.15   # cumulative technical_debt drop from baseline
S5_RHO_THRESHOLD = 0.30      # inter-agent |Δ| on the operative dimension
ABS_THRESHOLD = FAULT_THRESHOLD   # fixed absolute governance threshold (0.45)

# Heterogeneous healthy-basal shifts: project-to-project variation in "normal".
BASAL_SHIFTS = np.array([0.0, 0.05, 0.10, 0.15, 0.20])


@dataclass(frozen=True)
class MarginResult:
    scenario: str
    m_tensor: float        # mean balanced acc of the relative tensor detector
    m_baseline: float      # mean balanced acc of the absolute baseline detector
    m_advantage: float     # m_tensor - m_baseline (H_cross ordering statistic)
    degenerate: bool       # True when a causal class is absent (one-sided)
    note: str = ""


def _balanced_accuracy(pred: np.ndarray, y: np.ndarray) -> float:
    """Balanced accuracy: mean per-class recall (handles class skew at n<5)."""
    recalls = []
    for c in (0, 1):
        mask = y == c
        if mask.sum() > 0:
            recalls.append(float((pred[mask] == y[mask]).mean()))
    return float(np.mean(recalls)) if recalls else 0.0


def _tensor_pred(scenario: str, op: np.ndarray, k0_value: float) -> np.ndarray:
    """Relative tensor detector prediction for one replica.

    S3 → Δ from the scenario reference (k0); S5 → Ρ spread; others → Δ from the
    scenario clean reference (max operative value). All relative, so basal-invariant.
    """
    if scenario == "S5":
        spread = np.abs(op - op.mean())
        return (spread > S5_RHO_THRESHOLD).astype(int)
    if scenario == "S3":
        delta = op - k0_value
        return (delta < S3_DELTA_THRESHOLD).astype(int)
    # Direct faults: tensor reads V but relative to the scenario's clean reference.
    clean_ref = op.max()
    delta = op - clean_ref
    return (delta < S3_DELTA_THRESHOLD).astype(int)


def _baseline_pred(op: np.ndarray) -> np.ndarray:
    """Absolute baseline detector: fault if operative value below fixed threshold."""
    return (op < ABS_THRESHOLD).astype(int)


def compute_margin(scenario: str, scenario_entries: list,
                   y_causal: np.ndarray) -> MarginResult:
    """Compute M_tensor, M_baseline, M_advantage over the heterogeneous-basal ensemble.

    Note: this signature takes the scenario's CorpusEntry list (not the encoded
    tensor) because the ensemble re-encodes V per replica with a basal shift.
    """
    y = np.asarray(y_causal, dtype=int)
    has_clean = int((y == 0).sum()) > 0
    has_fault = int((y == 1).sum()) > 0
    degenerate = not (has_clean and has_fault)

    V, _ = encode_vector(scenario_entries)
    d = DIM_IDX[OPERATIVE_DIM[scenario]]
    base_op = V[:, d].copy()
    cycles = np.array([e.cycle for e in scenario_entries])
    k0_idx = int(np.argmin(cycles))

    t_accs, b_accs = [], []
    for shift in BASAL_SHIFTS:
        op = np.clip(base_op + shift, 0.0, 1.0)
        t_pred = _tensor_pred(scenario, op, op[k0_idx])
        b_pred = _baseline_pred(op)
        t_accs.append(_balanced_accuracy(t_pred, y))
        b_accs.append(_balanced_accuracy(b_pred, y))

    m_tensor = float(np.mean(t_accs))
    m_baseline = float(np.mean(b_accs))

    note = ""
    if degenerate:
        note = ("only one causal class present in corpus v1.0 — margin is "
                "one-sided; see DT-034 for the clean-pair extension")

    return MarginResult(
        scenario=scenario,
        m_tensor=m_tensor,
        m_baseline=m_baseline,
        m_advantage=m_tensor - m_baseline,
        degenerate=degenerate,
        note=note,
    )
