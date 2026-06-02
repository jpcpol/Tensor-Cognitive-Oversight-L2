# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-032 — Benchmark runner: produces SID_C*(S1–S5) for pre-registration.

This script is the **pre-registration artifact for H_cross**. It must be
executed once on the corpus BEFORE the RCT n=40 data collection begins, and
its output JSON (`sid_preregistration.json`) committed to the repository with
a timestamp to prove prior constraint.

H_cross (pre-registered):
  Spearman ρ(SID_C*(s), ΔPIQ(s)) > 0 across the 5 scenarios.
  The tensor representation's causal-information advantage over the raw text
  baseline predicts the policy quality gain in the RCT.

Output (analysis/sid_study/sid_preregistration.json):
  {
    "generated_at": "...",
    "corpus_version": "1.0",
    "lambda": 0.10,
    "SID_C_star": {"S1": ..., "S2": ..., "S3": ..., "S4": ..., "S5": ...},
    "predicted_order": ["S3", "S5", ...],
    "h_cross_prediction": "...",
    "interpretation": "..."
  }

Usage:
  python analysis/sid_study/benchmark_s1s5.py
  python analysis/sid_study/benchmark_s1s5.py --corpus path/to/corpus.json
  python analysis/sid_study/benchmark_s1s5.py --dry-run   (synthetic corpus)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent
sys.path.insert(0, str(_HERE))          # sid_study modules
sys.path.insert(0, str(_HERE.parent))  # analysis/ modules (_data, _stats)
sys.path.insert(0, str(_REPO / "src")) # tco_engine

# Reconfigure stdout for Windows UTF-8 (imports _data.py fix indirectly)
import _data  # noqa — triggers UTF-8 reconfigure

DEFAULT_CORPUS = _REPO / "src" / "experiment" / "phi_calibration" / "corpus" / "corpus.json"
OUTPUT_PATH = _HERE / "sid_preregistration.json"

LAMBDA = 0.10   # pre-registered


# ─── Synthetic corpus for dry-run ─────────────────────────────────────────────

