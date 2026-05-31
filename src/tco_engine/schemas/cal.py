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


# ─── Session runner ───────────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    session_id: Optional[str] = None   # defaults to participant's invited session


class ScenarioArtifact(BaseModel):
    id: str
    type: Literal["code", "yaml", "architecture", "ci_cd"]
    label: str
    content: str
    agent: str
    stage: str


class CorrectionInput(BaseModel):
    artifact_id: str
    severity: Literal["Low", "Medium", "High"] = "Medium"
    description: str
    location: str = ""
    time_to_first_correction_s: Optional[float] = None


class TaskSubmitRequest(BaseModel):
    task: str                          # T1..T4
    scenario: str                      # S1..S5
    response: str = ""                 # free-text / selected answer
    detected: Optional[bool] = None    # did the participant flag the fault?
    time_to_first_correction_s: Optional[float] = None
    corrections: list[CorrectionInput] = Field(default_factory=list)


class TLXRequest(BaseModel):
    checkpoint: Literal["post_t2", "post_t4"]
    mental_demand: int = Field(ge=0, le=100)
    physical_demand: int = Field(ge=0, le=100)
    temporal_demand: int = Field(ge=0, le=100)
    performance: int = Field(ge=0, le=100)
    effort: int = Field(ge=0, le=100)
    frustration: int = Field(ge=0, le=100)


class PolicyInjectRequest(BaseModel):
    scenario: str
    raw_policy: str


class TaskResultOut(BaseModel):
    task: str
    scenario: str
    accuracy: Optional[float] = None
    detected: Optional[bool] = None


class ResultsResponse(BaseModel):
    session_id: str
    group: Optional[str] = None
    status: str
    task_results: list[TaskResultOut]
    ncf: Optional[dict] = None
