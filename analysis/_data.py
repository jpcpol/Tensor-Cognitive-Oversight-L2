# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — Shared data layer for the statistical analysis suite.

Every hypothesis script (h1..h5, h_obs, ancova, effect_sizes) reads its data
through this module so the loading, schema and synthetic-fixture logic live in
exactly one place.

Two sources:

  1. Real data — `load_dataset(db_url=...)` reads the persisted `cal_*` tables
     via SQLAlchemy and flattens them into tidy pandas frames (one row per
     unit-of-analysis). Pilot sessions (`is_pilot=True`) and aborted sessions
     are excluded from the analytic frames.

  2. Synthetic data — `synthetic_dataset(...)` generates a reproducible
     RCT-shaped dataset whose effect structure is calibrated to the
     **pre-registered** prediction: the TCO effect scales with the Causal
     Complexity Index (CCI) of each scenario. This lets `--dry-run` exercise
     the full analytic pipeline (and assert it recovers the planted effects)
     long before a single real participant is run — the gate the roadmap
     requires.

The synthetic generator is NOT a result. It exists to (a) prove the scripts
execute end-to-end and (b) act as an analytic unit test: if a script cannot
recover an effect that was deliberately planted, the script is wrong.

Tidy frames produced by both sources
------------------------------------
  participants : one row / participant   (group, stratum, covariates)
  tlx          : one row / (session, checkpoint)
  tasks        : one row / (session, task, scenario)  + accuracy, detected, ttc
  ncf          : one row / session        (4 NCF proxies)
  policies     : one row / (session, scenario)  + piq_score, delta_vector
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

# Windows consoles default to cp1252 and choke on the mathematical symbols
# (Δ, ρ, η², −) these reports print. Force UTF-8 on stdout/stderr once, here,
# since every analysis script imports this module.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

# ─── Benchmark constants (pre-registered) ────────────────────────────────────

# Causal Complexity Index per scenario = number of tensor indices that must be
# read jointly to surface the causal structure C. Pre-registered in
# Documentacion/CAL_Benchmark_v1.md. This is the moderator for H_OBS.
CCI = {"S1": 1, "S4": 2, "S2": 2, "S3": 4, "S5": 3}

# Canonical task → scenario binding (from TASK_SEQUENCE / roadmap).
TASK_SCENARIO = {"T1": "S1", "T2": "S2", "T3": "S3", "T4": "S5"}

SCENARIOS = ["S1", "S2", "S3", "S4", "S5"]
GROUPS = ["control", "experimental"]
STRATA = ["junior", "mid", "senior"]

TLX_SUBSCALES = [
    "mental_demand", "physical_demand", "temporal_demand",
    "performance", "effort", "frustration",
]


@dataclass(frozen=True)
class Dataset:
    """Bundle of tidy analytic frames."""
    participants: pd.DataFrame
    tlx: pd.DataFrame
    tasks: pd.DataFrame
    ncf: pd.DataFrame
    policies: pd.DataFrame
    is_synthetic: bool

    def merged_tlx(self) -> pd.DataFrame:
        """tlx joined with participant group/stratum/covariates."""
        return self.tlx.merge(self.participants, on="participant_id", how="left")

    def merged_tasks(self) -> pd.DataFrame:
        return self.tasks.merge(self.participants, on="participant_id", how="left")

    def merged_policies(self) -> pd.DataFrame:
        return self.policies.merge(self.participants, on="participant_id", how="left")

    def merged_ncf(self) -> pd.DataFrame:
        return self.ncf.merge(self.participants, on="participant_id", how="left")


# ─── Raw-TLX aggregate ────────────────────────────────────────────────────────

def raw_tlx(row: pd.Series) -> float:
    """Unweighted Raw-TLX = mean of the six subscales (performance reverse-scored)."""
    perf = 100 - row["performance"]  # higher subjective performance → lower load
    vals = [row["mental_demand"], row["physical_demand"], row["temporal_demand"],
            perf, row["effort"], row["frustration"]]
    return float(np.mean(vals))


# ─── Real-data loader ─────────────────────────────────────────────────────────

