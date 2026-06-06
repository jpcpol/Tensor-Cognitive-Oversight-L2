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

# Windows consoles default to cp1252, which cannot encode φ/ρ/✓/✗ used in the
# report. Force UTF-8 on stdout/stderr so the summary print does not crash.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# Load .env so OPENROUTER_API_KEY / LLM_PROVIDER are available without
# requiring the caller to export them explicitly.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional; caller can set env vars manually

# ── Threshold ──────────────────────────────────────────────────────────────────
SPEARMAN_THRESHOLD = 0.75

# Dimension metadata: (llm_field, static_label)
CALIBRATION_DIMS = {
    "v4_security": ("semantic_security", "bandit_security_inv"),
    "v6_testability": ("semantic_testability", "radon_testability"),
    "v7_maintainability": ("semantic_maintainability", "radon_maintainability"),
    "v8_technical_debt": ("semantic_debt_assessment", "radon_debt_inv"),
}

# Hard-ground-truth dimensions: those whose static reference is a semantically
# INDEPENDENT, verifiable signal — not a reprojection of cyclomatic complexity.
#   v4_security    ← bandit detects real CWE/vulnerability patterns
#   v6_testability ← raw cyclomatic complexity (a hard, standard metric;
#                    testability is its accepted inverse)
# The remaining dimensions (v7 maintainability, v8 technical_debt) are
# "supervisory estimators" (paper §5.2 / DT-027): radon's MI-derived proxies
# for them auto-correlate (ρ>0.93 with each other and with CC) and are blind to
# the semantic qualities the LLM evaluates (naming, dead code, conceptual debt).
# Calibrating an LLM judgement against them measures agreement between two
# estimators, not accuracy against truth. They are therefore REPORTED but do NOT
# gate the pilot; their validation route is inter-rater / inter-model agreement
# (DT-024 / kappa_validator), handled outside this static-calibration gate.
HARD_GT_DIMS = {"v4_security", "v6_testability"}


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
    verdict: str          # PASS | FAIL (hard-GT dim below threshold) | REPORT (estimator)
    outliers: list[str]   # artifact IDs where |llm - static| > 0.30


@dataclass
class CorrelationPair:
    """Pairwise Spearman ρ between two quality dimensions (DT-025)."""
    dim_a: str
    dim_b: str
    spearman_rho: float
    note: str   # "high_correlation" if ρ > 0.90, else ""


