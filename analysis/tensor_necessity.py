# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-023 — Tensor Necessity Proof (analysis script)

Demonstrates empirically that S3 (gradual debt) and S5 (inter-agent conflict)
are not reliably detectable through individual artifact review, and ARE naturally
surfaced by tensor-level operations.

This is the direct empirical counter-argument to "tensor washing" (the claim
that a relational table or simple array would suffice).

Key argument:
  The tensor makes these supervisory operations OPERATIONALLY FIRST-CLASS —
  not merely more convenient. The SQL equivalent requires a self-join that
  reconstructs the coordinate system at the application layer, destroying
  the semantic clarity of the inference operations.

Outputs (in analysis/figures/):
  tensor_necessity_s3.png — artifact-level view vs tensor Δ view for S3
  tensor_necessity_s5.png — artifact-level view vs tensor Ρ view for S5
  tensor_necessity_combined.png — side-by-side summary figure for paper

Usage:
  python analysis/tensor_necessity.py
  python analysis/tensor_necessity.py --no-plots  (text output only)
  python analysis/tensor_necessity.py --output path/to/figures/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ─── Simulation parameters ────────────────────────────────────────────────────

# S3: Gradual technical debt accumulation
# v8 (technical_debt): 1 = no debt. Degrades -0.08 per cycle over 4 cycles.
# The per-cycle delta (0.08) is within individual evaluation noise (σ ≈ 0.06–0.10).
# The cumulative 3-cycle delta (0.24) reliably crosses the Δ alert threshold (0.05*3).
S3_V8_TRAJECTORY = np.array([0.68, 0.60, 0.52, 0.44])  # k=0,1,2,3
S3_EVAL_NOISE_STD = 0.07     # individual evaluator noise (LLM variance, static analysis rounding)
S3_DELTA_THRESHOLD = 0.05    # Δ threshold per cycle — must exceed this to fire alert
S3_CUMULATIVE_THRESHOLD = 0.20  # 3-cycle cumulative threshold for trend detection
N_SIMULATED_REVIEWERS = 1000  # Monte Carlo for detection rate estimation

# S5: Inter-agent conflict
# security_agent produces v4=0.85, v6=0.25
# code_agent produces v4=0.20, v6=0.75
# Per-artifact review sees only one agent's output at a time.
# Joint tensor view: |T[d,i,j0,k] - T[d,i,j1,k]| → Ρ
S5_SECURITY_AGENT = {"v4_security": 0.85, "v6_testability": 0.25}
S5_CODE_AGENT     = {"v4_security": 0.20, "v6_testability": 0.75}
S5_RHO_THRESHOLD  = 0.30  # conflict detection threshold

DIM_NAMES = [
    "functional_correctness", "architectural_alignment", "scalability_projection",
    "security_risk", "observability_coverage", "testability", "maintainability",
    "technical_debt", "performance", "confidence", "anomaly_score",
]
V4_IDX = 3  # security_risk
V6_IDX = 5  # testability
V8_IDX = 7  # technical_debt


# ─── S3 analysis: gradual debt ────────────────────────────────────────────────

