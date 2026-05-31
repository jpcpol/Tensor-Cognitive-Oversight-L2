# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Pydantic schemas for the CAL experiment platform (`/cal/api`).
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ─── Auth / registration ─────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    country: Optional[str] = None
    years_experience: int = Field(ge=0)
    education_level: Optional[Literal["undergraduate", "graduate", "other"]] = None
    institution: Optional[str] = None
    languages: Optional[str] = None
    ai_familiarity: Optional[int] = Field(default=None, ge=0, le=4)
    prior_tco_exposure: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    participant_id: str


class ConsentRequest(BaseModel):
    consent: bool


# ─── Participant self-view ────────────────────────────────────────────────────

class SessionSummary(BaseModel):
    id: str
    layer: str
    status: str
    is_pilot: bool
    scheduled_at: Optional[datetime] = None


class MeResponse(BaseModel):
    participant_id: str
    email: EmailStr
    name: str
    role: str
    group: Optional[str] = None
    experience_stratum: Optional[str] = None
    consent_given: bool
    current_session: Optional[SessionSummary] = None


# ─── Admin views ─────────────────────────────────────────────────────────────

class AdminParticipant(BaseModel):
    participant_id: str
    name: str
    email: EmailStr
    years_experience: int
    experience_stratum: Optional[str] = None
    group: Optional[str] = None
    ai_familiarity: Optional[int] = None
    prior_tco_exposure: bool
    consent_given: bool
    session_status: Optional[str] = None
    created_at: datetime


class GroupOverrideRequest(BaseModel):
    group: Literal["control", "experimental"]


class InviteRequest(BaseModel):
    participant_id: str
    scheduled_at: datetime
    layer: str = "L2"
    is_pilot: bool = False
