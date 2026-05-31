# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
SQLAlchemy models for the CAL experiment platform — tables `cal_*`.

**Layer-aware by design.** Participants are layer-agnostic (a person registers
once). Sessions carry a `layer` field (L2 / L3 / L4) so the same platform,
auth, randomization and admin dashboard serve every future CAL layer without
schema migration. `task` and `scenario` are free-form strings rather than
enums so L3/L4 can define their own task/scenario vocabularies.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SAEnum, Float, ForeignKey, Integer,
    JSON, String, Text,
)
from sqlalchemy.orm import relationship

from tco_engine.db.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


# ─── Participants (layer-agnostic identity) ──────────────────────────────────

class CalParticipant(Base):
    __tablename__ = "cal_participants"

    id              = Column(String, primary_key=True, default=new_uuid)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role            = Column(SAEnum("participant", "admin", name="cal_role"),
                             default="participant", nullable=False)

    # Professional profile (registration form)
    name             = Column(String, nullable=False)
    country          = Column(String, nullable=True)
    years_experience = Column(Integer, nullable=False)          # code review, ≥ 2
    education_level  = Column(SAEnum("undergraduate", "graduate", "other",
                                     name="cal_education"), nullable=True)
    institution      = Column(String, nullable=True)
    languages        = Column(String, nullable=True)            # primary ecosystems
    ai_familiarity   = Column(Integer, nullable=True)           # 0–4 — ANCOVA covariate
    prior_tco_exposure = Column(Boolean, default=False)         # disqualifier if true

    # Derived / assigned
    experience_stratum = Column(SAEnum("junior", "mid", "senior",
                                       name="cal_stratum"), nullable=True)
    group              = Column(SAEnum("control", "experimental",
                                       name="cal_group"), nullable=True)

    consent_at = Column(DateTime(timezone=True), nullable=True)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    sessions    = relationship("CalSession", back_populates="participant",
                               cascade="all, delete-orphan")
    invitations = relationship("CalInvitation", back_populates="participant",
                               cascade="all, delete-orphan")


# ─── Invitations (admin schedules a test date) ───────────────────────────────

class CalInvitation(Base):
    __tablename__ = "cal_invitations"

    id             = Column(String, primary_key=True, default=new_uuid)
    participant_id = Column(String, ForeignKey("cal_participants.id", ondelete="CASCADE"))
    layer          = Column(String, default="L2", nullable=False)
    scheduled_at   = Column(DateTime(timezone=True), nullable=False)
    token          = Column(String, unique=True, default=new_uuid)
    sent_at        = Column(DateTime(timezone=True), nullable=True)
    status         = Column(SAEnum("scheduled", "sent", "expired",
                                   name="cal_invite_status"), default="scheduled")
    created_at     = Column(DateTime(timezone=True), default=now_utc)

    participant = relationship("CalParticipant", back_populates="invitations")


# ─── Sessions (layer-aware experiment run) ───────────────────────────────────

class CalSession(Base):
    __tablename__ = "cal_sessions"

    id             = Column(String, primary_key=True, default=new_uuid)
    participant_id = Column(String, ForeignKey("cal_participants.id", ondelete="CASCADE"))
    layer          = Column(String, default="L2", nullable=False)   # L2 / L3 / L4
    status         = Column(SAEnum("invited", "in_progress", "completed", "aborted",
                                   name="cal_session_status"), default="invited")
    current_phase  = Column(String, nullable=True)   # registro/desacople/.../debriefing
    is_pilot       = Column(Boolean, default=False)  # excluded from final analysis
    started_at     = Column(DateTime(timezone=True), nullable=True)
    completed_at   = Column(DateTime(timezone=True), nullable=True)
    created_at     = Column(DateTime(timezone=True), default=now_utc)

    participant   = relationship("CalParticipant", back_populates="sessions")
    task_results  = relationship("CalTaskResult", back_populates="session",
                                 cascade="all, delete-orphan")
    tlx           = relationship("CalTLXMeasurement", back_populates="session",
                                 cascade="all, delete-orphan")
    ncf           = relationship("CalNCFProxy", back_populates="session",
                                 uselist=False, cascade="all, delete-orphan")
    policies      = relationship("CalPolicyIntent", back_populates="session",
                                 cascade="all, delete-orphan")
    events        = relationship("CalInteractionEvent", back_populates="session",
                                 cascade="all, delete-orphan")