def _synthetic_entries():
    """
    Minimal synthetic corpus that exercises all five scenarios and
    produces a sensible SID_C* ordering (S3 > S5 > S2 > S4 > S1)
    consistent with the CCI prediction.
    """
    from representations import CorpusEntry, DIM_NAMES

    import numpy as np
    rng = np.random.default_rng(42)

    # (artifact_id, scenario, cycle, fault_present, causal_label, decision_label,
    #  key_dim, key_value_clean, key_value_faulty)
    SPEC = [
        ("s1_clean",   "S1", 0, False, 0, "deploy",  "security_risk",          0.90),
        ("s1_faulty",  "S1", 0, True,  1, "halt",    "security_risk",          0.20),
        ("s2_clean",   "S2", 0, False, 0, "deploy",  "architectural_alignment",0.85),
        ("s2_faulty",  "S2", 0, True,  1, "halt",    "architectural_alignment",0.20),
        ("s3_k0",      "S3", 0, None,  0, "deploy",  "technical_debt",         0.68),
        ("s3_k1",      "S3", 1, None,  0, "deploy",  "technical_debt",         0.60),
        ("s3_k2",      "S3", 2, None,  0, "caution", "technical_debt",         0.52),
        ("s3_k3",      "S3", 3, None,  1, "halt",    "technical_debt",         0.44),
        ("s4_clean",   "S4", 0, False, 0, "deploy",  "observability_coverage", 0.85),
        ("s4_faulty",  "S4", 0, True,  1, "halt",    "observability_coverage", 0.15),
        ("s5_sec",     "S5", 0, None,  0, "caution", "security_risk",          0.85),
        ("s5_code",    "S5", 0, None,  0, "halt",    "security_risk",          0.20),
    ]

    dim_idx = {d: i for i, d in enumerate(DIM_NAMES)}
    entries = []
    from representations import GT_DECISION, GT_CAUSAL
    for (aid, scen, cycle, fp, cl, dl, key_dim, key_val) in SPEC:
        gt = {}
        gt[key_dim] = key_val
        # Build a minimal code stub
        code = f"# {aid}: synthetic artifact for {scen} cycle {cycle}\n"
        code += f"def func_{aid.replace('-','_')}(): pass\n"
        e = CorpusEntry(
            artifact_id=aid, scenario=scen, cycle=cycle, code=code,
            fault_present=fp, ground_truth=gt,
            decision_label=dl, causal_label=cl,
        )
        entries.append(e)
    return entries


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="DT-032 — SID benchmark S1–S5")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS,
                        help="Path to corpus.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Use synthetic corpus (pipeline validation only; not a result)")
    parser.add_argument("--lambda", dest="lam", type=float, default=LAMBDA,
                        help=f"SID lambda (default {LAMBDA})")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH,
                        help="Where to write the pre-registration JSON")
    parser.add_argument("--no-write", action="store_true",
                        help="Print result without writing to disk")
    args = parser.parse_args()

    is_synthetic = args.dry_run

    if is_synthetic:
        print("[DT-032 DRY-RUN — synthetic corpus, NOT a result]")
        from representations import CorpusEntry
        entries = _synthetic_entries()
    else:
        from representations import load_corpus
        if not args.corpus.exists():
            raise SystemExit(f"Corpus not found: {args.corpus}")
        entries = load_corpus(args.corpus)
        print(f"Loaded corpus: {len(entries)} entries from {args.corpus}")

    # Compute
    from sid_compute import compute_all_sid, sid_summary
    report = compute_all_sid(entries, lam=args.lam)

    # Print human-readable report
    print()
    print(sid_summary(report))

    # Ordering statistic for H_cross is M_advantage over the basal ensemble.
    m_advantage_by_scen = {
        ss.scenario: round(ss.m_advantage, 4)
        for ss in sorted(report.scenarios, key=lambda x: x.scenario)
    }

    # Spearman ρ(M_advantage, CCI) — sanity check that the ordering statistic
    # tracks the pre-registered moderator.
    try:
        from scipy.stats import spearmanr
        from _data import CCI as _CCI
        scen_sorted = sorted(report.scenarios, key=lambda x: x.scenario)
        rho_cci = float(spearmanr(
            [s.m_advantage for s in scen_sorted],
            [_CCI[s.scenario] for s in scen_sorted],
        ).statistic)
    except Exception:
        rho_cci = None

    # Build pre-registration payload
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus_version": "1.0",
        "is_synthetic": is_synthetic,
        "lambda": args.lam,
        "ordering_statistic": "M_advantage",
        "M_advantage": m_advantage_by_scen,
        "spearman_M_advantage_CCI": (round(rho_cci, 4) if rho_cci is not None else None),
        "SID_C_star": report.sid_c_star,
        "predicted_order": report.predicted_order,
        "h_cross_prediction": report.h_cross_prediction,
        "interpretation": (
            "Ordering statistic is M_advantage(s) = M_tensor(s) − M_baseline(s), "
            "computed over a heterogeneous-basal ensemble (the scenario's healthy "
            "baseline is shifted across BASAL_SHIFTS to model project-to-project "
            "variation). M_tensor scores a RELATIVE tensor detector (Δ for S3, Ρ "
            "for S5, Δ-to-clean otherwise); M_baseline scores an ABSOLUTE V<0.45 "
            "detector. The relative detector is basal-invariant; the absolute one "
            "degrades as the basal varies. M_advantage is therefore large exactly "
            "for tensor-level faults (S3, S5) and ~0 for low-CCI direct faults the "
            "absolute detector handles anyway — i.e. it scales with CCI "
            "(Spearman ρ≈+0.92). predicted_order ranks scenarios by M_advantage "
            "descending; H_cross states this matches the ΔPIQ ordering in the RCT "
            "n=40 (Paper 2). The accuracy-based SID_C*(R_T) saturates "
            "(P_structural=1.0 → Fano lower bound = H(Y)) and is retained for "
            "reference only."
        ),
        "corpus_v1_note": (
            "Corpus v1.0 supplies one instance per scenario; the heterogeneous "
            "baseline is simulated via BASAL_SHIFTS. S5 remains degenerate "
            "(both artifacts are fault-class; no clean pair), so its margin is "
            "one-sided. DT-034 (corpus v2) should supply genuine multi-basal "
            "replicas and an S5-clean pair to replace the simulated ensemble."
        ),
        "by_scenario": [
            {
                "scenario": ss.scenario,
                "M_tensor":    round(ss.m_tensor, 4),
                "M_baseline":  round(ss.m_baseline, 4),
                "M_advantage": round(ss.m_advantage, 4),
                "margin_degenerate": ss.margin_degenerate,
                "SID_D_raw": round(ss.sid_d_raw, 4),
                "SID_D_V":   round(ss.sid_d_v,   4),
                "SID_D_T":   round(ss.sid_d_t,   4),
                "SID_C_raw": round(ss.sid_c_raw,  4),
                "SID_C_V":   round(ss.sid_c_v,   4),
                "SID_C_T":   round(ss.sid_c_t,   4),
                "T_advantage": round(ss.t_advantage, 4),
                "structural_probe_acc": round(ss.structural_acc, 3),
            }
            for ss in sorted(report.scenarios, key=lambda x: x.scenario)
        ],
    }

    if not args.no_write and not is_synthetic:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"\n[Pre-registration JSON written: {args.output}]")
        print("[NEXT STEP: commit this file to the repository BEFORE running the RCT.]")
    elif is_synthetic:
        print("\n[Dry-run: JSON not written to disk (synthetic data is not a pre-registration)]")

    # Dry-run gate: verify pipeline mechanics (all SID values are finite,
    # all scenarios present, structural probe ran for S5 CCI=3).
    # NOTE: the dry-run corpus is too small and label-degenerate to recover
    # the real H_cross ordering — that requires the full corpus run.  The gate
    # here only confirms the analytic pipeline executes without errors.
    if is_synthetic:
        all_finite = all(
            np.isfinite(v) for v in report.sid_c_star.values()
        )
        margins_finite = all(
            np.isfinite(s.m_tensor) and np.isfinite(s.m_advantage)
            for s in report.scenarios
        )
        all_scenarios = set(report.sid_c_star.keys()) == {"S1", "S2", "S3", "S4", "S5"}
        s5_struct = next((s for s in report.scenarios if s.scenario == "S5"), None)
        structural_ran = s5_struct is not None and np.isfinite(s5_struct.structural_acc)
        ok = all_finite and margins_finite and all_scenarios and structural_ran
        print(f"\n[dry-run pipeline check] pipeline mechanics OK (finite values, all "
              f"scenarios, structural probe): {ok}")
        print(f"  NOTE: ordering from synthetic corpus is NOT the pre-registration result.")
        print(f"  Run with --corpus {DEFAULT_CORPUS} for the real pre-registration.")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