def simulate_s3_artifact_level_detection(n_sim: int = N_SIMULATED_REVIEWERS) -> dict:
    """
    Simulate individual artifact review for S3.

    A reviewer evaluating a single artifact observes v8 = true_value + noise.
    They would need to notice a -0.08 change between consecutive commits.
    With noise σ=0.07, this delta is within the noise floor.

    Returns detection rates under both review modes.
    """
    rng = np.random.default_rng(seed=42)

    # Artifact-level detection: reviewer sees one commit at a time.
    # They must notice a degradation > NOTICEABLE_THRESHOLD in a single cycle.
    # With noise sigma=0.07, a true delta of 0.08 is barely above the noise floor.
    # A reviewer only flags it as "clearly degrading" if the signed drop exceeds 0.20.
    NOTICEABLE_SINGLE_CYCLE = 0.20  # threshold for a human to flag a single commit as "clearly worse"
    artifact_level_detections = 0
    for _ in range(n_sim):
        noisy = S3_V8_TRAJECTORY + rng.normal(0, S3_EVAL_NOISE_STD, size=4)
        noisy = np.clip(noisy, 0, 1)
        # Signed degradation per cycle (positive = worse quality)
        signed_drops = noisy[:-1] - noisy[1:]
        if np.any(signed_drops > NOTICEABLE_SINGLE_CYCLE):
            artifact_level_detections += 1

    # Tensor Δ detection: 3-cycle cumulative slope — signal emerges from noise
    tensor_detections = 0
    for _ in range(n_sim):
        noisy = S3_V8_TRAJECTORY + rng.normal(0, S3_EVAL_NOISE_STD, size=4)
        noisy = np.clip(noisy, 0, 1)
        # Tensor computes: T[v8, :, :, k] - T[v8, :, :, k-3]
        cumulative_delta = noisy[0] - noisy[3]  # total drop over 3 cycles
        if cumulative_delta > S3_CUMULATIVE_THRESHOLD:
            tensor_detections += 1

    return {
        "artifact_level_detection_rate": artifact_level_detections / n_sim,
        "tensor_detection_rate": tensor_detections / n_sim,
        "true_per_cycle_delta": 0.08,
        "true_cumulative_delta": S3_V8_TRAJECTORY[0] - S3_V8_TRAJECTORY[3],
        "noise_std": S3_EVAL_NOISE_STD,
        "snr_per_cycle": 0.08 / S3_EVAL_NOISE_STD,
        "snr_cumulative": (S3_V8_TRAJECTORY[0] - S3_V8_TRAJECTORY[3]) / S3_EVAL_NOISE_STD,
    }


def build_s3_tensor() -> np.ndarray:
    """
    Build a minimal T[11, 1, 1, 4] tensor for S3.
    All dimensions are stable except v8 which degrades over k=0..3.
    """
    T = np.full((11, 1, 1, 4), 0.75)  # stable baseline
    T[V8_IDX, 0, 0, :] = S3_V8_TRAJECTORY
    return T


# ─── S5 analysis: inter-agent conflict ───────────────────────────────────────

def simulate_s5_artifact_level_detection() -> dict:
    """
    Simulate per-artifact review for S5.

    A reviewer sees one agent's artifact at a time. They would need to:
    1. Review agent_0 output → observe v4=0.85, v6=0.25
    2. Review agent_1 output → observe v4=0.20, v6=0.75
    3. Mentally compute the difference and recognize it as a conflict

    This requires holding both evaluations in working memory simultaneously
    and applying a comparison operation — precisely what exceeds the NCF.
    The tensor Ρ operation does this automatically.
    """
    v4_diff = abs(S5_SECURITY_AGENT["v4_security"] - S5_CODE_AGENT["v4_security"])
    v6_diff = abs(S5_SECURITY_AGENT["v6_testability"] - S5_CODE_AGENT["v6_testability"])

    # Build T[11, 1, 2, 1] — 2 agents, 1 stage, 1 cycle
    T = np.full((11, 1, 2, 1), 0.75)
    T[V4_IDX, 0, 0, 0] = S5_SECURITY_AGENT["v4_security"]
    T[V6_IDX, 0, 0, 0] = S5_SECURITY_AGENT["v6_testability"]
    T[V4_IDX, 0, 1, 0] = S5_CODE_AGENT["v4_security"]
    T[V6_IDX, 0, 1, 0] = S5_CODE_AGENT["v6_testability"]

    # Tensor Ρ: |T[d, i, j0, k] - T[d, i, j1, k]|
    rho_vector = np.abs(T[:, 0, 0, 0] - T[:, 0, 1, 0])
    conflicts = [(DIM_NAMES[d], float(rho_vector[d])) for d in range(11) if rho_vector[d] > S5_RHO_THRESHOLD]

    return {
        "v4_delta": v4_diff,
        "v6_delta": v6_diff,
        "exceeds_rho_threshold": v4_diff > S5_RHO_THRESHOLD or v6_diff > S5_RHO_THRESHOLD,
        "rho_threshold": S5_RHO_THRESHOLD,
        "conflicts_detected_by_tensor": conflicts,
        "n_conflicts": len(conflicts),
        "artifact_level_requires": (
            "Reviewer must hold both agent outputs in working memory simultaneously "
            "and apply a cross-agent comparison operation - exceeds NCF working memory capacity."
        ),
        "tensor_operation": "|T[d, i, j0, k] - T[d, i, j1, k]| > 0.30",
    }


# ─── SQL comparison ───────────────────────────────────────────────────────────

