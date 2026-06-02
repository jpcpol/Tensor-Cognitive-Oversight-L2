# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — Result figures for the paper.

Generates the headline figures from the same `run()` outputs the hypothesis
scripts use, so figures and tables can never drift apart.

Figures (analysis/figures/):
  fig_h_obs_cci_slope.png   — PRIMARY: experimental advantage vs CCI (the
                              H_OBS signature) with the fitted slope.
  fig_h1_tlx.png            — Raw-TLX distribution by group (violin/box).
  fig_h2_accuracy_by_cci.png — detection rate by scenario, ordered by CCI.
  fig_effect_sizes.png      — forest plot of all effect sizes with 95% CIs.

Usage:
  python analysis/visualizations.py --dry-run
  python analysis/visualizations.py --db sqlite:///tco_cal.db --output figs/
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from _data import CCI, add_common_args, banner, raw_tlx, resolve_dataset

import h1_cognitive_load as h1
import h2_decision_accuracy as h2
import h_obs_causal as hobs
import effect_sizes as es


def _figs(output: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    return plt, output


def fig_h_obs(ds, plt, out: Path) -> None:
    r = hobs.run(ds)
    rows = r["gap_by_cci"]
    ccis = [x["cci"] for x in rows]
    gaps = [x["gap"] for x in rows]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(ccis, gaps, s=90, color="tomato", zorder=5, label="observed gap")
    if "gap_slope" in r:
        s = r["gap_slope"]
        xs = np.linspace(min(ccis), max(ccis), 50)
        ax.plot(xs, s["slope"] * xs + (gaps[0] - s["slope"] * ccis[0]),
                "--", color="steelblue",
                label=f"slope={s['slope']:+.3f}/CCI  R²={s['r2']:.2f}")
    ax.axhline(0, color="gray", lw=0.8)
    ax.set_title("H_OBS (PRIMARY): TCO advantage scales with Causal Complexity",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("Causal Complexity Index (CCI)")
    ax.set_ylabel("Experimental − Control accuracy gap")
    ax.set_xticks(ccis)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_h_obs_cci_slope.png", dpi=150)
    plt.close(fig)
    print(f"  saved {out / 'fig_h_obs_cci_slope.png'}")


def fig_h1(ds, plt, out: Path) -> None:
    tlx = ds.merged_tlx()
    tlx = tlx[tlx["checkpoint"] == "post_t4"].copy()
    tlx["raw_tlx"] = tlx.apply(raw_tlx, axis=1)
    exp = tlx.loc[tlx["group"] == "experimental", "raw_tlx"].to_numpy()
    ctl = tlx.loc[tlx["group"] == "control", "raw_tlx"].to_numpy()

    fig, ax = plt.subplots(figsize=(6, 5))
    parts = ax.violinplot([ctl, exp], showmeans=True)
    for pc, c in zip(parts["bodies"], ["steelblue", "tomato"]):
        pc.set_facecolor(c)
        pc.set_alpha(0.6)
    ax.set_xticks([1, 2])
    ax.set_xticklabels(["control", "experimental"])
    ax.set_ylabel("Raw-TLX (cognitive load)")
    ax.set_title("H1: Cognitive load by group (post-T4)", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "fig_h1_tlx.png", dpi=150)
    plt.close(fig)
    print(f"  saved {out / 'fig_h1_tlx.png'}")


def fig_h2(ds, plt, out: Path) -> None:
    r = h2.run(ds)
    rows = r["per_scenario"]
    scens = [f"{x['scenario']}\n(CCI={x['cci']})" for x in rows]
    exp = [x["exp_rate"] for x in rows]
    ctl = [x["ctl_rate"] for x in rows]
    x = np.arange(len(rows))
    w = 0.38

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w / 2, ctl, w, label="control", color="steelblue", alpha=0.8)
    ax.bar(x + w / 2, exp, w, label="experimental", color="tomato", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(scens, fontsize=9)
    ax.set_ylabel("Detection rate")
    ax.set_ylim(0, 1.05)
    ax.set_title("H2: Detection rate by scenario (ordered by CCI)",
                 fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_h2_accuracy_by_cci.png", dpi=150)
    plt.close(fig)
    print(f"  saved {out / 'fig_h2_accuracy_by_cci.png'}")


def fig_forest(ds, plt, out: Path) -> None:
    rows = [r for r in es.collect(ds) if r["ci_low"] == r["ci_low"]]  # has CI
    labels = [f"{r['hypothesis']}: {r['outcome']}" for r in rows]
    vals = [r["value"] for r in rows]
    los = [r["ci_low"] for r in rows]
    his = [r["ci_high"] for r in rows]
    y = np.arange(len(rows))

    fig, ax = plt.subplots(figsize=(8, 0.7 * len(rows) + 1.5))
    ax.errorbar(vals, y, xerr=[np.array(vals) - np.array(los),
                               np.array(his) - np.array(vals)],
                fmt="o", color="black", capsize=4)
    ax.axvline(0, color="gray", lw=0.8, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Effect size (with 95% CI)")
    ax.set_title("Unified effect sizes", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "fig_effect_sizes.png", dpi=150)
    plt.close(fig)
    print(f"  saved {out / 'fig_effect_sizes.png'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Result figures")
    add_common_args(parser)
    parser.add_argument("--output", "-o", type=Path,
                        default=Path(__file__).parent / "figures")
    args = parser.parse_args()

    ds = resolve_dataset(args)
    banner("DT-030 / Visualizations", ds)

    if args.no_plots:
        print("  [--no-plots set; nothing to render]")
        return
    try:
        plt, out = _figs(args.output)
    except ImportError:
        print("  [matplotlib not available — skipping]")
        return

    fig_h_obs(ds, plt, out)
    fig_h1(ds, plt, out)
    fig_h2(ds, plt, out)
    fig_forest(ds, plt, out)
    print(f"\n  All figures written to {out}")


if __name__ == "__main__":
    main()
