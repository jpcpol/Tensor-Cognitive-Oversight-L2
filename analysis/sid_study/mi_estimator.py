# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-032 — Mutual Information estimator: I(R; Y) from probe accuracy.

The relationship between probe accuracy and mutual information:

  For a k-class problem with balanced classes, an accuracy-based lower bound on
  I(R; Y) is:

      I(R; Y) ≥ H(Y) + P_acc × log(P_acc) + (1 - P_acc) × log((1-P_acc)/(k-1))
             = H(Y) - H_binary(P_acc) - (1 - P_acc) × log(k-1)

  where H(Y) = log(k) for balanced classes (worst-case assumption for our small
  corpus). This is Fano's inequality rearranged, providing a conservative
  lower bound.

  For the structural probe (P_structural), we use the direct empirical accuracy
  as a surrogate since it has no training variance — it's a fixed threshold rule.

Complexity C(R):

  The complexity term in SID*(R) = I(R;Y)/(C(R)+λ·H_noise(R)) normalizes by
  the cost of accessing the representation. We use:

    C(R_raw) = log(1 + vocab_size)   — number of distinct tokens encoded
    C(R_V)   = 11                    — dimensionality (fixed)
    C(R_T)   = mean_n_cells_read     — mean tensor cells accessed (from encoders)

Noise entropy H_noise(R):

  H_noise captures within-representation variance that doesn't correlate with Y.
  We estimate it as the entropy of the residuals after projecting out the
  Y-correlated component: H_noise ≈ H(R | first_linear_component).
  With n=12 this is approximated as the mean column entropy of R after
  standardization, minus the entropy explained by y.

  λ (lambda) is a weighting hyperparameter; default λ=0.1 as pre-registered
  in CAL_Benchmark_v1.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class MIEstimate:
    representation: str
    label_type: Literal["D", "C"]      # D = decision, C = causal structure
    probe_accuracy: float
    balanced_accuracy: float
    mi_lower_bound: float              # I(R;Y) lower bound via Fano
    complexity: float                  # C(R)
    h_noise: float                     # H_noise(R) estimate
    n_classes: int
    n_samples: int


LAMBDA = 0.10   # pre-registered (CAL_Benchmark_v1.md)


def _fano_mi_lower_bound(accuracy: float, n_classes: int, h_y: float) -> float:
    """
    Mutual information lower bound from probe accuracy via Fano's inequality.

    I(R; Y) ≥ H(Y) - H(e) where e is the error probability, and
    H(e) = -P_e log P_e - (1-P_e) log((1-P_e)/(k-1)) for k classes.
    """
    eps = max(1e-10, min(1 - 1e-10, 1.0 - accuracy))
    p_correct = 1.0 - eps

    # Conditional entropy upper bound (Fano)
    if n_classes <= 1:
        return 0.0
    log_k_minus_1 = np.log(n_classes - 1) if n_classes > 1 else 0.0
    h_fano = -(eps * np.log(max(eps, 1e-10)) +
               p_correct * np.log(max(p_correct, 1e-10)) +
               (1 - p_correct) * log_k_minus_1 if n_classes > 1 else 0)
    return float(max(0.0, h_y - h_fano))


def _entropy_from_counts(values: np.ndarray) -> float:
    """Shannon entropy H(X) from a 1-D array of discrete or continuous values."""
    _, counts = np.unique(np.round(values, 2), return_counts=True)
    p = counts / counts.sum()
    return float(-np.sum(p * np.log(p + 1e-12)))


def estimate_h_noise(X: np.ndarray, y: np.ndarray) -> float:
    """
    Approximate noise entropy: residual column entropy after removing the
    component aligned with y.  Conservative: uses mean column entropy of X
    minus the contribution of the first linear discriminant.
    """
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

    if len(np.unique(y)) < 2 or X.shape[1] == 0:
        return 0.0
    try:
        lda = LinearDiscriminantAnalysis(n_components=1)
        proj = lda.fit_transform(X, y).ravel()   # explained component
        explained_h = _entropy_from_counts(proj)
        total_h = float(np.mean([_entropy_from_counts(X[:, j]) for j in range(X.shape[1])]))
        return float(max(0.0, total_h - explained_h))
    except Exception:
        return float(np.mean([_entropy_from_counts(X[:, j]) for j in range(X.shape[1])]))


def estimate_mi(
    X: np.ndarray,
    y_labels: list[str] | np.ndarray,
    probe_acc: float,
    bal_acc: float,
    complexity: float,
    representation: str,
    label_type: Literal["D", "C"],
) -> MIEstimate:
    """
    Wrap probe accuracy into an MI estimate and compute SID inputs.
    """
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y = le.fit_transform(y_labels)
    n_classes = len(le.classes_)
    n = len(y)

    # H(Y): use empirical class distribution
    _, counts = np.unique(y, return_counts=True)
    p = counts / counts.sum()
    h_y = float(-np.sum(p * np.log(p + 1e-12)))

    mi_lb = _fano_mi_lower_bound(probe_acc, n_classes, h_y)
    h_noise = estimate_h_noise(X, y)

    return MIEstimate(
        representation=representation,
        label_type=label_type,
        probe_accuracy=probe_acc,
        balanced_accuracy=bal_acc,
        mi_lower_bound=mi_lb,
        complexity=complexity,
        h_noise=h_noise,
        n_classes=n_classes,
        n_samples=n,
    )


def sid_star(mi: MIEstimate, lam: float = LAMBDA) -> float:
    """
    SID*(R) = I(R;Y) / (C(R) + λ · H_noise(R))

    Higher is better: a representation that is both informative about Y AND
    compact AND low-noise achieves the highest SID*.

    Returns 0 if denominator is zero.
    """
    denom = mi.complexity + lam * mi.h_noise
    if denom < 1e-10:
        return 0.0
    return float(mi.mi_lower_bound / denom)