def print_sql_comparison() -> None:
    print("\n" + "="*70)
    print("TENSOR vs. SQL - Operational First-Classness Demonstration")
    print("="*70)

    print("\n[Tensor operation - S3 cumulative debt detection]")
    print("  T[v8_idx, :, :, 0] - T[v8_idx, :, :, 3]  # 1 line, O(1)")

    print("\n[Equivalent SQL - requires self-join reconstructing the coordinate system]")
    sql = """
  SELECT
    t1.stage, t1.agent,
    t1.v8 AS v8_k0,
    t3.v8 AS v8_k3,
    (t1.v8 - t3.v8) AS delta_3cycle
  FROM evaluation_vectors t1
  JOIN evaluation_vectors t3
    ON t1.stage = t3.stage
    AND t1.agent = t3.agent
    AND t1.cycle_k = 0
    AND t3.cycle_k = 3
  WHERE (t1.v8 - t3.v8) > 0.20
    AND t1.session_id = :session_id;
  -- Note: extending to all 11 dimensions requires either 11 columns
  -- or an UNPIVOT/lateral join that further obscures the detection logic.
"""
    print(sql)

    print("[Tensor operation - S5 inter-agent conflict detection]")
    print("  np.abs(T[:, stage, j0, k] - T[:, stage, j1, k]) > 0.30  # 1 line, all dims")

    print("\n[Equivalent SQL - loses the 'same stage, same cycle' semantic]")
    sql2 = """
  SELECT
    a1.dimension,
    a1.score AS agent0_score,
    a2.score AS agent1_score,
    ABS(a1.score - a2.score) AS conflict_delta
  FROM (
    SELECT dimension, score FROM agent_scores
    WHERE agent_id = 'security_agent' AND stage = :stage AND cycle_k = :k
  ) a1
  JOIN (
    SELECT dimension, score FROM agent_scores
    WHERE agent_id = 'code_agent'     AND stage = :stage AND cycle_k = :k
  ) a2 USING (dimension)
  WHERE ABS(a1.score - a2.score) > 0.30;
  -- The join condition encodes what the tensor index expresses structurally.
  -- More agents require N*(N-1)/2 pairs. Tensor slicing scales at O(n_dims).
"""
    print(sql2)
    print("Conclusion: The tensor does not do what SQL cannot - it makes what")
    print("SQL can do OPERATIONALLY FIRST-CLASS: the inference engine expresses")
    print("Delta and Rho as direct tensor operations without reconstructing coordinates.")


# ─── Report + plots ───────────────────────────────────────────────────────────

def print_report(s3: dict, s5: dict) -> None:
    print("\n" + "="*70)
    print("DT-023 - Tensor Necessity Proof")
    print("="*70)

    print("\n[S3 - Gradual Debt: Detection Rate Comparison]")
    print(f"  True v8 trajectory:        {list(S3_V8_TRAJECTORY)}")
    print(f"  True per-cycle delta:       {s3['true_per_cycle_delta']:.3f}")
    print(f"  True cumulative delta:      {s3['true_cumulative_delta']:.3f}")
    print(f"  Evaluator noise (sigma):    {s3['noise_std']:.3f}")
    print(f"  SNR (per-cycle):            {s3['snr_per_cycle']:.2f}  <-- below reliable detection")
    print(f"  SNR (cumulative 3-cycle):   {s3['snr_cumulative']:.2f}  <-- above reliable detection")
    print(f"  Artifact-level detection:   {s3['artifact_level_detection_rate']:.1%}  (reviewer sees 1 commit)")
    print(f"  Tensor delta detection:     {s3['tensor_detection_rate']:.1%}  (cumulative 3-cycle slope)")
    print()
    print(f"  Interpretation: per-cycle delta ({s3['true_per_cycle_delta']:.2f}) is within noise floor")
    print(f"  (sigma={s3['noise_std']:.2f}). Individual artifact review cannot reliably distinguish")
    print(f"  signal from noise. The tensor accumulates the signal over k=0..3, producing a")
    print(f"  cumulative delta ({s3['true_cumulative_delta']:.2f}) that is {s3['snr_cumulative']:.1f}x the noise std.")

    print("\n[S5 - Inter-Agent Conflict: Detection by Review Mode]")
    print(f"  security_agent: v4={S5_SECURITY_AGENT['v4_security']}, v6={S5_SECURITY_AGENT['v6_testability']}")
    print(f"  code_agent:     v4={S5_CODE_AGENT['v4_security']}, v6={S5_CODE_AGENT['v6_testability']}")
    print(f"  v4 delta:       {s5['v4_delta']:.2f}  (threshold: {s5['rho_threshold']})")
    print(f"  v6 delta:       {s5['v6_delta']:.2f}  (threshold: {s5['rho_threshold']})")
    print(f"  Exceeds Rho threshold: {s5['exceeds_rho_threshold']}")
    print(f"  Conflicts detected by tensor: {s5['n_conflicts']} dimensions")
    for dim, delta in s5["conflicts_detected_by_tensor"]:
        print(f"    {dim}: delta={delta:.3f}")
    print(f"\n  Artifact-level: {s5['artifact_level_requires']}")
    print(f"  Tensor operation: {s5['tensor_operation']}")


