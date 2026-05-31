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
from tco_engine.core.ncf_compute import SCENARIO_CATEGORY, SEVERITY_SCALE, compute_ncf_for_session
from tco_engine.db.database import get_db
from tco_engine.db.models import (
    CalInteractionEvent, CalInvitation, CalNCFProxy, CalParticipant,
    CalPolicyIntent, CalSession, CalTaskResult, CalTLXMeasurement,
)
from tco_engine.schemas.cal import (
    AdminParticipant, ConsentRequest, GroupOverrideRequest, InviteRequest,
    LoginRequest, MeResponse, PolicyInjectRequest, RegisterRequest,
    ResultsResponse, ScenarioArtifact, SessionSummary, StartSessionRequest,
    TaskResultOut, TaskSubmitRequest, TLXRequest, TokenResponse,
)

router = APIRouter()


def _artifact_tab(artifact_type: str) -> str:
    t = (artifact_type or "").lower()
    if "yaml" in t:
        return "yaml"
    if "ci_cd" in t or "cicd" in t or "ci/cd" in t:
        return "ci_cd"
    if "arch" in t:
        return "architecture"
    return "code"


def _owned_session(db: Session, session_id: str, participant: CalParticipant) -> CalSession:
    session = db.query(CalSession).filter(CalSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.participant_id != participant.id and participant.role != "admin":
        raise HTTPException(status_code=403, detail="Not your session")
    return session


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


# ─── Session runner ───────────────────────────────────────────────────────────

@router.get("/scenario/{scenario_id}", response_model=list[ScenarioArtifact])
def get_scenario(
    scenario_id: str,
    cycle_k: int = 0,
    _participant: CalParticipant = Depends(get_current_participant),
):
    try:
        from pipeline.scenarios import get_scenario as load_scenario
        mod = load_scenario(scenario_id)
        raw = mod.get_artifacts(cycle_k)
    except (ImportError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=f"Scenario unavailable: {exc}")

    return [
        ScenarioArtifact(
            id=a["id"],
            type=_artifact_tab(a.get("artifact_type", "")),
            label=a["id"].replace("_", " "),
            content=a["content"],
            agent=a.get("agent_id", "unknown"),
            stage=a.get("stage", "unknown"),
        )
        for a in raw
    ]


@router.post("/session/start")
def start_session(
    req: StartSessionRequest,
    participant: CalParticipant = Depends(get_current_participant),
    db: Session = Depends(get_db),
):
    if req.session_id:
        session = _owned_session(db, req.session_id, participant)
    else:
        session = db.query(CalSession).filter(
            CalSession.participant_id == participant.id,
            CalSession.status == "invited",
        ).order_by(CalSession.created_at.desc()).first()
        if not session:
            raise HTTPException(status_code=404, detail="No invited session to start")

    if session.status == "completed":
        raise HTTPException(status_code=409, detail="Session already completed")
    session.status = "in_progress"
    session.started_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "session_id": session.id, "status": session.status}


@router.post("/session/{session_id}/task")
def submit_task(
    session_id: str,
    req: TaskSubmitRequest,
    participant: CalParticipant = Depends(get_current_participant),
    db: Session = Depends(get_db),
):
    session = _owned_session(db, session_id, participant)
    accuracy = (1.0 if req.detected else 0.0) if req.detected is not None else None

    db.add(CalTaskResult(
        session_id=session.id,
        task=req.task,
        scenario=req.scenario,
        accuracy=accuracy,
        detected=req.detected,
        time_to_first_correction_s=req.time_to_first_correction_s,
        raw_response={"response": req.response,
                      "corrections": [c.model_dump() for c in req.corrections]},
    ))

    category = SCENARIO_CATEGORY.get(req.scenario.upper(), "other")
    for c in req.corrections:
        db.add(CalInteractionEvent(
            session_id=session.id,
            event_type="correction",
            artifact_id=c.artifact_id,
            payload={
                "task": req.task,
                "scenario": req.scenario,
                "fault_category": category,
                "severity": SEVERITY_SCALE.get(c.severity, 3),
                "description": c.description,
                "location": c.location,
                "time_to_first_correction_s": c.time_to_first_correction_s,
            },
        ))
    db.commit()
    return {"ok": True, "task": req.task, "scenario": req.scenario, "accuracy": accuracy}


@router.post("/session/{session_id}/tlx")
def submit_tlx(
    session_id: str,
    req: TLXRequest,
    participant: CalParticipant = Depends(get_current_participant),
    db: Session = Depends(get_db),
):
    session = _owned_session(db, session_id, participant)
    db.add(CalTLXMeasurement(
        session_id=session.id,
        checkpoint=req.checkpoint,
        mental_demand=req.mental_demand,
        physical_demand=req.physical_demand,
        temporal_demand=req.temporal_demand,
        performance=req.performance,
        effort=req.effort,
        frustration=req.frustration,
    ))
    db.commit()
    return {"ok": True, "checkpoint": req.checkpoint}


@router.post("/session/{session_id}/policy")
def inject_policy(
    session_id: str,
    req: PolicyInjectRequest,
    participant: CalParticipant = Depends(get_current_participant),
    db: Session = Depends(get_db),
):
    session = _owned_session(db, session_id, participant)
    policy = CalPolicyIntent(
        session_id=session.id,
        scenario=req.scenario,
        raw_policy=req.raw_policy,
    )
    db.add(policy)
    db.add(CalInteractionEvent(
        session_id=session.id,
        event_type="policy_submit",
        payload={"scenario": req.scenario},
    ))
    db.commit()
    db.refresh(policy)
    # PIQ scoring is wired in a later step (LLM-Judge) — raw policy stored now.
    return {"ok": True, "policy_id": policy.id}


@router.post("/session/{session_id}/complete")
def complete_session(
    session_id: str,
    participant: CalParticipant = Depends(get_current_participant),
    db: Session = Depends(get_db),
):
    session = _owned_session(db, session_id, participant)
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)

    ncf = compute_ncf_for_session(session)
    if ncf:
        proxies = ncf["proxies"]
        db.add(CalNCFProxy(
            session_id=session.id,
            working_memory_saturation=proxies["working_memory_saturation"],
            mean_sigma_severity=proxies["mean_sigma_severity"],
            sigma_accuracy=proxies["sigma_accuracy"],
            iqr_attention_fragmentation_s=proxies["iqr_attention_fragmentation_s"],
            ncf_at_frontier=ncf["ncf_at_frontier"],
        ))
    db.commit()
    return {"ok": True, "status": "completed", "ncf_computed": ncf is not None}


@router.get("/session/{session_id}/results", response_model=ResultsResponse)
def session_results(
    session_id: str,
    participant: CalParticipant = Depends(get_current_participant),
    db: Session = Depends(get_db),
):
    session = _owned_session(db, session_id, participant)
    ncf_row = session.ncf
    ncf_dict = None
    if ncf_row:
        ncf_dict = {
            "working_memory_saturation": ncf_row.working_memory_saturation,
            "mean_sigma_severity": ncf_row.mean_sigma_severity,
            "sigma_accuracy": ncf_row.sigma_accuracy,
            "iqr_attention_fragmentation_s": ncf_row.iqr_attention_fragmentation_s,
            "ncf_at_frontier": ncf_row.ncf_at_frontier,
        }
    return ResultsResponse(
        session_id=session.id,
        group=session.participant.group,
        status=session.status,
        task_results=[
            TaskResultOut(task=r.task, scenario=r.scenario,
                          accuracy=r.accuracy, detected=r.detected)
            for r in session.task_results
        ],
        ncf=ncf_dict,
    )
