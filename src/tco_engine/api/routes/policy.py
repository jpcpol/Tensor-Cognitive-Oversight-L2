# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Policy endpoint — P_new → PolicyIntent + PIQ scoring.

Phase 2 placeholder. The policy processor (`core/policy_processor.py`) and the
PIQ LLM-Judge (`src/experiment/piq_evaluation/`) are wired here once the
experiment runner (Phase 2) lands.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/inject")
def inject_policy():
    raise HTTPException(
        status_code=501,
        detail="Policy injection lands in Phase 2 (experiment runner).",
    )