def load_dataset(db_url: str) -> Dataset:
    """
    Load tidy analytic frames from the persisted cal_* tables.

    Only completed, non-pilot sessions are included. Each session is attributed
    to its participant so group / stratum / covariate joins work downstream.
    """
    import sys
    from pathlib import Path

    src = Path(__file__).parent.parent / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from tco_engine.db.models import (  # noqa: E402
        CalParticipant, CalSession, CalTaskResult,
        CalTLXMeasurement, CalNCFProxy, CalPolicyIntent,
    )

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        sessions = (
            db.query(CalSession)
            .filter(CalSession.status == "completed", CalSession.is_pilot.is_(False))
            .all()
        )
        sid_to_pid = {s.id: s.participant_id for s in sessions}
        sids = list(sid_to_pid)

        participants_rows, tlx_rows, task_rows, ncf_rows, policy_rows = [], [], [], [], []

        pids = {p.id: p for p in db.query(CalParticipant).all()}
        for pid in {sid_to_pid[s] for s in sids}:
            p = pids[pid]
            participants_rows.append(dict(
                participant_id=p.id, group=p.group, stratum=p.experience_stratum,
                years_experience=p.years_experience, ai_familiarity=p.ai_familiarity,
            ))

        for m in db.query(CalTLXMeasurement).filter(CalTLXMeasurement.session_id.in_(sids)):
            tlx_rows.append(dict(
                session_id=m.session_id, participant_id=sid_to_pid[m.session_id],
                checkpoint=m.checkpoint,
                mental_demand=m.mental_demand, physical_demand=m.physical_demand,
                temporal_demand=m.temporal_demand, performance=m.performance,
                effort=m.effort, frustration=m.frustration,
            ))
        for r in db.query(CalTaskResult).filter(CalTaskResult.session_id.in_(sids)):
            task_rows.append(dict(
                session_id=r.session_id, participant_id=sid_to_pid[r.session_id],
                task=r.task, scenario=r.scenario, accuracy=r.accuracy,
                detected=r.detected, time_to_first_correction_s=r.time_to_first_correction_s,
            ))
        for n in db.query(CalNCFProxy).filter(CalNCFProxy.session_id.in_(sids)):
            ncf_rows.append(dict(
                session_id=n.session_id, participant_id=sid_to_pid[n.session_id],
                working_memory_saturation=n.working_memory_saturation,
                mean_sigma_severity=n.mean_sigma_severity,
                sigma_accuracy=n.sigma_accuracy,
                iqr_attention_fragmentation_s=n.iqr_attention_fragmentation_s,
            ))
        for pol in db.query(CalPolicyIntent).filter(CalPolicyIntent.session_id.in_(sids)):
            policy_rows.append(dict(
                session_id=pol.session_id, participant_id=sid_to_pid[pol.session_id],
                scenario=pol.scenario, piq_score=pol.piq_score,
                delta_vector=None,  # populated post-hoc by the φ pipeline if available
            ))

        return Dataset(
            participants=pd.DataFrame(participants_rows),
            tlx=pd.DataFrame(tlx_rows),
            tasks=pd.DataFrame(task_rows),
            ncf=pd.DataFrame(ncf_rows),
            policies=pd.DataFrame(policy_rows),
            is_synthetic=False,
        )
    finally:
        db.close()


# ─── Synthetic generator (analytic-pipeline fixture) ─────────────────────────

