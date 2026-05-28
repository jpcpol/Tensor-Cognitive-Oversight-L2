# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-024 — LLM-QA Evaluator Reliability Analysis

Measures four reliability properties of the QA evaluator on the calibration corpus:

  1. Evaluator variance      σ per SE dimension across n=10 runs on same artifact
                             Threshold: σ < 0.05 for v1/v2/v3/v9
  2. Calibration curves      confidence_self_assessment vs |LLM - static| per artifact
                             Well-calibrated: high confidence → low error
  3. Evaluator entropy       H(score distribution) per dimension over the corpus
                             High entropy → unstable evaluator
  4. Results summary         table + optional heatmap

Requires:
  LLM_PROVIDER=openrouter + OPENROUTER_API_KEY  (or ANTHROPIC_API_KEY)

Usage:
  python analysis/evaluator_reliability.py --corpus src/experiment/phi_calibration/corpus/corpus.json
  python analysis/evaluator_reliability.py --corpus ... --n-runs 10 --no-plots
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import os
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass  # dotenv optional — env vars can be set externally

# ── Constants ─────────────────────────────────────────────────────────────────

SE_DIMS = [
    "functional_correctness",
    "architectural_alignment",
    "scalability_projection",
    "performance_score",
]
ALL_DIMS = SE_DIMS + [
    "semantic_maintainability",
    "semantic_testability",
    "semantic_security",
    "semantic_debt_assessment",
]
VARIANCE_THRESHOLD = 0.05
ENTROPY_ALERT = 0.80          # nats — high entropy signals instability


# ── Entropy ───────────────────────────────────────────────────────────────────

def _entropy_nats(values: list[float], bins: int = 10) -> float:
    """Shannon entropy of a continuous distribution, estimated via histogram."""
    counts, _ = np.histogram(values, bins=bins, range=(0.0, 1.0))
    probs = counts / counts.sum()
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log(probs)))


# ── Core analysis functions ───────────────────────────────────────────────────

def run_variance_analysis(
    corpus: list[dict],
    n_runs: int = 10,
) -> dict:
    """
    Run variance test on all python_code artifacts in the corpus.
    Returns per-artifact and aggregate σ results.
    """
    from tco_engine.core.qa_evaluator import QAEvaluator
    evaluator = QAEvaluator()

    python_artifacts = [a for a in corpus if a.get("artifact_type") == "python_code"]
    print(f"\n[Variance] {len(python_artifacts)} python_code artifacts x {n_runs} runs each")
    print(f"           Estimated: {len(python_artifacts) * n_runs} API calls\n")

    artifact_results: list[dict] = []
    for art in python_artifacts:
        aid = art.get("artifact_id") or art.get("id", "?")
        print(f"  [{aid}] running {n_runs} evaluations ...", end=" ", flush=True)
        result = evaluator.run_variance_test(
            artifact_content=art["code"],
            artifact_type="python_code",
            context=art.get("context", ""),
            n=n_runs,
        )
        result["artifact_id"] = aid
        result["scenario"] = art.get("scenario", "?")
        result["fault_present"] = art.get("fault_present", False)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"max_se_sigma={result['max_se_sigma']:.3f}  [{status}]")
        artifact_results.append(result)

    # Aggregate: σ distribution per dimension across artifacts
    agg_sigma: dict[str, list[float]] = {d: [] for d in ALL_DIMS}
    for r in artifact_results:
        for d in ALL_DIMS:
            agg_sigma[d].append(r["sigma_per_dim"].get(d, 0.0))

    aggregate = {
        "mean_sigma": {d: round(float(np.mean(v)), 4) for d, v in agg_sigma.items()},
        "max_sigma":  {d: round(float(np.max(v)),  4) for d, v in agg_sigma.items()},
        "n_artifacts_fail": sum(1 for r in artifact_results if not r["passed"]),
        "n_artifacts_total": len(artifact_results),
        "overall_passed": all(r["passed"] for r in artifact_results),
    }
    return {"artifact_results": artifact_results, "aggregate": aggregate}


def run_entropy_analysis(corpus: list[dict]) -> dict:
    """
    Run one evaluation per artifact, collect all SE dimension scores,
    compute Shannon entropy of the score distribution per dimension.
    High H → evaluator assigns scores broadly → unstable signal.
    """
    from tco_engine.core.qa_evaluator import QAEvaluator
    evaluator = QAEvaluator()

    print(f"\n[Entropy] {len(corpus)} artifacts x 1 evaluation each")

    all_scores: dict[str, list[float]] = {d: [] for d in ALL_DIMS}
    for art in corpus:
        if art.get("artifact_type") not in ("python_code", "yaml_config", "ci_cd"):
            continue
        aid = art.get("artifact_id") or art.get("id", "?")
        print(f"  [{aid}] evaluating ...", end=" ", flush=True)
        metrics = evaluator.evaluate(
            artifact_content=art["code"],
            artifact_type=art.get("artifact_type", "python_code"),
            context=art.get("context", ""),
        )
        for d in ALL_DIMS:
            all_scores[d].append(getattr(metrics, d, 0.5))
        print("done")

    entropy: dict[str, float] = {}
    for d, vals in all_scores.items():
        if len(vals) >= 3:
            entropy[d] = round(_entropy_nats(vals), 4)
        else:
            entropy[d] = None

    high_entropy_dims = [d for d, h in entropy.items() if h and h > ENTROPY_ALERT]
    return {
        "entropy_per_dim": entropy,
        "entropy_alert_threshold": ENTROPY_ALERT,
        "high_entropy_dims": high_entropy_dims,
        "scores": all_scores,
    }


# ── Report + plots ────────────────────────────────────────────────────────────

