# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Stratified randomization for group assignment.

Preserves the experience-balanced design of the participant session protocol
(Junior 2–4y, Mid 5–9y, Senior 10+y). Within each stratum, a new participant
is assigned to whichever group currently has fewer members in that stratum;
ties are broken randomly. The admin can override the assignment afterwards.
"""
import random

from sqlalchemy.orm import Session

from tco_engine.db.models import CalParticipant


def stratum_for_experience(years: int) -> str:
    if years <= 4:
        return "junior"
    if years <= 9:
        return "mid"
    return "senior"


def assign_group(db: Session, stratum: str) -> str:
    """
    Balanced assignment within a stratum: pick the group with fewer current
    members; random tie-break. Returns "control" or "experimental".
    """
    n_control = db.query(CalParticipant).filter(
        CalParticipant.experience_stratum == stratum,
        CalParticipant.group == "control",
    ).count()
    n_experimental = db.query(CalParticipant).filter(
        CalParticipant.experience_stratum == stratum,
        CalParticipant.group == "experimental",
    ).count()

    if n_control < n_experimental:
        return "control"
    if n_experimental < n_control:
        return "experimental"
    return random.choice(["control", "experimental"])
