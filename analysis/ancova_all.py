# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — ANCOVA across outcomes, adjusting for participant covariates.

Pre-registered covariates (collected at registration):
  • years_experience  — code-review experience (≥2 inclusion floor)
  • ai_familiarity    — 0–4 self-rated familiarity with AI dev tools
  • experience_stratum — junior / mid / senior (randomization strata)

For each primary outcome we fit:
    outcome ~ C(group) + years_experience + ai_familiarity + C(stratum)
and report the adjusted group effect with partial η². ANCOVA increases power
by removing covariate variance and guards against covariate imbalance that
randomization at n=40 may not fully neutralize.

Outcomes:
  • raw_tlx (post_t4)        — H1, lower is better
  • accuracy (mean)          — H2, higher is better
  • time_to_first_correction — H4, lower is better

Usage:
  python analysis/ancova_all.py --dry-run
  python analysis/ancova_all.py --db sqlite:///tco_cal.db
"""
from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd

from _data import add_common_args, banner, raw_tlx, resolve_dataset
from _stats import stars


def _ancova(df: pd.DataFrame, dv: str) -> dict:
    """statsmodels OLS ANCOVA; returns adjusted group effect + partial η²."""
    import statsmodels.api as sm
    from statsmodels.formula.api import ols

    data = df.dropna(subset=[dv, "group", "years_experience", "ai_familiarity",
                             "stratum"]).copy()
    data = data.rename(columns={dv: "y"})
    formula = "y ~ C(group) + years_experience + ai_familiarity + C(stratum)"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ols(formula, data=data).fit()
        aov = sm.stats.anova_lm(model, typ=2)

    # partial η² = SS_effect / (SS_effect + SS_resid)
    ss_resid = aov.loc["Residual", "sum_sq"]
    rows = {}
    for term in aov.index:
        if term == "Residual":
            continue
        ss = aov.loc[term, "sum_sq"]
        rows[term] = dict(
            F=float(aov.loc[term, "F"]), p=float(aov.loc[term, "PR(>F)"]),
            partial_eta2=float(ss / (ss + ss_resid)),
        )
    # Adjusted group means via the fitted model (EMM-style at covariate means)
    group_coef = next((c for c in model.params.index if c.startswith("C(group)")), None)
    adj_effect = float(model.params[group_coef]) if group_coef else float("nan")
    return dict(terms=rows, adjusted_group_effect=adj_effect, n=len(data))


def _build_frames(ds):
    parts = ds.participants

    # raw_tlx @ post_t4 per participant
    tlx = ds.merged_tlx()
    tlx = tlx[tlx["checkpoint"] == "post_t4"].copy()
    tlx["raw_tlx"] = tlx.apply(raw_tlx, axis=1)
    tlx_pp = tlx.groupby("participant_id", as_index=False)["raw_tlx"].mean()

    tasks = ds.merged_tasks()
    acc_pp = tasks.groupby("participant_id", as_index=False)["accuracy"].mean()
    ttc_pp = (tasks.dropna(subset=["time_to_first_correction_s"])
              .groupby("participant_id", as_index=False)["time_to_first_correction_s"].mean())

    base = parts[["participant_id", "group", "stratum", "years_experience",
                  "ai_familiarity"]]
    frames = {
        "raw_tlx (H1, ↓)": base.merge(tlx_pp, on="participant_id"),
        "accuracy (H2, ↑)": base.merge(acc_pp, on="participant_id"),
        "time_to_correct (H4, ↓)": base.merge(ttc_pp, on="participant_id"),
    }
    dv_map = {
        "raw_tlx (H1, ↓)": "raw_tlx",
        "accuracy (H2, ↑)": "accuracy",
        "time_to_correct (H4, ↓)": "time_to_first_correction_s",
    }
    return frames, dv_map


def run(ds) -> dict:
    frames, dv_map = _build_frames(ds)
    out = {}
    for label, df in frames.items():
        out[label] = _ancova(df, dv_map[label])
    return out


def report(r: dict) -> None:
    for label, res in r.items():
        print(f"\n{label}   (n={res['n']})")
        print(f"  {'term':22s} {'F':>9s} {'p':>10s}  {'partial η²':>10s}")
        for term, v in res["terms"].items():
            name = term.replace("C(group)", "group").replace("C(stratum)", "stratum")
            print(f"  {name:22s} {v['F']:9.3f} {v['p']:10.4g} {stars(v['p']):>3s} "
                  f"{v['partial_eta2']:10.3f}")
        print(f"  adjusted group effect (β): {res['adjusted_group_effect']:+.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ANCOVA across outcomes")
    add_common_args(parser)
    args = parser.parse_args()

    ds = resolve_dataset(args)
    banner("DT-030 / ANCOVA — covariate-adjusted group effects", ds)
    r = run(ds)
    report(r)

    if ds.is_synthetic:
        # The group term should remain significant for accuracy after adjustment.
        acc = r["accuracy (H2, ↑)"]["terms"]
        gkey = next(k for k in acc if "group" in k)
        ok = acc[gkey]["p"] < 0.05
        print(f"\n[dry-run pipeline check] group effect survives covariate "
              f"adjustment (accuracy): {ok}")
        raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