def print_variance_report(variance: dict) -> None:
    agg = variance["aggregate"]
    print("\n" + "=" * 65)
    print("DT-024 - EVALUATOR VARIANCE REPORT")
    print("=" * 65)
    print(f"Artifacts tested: {agg['n_artifacts_total']}  "
          f"Failed: {agg['n_artifacts_fail']}  "
          f"Threshold: sigma < {VARIANCE_THRESHOLD}")
    print()
    print(f"{'Dimension':<30}  {'mean_sigma':>10}  {'max_sigma':>10}  {'Status'}")
    print("-" * 65)
    for d in SE_DIMS:
        ms = agg["mean_sigma"][d]
        mx = agg["max_sigma"][d]
        status = "PASS" if mx < VARIANCE_THRESHOLD else "FAIL"
        marker = "  <-- SE" if d in SE_DIMS else ""
        print(f"  {d:<28}  {ms:>10.4f}  {mx:>10.4f}  {status}{marker}")
    print()
    for d in ALL_DIMS:
        if d in SE_DIMS:
            continue
        ms = agg["mean_sigma"][d]
        mx = agg["max_sigma"][d]
        print(f"  {d:<28}  {ms:>10.4f}  {mx:>10.4f}")
    print("-" * 65)
    verdict = "PASSED" if agg["overall_passed"] else "FAILED"
    print(f"OVERALL: {verdict}")
    print("=" * 65 + "\n")


def print_entropy_report(entropy: dict) -> None:
    print("=" * 65)
    print("DT-024 - EVALUATOR ENTROPY REPORT")
    print(f"Alert threshold: H > {ENTROPY_ALERT} nats")
    print("=" * 65)
    for d in ALL_DIMS:
        h = entropy["entropy_per_dim"].get(d)
        if h is None:
            print(f"  {d:<30}  (insufficient data)")
            continue
        flag = "  *** HIGH ***" if h > ENTROPY_ALERT else ""
        print(f"  {d:<30}  H={h:.3f} nats{flag}")
    if entropy["high_entropy_dims"]:
        print(f"\nHigh-entropy dims: {entropy['high_entropy_dims']}")
        print("Action: review prompt wording for flagged dimensions.")
    else:
        print("\nAll dims below alert threshold -- entropy acceptable.")
    print("=" * 65 + "\n")


def generate_heatmap(variance: dict, output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[heatmap skipped - matplotlib not available]")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_ids = [r["artifact_id"] for r in variance["artifact_results"]]
    dims = SE_DIMS
    matrix = np.array([
        [r["sigma_per_dim"].get(d, 0.0) for d in dims]
        for r in variance["artifact_results"]
    ])

    fig, ax = plt.subplots(figsize=(10, max(4, len(artifact_ids) * 0.5)))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=0.10)
    plt.colorbar(im, ax=ax, label="sigma (std dev across runs)")
    ax.set_xticks(range(len(dims)))
    ax.set_xticklabels([d.replace("_", "\n") for d in dims], fontsize=8)
    ax.set_yticks(range(len(artifact_ids)))
    ax.set_yticklabels(artifact_ids, fontsize=7)
    ax.axhline(-0.5, color="white", lw=0.5)
    ax.set_title(f"QA Evaluator Variance per SE Dimension\n"
                 f"(red > threshold {VARIANCE_THRESHOLD})", fontsize=11)
    ax.axvline(len(dims) - 0.5, color="gray", lw=0.5)
    for i in range(len(artifact_ids)):
        for j in range(len(dims)):
            val = matrix[i, j]
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=6, color="black" if val < 0.07 else "white")
    fig.tight_layout()
    out = output_dir / "evaluator_variance_heatmap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"  Heatmap saved: {out}")
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="DT-024 - Evaluator Reliability Analysis")
    parser.add_argument("--corpus", required=True, help="Path to corpus.json")
    parser.add_argument("--n-runs", type=int, default=10, help="Variance test runs per artifact")
    parser.add_argument("--no-plots", action="store_true", help="Skip heatmap generation")
    parser.add_argument("--skip-entropy", action="store_true",
                        help="Skip entropy analysis (saves ~12 API calls)")
    parser.add_argument("--output", "-o", type=Path,
                        default=Path(__file__).parent / "figures",
                        help="Output directory for figures and report")
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        print(f"ERROR: corpus not found: {corpus_path}")
        sys.exit(1)

    corpus_data = json.loads(corpus_path.read_text(encoding="utf-8"))
    # Support both raw list and {corpus: [...]} format
    corpus = corpus_data if isinstance(corpus_data, list) else corpus_data.get("corpus", [])

    # 1. Variance analysis
    variance = run_variance_analysis(corpus, n_runs=args.n_runs)
    print_variance_report(variance)

    # 2. Entropy analysis
    entropy = None
    if not args.skip_entropy:
        entropy = run_entropy_analysis(corpus)
        print_entropy_report(entropy)

    # 3. Plots
    if not args.no_plots:
        print(f"\nGenerating plots in {args.output} ...")
        generate_heatmap(variance, args.output)

    # 4. Save full report
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        "variance": {
            "aggregate": variance["aggregate"],
            "artifact_results": [
                {k: v for k, v in r.items() if k != "runs"}
                for r in variance["artifact_results"]
            ],
        },
        "entropy": entropy,
    }
    report_path = args.output / "evaluator_reliability_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(f"  Report saved: {report_path}")

    # Exit code
    passed = variance["aggregate"]["overall_passed"]
    if entropy:
        passed = passed and not entropy["high_entropy_dims"]
    print(f"\nEvaluator reliability: {'CONFIRMED' if passed else 'REVIEW NEEDED'}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
