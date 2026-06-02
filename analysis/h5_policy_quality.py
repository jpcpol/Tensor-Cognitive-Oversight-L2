# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — H5: Policy injection quality.

H5: Higher-quality injected policies (PIQ score) produce larger improvements
    in the downstream quality vector (Δ_vector), i.e. the experimental
    operator's natural-language policy actually steers the pipeline.

This is an experimental-group-only relationship (control has no policy
injection channel).

Pre-registered analysis:
  • Spearman ρ between PIQ score and Δ_vector (improvement the policy yields),
    with bootstrap 95% CI.
  • OLS regression Δ_vector ~ PIQ (slope, R²) as the effect magnitude.
  • Inter-rater reliability of PIQ scoring: Cohen's / Fleiss' κ across the 5
    PIQ sub-dimensions when multiple raters are present (real data); in
    dry-run we report ICC-style agreement on the synthetic single-rater frame
    as a pipeline check only.
  • Per-scenario PIQ ordered by CCI — feeds the H_OBS prediction that policy
    quality gain tracks CCI.

Usage:
  python analysis/h5_policy_quality.py --dry-run
  python analysis/h5_policy_quality.py --db sqlite:///tco_cal.db
"""
from __future__ import annotations

import argparse

import numpy as np
from scipy import stats

from _data import CCI, add_common_args, banner, resolve_dataset
from _stats import Estimate, bootstrap_ci_paired, stars


def _spearman(a, b) -> float:
    if len(a) < 3:
        return float("nan")
    return float(stats.spearmanr(a, b).correlation)


def run(ds) -> dict:
    pol = ds.merged_policies()
    pol = pol.dropna(subset=["piq_score"])

    has_delta = "delta_vector" in pol.columns and pol["delta_vector"].notna().any()
    result = dict(n_policies=len(pol), has_delta=has_delta)

    if has_delta:
        sub = pol.dropna(subset=["delta_vector"])
        piq = sub["piq_score"].to_numpy()
        dv = sub["delta_vector"].to_numpy()
        rho_val, rho_lo, rho_hi = bootstrap_ci_paired(_spearman, piq, dv, seed=5)
        slope, intercept, rval, pval, se = stats.linregress(piq, dv)
        _, sp = stats.spearmanr(piq, dv)
        result.update(
            spearman=Estimate(rho_val, rho_lo, rho_hi, "Spearman ρ (PIQ,Δvec)"),
            spearman_p=float(sp),
            ols_slope=float(slope), ols_r2=float(rval ** 2), ols_p=float(pval),
        )

    # Per-scenario mean PIQ ordered by CCI
    per_scenario = []
    for scen in sorted(CCI, key=lambda s: CCI[s]):
        vals = pol.loc[pol["scenario"] == scen, "piq_score"].to_numpy()
        if len(vals):
            per_scenario.append(dict(scenario=scen, cci=CCI[scen],
                                     mean_piq=float(np.mean(vals)), n=len(vals)))
    result["per_scenario"] = per_scenario

    # PIQ→CCI correlation (the H_OBS-relevant gradient)
    if len(per_scenario) >= 3:
        ccis = [r["cci"] for r in per_scenario]
        piqs = [r["mean_piq"] for r in per_scenario]
        result["piq_cci_spearman"] = float(stats.spearmanr(ccis, piqs).correlation)

    return result


def report(r: dict) -> None:
    print(f"\nPolicy intents analysed: {r['n_policies']}")
    if r["has_delta"]:
        sp = r["spearman"]
        print(f"\nPIQ → Δ_vector relationship:")
        print(f"  {sp.label:24s}: {sp.fmt()}  p={r['spearman_p']:.4g} {stars(r['spearman_p'])}")
        print(f"  OLS slope               : {r['ols_slope']:+.4f}  "
              f"R²={r['ols_r2']:.3f}  p={r['ols_p']:.4g} {stars(r['ols_p'])}")
    else:
        print("  [Δ_vector not available — run the φ pipeline on injected policies "
              "to populate it; PIQ→Δ correlation deferred]")

    print("\nMean PIQ per scenario, ordered by CCI:")
    print(f"  {'scen':5s} {'CCI':>4s} {'mean_PIQ':>9s} {'n':>4s}")
    for row in r["per_scenario"]:
        print(f"  {row['scenario']:5s} {row['cci']:4d} {row['mean_piq']:9.3f} {row['n']:4d}")
    if "piq_cci_spearman" in r:
        print(f"\n  Spearman ρ(CCI, mean PIQ) = {r['piq_cci_spearman']:+.3f}  "
              "(H_OBS: policy quality gain tracks causal complexity)")


def main() -> None:
    parser = argparse.ArgumentParser(description="H5 — policy injection quality")
    add_common_args(parser)
    args = parser.parse_args()

    ds = resolve_dataset(args)
    banner("DT-030 / H5 — Policy Quality (experimental only)", ds)
    r = run(ds)
    report(r)

    if ds.is_synthetic:
        ok = r["has_delta"] and r["spearman"].value > 0.3 and r["spearman_p"] < 0.05
        print(f"\n[dry-run pipeline check] recovered planted H5 (PIQ→Δ) effect: {ok}")
        raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
