# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — Unified effect-size table.

Aggregates the headline effect sizes from every hypothesis script into one
table with bootstrap 95% CIs, for the paper's results section and the
pre-registration's "smallest effect size of interest" check.

Reuses each hypothesis module's `run()` so the numbers here are guaranteed
identical to the per-hypothesis reports — single source of truth.

Emits a plain text table and, with --csv, a machine-readable CSV
(analysis/figures/effect_sizes.csv) for the LaTeX table generator.

Usage:
  python analysis/effect_sizes.py --dry-run
  python analysis/effect_sizes.py --dry-run --csv
  python analysis/effect_sizes.py --db sqlite:///tco_cal.db --csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from _data import add_common_args, banner, resolve_dataset
from _stats import interpret_d, stars

import h1_cognitive_load as h1
import h2_decision_accuracy as h2
import h4_early_detection as h4
import h5_policy_quality as h5
import h_obs_causal as hobs


def collect(ds) -> list[dict]:
    """Run every hypothesis module once and extract its headline effect size."""
    rows: list[dict] = []

    r1 = h1.run(ds)
    d = r1["cohens_d"]
    rows.append(dict(hypothesis="H1", outcome="Raw-TLX (load, ↓)",
                     measure="Cohen's d", value=d.value, ci_low=d.ci_low,
                     ci_high=d.ci_high, p=r1["p"], interp=interpret_d(d.value)))

    r2 = h2.run(ds)
    d = r2["cohens_d"]
    rows.append(dict(hypothesis="H2", outcome="Decision accuracy (↑)",
                     measure="Cohen's d", value=d.value, ci_low=d.ci_low,
                     ci_high=d.ci_high, p=r2["p"], interp=interpret_d(d.value)))

    r4 = h4.run(ds)
    cd = r4["cliffs_delta"]
    rows.append(dict(hypothesis="H4", outcome="Time-to-correct (↓)",
                     measure="Cliff's δ", value=cd.value, ci_low=cd.ci_low,
                     ci_high=cd.ci_high, p=r4["p"], interp=""))

    r5 = h5.run(ds)
    if r5.get("has_delta"):
        sp = r5["spearman"]
        rows.append(dict(hypothesis="H5", outcome="PIQ → Δ_vector",
                         measure="Spearman ρ", value=sp.value, ci_low=sp.ci_low,
                         ci_high=sp.ci_high, p=r5["spearman_p"], interp=""))

    rh = hobs.run(ds)
    cd = rh["contrast_d"]
    rows.append(dict(hypothesis="H_OBS", outcome="hi−lo CCI gap (PRIMARY)",
                     measure="Cohen's d", value=cd.value, ci_low=cd.ci_low,
                     ci_high=cd.ci_high, p=rh["contrast_p"],
                     interp=interpret_d(cd.value)))
    if "anova" in rh:
        a = rh["anova"]
        rows.append(dict(hypothesis="H_OBS", outcome="Group×CCI interaction",
                         measure="partial η²", value=a["np2"], ci_low=float("nan"),
                         ci_high=float("nan"), p=a["p"], interp=""))
    return rows


def report(rows: list[dict]) -> None:
    print(f"\n  {'H':6s} {'outcome':26s} {'measure':12s} {'estimate [95% CI]':24s} "
          f"{'p':>10s}  {'':4s}")
    print("  " + "-" * 86)
    for r in rows:
        if r["ci_low"] == r["ci_low"]:  # not NaN
            est = f"{r['value']:+.3f} [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]"
        else:
            est = f"{r['value']:+.3f}"
        print(f"  {r['hypothesis']:6s} {r['outcome']:26s} {r['measure']:12s} "
              f"{est:24s} {r['p']:10.4g} {stars(r['p']):>3s}  {r['interp']}")


def write_csv(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["hypothesis", "outcome", "measure",
                                          "value", "ci_low", "ci_high", "p", "interp"])
        w.writeheader()
        w.writerows(rows)
    print(f"\n  CSV written: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified effect-size table")
    add_common_args(parser)
    parser.add_argument("--csv", action="store_true", help="Also write figures/effect_sizes.csv")
    args = parser.parse_args()

    ds = resolve_dataset(args)
    banner("DT-030 / Effect Sizes — unified table", ds)
    rows = collect(ds)
    report(rows)
    if args.csv:
        write_csv(rows, Path(__file__).parent / "figures" / "effect_sizes.csv")

    if ds.is_synthetic:
        # Every headline effect should be non-trivial and in the expected direction.
        primary = next(r for r in rows if r["hypothesis"] == "H_OBS"
                       and r["measure"] == "Cohen's d")
        ok = primary["value"] > 0.5 and primary["p"] < 0.05
        print(f"\n[dry-run pipeline check] primary H_OBS effect non-trivial: {ok}")
        raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