# ─── Task results ────────────────────────────────────────────────────────────

class CalTaskResult(Base):
    __tablename__ = "cal_task_results"

    id          = Column(String, primary_key=True, default=new_uuid)
    session_id  = Column(String, ForeignKey("cal_sessions.id", ondelete="CASCADE"))
    task        = Column(String, nullable=False)   # T1..T4 (layer-specific)
    scenario    = Column(String, nullable=False)   # S1..S5 (layer-specific)
    accuracy    = Column(Float, nullable=True)
    detected    = Column(Boolean, nullable=True)
    time_to_first_correction_s = Column(Float, nullable=True)
    raw_response = Column(JSON, nullable=True)
    created_at  = Column(DateTime(timezone=True), default=now_utc)

    session = relationship("CalSession", back_populates="task_results")


# ─── NASA Raw-TLX measurements ───────────────────────────────────────────────

class CalTLXMeasurement(Base):
    __tablename__ = "cal_tlx_measurements"

    id              = Column(String, primary_key=True, default=new_uuid)
    session_id      = Column(String, ForeignKey("cal_sessions.id", ondelete="CASCADE"))
    checkpoint      = Column(SAEnum("post_t2", "post_t4", name="cal_tlx_checkpoint"),
                             nullable=False)
    mental_demand   = Column(Integer, nullable=True)   # 0–100
    physical_demand = Column(Integer, nullable=True)
    temporal_demand = Column(Integer, nullable=True)
    performance     = Column(Integer, nullable=True)
    effort          = Column(Integer, nullable=True)
    frustration     = Column(Integer, nullable=True)
    created_at      = Column(DateTime(timezone=True), default=now_utc)

    session = relationship("CalSession", back_populates="tlx")


# ─── NCF proxies (one row per session) ───────────────────────────────────────

class CalNCFProxy(Base):
    __tablename__ = "cal_ncf_proxies"

    id          = Column(String, primary_key=True, default=new_uuid)
    session_id  = Column(String, ForeignKey("cal_sessions.id", ondelete="CASCADE"))
    working_memory_saturation     = Column(Float, nullable=True)
    mean_sigma_severity           = Column(Float, nullable=True)
    sigma_accuracy                = Column(Float, nullable=True)
    iqr_attention_fragmentation_s = Column(Float, nullable=True)
    ncf_at_frontier               = Column(Boolean, nullable=True)
    created_at  = Column(DateTime(timezone=True), default=now_utc)

    session = relationship("CalSession", back_populates="ncf")


# ─── Policy intents (experimental group) ─────────────────────────────────────

class CalPolicyIntent(Base):
    __tablename__ = "cal_policy_intents"

    id         = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("cal_sessions.id", ondelete="CASCADE"))
    scenario   = Column(String, nullable=False)
    raw_policy = Column(Text, nullable=False)
    piq_d1     = Column(Integer, nullable=True)
    piq_d2     = Column(Integer, nullable=True)
    piq_d3     = Column(Integer, nullable=True)
    piq_d4     = Column(Integer, nullable=True)
    piq_d5     = Column(Integer, nullable=True)
    piq_score  = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    session = relationship("CalSession", back_populates="policies")


# ─── Interaction events (feeds interaction_timer.py) ─────────────────────────

class CalInteractionEvent(Base):
    __tablename__ = "cal_interaction_events"

    id          = Column(String, primary_key=True, default=new_uuid)
    session_id  = Column(String, ForeignKey("cal_sessions.id", ondelete="CASCADE"))
    ts          = Column(DateTime(timezone=True), default=now_utc)
    event_type  = Column(String, nullable=False)   # view/click/correction/policy_submit
    artifact_id = Column(String, nullable=True)
    payload     = Column(JSON, nullable=True)

    session = relationship("CalSession", back_populates="events")
