# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
CAL experiment platform router — `/cal/api`.

Phase 1 (backend foundation): self-service registration with stratified group
assignment, JWT login, informed consent, participant self-view, and the admin
participant listing / group override / invitation scheduling. Session-runner
endpoints (start / scenario / correction / tlx / policy / complete) land in
Phase 2.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tco_engine.core import randomization
from tco_engine.core.auth import (
    create_token, get_current_admin, get_current_participant,
    hash_password, verify_password,
)
from tco_engine.core.email_service import send_invitation_email, send_welcome_email
from tco_engine.db.database import get_db
from tco_engine.db.models import CalInvitation, CalParticipant, CalSession
from tco_engine.schemas.cal import (
    AdminParticipant, ConsentRequest, GroupOverrideRequest, InviteRequest,
    LoginRequest, MeResponse, RegisterRequest, SessionSummary, TokenResponse,
)

router = APIRouter()


# ─── Auth / registration ─────────────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(CalParticipant).filter(CalParticipant.email == req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    stratum = randomization.stratum_for_experience(req.years_experience)
    group = randomization.assign_group(db, stratum)

    participant = CalParticipant(
        email=req.email,
        hashed_password=hash_password(req.password),
        role="participant",
        name=req.name,
        country=req.country,
        years_experience=req.years_experience,
        education_level=req.education_level,
        institution=req.institution,
        languages=req.languages,
        ai_familiarity=req.ai_familiarity,
        prior_tco_exposure=req.prior_tco_exposure,
        experience_stratum=stratum,
        group=group,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)

    send_welcome_email(participant.email, participant.name)

    return TokenResponse(
        access_token=create_token(participant.id),
        role=participant.role,
        participant_id=participant.id,
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    participant = db.query(CalParticipant).filter(
        CalParticipant.email == req.email
    ).first()
    if not participant or not verify_password(req.password, participant.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not participant.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    return TokenResponse(
        access_token=create_token(participant.id),
        role=participant.role,
        participant_id=participant.id,
    )


@router.post("/auth/consent")
def consent(
    req: ConsentRequest,
    participant: CalParticipant = Depends(get_current_participant),
    db: Session = Depends(get_db),
):
    if not req.consent:
        raise HTTPException(status_code=400, detail="Consent is required to proceed")
    participant.consent_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "consent_at": participant.consent_at}


# ─── Participant self-view ────────────────────────────────────────────────────

def _current_session_summary(db: Session, participant_id: str) -> SessionSummary | None:
    session = db.query(CalSession).filter(
        CalSession.participant_id == participant_id,
        CalSession.status.in_(["invited", "in_progress"]),
    ).order_by(CalSession.created_at.desc()).first()
    if not session:
        return None
    invite = db.query(CalInvitation).filter(
        CalInvitation.participant_id == participant_id
    ).order_by(CalInvitation.scheduled_at.desc()).first()
    return SessionSummary(
        id=session.id,
        layer=session.layer,
        status=session.status,
        is_pilot=session.is_pilot,
        scheduled_at=invite.scheduled_at if invite else None,
    )


@router.get("/me", response_model=MeResponse)
def me(
    participant: CalParticipant = Depends(get_current_participant),
    db: Session = Depends(get_db),
):
    return MeResponse(
        participant_id=participant.id,
        email=participant.email,
        name=participant.name,
        role=participant.role,
        group=participant.group,
        experience_stratum=participant.experience_stratum,
        consent_given=participant.consent_at is not None,
        current_session=_current_session_summary(db, participant.id),
    )


# ─── Admin ───────────────────────────────────────────────────────────────────

@router.get("/admin/participants", response_model=list[AdminParticipant])
def admin_participants(
    _admin: CalParticipant = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(CalParticipant).filter(
        CalParticipant.role == "participant"
    ).order_by(CalParticipant.created_at.desc()).all()

    out: list[AdminParticipant] = []
    for p in rows:
        latest = db.query(CalSession).filter(
            CalSession.participant_id == p.id
        ).order_by(CalSession.created_at.desc()).first()
        out.append(AdminParticipant(
            participant_id=p.id,
            name=p.name,
            email=p.email,
            years_experience=p.years_experience,
            experience_stratum=p.experience_stratum,
            group=p.group,
            ai_familiarity=p.ai_familiarity,
            prior_tco_exposure=p.prior_tco_exposure,
            consent_given=p.consent_at is not None,
            session_status=latest.status if latest else None,
            created_at=p.created_at,
        ))
    return out


@router.post("/admin/participant/{participant_id}/group")
def admin_override_group(
    participant_id: str,
    req: GroupOverrideRequest,
    _admin: CalParticipant = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    participant = db.query(CalParticipant).filter(
        CalParticipant.id == participant_id
    ).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    participant.group = req.group
    db.commit()
    return {"ok": True, "participant_id": participant_id, "group": req.group}


@router.post("/admin/invite")
def admin_invite(
    req: InviteRequest,
    _admin: CalParticipant = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    participant = db.query(CalParticipant).filter(
        CalParticipant.id == req.participant_id
    ).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    invitation = CalInvitation(
        participant_id=participant.id,
        layer=req.layer,
        scheduled_at=req.scheduled_at,
    )
    session = CalSession(
        participant_id=participant.id,
        layer=req.layer,
        status="invited",
        is_pilot=req.is_pilot,
    )
    db.add(invitation)
    db.add(session)

    sent = send_invitation_email(
        participant.email, participant.name, req.scheduled_at.isoformat()
    )
    invitation.status = "sent" if sent else "scheduled"
    if sent:
        invitation.sent_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(session)
    return {
        "ok": True,
        "session_id": session.id,
        "invitation_status": invitation.status,
        "email_sent": sent,
    }
