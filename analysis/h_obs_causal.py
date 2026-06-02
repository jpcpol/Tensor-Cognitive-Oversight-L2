# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — H_OBS: causal observability (PRIMARY hypothesis).

H_OBS: The benefit of the TCO Dashboard scales with the Causal Complexity
       Index (CCI) of the scenario. Formally, the Group × CCI interaction is
       positive: the experimental advantage is small/absent for low-CCI
       scenarios (S1, S4) and large for high-CCI scenarios (S3, S5).

       Operational prediction (pre-registered):
           ΔPIQ(S3, S5)  >>  ΔPIQ(S1, S4)
       and, on the shared accuracy outcome, the Group × CCI interaction term
       is significant and positive.

This is the program's central claim under the causal-observability reframing
(CAL_Benchmark_v1.md). H1/H2/H4/H5 are secondary / triangulating.

Design note: CCI is a between-scenario (within-participant) factor; Group is
between-participants. Each participant sees all scenarios → mixed (split-plot)
ANOVA on the accuracy outcome, with the Group × CCI(-as-ordinal) interaction
as the term of interest. We complement the omnibus ANOVA with a directly
pre-registered contrast: mean experimental−control gap on {S3,S5} vs {S1,S4}.

Usage:
  python analysis/h_obs_causal.py --dry-run
  python analysis/h_obs_causal.py --db sqlite:///tco_cal.db
