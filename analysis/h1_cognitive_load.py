# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — H1: Cognitive load.

H1: The TCO Dashboard (experimental) reduces operator cognitive load relative
    to traditional HITL review (control), measured by NASA Raw-TLX.

Pre-registered analysis:
  • Primary: Mann-Whitney U on Raw-TLX (post_t4 checkpoint), one-sided
    (experimental < control). TLX is ordinal/bounded → nonparametric.
  • Effect size: Cohen's d + rank-biserial, both with bootstrap 95% CIs.
  • Per-subscale exploratory breakdown (which load component moves).

  NOTE (consultant): Raw-TLX is a secondary/triangulating measure, not the
  causal claim of the program. H_OBS (h_obs_causal.py) is primary. Reported
  here for completeness and to flag the circularity caveat (a richer display
  can raise *some* TLX subscales while lowering global load).

Usage:
  python analysis/h1_cognitive_load.py --dry-run
  python analysis/h1_cognitive_load.py --db sqlite:///tco_cal.db
"""
from __future__ import annotations

import argparse

import numpy as np
from scipy import stats

from _data import TLX_SUBSCALES, add_common_args, banner, raw_tlx, resolve_dataset
from _stats import (Estimate, bootstrap_ci, cohens_d, interpret_d,
                    rank_biserial_from_u, stars)

CHECKPOINT = "post_t4"  # heaviest load checkpoint (follows S5, CCI=3)


def run(ds) -> dict:
    tlx = ds.merged_tlx()
    tlx = tlx[tlx["checkpoint"] == CHECKPOINT].copy()
    tlx["raw_tlx"] = tlx.apply(raw_tlx, axis=1)

    exp = tlx.loc[tlx["group"] == "experimental", "raw_tlx"].to_numpy()
    ctl = tlx.loc[tlx["group"] == "control", "raw_tlx"].to_numpy()

    # Mann-Whitney U, one-sided: experimental load < control load
    u, p = stats.mannwhitneyu(exp, ctl, alternative="less")
    rbc = rank_biserial_from_u(u, len(exp), len(ctl))

    d_val, d_lo, d_hi = bootstrap_ci(cohens_d, exp, ctl, seed=1)
    d_est = Estimate(d_val, d_lo, d_hi, "Cohen's d (exp−ctl)")

    # Per-subscale exploratory (Mann-Whitney per subscale)
    subscales = {}
    for s in TLX_SUBSCALES:
        e = tlx.loc[tlx["group"] == "experimental", s].to_numpy()
        c = tlx.loc[tlx["group"] == "control", s].to_numpy()
        us, ps = stats.mannwhitneyu(e, c, alternative="two-sided")
        subscales[s] = dict(exp_mean=float(np.mean(e)), ctl_mean=float(np.mean(c)),
                            u=float(us), p=float(ps))

    return dict(
        checkpoint=CHECKPOINT,
        n_exp=len(exp), n_ctl=len(ctl),
        exp_mean=float(np.mean(exp)), ctl_mean=float(np.mean(ctl)),
        u=float(u), p=float(p), rank_biserial=rbc, cohens_d=d_est,
        subscales=subscales,
    )


def report(r: dict) -> None:
    print(f"\nRaw-TLX @ {r['checkpoint']}  (n_exp={r['n_exp']}, n_ctl={r['n_ctl']})")
    print(f"  experimental mean : {r['exp_mean']:6.2f}")
    print(f"  control mean      : {r['ctl_mean']:6.2f}")
    print(f"  difference        : {r['exp_mean'] - r['ctl_mean']:+6.2f}")
    print(f"\nMann-Whitney U (one-sided, exp<ctl): U={r['u']:.1f}  p={r['p']:.4g} {stars(r['p'])}")
    print(f"  rank-biserial r   : {r['rank_biserial']:+.3f}")
    d = r["cohens_d"]
    print(f"  {d.label:22s}: {d.fmt()}  ({interpret_d(d.value)})")

    print("\nPer-subscale (exploratory, two-sided):")
    print(f"  {'subscale':18s} {'exp':>7s} {'ctl':>7s} {'Δ':>7s}  {'p':>8s}")
    for s, v in r["subscales"].items():
        delta = v["exp_mean"] - v["ctl_mean"]
        print(f"  {s:18s} {v['exp_mean']:7.1f} {v['ctl_mean']:7.1f} {delta:+7.1f}  "
              f"{v['p']:8.4g} {stars(v['p'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description="H1 — cognitive load (NASA Raw-TLX)")
    add_common_args(parser)
    args = parser.parse_args()

    ds = resolve_dataset(args)
    banner("DT-030 / H1 — Cognitive Load", ds)
    r = run(ds)
    report(r)

    # Dry-run gate: synthetic data plants exp < ctl → must recover direction.
    if ds.is_synthetic:
        ok = r["exp_mean"] < r["ctl_mean"] and r["p"] < 0.05
        print(f"\n[dry-run pipeline check] recovered planted H1 effect: {ok}")
        raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