def synthetic_dataset(n_per_group: int = 20, seed: int = 7) -> Dataset:
    """
    Generate a reproducible RCT-shaped dataset with the pre-registered effect
    structure planted in. NOT a result — a fixture / analytic unit test.

    Planted effects (so the scripts have something to recover):
      • TLX (H1): experimental group lower load; effect grows with mean CCI.
      • Accuracy (H2): experimental higher detection; per-scenario gain ∝ CCI.
      • time-to-correct (H4): experimental faster, strongest on S3 (CCI=4).
      • PIQ (H5): present only for experimental group; PIQ correlates with the
        planted Δ-vector improvement.
      • H_OBS: ΔPIQ(S3,S5) >> ΔPIQ(S1,S4) by construction (gain weighted by CCI).
    """
    rng = np.random.default_rng(seed)
    mean_cci = np.mean(list(CCI.values()))

    # ── participants ──
    prows = []
    for g in GROUPS:
        for _ in range(n_per_group):
            stratum = rng.choice(STRATA, p=[0.3, 0.4, 0.3])
            years = {"junior": rng.integers(2, 4), "mid": rng.integers(4, 8),
                     "senior": rng.integers(8, 20)}[stratum]
            prows.append(dict(
                participant_id=f"P{len(prows):03d}",
                group=g, stratum=stratum,
                years_experience=int(years),
                ai_familiarity=int(rng.integers(0, 5)),
            ))
    participants = pd.DataFrame(prows)

    def cci_norm(s: str) -> float:
        """CCI of scenario s normalized to [0,1] over the observed range."""
        lo, hi = min(CCI.values()), max(CCI.values())
        return (CCI[s] - lo) / (hi - lo)

    # ── TLX (two checkpoints) ──
    tlx_rows = []
    for _, p in participants.iterrows():
        is_exp = p["group"] == "experimental"
        # Base load reduced by skill; experimental gets a CCI-weighted reduction.
        skill = {"junior": 8, "mid": 0, "senior": -8}[p["stratum"]]
        for cp in ("post_t2", "post_t4"):
            # post_t4 follows S5 (CCI=3) → heavier; post_t2 follows S2 (CCI=2)
            cp_cci = CCI["S5"] if cp == "post_t4" else CCI["S2"]
            base = 55 + skill + 4 * cp_cci + rng.normal(0, 6)
            relief = 14 * (cp_cci / max(CCI.values())) if is_exp else 0.0
            center = np.clip(base - relief, 5, 95)

            def jitter(c, lo=0, hi=100):
                return int(np.clip(rng.normal(c, 9), lo, hi))

            tlx_rows.append(dict(
                session_id=f"S_{p['participant_id']}", participant_id=p["participant_id"],
                checkpoint=cp,
                mental_demand=jitter(center), physical_demand=jitter(15),
                temporal_demand=jitter(center - 5),
                performance=jitter(70 + (10 if is_exp else 0)),
                effort=jitter(center), frustration=jitter(center - 10),
            ))
    tlx = pd.DataFrame(tlx_rows)

    # ── tasks (one per scenario; T-tasks map T1..T4, plus S4 as a probe row) ──
    task_rows = []
    for _, p in participants.iterrows():
        is_exp = p["group"] == "experimental"
        skill = {"junior": -0.05, "mid": 0.0, "senior": 0.05}[p["stratum"]]
        for task, scen in list(TASK_SCENARIO.items()) + [("T4b", "S4")]:
            c = cci_norm(scen)
            # Control detection drops as CCI rises (S3/S5 ~invisible to raw review).
            base_p = 0.85 - 0.55 * c + skill
            gain = (0.45 * c) if is_exp else 0.0  # experimental gain ∝ CCI
            p_detect = float(np.clip(base_p + gain, 0.02, 0.98))
            detected = rng.random() < p_detect
            accuracy = float(np.clip(p_detect + rng.normal(0, 0.08), 0, 1))
            # time-to-correct: faster when detected & experimental, esp. high CCI
            if detected:
                ttc = rng.normal(140 - (40 * c if is_exp else -25 * c), 25)
            else:
                ttc = rng.normal(300, 40)  # flailing
            task_rows.append(dict(
                session_id=f"S_{p['participant_id']}", participant_id=p["participant_id"],
                task=task, scenario=scen,
                accuracy=round(accuracy, 3), detected=bool(detected),
                time_to_first_correction_s=round(float(max(ttc, 5)), 1),
            ))
    tasks = pd.DataFrame(task_rows)

    # ── NCF proxies ──
    ncf_rows = []
    for _, p in participants.iterrows():
        is_exp = p["group"] == "experimental"
        wm = np.clip(rng.normal(60 - (12 if is_exp else 0) + 4 * mean_cci, 8), 0, 100)
        ncf_rows.append(dict(
            session_id=f"S_{p['participant_id']}", participant_id=p["participant_id"],
            working_memory_saturation=round(float(wm), 2),
            mean_sigma_severity=round(float(abs(rng.normal(1.4 - (0.3 if is_exp else 0), 0.3))), 3),
            sigma_accuracy=round(float(abs(rng.normal(0.15, 0.05))), 3),
            iqr_attention_fragmentation_s=round(float(abs(rng.normal(12 - (3 if is_exp else 0), 3))), 2),
        ))
    ncf = pd.DataFrame(ncf_rows)

    # ── policies (experimental only): PIQ + planted Δ-vector improvement ──
    policy_rows = []
    for _, p in participants.iterrows():
        if p["group"] != "experimental":
            continue
        for scen in SCENARIOS:
            c = cci_norm(scen)
            # PIQ higher where the dashboard makes C legible (high CCI) — this is
            # the H_OBS signature: policy quality gain tracks CCI.
            piq = float(np.clip(rng.normal(2.6 + 1.6 * c, 0.5), 1, 5))
            # Δ-vector improvement the policy produces, correlated with PIQ (H5).
            delta = float(np.clip(0.04 * piq + rng.normal(0, 0.03), -0.1, 0.4))
            policy_rows.append(dict(
                session_id=f"S_{p['participant_id']}", participant_id=p["participant_id"],
                scenario=scen, piq_score=round(piq, 3), delta_vector=round(delta, 4),
            ))
    policies = pd.DataFrame(policy_rows)

    return Dataset(participants, tlx, tasks, ncf, policies, is_synthetic=True)


# ─── CLI helper shared by all scripts ─────────────────────────────────────────

def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", type=str, default=None,
                        help="SQLAlchemy URL for the cal_* DB (e.g. sqlite:///tco_cal.db). "
                             "If omitted, requires --dry-run.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Use a synthetic dataset to validate the analytic pipeline.")
    parser.add_argument("--n-per-group", type=int, default=20,
                        help="Synthetic participants per group (dry-run only).")
    parser.add_argument("--seed", type=int, default=7, help="Synthetic RNG seed.")
    parser.add_argument("--no-plots", action="store_true", help="Skip matplotlib output.")


def resolve_dataset(args: argparse.Namespace) -> Dataset:
    """Pick the data source from parsed args; fail loudly if neither is given."""
    if args.db:
        return load_dataset(args.db)
    if getattr(args, "dry_run", False):
        return synthetic_dataset(n_per_group=args.n_per_group, seed=args.seed)
    raise SystemExit(
        "No data source: pass --db <url> for real data or --dry-run for the "
        "synthetic analytic fixture."
    )


def banner(title: str, ds: Optional[Dataset] = None) -> None:
    print("=" * 72)
    print(title)
    if ds is not None and ds.is_synthetic:
        print("  [SYNTHETIC DRY-RUN — fixture data, not a result]")
    print("=" * 72)
