# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
S1 — Authentication SQL injection

Fault: string-concatenation SQL queries + MD5 for password hashing.
Structurally detectable with static analysis (bandit B608, B324).
Target: v4 (security_risk) drops from ~0.90 to ~0.20 when fault is present.

Ground truth for phi calibration:
  s1_auth_clean:  v4_approx=0.90  (no significant bandit findings)
  s1_auth_faulty: v4_approx=0.20  (B608 HIGH x2, B324 MEDIUM x1)
"""
from __future__ import annotations

SCENARIO_ID = "S1"
DESCRIPTION = "Authentication module — SQL injection vulnerability"
FAULT_TYPE = "sql_injection"
N_CYCLES = 1

GROUND_TRUTH: dict[str, dict] = {
    "s1_auth_clean": {
        "v4_security_risk_approx": 0.90,
        "fault_present": False,
        "expected_bandit_severity": "none",
    },
    "s1_auth_faulty": {
        "v4_security_risk_approx": 0.20,
        "fault_present": True,
        "expected_bandit_severity": "HIGH",
        "fault_description": "SQL injection via f-string in WHERE clause; MD5 for password hash",
    },
}

_CLEAN_AUTH = """\
import hashlib
import hmac
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, username: str, password: str) -> dict | None:
    logger.info("Auth attempt: %s", username)
    row = db.execute(
        text("SELECT id, password_hash FROM users WHERE username = :u"),
        {"u": username},
    ).fetchone()
    if not row:
        logger.warning("User not found: %s", username)
        return None
    candidate = hashlib.sha256(password.encode()).hexdigest()
    if not hmac.compare_digest(row.password_hash, candidate):
        logger.warning("Invalid credentials: %s", username)
        return None
    logger.info("Authenticated user id=%s", row.id)
    return {"id": row.id, "username": username}


def get_user_by_id(db: Session, user_id: int) -> dict | None:
    logger.info("Fetching user id=%s", user_id)
    row = db.execute(
        text("SELECT id, username, email FROM users WHERE id = :uid"),
        {"uid": user_id},
    ).fetchone()
    return {"id": row.id, "username": row.username} if row else None
"""

_FAULTY_AUTH = """\
import hashlib
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, username: str, password: str) -> dict | None:
    # B608: SQL injection — f-string in WHERE clause
    query = "SELECT id, password_hash FROM users WHERE username='" + username + "'"
    row = db.execute(text(query)).fetchone()
    if not row:
        return None
    # B324: use of MD5 for password hashing
    pw_hash = hashlib.md5(password.encode()).hexdigest()
    if row.password_hash != pw_hash:
        return None
    return {"id": row.id, "username": username}


def get_user_by_id(db: Session, user_id: int) -> dict | None:
    # B608: SQL injection — direct concatenation
    query = "SELECT id, username, email FROM users WHERE id=" + str(user_id)
    row = db.execute(text(query)).fetchone()
    return {"id": row.id, "username": row.username} if row else None
"""


def get_artifacts(cycle_k: int = 0) -> list[dict]:
    base_context = "User authentication module. Stage: build. Scenario: S1."
    return [
        {
            "id": "s1_auth_clean",
            "agent_id": "code_agent",
            "stage": "build",
            "content": _CLEAN_AUTH,
            "artifact_type": "python_code",
            "context": base_context + " No fault injected.",
        },
        {
            "id": "s1_auth_faulty",
            "agent_id": "code_agent",
            "stage": "build",
            "content": _FAULTY_AUTH,
            "artifact_type": "python_code",
            "context": base_context + " SQL injection fault injected.",
        },
    ]
