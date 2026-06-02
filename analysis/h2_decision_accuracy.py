# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — H2: Decision accuracy.

H2: The experimental group makes more accurate supervisory decisions
    (fault detection / risk assessment) than control.

Pre-registered analysis:
  • Detection: per-scenario detection rate (binary `detected`) compared with a
    chi-square / Fisher exact test; overall precision & recall against ground
    truth (every scenario contains a true fault → recall = detection rate).
  • Continuous accuracy: Mann-Whitney U on per-participant mean accuracy;
    Cohen's d + Cliff's delta with bootstrap CIs.
  • **Per-scenario breakdown ordered by CCI** — this is where the H_OBS
    signature shows up: the control/experimental gap should widen with CCI
    (S3, S5 ~invisible to raw review). The formal moderation test lives in
    h_obs_causal.py; here we report the descriptive gap.

Usage:
  python analysis/h2_decision_accuracy.py --dry-run
  python analysis/h2_decision_accuracy.py --db sqlite:///tco_cal.db
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats

from _data import CCI, add_common_args, banner, resolve_dataset
from _stats import (Estimate, bootstrap_ci, cliffs_delta, cohens_d,
                    interpret_d, stars)


def _per_participant_accuracy(tasks: pd.DataFrame) -> pd.DataFrame:
    """Mean accuracy per participant (collapsing scenarios)."""
    return (tasks.groupby(["participant_id", "group"], as_index=False)["accuracy"]
            .mean())


def run(ds) -> dict:
    tasks = ds.merged_tasks()

    # ── Continuous accuracy: per-participant mean ──
    pa = _per_participant_accuracy(tasks)
    exp = pa.loc[pa["group"] == "experimental", "accuracy"].to_numpy()
    ctl = pa.loc[pa["group"] == "control", "accuracy"].to_numpy()
    u, p = stats.mannwhitneyu(exp, ctl, alternative="greater")
    d_val, d_lo, d_hi = bootstrap_ci(cohens_d, exp, ctl, seed=2)
    cd_val, cd_lo, cd_hi = bootstrap_ci(cliffs_delta, exp, ctl, seed=2)

    # ── Detection: pooled precision / recall (every scenario has a true fault) ──
    # TP = experimental detections; recall = detection rate; precision requires
    # false positives → we treat warm-up S0 (no fault) absent here, so precision
    # is reported per-group as detections / (detections + spurious). With all-
    # fault scenarios, recall = mean(detected). Precision is reported as 1.0 by
    # construction unless raw_response carries false-positive flags (real data).
    detection = (tasks.groupby("group")["detected"].mean().to_dict())

    # ── Per-scenario gap, ordered by CCI ──
    rows = []
    for scen in sorted(CCI, key=lambda s: CCI[s]):
        sub = tasks[tasks["scenario"] == scen]
        e = sub.loc[sub["group"] == "experimental", "detected"].astype(float)
        c = sub.loc[sub["group"] == "control", "detected"].astype(float)
        # Fisher exact on the 2x2 detected/missed table
        table = [[int(e.sum()), int((1 - e).sum())],
                 [int(c.sum()), int((1 - c).sum())]]
        try:
            _, fisher_p = stats.fisher_exact(table, alternative="greater")
        except ValueError:
            fisher_p = float("nan")
        rows.append(dict(
            scenario=scen, cci=CCI[scen],
            exp_rate=float(e.mean()), ctl_rate=float(c.mean()),
            gap=float(e.mean() - c.mean()), p=float(fisher_p),
        ))

    return dict(
        n_exp=len(exp), n_ctl=len(ctl),
        exp_acc=float(np.mean(exp)), ctl_acc=float(np.mean(ctl)),
        u=float(u), p=float(p),
        cohens_d=Estimate(d_val, d_lo, d_hi, "Cohen's d (acc)"),
        cliffs_delta=Estimate(cd_val, cd_lo, cd_hi, "Cliff's delta"),
        detection_rate=detection,
        per_scenario=rows,
    )


def report(r: dict) -> None:
    print(f"\nMean decision accuracy  (n_exp={r['n_exp']}, n_ctl={r['n_ctl']})")
    print(f"  experimental : {r['exp_acc']:.3f}")
    print(f"  control      : {r['ctl_acc']:.3f}")
    print(f"  Mann-Whitney U (exp>ctl): U={r['u']:.1f}  p={r['p']:.4g} {stars(r['p'])}")
    for est in (r["cohens_d"], r["cliffs_delta"]):
        extra = f"  ({interpret_d(est.value)})" if "d (" in est.label else ""
        print(f"  {est.label:16s}: {est.fmt()}{extra}")

    print("\nPooled detection rate (recall; all scenarios contain a true fault):")
    for g, rate in r["detection_rate"].items():
        print(f"  {g:13s}: {rate:.3f}")

    print("\nPer-scenario detection gap, ordered by CCI (H_OBS signature):")
    print(f"  {'scen':5s} {'CCI':>4s} {'exp':>6s} {'ctl':>6s} {'gap':>7s}  {'Fisher p':>9s}")
    for row in r["per_scenario"]:
        print(f"  {row['scenario']:5s} {row['cci']:4d} {row['exp_rate']:6.2f} "
              f"{row['ctl_rate']:6.2f} {row['gap']:+7.2f}  {row['p']:9.4g} {stars(row['p'])}")


def main() -> None:
    parser = argparse.ArgumentParser(description="H2 — decision accuracy")
    add_common_args(parser)
    args = parser.parse_args()

    ds = resolve_dataset(args)
    banner("DT-030 / H2 — Decision Accuracy", ds)
    r = run(ds)
    report(r)

    if ds.is_synthetic:
        # Planted: experimental more accurate, and the gap grows with CCI.
        gaps = {row["scenario"]: row["gap"] for row in r["per_scenario"]}
        monotone = gaps["S3"] > gaps["S1"] and gaps["S5"] > gaps["S1"]
        ok = r["exp_acc"] > r["ctl_acc"] and r["p"] < 0.05 and monotone
        print(f"\n[dry-run pipeline check] recovered planted H2 + CCI gradient: {ok}")
        raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
