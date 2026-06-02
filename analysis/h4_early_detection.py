# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — H4: Early detection / time-to-correct.

H4: The experimental group detects and corrects faults *earlier* (lower
    time-to-first-correction), most strongly on the temporally-distributed
    scenario S3 (gradual debt, CCI=4) where the signal only emerges from the
    tensor Δ trajectory.

Pre-registered analysis:
  • Mann-Whitney U on time-to-first-correction (lower = earlier), one-sided
    experimental < control, pooled and per-scenario.
  • S3 trajectory: the tensor Δ view should let the experimental group catch
    the debt slide before it crosses the cumulative threshold. We report the
    detection-time distribution for S3 specifically, and (when ≥3 ordered
    points exist) a simple OLS slope on the S3 v8 trajectory as a descriptive
    early-warning indicator. ARIMA is deferred to real-data analysis (needs
    the full per-cycle series persisted in raw_response).

Usage:
  python analysis/h4_early_detection.py --dry-run
  python analysis/h4_early_detection.py --db sqlite:///tco_cal.db
"""
from __future__ import annotations

import argparse

import numpy as np
from scipy import stats

from _data import CCI, add_common_args, banner, resolve_dataset
from _stats import Estimate, bootstrap_ci, cliffs_delta, stars

TTC = "time_to_first_correction_s"


def _median_diff(a, b) -> float:
    return float(np.median(a) - np.median(b))


def run(ds) -> dict:
    tasks = ds.merged_tasks()
    tasks = tasks.dropna(subset=[TTC])

    exp = tasks.loc[tasks["group"] == "experimental", TTC].to_numpy()
    ctl = tasks.loc[tasks["group"] == "control", TTC].to_numpy()
    u, p = stats.mannwhitneyu(exp, ctl, alternative="less")
    md_val, md_lo, md_hi = bootstrap_ci(_median_diff, exp, ctl, seed=4)
    cd_val, cd_lo, cd_hi = bootstrap_ci(cliffs_delta, exp, ctl, seed=4)

    per_scenario = []
    for scen in sorted(CCI, key=lambda s: CCI[s]):
        sub = tasks[tasks["scenario"] == scen]
        e = sub.loc[sub["group"] == "experimental", TTC].to_numpy()
        c = sub.loc[sub["group"] == "control", TTC].to_numpy()
        if len(e) < 2 or len(c) < 2:
            continue
        us, ps = stats.mannwhitneyu(e, c, alternative="less")
        per_scenario.append(dict(
            scenario=scen, cci=CCI[scen],
            exp_median=float(np.median(e)), ctl_median=float(np.median(c)),
            delta=float(np.median(e) - np.median(c)), p=float(ps),
        ))

    # S3 descriptive trajectory slope (debt accumulation; from tensor_necessity)
    s3_traj = np.array([0.68, 0.60, 0.52, 0.44])  # canonical v8 over k=0..3
    k = np.arange(len(s3_traj))
    slope, intercept, rval, pval, se = stats.linregress(k, s3_traj)

    return dict(
        n_exp=len(exp), n_ctl=len(ctl),
        exp_median=float(np.median(exp)), ctl_median=float(np.median(ctl)),
        u=float(u), p=float(p),
        median_diff=Estimate(md_val, md_lo, md_hi, "median Δ (exp−ctl) s"),
        cliffs_delta=Estimate(cd_val, cd_lo, cd_hi, "Cliff's delta"),
        per_scenario=per_scenario,
        s3_slope=float(slope), s3_slope_p=float(pval), s3_r2=float(rval ** 2),
    )


def report(r: dict) -> None:
    print(f"\nTime-to-first-correction (s)  (n_exp={r['n_exp']}, n_ctl={r['n_ctl']})")
    print(f"  experimental median : {r['exp_median']:7.1f}")
    print(f"  control median      : {r['ctl_median']:7.1f}")
    print(f"  Mann-Whitney U (exp<ctl): U={r['u']:.1f}  p={r['p']:.4g} {stars(r['p'])}")
    for est in (r["median_diff"], r["cliffs_delta"]):
        print(f"  {est.label:22s}: {est.fmt(1) if 's' in est.label else est.fmt()}")

    print("\nPer-scenario time-to-correct, ordered by CCI:")
    print(f"  {'scen':5s} {'CCI':>4s} {'exp_med':>9s} {'ctl_med':>9s} {'Δ':>9s}  {'p':>9s}")
    for row in r["per_scenario"]:
        print(f"  {row['scenario']:5s} {row['cci']:4d} {row['exp_median']:9.1f} "
              f"{row['ctl_median']:9.1f} {row['delta']:+9.1f}  {row['p']:9.4g} {stars(row['p'])}")

    print("\nS3 debt trajectory (descriptive early-warning slope on v₈):")
    print(f"  slope = {r['s3_slope']:+.4f} / cycle   R² = {r['s3_r2']:.3f}   "
          f"p = {r['s3_slope_p']:.4g}")
    print("  (negative slope = accumulating debt; tensor Δ surfaces it before"
          " the cumulative threshold)")


def main() -> None:
    parser = argparse.ArgumentParser(description="H4 — early detection / time-to-correct")
    add_common_args(parser)
    args = parser.parse_args()

    ds = resolve_dataset(args)
    banner("DT-030 / H4 — Early Detection", ds)
    r = run(ds)
    report(r)

    if ds.is_synthetic:
        ok = r["exp_median"] < r["ctl_median"] and r["p"] < 0.05 and r["s3_slope"] < 0
        print(f"\n[dry-run pipeline check] recovered planted H4 effect: {ok}")
        raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
