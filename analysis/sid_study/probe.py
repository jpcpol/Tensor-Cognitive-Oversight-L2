# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-032 — Probes: linear and structural.

Two probing methods:

  P_linear (R, y)
      Logistic regression with L2 regularization trained on representation R
      to predict label y. Accuracy is estimated with leave-one-out (LOO)
      cross-validation — the only unbiased estimator available for n=12.
      Returns: accuracy ∈ [0,1] and balanced accuracy (handles class skew).

  P_structural (R_T, y)
      For the tensor representation only: reads the fault signal directly from
      the pre-specified tensor index without any learning. This is the upper
      bound for R_T — if a human *knows* to look at the right index, can they
      see the fault? Measures I(index; y) directly.

      Each scenario has a pre-specified "operative dimension":
        S1 → security_risk (d=3)
        S2 → architectural_alignment (d=1)
        S3 → technical_debt trajectory (d=7, delta feature)
        S4 → observability_coverage (d=4)
        S5 → rho(security_risk, testability) (d=3 and d=5 in the Ρ block)

      P_structural computes the threshold-based detection accuracy using the
      ground-truth CCI-specified operation, without any training.

The distinction matters for SID:
  - P_linear accuracy = what ANY learner can extract from R (statistical capacity)
  - P_structural accuracy = what the TCO inference engine extracts from R_T
    (operational capacity, always ≥ P_linear for a well-designed system)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ─── Constants ────────────────────────────────────────────────────────────────

# Tensor R_T block layout: [V (11), Δ (11), Ρ (11)] → indices
V_OFFSET, DELTA_OFFSET, RHO_OFFSET = 0, 11, 22

# Per-scenario operative dimension (0-indexed, matching DIM_NAMES)
DIM_IDX = {
    "security_risk": 3,
    "architectural_alignment": 1,
    "technical_debt": 7,
    "observability_coverage": 4,
    "testability": 5,
}

OPERATIVE_DIM: dict[str, str] = {
    "S1": "security_risk",
    "S2": "architectural_alignment",
    "S3": "technical_debt",   # uses Δ block
    "S4": "observability_coverage",
    "S5": "security_risk",    # uses Ρ block (Δ(security_risk, testability))
}

# Detection threshold: value below this → fault signal present
FAULT_THRESHOLD = 0.45


@dataclass(frozen=True)
class ProbeResult:
    method: Literal["linear", "structural"]
    representation: str          # "raw", "V", "T"
    accuracy: float              # LOO accuracy (linear) or threshold accuracy (structural)
    balanced_accuracy: float
    n_samples: int
    scenario: str                # scenario the probe was applied to, or "all"
    note: str = ""


# ─── P_linear ─────────────────────────────────────────────────────────────────

def probe_linear(
    X: np.ndarray,
    y_labels: list[str] | np.ndarray,
    representation: str,
    scenario: str = "all",
    C: float = 1.0,
    random_state: int = 42,
) -> ProbeResult:
    """
    LOO logistic regression probe.

    With n=12 the training set is 11 samples per fold — linear regression is
    appropriate (avoids overfitting). Stratified k-fold is not possible at
    n=12 with 3 classes, so LOO is the correct choice per Belinkov (2022).
    """
    le = LabelEncoder()
    y = le.fit_transform(y_labels)
    n = len(y)

    if n < 3:
        return ProbeResult("linear", representation, float("nan"),
                           float("nan"), n, scenario, "too few samples")

    loo = LeaveOneOut()
    scaler = StandardScaler()
    preds = np.empty(n, dtype=int)

    for train_idx, test_idx in loo.split(X):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr = y[train_idx]

        X_tr_sc = scaler.fit_transform(X_tr)
        X_te_sc = scaler.transform(X_te)

        # Reduced C when training set is small to avoid degenerate solutions
        clf = LogisticRegression(
            C=C, max_iter=1000, solver="lbfgs",
            random_state=random_state,
        )
        try:
            clf.fit(X_tr_sc, y_tr)
            preds[test_idx] = clf.predict(X_te_sc)
        except Exception:
            preds[test_idx] = y_tr[0]   # fallback: majority class

    acc = float(np.mean(preds == y))
    bal_acc = float(balanced_accuracy_score(y, preds))
    return ProbeResult("linear", representation, acc, bal_acc, n, scenario)


# ─── P_structural ─────────────────────────────────────────────────────────────

def probe_structural(
    X_T: np.ndarray,
    entries_for_scenario: list,
    scenario: str,
) -> ProbeResult:
    """
    Threshold-based detection from the operative tensor index — no learning.

    Uses the CCI-specified operation for each scenario:
      S1, S2, S4 → V block, operative dimension
      S3          → Δ block, technical_debt (cumulative drop > 0.15)
      S5          → Ρ block, security_risk delta > 0.30

    y_true is the causal_label from each entry (1 = fault's causal structure
    is present, 0 = not present or clean).
    """
    from representations import DIM_NAMES  # noqa

    dim = OPERATIVE_DIM.get(scenario, "security_risk")
    d = DIM_IDX[dim]
    y_true = np.array([e.causal_label for e in entries_for_scenario], dtype=int)
    n = len(y_true)

    if n == 0:
        return ProbeResult("structural", "T", float("nan"), float("nan"),
                           0, scenario, "no entries")

    preds = np.zeros(n, dtype=int)

    if scenario == "S3":
        # Δ operation: cumulative technical_debt drop in the delta block
        delta_val = X_T[:, DELTA_OFFSET + d]   # V(k) - V(k=0) in T dimension
        preds = (delta_val < -0.15).astype(int)   # debt dropped > 0.15 from baseline

    elif scenario == "S5":
        # Ρ operation: |security_risk(j0) - security_risk(j1)| > 0.30
        rho_sec = X_T[:, RHO_OFFSET + DIM_IDX["security_risk"]]
        rho_test = X_T[:, RHO_OFFSET + DIM_IDX["testability"]]
        preds = ((rho_sec > 0.30) | (rho_test > 0.30)).astype(int)

    else:
        # Direct read: operative dimension in V block below fault threshold
        v_val = X_T[:, V_OFFSET + d]
        preds = (v_val < FAULT_THRESHOLD).astype(int)

    acc = float(np.mean(preds == y_true))
    bal_acc = float(balanced_accuracy_score(y_true, preds))
    return ProbeResult("structural", "T", acc, bal_acc, n, scenario)