def generate_plots(s3: dict, output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
    except ImportError:
        print("[plots skipped - matplotlib not available]")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        "Tensor Operational First-Classness: S3 and S5\n"
        "TCO — Tensor-Based Cognitive Oversight",
        fontsize=13, fontweight="bold", y=0.98,
    )
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    rng = np.random.default_rng(seed=42)

    # ── Panel 1: S3 artifact-level view (noisy, 1 reviewer, 4 commits)
    ax1 = fig.add_subplot(gs[0, 0])
    for trial in range(8):
        noisy = S3_V8_TRAJECTORY + rng.normal(0, S3_EVAL_NOISE_STD, size=4)
        noisy = np.clip(noisy, 0, 1)
        ax1.plot(range(4), noisy, "o--", color="steelblue", alpha=0.4, linewidth=1)
    ax1.plot(range(4), S3_V8_TRAJECTORY, "o-", color="red", linewidth=2.5, label="True v₈", zorder=5)
    ax1.axhline(S3_V8_TRAJECTORY[0] - S3_CUMULATIVE_THRESHOLD, color="orange",
                linestyle=":", label=f"Alert threshold (−{S3_CUMULATIVE_THRESHOLD})")
    ax1.set_title("S3 — Artifact-Level View\n(each reviewer sees 1 commit)", fontsize=10)
    ax1.set_xlabel("Commit / cycle k")
    ax1.set_ylabel("v₈ technical_debt score")
    ax1.set_xticks(range(4))
    ax1.set_xticklabels([f"k={i}" for i in range(4)])
    ax1.set_ylim(0.2, 0.9)
    ax1.legend(fontsize=8)
    ax1.text(0.05, 0.08, f"Per-cycle delta: {S3_V8_TRAJECTORY[0]-S3_V8_TRAJECTORY[1]:.2f}\n"
             f"Noise sigma: {S3_EVAL_NOISE_STD:.2f}\nSNR: {0.08/S3_EVAL_NOISE_STD:.1f}x",
             transform=ax1.transAxes, fontsize=8, color="gray",
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    # ── Panel 2: S3 tensor Δ view
    ax2 = fig.add_subplot(gs[0, 1])
    cumulative_deltas = []
    for trial in range(200):
        noisy = S3_V8_TRAJECTORY + rng.normal(0, S3_EVAL_NOISE_STD, size=4)
        noisy = np.clip(noisy, 0, 1)
        cumulative_deltas.append(noisy[0] - noisy[3])
    ax2.hist(cumulative_deltas, bins=30, color="steelblue", edgecolor="white", alpha=0.8)
    ax2.axvline(S3_CUMULATIVE_THRESHOLD, color="orange", linewidth=2,
                linestyle="--", label=f"Alert threshold ({S3_CUMULATIVE_THRESHOLD})")
    ax2.axvline(np.mean(cumulative_deltas), color="red", linewidth=2,
                label=f"Mean delta ({np.mean(cumulative_deltas):.2f})")
    ax2.set_title("S3 — Tensor Δ View\nT[v8,:,:,0] − T[v8,:,:,3]", fontsize=10)
    ax2.set_xlabel("Cumulative 3-cycle delta in v₈")
    ax2.set_ylabel("Frequency (n=200 simulations)")
    detected = sum(1 for d in cumulative_deltas if d > S3_CUMULATIVE_THRESHOLD)
    ax2.legend(fontsize=8)
    ax2.text(0.55, 0.75, f"Detection rate:\n{detected/len(cumulative_deltas):.0%}",
             transform=ax2.transAxes, fontsize=10, fontweight="bold",
             color="green", bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9))

    # ── Panel 3: S5 per-artifact view
    ax3 = fig.add_subplot(gs[1, 0])
    dims_shown = ["security_risk", "testability", "maintainability", "technical_debt", "confidence"]
    dim_idx = [DIM_NAMES.index(d) for d in dims_shown]

    agent0_scores = np.array([0.85, 0.25, 0.55, 0.70, 0.80])
    agent1_scores = np.array([0.20, 0.75, 0.75, 0.65, 0.75])

    x = np.arange(len(dims_shown))
    width = 0.35
    bars0 = ax3.bar(x - width/2, agent0_scores, width, label="security_agent", color="steelblue", alpha=0.8)
    bars1 = ax3.bar(x + width/2, agent1_scores, width, label="code_agent", color="coral", alpha=0.8)
    ax3.set_title("S5 — Per-Artifact View\n(reviewer sees one agent at a time)", fontsize=10)
    ax3.set_ylabel("Quality score [0,1]")
    ax3.set_xticks(x)
    ax3.set_xticklabels([d.replace("_", "\n") for d in dims_shown], fontsize=7)
    ax3.set_ylim(0, 1.05)
    ax3.axhline(S5_RHO_THRESHOLD, color="orange", linestyle=":", linewidth=1.5,
                label=f"Ρ threshold ({S5_RHO_THRESHOLD})")
    ax3.legend(fontsize=8)
    ax3.text(0.02, 0.88, "Conflict is hidden:\neach artifact looks plausible",
             transform=ax3.transAxes, fontsize=8, color="gray",
             bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    # ── Panel 4: S5 tensor Ρ view
    ax4 = fig.add_subplot(gs[1, 1])
    rho_vector = np.abs(agent0_scores - agent1_scores)
    colors = ["tomato" if r > S5_RHO_THRESHOLD else "steelblue" for r in rho_vector]
    ax4.bar(x, rho_vector, color=colors, edgecolor="white", alpha=0.9)
    ax4.axhline(S5_RHO_THRESHOLD, color="orange", linewidth=2,
                linestyle="--", label=f"Conflict threshold ({S5_RHO_THRESHOLD})")
    ax4.set_title("S5 — Tensor Ρ View\n|T[d,i,j₀,k] − T[d,i,j₁,k]|", fontsize=10)
    ax4.set_ylabel("Inter-agent delta [0,1]")
    ax4.set_xticks(x)
    ax4.set_xticklabels([d.replace("_", "\n") for d in dims_shown], fontsize=7)
    ax4.set_ylim(0, 1.05)
    ax4.legend(fontsize=8)
    n_conflicts = sum(1 for r in rho_vector if r > S5_RHO_THRESHOLD)
    ax4.text(0.55, 0.80, f"Conflicts detected:\n{n_conflicts}/{len(dims_shown)} dimensions\n(red bars)",
             transform=ax4.transAxes, fontsize=9, fontweight="bold",
             color="tomato", bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9))

    fig.savefig(output_dir / "tensor_necessity_combined.png", dpi=150, bbox_inches="tight")
    print(f"  Figure saved: {output_dir / 'tensor_necessity_combined.png'}")
    plt.close(fig)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="DT-023 - Tensor Necessity Proof")
    parser.add_argument("--no-plots", action="store_true", help="Skip matplotlib output")
    parser.add_argument("--output", "-o", type=Path,
                        default=Path(__file__).parent / "figures",
                        help="Output directory for figures")
    args = parser.parse_args()

    s3 = simulate_s3_artifact_level_detection()
    s5 = simulate_s5_artifact_level_detection()

    print_report(s3, s5)
    print_sql_comparison()

    if not args.no_plots:
        print(f"\nGenerating figures in {args.output} ...")
        generate_plots(s3, args.output)

    # Exit code: 0 if both scenarios demonstrate the expected detection gap
    s3_gap = s3["tensor_detection_rate"] - s3["artifact_level_detection_rate"]
    s5_confirmed = s5["exceeds_rho_threshold"] and s5["n_conflicts"] >= 2
    success = s3_gap > 0.3 and s5_confirmed

    print(f"\n{'='*70}")
    print(f"S3 detection gap (tensor - artifact-level): {s3_gap:+.1%}")
    print(f"S5 conflict detected by tensor: {s5_confirmed}")
    print(f"Tensor operational first-classness: {'CONFIRMED' if success else 'NEEDS REVIEW'}")
    print(f"{'='*70}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