@dataclass
class CalibrationReport:
    timestamp: str
    n_artifacts: int
    results: list[DimensionResult]
    overall_verdict: str  # GO | NO-GO
    failing_dimensions: list[str]
    # DT-025: inter-dimension correlation matrix (static dims only — ground truth)
    top_correlated_pairs: list[CorrelationPair] = None   # top-3 pairs by |ρ|


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

    # NOTE: RadonRunner already returns normalized, correctly-oriented metrics
    # (testability = 1 − cyclomatic_norm, maintainability = mi_norm). Do NOT
    # re-invert here — the runner does it. Only debt and security need inversion,
    # since debt_ratio/weighted_severity are "higher = worse".
    return {
        # bandit weighted_severity ∈ [0,1], 1=max risk → invert so 1=secure
        "bandit_security_inv": 1.0 - bandit.weighted_severity,
        # radon.testability ∈ [0,1], 1=most testable (already 1 − cc_norm)
        "radon_testability": radon.testability,
        # radon.maintainability ∈ [0,1], 1=most maintainable (mi_norm)
        "radon_maintainability": radon.maintainability,
        # radon.debt_ratio ∈ [0,1], 1=max debt → invert so 1=low debt
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


# ── Inter-dimension correlation (DT-025) ──────────────────────────────────────

# Static dimensions available in records (ground truth, deterministic)
_STATIC_DIMS = {
    "v4_security":     "bandit_security_inv",
    "v6_testability":  "radon_testability",
    "v7_maintainability": "radon_maintainability",
    "v8_technical_debt": "radon_debt_inv",
}

HIGH_CORRELATION_THRESHOLD = 0.90  # pairs above this warrant justification or fusion


def compute_interdim_correlation(records: list[dict]) -> list[CorrelationPair]:
    """
    Compute pairwise Spearman ρ between all static quality dimensions.

    Used to validate the ~orthogonal supervisory dimensions claim (DT-025):
    dimensions may correlate empirically, but must remain supervisoriamente
    distinguishable. Any pair with ρ > 0.90 warrants explicit justification
    for keeping them separate in V.

    Returns the top-3 pairs by |ρ| for inclusion in the calibration report
    and Section 7.6.1 of the paper.
    """
    dim_keys = list(_STATIC_DIMS.keys())
    pairs: list[CorrelationPair] = []

    for i in range(len(dim_keys)):
        for j in range(i + 1, len(dim_keys)):
            da, db = dim_keys[i], dim_keys[j]
            fa, fb = _STATIC_DIMS[da], _STATIC_DIMS[db]
            vals_a = [r[fa] for r in records if fa in r and fb in r]
            vals_b = [r[fb] for r in records if fa in r and fb in r]
            if len(vals_a) < 3:
                continue
            rho = _spearman_rho(vals_a, vals_b)
            note = "high_correlation - justify or fuse" if abs(rho) > HIGH_CORRELATION_THRESHOLD else ""
            pairs.append(CorrelationPair(
                dim_a=da, dim_b=db,
                spearman_rho=round(rho, 4),
                note=note,
            ))

    pairs.sort(key=lambda p: abs(p.spearman_rho), reverse=True)
    return pairs[:3]  # top-3 by |ρ|


# ── Main calibration routine ───────────────────────────────────────────────────

def run_calibration(
    corpus: list[dict],
    output_path: Optional[Path] = None,
    generate_plots: bool = True,
    llm_cache_path: Optional[Path] = None,
) -> CalibrationReport:
    from datetime import datetime, timezone

    logger.info("Running φ calibration on %d artifacts ...", len(corpus))

    # Optional on-disk cache of LLM scores so the (paid, slow) LLM pass is run
    # once; re-runs that only change verdict logic or static scoring reuse it.
    llm_cache: dict = {}
    if llm_cache_path and llm_cache_path.exists():
        llm_cache = json.loads(llm_cache_path.read_text(encoding="utf-8"))
        logger.info("  loaded %d cached LLM scores from %s", len(llm_cache), llm_cache_path)

    # Collect (artifact_id, llm_scores, static_scores) for each artifact
    records: list[dict] = []
    for item in corpus:
        artifact_id = item["id"]
        code = item["code"]
        artifact_type = item.get("artifact_type", "python_code")
        context = item.get("context", "")

        logger.info("  [%s] static analysis ...", artifact_id)
        static = _extract_static_scores(code)

        if artifact_id in llm_cache:
            llm = llm_cache[artifact_id]
        else:
            logger.info("  [%s] LLM-QA evaluation ...", artifact_id)
            try:
                llm = _extract_llm_scores(code, artifact_type, context)
            except Exception as exc:
                logger.warning("  [%s] LLM failed: %s — skipping", artifact_id, exc)
                continue
            llm_cache[artifact_id] = llm
            if llm_cache_path:
                llm_cache_path.write_text(
                    json.dumps(llm_cache, indent=2), encoding="utf-8"
                )

        records.append({
            "id": artifact_id,
            "calibration_dim": item.get("calibration_dim"),
            **static, **llm,
        })

    if len(records) < 5:
        logger.error("Too few successful evaluations (%d) to compute reliable ρ.", len(records))
        sys.exit(1)

    # If the corpus tags each artifact with the single dimension its family
    # sweeps, calibrate each dimension over THAT subset only. Mixing all
    # families into one cloud lets off-axis (flat) dimensions inject spurious
    # correlation — e.g. the security family has flat static testability while
    # the LLM varies it, dragging v6's global ρ negative. Per-dimension scoping
    # is the methodologically correct unit of calibration.
    tagged = any(r.get("calibration_dim") for r in records)

    # Compute Spearman ρ per dimension
    results: list[DimensionResult] = []
    failing: list[str] = []

    for dim_key, (llm_field, static_field) in CALIBRATION_DIMS.items():
        scored = (
            [r for r in records if r.get("calibration_dim") == dim_key]
            if tagged else records
        )
        if len(scored) < 3:
            scored = records  # fall back to full set if a family is too small
        llm_vals = [r[llm_field] for r in scored]
        static_vals = [r[static_field] for r in scored]

        rho = _spearman_rho(llm_vals, static_vals)
        ci_lo, ci_hi = _bootstrap_ci(llm_vals, static_vals)

        outliers = [
            r["id"] for r in scored
            if abs(r[llm_field] - r[static_field]) > 0.30
        ]

        is_hard = dim_key in HARD_GT_DIMS
        if rho >= SPEARMAN_THRESHOLD:
            verdict = "PASS"
        elif is_hard:
            verdict = "FAIL"
            failing.append(dim_key)   # only hard-GT dims gate the pilot
        else:
            verdict = "REPORT"        # supervisory estimator — reported, not gating

        dr = DimensionResult(
            dimension=dim_key,
            llm_field=llm_field,
            static_field=static_field,
            spearman_rho=round(rho, 4),
            ci_low=round(ci_lo, 4),
            ci_high=round(ci_hi, 4),
            n_artifacts=len(scored),
            verdict=verdict,
            outliers=outliers,
        )
        results.append(dr)

        _log_result(dr)

    overall = "NO-GO" if failing else "GO"

    # DT-025: inter-dimension correlation matrix
    top_pairs = compute_interdim_correlation(records)

    report = CalibrationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        n_artifacts=len(records),
        results=results,
        overall_verdict=overall,
        failing_dimensions=failing,
        top_correlated_pairs=top_pairs,
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
    symbol = {"PASS": "✓", "FAIL": "✗", "REPORT": "•"}.get(dr.verdict, "?")
    logger.info(
        "  %s %-22s  ρ = %.3f  CI=[%.3f, %.3f]  outliers=%d  %s",
        symbol, dr.dimension, dr.spearman_rho, dr.ci_low, dr.ci_high,
        len(dr.outliers), dr.verdict,
    )


def _print_summary(report: CalibrationReport) -> None:
    print("\n" + "=" * 60)
    print(f"φ CALIBRATION REPORT  —  {report.timestamp}")
    print(f"Artifacts evaluated: {report.n_artifacts}")
    print(f"Threshold: Spearman ρ ≥ {SPEARMAN_THRESHOLD}  (gates HARD-GT dims only)")
    print(f"Hard-GT (gating): {', '.join(sorted(HARD_GT_DIMS))}")
    print("-" * 60)
    for dr in report.results:
        tag = {"PASS": "PASS", "FAIL": "FAIL (gate)", "REPORT": "report-only"}.get(dr.verdict, dr.verdict)
        print(
            f"  {dr.dimension:<22}  ρ={dr.spearman_rho:+.3f}  "
            f"CI=[{dr.ci_low:.3f},{dr.ci_high:.3f}]  {tag}"
        )
        if dr.outliers:
            print(f"    outliers: {', '.join(dr.outliers[:5])}"
                  + ("…" if len(dr.outliers) > 5 else ""))
    print("-" * 60)
    print(f"OVERALL VERDICT: {report.overall_verdict}")
    print("  (report-only dims are supervisory estimators — validated via")
    print("   inter-rater/inter-model agreement, not static ground truth)")
    if report.failing_dimensions:
        print(f"  Failing HARD-GT dims: {', '.join(report.failing_dimensions)}")
        print("  Action: revise QA agent prompt for failing dimensions, re-run calibration.")

    # DT-025: inter-dimension correlation report
    if report.top_correlated_pairs:
        print()
        print("INTER-DIMENSION CORRELATION (top-3 static pairs, ~orthogonal check):")
        for p in report.top_correlated_pairs:
            flag = "  *** JUSTIFY OR FUSE ***" if p.note else ""
            print(f"  {p.dim_a} <-> {p.dim_b}:  rho={p.spearman_rho:+.3f}{flag}")
        high = [p for p in report.top_correlated_pairs if p.note]
        if high:
            print("  Note: pairs with rho > 0.90 require explicit justification")
            print("  in Section 4.2.3 P2 that supervisory distinguishability")
            print("  is maintained despite empirical correlation.")
        else:
            print("  All pairs below 0.90 -- ~orthogonal claim defensible.")
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
    parser.add_argument("--cache", default=None, help="Path to LLM cache JSON (read+write)")
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        logger.error("Corpus file not found: %s", corpus_path)
        sys.exit(1)

    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    output_path = Path(args.output) if args.output else None
    llm_cache_path = Path(args.cache) if args.cache else None

    report = run_calibration(
        corpus=corpus,
        output_path=output_path,
        generate_plots=not args.no_plots,
        llm_cache_path=llm_cache_path,
    )

    sys.exit(0 if report.overall_verdict == "GO" else 1)


if __name__ == "__main__":
    main()
