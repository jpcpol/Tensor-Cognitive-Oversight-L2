# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — Shared statistical primitives.

Small, dependency-light effect-size and resampling helpers used across the
hypothesis scripts so the formulas are defined once and tested once.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


@dataclass(frozen=True)
class Estimate:
    """A point estimate with a (typically bootstrap) confidence interval."""
    value: float
    ci_low: float
    ci_high: float
    label: str = ""

    def fmt(self, p: int = 3) -> str:
        return f"{self.value:.{p}f} [{self.ci_low:.{p}f}, {self.ci_high:.{p}f}]"


def cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    """Cohen's d with pooled SD (a = treatment, b = control)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    s_pool = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    if s_pool == 0:
        return 0.0
    return float((a.mean() - b.mean()) / s_pool)


def hedges_g(a: Sequence[float], b: Sequence[float]) -> float:
    """Hedges' g — Cohen's d with small-sample bias correction."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a) + len(b)
    j = 1.0 - (3.0 / (4.0 * (n - 2) - 1.0)) if n > 2 else 1.0
    return float(cohens_d(a, b) * j)


def rank_biserial_from_u(u: float, n1: int, n2: int) -> float:
    """Rank-biserial correlation effect size for Mann-Whitney U."""
    return float(1.0 - (2.0 * u) / (n1 * n2))


def cliffs_delta(a: Sequence[float], b: Sequence[float]) -> float:
    """Cliff's delta — nonparametric effect size (a vs b), in [-1, 1]."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    gt = sum((x > b).sum() for x in a)
    lt = sum((x < b).sum() for x in a)
    n = len(a) * len(b)
    return float((gt - lt) / n) if n else float("nan")


def bootstrap_ci(
    stat_fn: Callable[..., float],
    *samples: Sequence[float],
    n_boot: int = 10_000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float, float]:
    """
    Percentile bootstrap CI for an arbitrary statistic over one or more samples.

    Each sample is resampled independently with replacement. Returns
    (point_estimate, ci_low, ci_high).
    """
    rng = np.random.default_rng(seed)
    arrs = [np.asarray(s, float) for s in samples]
    point = stat_fn(*arrs)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        resampled = [a[rng.integers(0, len(a), len(a))] for a in arrs]
        boots[i] = stat_fn(*resampled)
    lo, hi = np.nanpercentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(point), float(lo), float(hi)


def bootstrap_ci_paired(
    stat_fn: Callable[[np.ndarray, np.ndarray], float],
    x: Sequence[float],
    y: Sequence[float],
    n_boot: int = 10_000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float, float]:
    """
    Percentile bootstrap CI for a *paired* statistic (e.g. a correlation).

    Unlike `bootstrap_ci`, the same resampled row indices are applied to both
    x and y, preserving the pairing — essential for correlation/regression
    statistics, where independent resampling would collapse the estimate toward
    zero.
    """
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    point = stat_fn(x, y)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        boots[i] = stat_fn(x[idx], y[idx])
    lo, hi = np.nanpercentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(point), float(lo), float(hi)


def interpret_d(d: float) -> str:
    ad = abs(d)
    if np.isnan(d):
        return "n/a"
    if ad < 0.2:
        return "negligible"
    if ad < 0.5:
        return "small"
    if ad < 0.8:
        return "medium"
    return "large"


def stars(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"