"""
from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd
from scipy import stats

from _data import CCI, add_common_args, banner, resolve_dataset
from _stats import Estimate, bootstrap_ci, cohens_d, interpret_d, stars

HIGH_CCI = ["S3", "S5"]   # CCI 4, 3 — invisible / hard for raw review
LOW_CCI = ["S1", "S4"]    # CCI 1, 2 — visible in a single artifact


def _gap_contrast(exp_hi, ctl_hi, exp_lo, ctl_lo) -> float:
    """Pre-registered contrast: (gap on high-CCI) − (gap on low-CCI)."""
    return float((np.mean(exp_hi) - np.mean(ctl_hi)) - (np.mean(exp_lo) - np.mean(ctl_lo)))


def run(ds) -> dict:
    tasks = ds.merged_tasks().copy()
    tasks["cci"] = tasks["scenario"].map(CCI)
    tasks = tasks.dropna(subset=["cci", "accuracy"])

    result: dict = {}

    # ── 1) Mixed ANOVA: accuracy ~ Group (between) * CCI (within) ──
    # Average accuracy per participant × cci level so cci is a clean within factor.
    cell = (tasks.groupby(["participant_id", "group", "cci"], as_index=False)["accuracy"]
            .mean())
    try:
        import pingouin as pg
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            aov = pg.mixed_anova(data=cell, dv="accuracy", within="cci",
                                 between="group", subject="participant_id")
        # pingouin ≥0.5.4 names the uncorrected p-value column "p-unc";
        # ≥0.6 renames it "p_unc". Support both.
        p_col = "p-unc" if "p-unc" in aov.columns else "p_unc"
        inter = aov[aov["Source"] == "Interaction"]
        if len(inter):
            row = inter.iloc[0]
            result["anova"] = dict(
                F=float(row["F"]), p=float(row[p_col]),
                np2=float(row.get("np2", np.nan)),
                df1=float(row["DF1"]), df2=float(row["DF2"]),
            )
        result["anova_table"] = aov[["Source", "F", p_col]].to_dict("records")
    except Exception as exc:  # pragma: no cover — pingouin optional
        result["anova_error"] = str(exc)

    # ── 2) Pre-registered contrast: ΔPIQ / Δaccuracy high-CCI vs low-CCI ──
    def grp(scs, g):
        return tasks[(tasks["scenario"].isin(scs)) & (tasks["group"] == g)]["accuracy"].to_numpy()

    exp_hi, ctl_hi = grp(HIGH_CCI, "experimental"), grp(HIGH_CCI, "control")
    exp_lo, ctl_lo = grp(LOW_CCI, "experimental"), grp(LOW_CCI, "control")

    gap_hi = float(np.mean(exp_hi) - np.mean(ctl_hi))
    gap_lo = float(np.mean(exp_lo) - np.mean(ctl_lo))
    c_val, c_lo, c_hi = bootstrap_ci(_gap_contrast, exp_hi, ctl_hi, exp_lo, ctl_lo, seed=6)

    # Mann-Whitney on the per-participant (high−low) gap-of-gaps direction:
    # build per-participant high-CCI mean minus low-CCI mean, compare groups.
    pp = (tasks.assign(band=np.where(tasks["scenario"].isin(HIGH_CCI), "hi",
                                     np.where(tasks["scenario"].isin(LOW_CCI), "lo", "mid")))
          .query("band in ['hi','lo']")
          .pivot_table(index=["participant_id", "group"], columns="band",
                       values="accuracy", aggfunc="mean")
          .reset_index())
    pp["hi_minus_lo"] = pp["hi"] - pp["lo"]
    e = pp.loc[pp["group"] == "experimental", "hi_minus_lo"].to_numpy()
    cc = pp.loc[pp["group"] == "control", "hi_minus_lo"].to_numpy()
    u, p_contrast = stats.mannwhitneyu(e, cc, alternative="greater")
    d_val, d_lo, d_hi = bootstrap_ci(cohens_d, e, cc, seed=6)

    result.update(
        gap_high_cci=gap_hi, gap_low_cci=gap_lo,
        contrast=Estimate(c_val, c_lo, c_hi, "ΔΔ accuracy (hi−lo CCI)"),
        contrast_u=float(u), contrast_p=float(p_contrast),
        contrast_d=Estimate(d_val, d_lo, d_hi, "Cohen's d (hi−lo gap)"),
    )

    # ── 3) Effect-by-CCI table (gap per CCI level, for the slope visual) ──
    by_cci = []
    for c in sorted(tasks["cci"].unique()):
        sub = tasks[tasks["cci"] == c]
        eg = sub.loc[sub["group"] == "experimental", "accuracy"].mean()
        cg = sub.loc[sub["group"] == "control", "accuracy"].mean()
        by_cci.append(dict(cci=int(c), gap=float(eg - cg)))
    result["gap_by_cci"] = by_cci
    if len(by_cci) >= 3:
        ccis = [r["cci"] for r in by_cci]
        gaps = [r["gap"] for r in by_cci]
        sl, _, rval, pval, _ = stats.linregress(ccis, gaps)
        result["gap_slope"] = dict(slope=float(sl), r2=float(rval ** 2), p=float(pval))

    return result


def report(r: dict) -> None:
    print("\n[Primary] Group × CCI interaction (mixed ANOVA on accuracy):")
    if "anova" in r:
        a = r["anova"]
        print(f"  F({a['df1']:.0f},{a['df2']:.0f}) = {a['F']:.3f}   "
              f"p = {a['p']:.4g} {stars(a['p'])}   partial η² = {a['np2']:.3f}")
    elif "anova_error" in r:
        print(f"  [ANOVA unavailable: {r['anova_error']}]")

    print("\n[Pre-registered contrast] experimental−control accuracy gap:")
    print(f"  high-CCI (S3,S5) gap : {r['gap_high_cci']:+.3f}")
    print(f"  low-CCI  (S1,S4) gap : {r['gap_low_cci']:+.3f}")
    print(f"  {r['contrast'].label:24s}: {r['contrast'].fmt()}")
    print(f"  Mann-Whitney (hi−lo, exp>ctl): U={r['contrast_u']:.1f}  "
          f"p={r['contrast_p']:.4g} {stars(r['contrast_p'])}")
    cd = r["contrast_d"]
    print(f"  {cd.label:24s}: {cd.fmt()}  ({interpret_d(cd.value)})")

    print("\nExperimental advantage as a function of CCI:")
    print(f"  {'CCI':>4s} {'gap':>8s}")
    for row in r["gap_by_cci"]:
        print(f"  {row['cci']:4d} {row['gap']:+8.3f}")
    if "gap_slope" in r:
        s = r["gap_slope"]
        print(f"  slope = {s['slope']:+.4f} gap/CCI   R² = {s['r2']:.3f}   "
              f"p = {s['p']:.4g}")
        print("  → positive slope is the H_OBS signature: benefit ∝ causal complexity")


def main() -> None:
    parser = argparse.ArgumentParser(description="H_OBS — causal observability (PRIMARY)")
    add_common_args(parser)
    args = parser.parse_args()

    ds = resolve_dataset(args)
    banner("DT-030 / H_OBS — Causal Observability (PRIMARY)", ds)
    r = run(ds)
    report(r)

    if ds.is_synthetic:
        slope_ok = r.get("gap_slope", {}).get("slope", -1) > 0
        contrast_ok = r["contrast"].value > 0 and r["contrast_p"] < 0.05
        ok = slope_ok and contrast_ok
        print(f"\n[dry-run pipeline check] recovered planted H_OBS (benefit∝CCI): {ok}")
        raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
