# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
φ Calibration Suite — Pre-pilot no-go gate (DT-021 / DT-019)

Measures Spearman ρ between LLM-QA semantic scores and static analysis ground truth
for the four dimensions that both sources cover:

  v4 security_risk      : semantic_security        vs bandit weighted_severity (inverted)
  v6 testability        : semantic_testability      vs radon 1 − cyclomatic_norm
  v7 maintainability    : semantic_maintainability  vs radon maintainability_index (normalized)
  v8 technical_debt     : semantic_debt_assessment  vs radon 1 − debt_ratio

NO-GO threshold: Spearman ρ < 0.75 for any dimension → abort pilot, revise prompts.

Usage:
    python -m src.experiment.phi_calibration.phi_calibration \
        --corpus path/to/corpus.json [--output report.json] [--no-plots]

Corpus JSON format:
    [
      {
        "id": "s1_injection",
        "code": "...",
        "artifact_type": "python_code",
        "context": "Auth module",
        "scenario": "S1"
      },
      ...
    ]
"""

from __future__ import annotations

import argparse
import json
import sys
import os
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ── Threshold ──────────────────────────────────────────────────────────────────
SPEARMAN_THRESHOLD = 0.75

# Dimension metadata: (llm_field, static_label)
CALIBRATION_DIMS = {
    "v4_security": ("semantic_security", "bandit_security_inv"),
    "v6_testability": ("semantic_testability", "radon_testability"),
    "v7_maintainability": ("semantic_maintainability", "radon_maintainability"),
    "v8_technical_debt": ("semantic_debt_assessment", "radon_debt_inv"),
}


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class DimensionResult:
    dimension: str
    llm_field: str
    static_field: str
    spearman_rho: float
    ci_low: float
    ci_high: float
    n_artifacts: int
    verdict: str          # PASS | FAIL
    outliers: list[str]   # artifact IDs where |llm - static| > 0.30


@dataclass
class CalibrationReport:
    timestamp: str
    n_artifacts: int
    results: list[DimensionResult]
    overall_verdict: str  # GO | NO-GO
    failing_dimensions: list[str]


# ── Statistical helpers ────────────────────────────────────────────────────────

def _spearman_rho(x: list[float], y: list[float]) -> float:
    """Spearman correlation without scipy dependency (rank-based Pearson)."""
    n = len(x)
    if n < 3:
        return float("nan")
    rx = _rank(x)
    ry = _rank(y)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den = (sum((r - mx) ** 2 for r in rx) * sum((r - my) ** 2 for r in ry)) ** 0.5
    return num / den if den > 0 else 0.0


def _rank(values: list[float]) -> list[float]:
    sorted_vals = sorted(enumerate(values), key=lambda t: t[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(sorted_vals):
        j = i
        # find tied group
        while j < len(sorted_vals) - 1 and sorted_vals[j + 1][1] == sorted_vals[j][1]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[sorted_vals[k][0]] = avg_rank
        i = j + 1
    return ranks


def _bootstrap_ci(
    x: list[float], y: list[float], n_boot: int = 1000, alpha: float = 0.05
) -> tuple[float, float]:
    """Bootstrap 95% CI for Spearman ρ."""
    rng = np.random.default_rng(seed=42)
    n = len(x)
    boot_rhos = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        xb = [x[i] for i in idx]
        yb = [y[i] for i in idx]
        boot_rhos.append(_spearman_rho(xb, yb))
    lo = float(np.nanpercentile(boot_rhos, 100 * alpha / 2))
    hi = float(np.nanpercentile(boot_rhos, 100 * (1 - alpha / 2)))
    return lo, hi


# ── Score extraction ───────────────────────────────────────────────────────────

def _extract_static_scores(code: str) -> dict[str, float]:
    """Run radon + bandit and return the four static-analysis dimensions."""
    from src.tco_engine.static_analysis.radon_runner import RadonRunner
    from src.tco_engine.static_analysis.bandit_runner import BanditRunner

    radon = RadonRunner().analyze(code)
    bandit = BanditRunner().scan(code)

    return {
        # bandit returns weighted_severity ∈ [0,1] where 1=max risk; invert for security
        "bandit_security_inv": 1.0 - bandit.weighted_severity,
        # radon cyclomatic_norm ∈ [0,1] where 1=max complexity; invert for testability
        "radon_testability": 1.0 - radon.cyclomatic_norm,
        # radon maintainability_index already normalized ∈ [0,1]
        "radon_maintainability": radon.maintainability_index,
        # radon debt_ratio ∈ [0,1] where 1=max debt; invert for debt assessment
        "radon_debt_inv": 1.0 - radon.debt_ratio,
    }


def _extract_llm_scores(code: str, artifact_type: str, context: str) -> dict[str, float]:
    """Run LLM-QA evaluator and return the four LLM calibration dimensions."""
    from src.tco_engine.core.qa_evaluator import QAEvaluator

    evaluator = QAEvaluator()
    metrics = evaluator.evaluate(code, artifact_type=artifact_type, context=context)  # type: ignore[arg-type]
    return {
        "semantic_security": metrics.semantic_security,
        "semantic_testability": metrics.semantic_testability,
        "semantic_maintainability": metrics.semantic_maintainability,
        "semantic_debt_assessment": metrics.semantic_debt_assessment,
    }


# ── Main calibration routine ───────────────────────────────────────────────────

def run_calibration(
    corpus: list[dict],
    output_path: Optional[Path] = None,
    generate_plots: bool = True,
) -> CalibrationReport:
    from datetime import datetime, timezone

    logger.info("Running φ calibration on %d artifacts ...", len(corpus))

    # Collect (artifact_id, llm_scores, static_scores) for each artifact
    records: list[dict] = []
    for item in corpus:
        artifact_id = item["id"]
        code = item["code"]
        artifact_type = item.get("artifact_type", "python_code")
        context = item.get("context", "")

        logger.info("  [%s] static analysis ...", artifact_id)
        static = _extract_static_scores(code)

        logger.info("  [%s] LLM-QA evaluation ...", artifact_id)
        try:
            llm = _extract_llm_scores(code, artifact_type, context)
        except Exception as exc:
            logger.warning("  [%s] LLM failed: %s — skipping", artifact_id, exc)
            continue

        records.append({"id": artifact_id, **static, **llm})

    if len(records) < 5:
        logger.error("Too few successful evaluations (%d) to compute reliable ρ.", len(records))
        sys.exit(1)

    # Compute Spearman ρ per dimension
    results: list[DimensionResult] = []
    failing: list[str] = []

    for dim_key, (llm_field, static_field) in CALIBRATION_DIMS.items():
        llm_vals = [r[llm_field] for r in records]
        static_vals = [r[static_field] for r in records]

        rho = _spearman_rho(llm_vals, static_vals)
        ci_lo, ci_hi = _bootstrap_ci(llm_vals, static_vals)

        outliers = [
            r["id"] for r in records
            if abs(r[llm_field] - r[static_field]) > 0.30
        ]

        verdict = "PASS" if rho >= SPEARMAN_THRESHOLD else "FAIL"
        if verdict == "FAIL":
            failing.append(dim_key)

        dr = DimensionResult(
            dimension=dim_key,
            llm_field=llm_field,
            static_field=static_field,
            spearman_rho=round(rho, 4),
            ci_low=round(ci_lo, 4),
            ci_high=round(ci_hi, 4),
            n_artifacts=len(records),
            verdict=verdict,
            outliers=outliers,
        )
        results.append(dr)

        _log_result(dr)

    overall = "NO-GO" if failing else "GO"

    report = CalibrationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        n_artifacts=len(records),
        results=results,
        overall_verdict=overall,
        failing_dimensions=failing,
    )

    _print_summary(report)

    if output_path:
        output_path.write_text(
            json.dumps(asdict(report), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Report saved → %s", output_path)

    if generate_plots:
        _generate_scatter_plots(records, output_path)

    return report


def _log_result(dr: DimensionResult) -> None:
    symbol = "✓" if dr.verdict == "PASS" else "✗"
    logger.info(
        "  %s %-22s  ρ = %.3f  CI=[%.3f, %.3f]  outliers=%d  %s",
        symbol, dr.dimension, dr.spearman_rho, dr.ci_low, dr.ci_high,
        len(dr.outliers), dr.verdict,
    )


def _print_summary(report: CalibrationReport) -> None:
    print("\n" + "=" * 60)
    print(f"φ CALIBRATION REPORT  —  {report.timestamp}")
    print(f"Artifacts evaluated: {report.n_artifacts}")
    print(f"Threshold: Spearman ρ ≥ {SPEARMAN_THRESHOLD}")
    print("-" * 60)
    for dr in report.results:
        mark = "PASS" if dr.verdict == "PASS" else "FAIL"
        print(
            f"  {dr.dimension:<22}  ρ={dr.spearman_rho:+.3f}  "
            f"CI=[{dr.ci_low:.3f},{dr.ci_high:.3f}]  {mark}"
        )
        if dr.outliers:
            print(f"    outliers: {', '.join(dr.outliers[:5])}"
                  + ("…" if len(dr.outliers) > 5 else ""))
    print("-" * 60)
    print(f"OVERALL VERDICT: {report.overall_verdict}")
    if report.failing_dimensions:
        print(f"  Failing: {', '.join(report.failing_dimensions)}")
        print("  Action: revise QA agent prompt for failing dimensions, re-run calibration.")
    print("=" * 60 + "\n")


def _generate_scatter_plots(records: list[dict], output_path: Optional[Path]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not installed — skipping scatter plots")
        return

    plot_dir = (output_path.parent if output_path else Path(".")) / "phi_calibration_plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    for dim_key, (llm_field, static_field) in CALIBRATION_DIMS.items():
        llm_vals = [r[llm_field] for r in records]
        static_vals = [r[static_field] for r in records]
        ids = [r["id"] for r in records]

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(static_vals, llm_vals, s=60, alpha=0.75, color="#4a90d9")
        for i, aid in enumerate(ids):
            if abs(llm_vals[i] - static_vals[i]) > 0.30:
                ax.annotate(aid, (static_vals[i], llm_vals[i]),
                            fontsize=7, color="tomato",
                            xytext=(4, 4), textcoords="offset points")
        ax.plot([0, 1], [0, 1], "k--", lw=0.8, alpha=0.4, label="ideal")
        rho = _spearman_rho(llm_vals, static_vals)
        ax.set_title(f"{dim_key}  ρ={rho:.3f}", fontsize=11)
        ax.set_xlabel(f"Static: {static_field}")
        ax.set_ylabel(f"LLM: {llm_field}")
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(plot_dir / f"{dim_key}.png", dpi=150)
        plt.close(fig)

    logger.info("Scatter plots saved → %s", plot_dir)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="TCO φ Calibration Suite")
    parser.add_argument("--corpus", required=True, help="Path to corpus JSON file")
    parser.add_argument("--output", default=None, help="Path to save calibration report JSON")
    parser.add_argument("--no-plots", action="store_true", help="Skip scatter plot generation")
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        logger.error("Corpus file not found: %s", corpus_path)
        sys.exit(1)

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    output_path = Path(args.output) if args.output else None

    report = run_calibration(
        corpus=corpus,
        output_path=output_path,
        generate_plots=not args.no_plots,
    )

    sys.exit(0 if report.overall_verdict == "GO" else 1)


if __name__ == "__main__":
    main()
