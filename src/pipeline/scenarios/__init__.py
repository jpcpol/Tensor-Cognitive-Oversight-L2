# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""Scenario registry — all 5 fault scenarios for the TCO experiment."""
from __future__ import annotations

from pipeline.scenarios import s1_auth, s2_arch, s3_debt, s4_deploy, s5_conflict

# Ordered list for corpus iteration
ALL_SCENARIOS = [s1_auth, s2_arch, s3_debt, s4_deploy, s5_conflict]

SCENARIO_MAP: dict[str, object] = {
    "S1": s1_auth,
    "S2": s2_arch,
    "S3": s3_debt,
    "S4": s4_deploy,
    "S5": s5_conflict,
}


def get_scenario(scenario_id: str):
    mod = SCENARIO_MAP.get(scenario_id.upper())
    if mod is None:
        raise ValueError(f"Unknown scenario: {scenario_id!r}. Valid: {list(SCENARIO_MAP)}")
    return mod
