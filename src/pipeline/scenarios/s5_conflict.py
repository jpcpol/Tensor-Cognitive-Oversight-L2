# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
S5 — Inter-agent conflict (indetectable with raw artifact review)

Two agents produce competing implementations of the same authentication module
with opposing quality tradeoffs:

  security_agent (agent_0): hardened JWT auth — high v4, low v6/v7
  code_agent     (agent_1): clean simple auth — low v4, high v6/v7

The conflict is INDETECTABLE by reviewing either artifact in isolation.
Only T[:, build_stage, j0, k] vs T[:, build_stage, j1, k] tensor comparison
reveals: |T[v4, :, j0, k] - T[v4, :, j1, k]| > 0.50 (high conflict on security)
         |T[v6, :, j0, k] - T[v6, :, j1, k]| > 0.45 (conflict on testability)

Ground truth for Ρ (inter-agent conflict) computation:
  v4 delta ≈ 0.65  (security_agent: 0.85 vs code_agent: 0.20)
  v6 delta ≈ 0.50  (security_agent: 0.25 vs code_agent: 0.75)
"""
from __future__ import annotations

SCENARIO_ID = "S5"
DESCRIPTION = "Auth module — inter-agent conflict (security vs. testability)"
FAULT_TYPE = "inter_agent_conflict"
N_CYCLES = 1

GROUND_TRUTH: dict[str, dict] = {
    "s5_auth_security_agent": {
        "v4_security_approx": 0.85,
        "v6_testability_approx": 0.25,
        "agent": "security_agent",
        "profile": "hardened: JWT validation, rate limiting, bcrypt — complex, hard to test",
    },
    "s5_auth_code_agent": {
        "v4_security_approx": 0.20,
        "v6_testability_approx": 0.75,
        "agent": "code_agent",
        "profile": "clean: simple token lookup — highly testable but SQL injection present",
    },
    "conflict": {
        "v4_delta_approx": 0.65,
        "v6_delta_approx": 0.50,
        "exceeds_rho_threshold": True,
        "rho_threshold": 0.30,
    },
}

# Agent 0 (security_agent): hardened but complex JWT auth — high v4, low v6
_SECURITY_AGENT_AUTH = """\
import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

_RATE_LIMIT_STORE: dict[str, list[float]] = {}
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300
_TOKEN_TTL = 3600
_ISSUED_TOKENS: dict[str, dict] = {}


@dataclass
class AuthResult:
    success: bool
    user_id: Optional[int]
    token: Optional[str]
    reason: Optional[str]


def _check_rate_limit(identifier: str) -> bool:
    now = time.time()
    attempts = _RATE_LIMIT_STORE.get(identifier, [])
    attempts = [t for t in attempts if now - t < _WINDOW_SECONDS]
    if len(attempts) >= _MAX_ATTEMPTS:
        logger.warning("Rate limit exceeded for %s", identifier)
        return False
    attempts.append(now)
    _RATE_LIMIT_STORE[identifier] = attempts
    return True


def _generate_token(user_id: int) -> str:
    raw = f"{user_id}:{time.time()}:{os.urandom(16).hex()}"
    return hmac.new(
        os.environ.get("SECRET_KEY", "default").encode(),
        raw.encode(),
        hashlib.sha256,
    ).hexdigest()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()


def _validate_token(token: str) -> Optional[dict]:
    entry = _ISSUED_TOKENS.get(token)
    if not entry:
        return None
    if time.time() - entry["issued_at"] > _TOKEN_TTL:
        del _ISSUED_TOKENS[token]
        logger.info("Token expired for user %s", entry["user_id"])
        return None
    return entry


def authenticate_user(db, username: str, password: str, client_ip: str) -> AuthResult:
    logger.info("Auth attempt: user=%s ip=%s", username, client_ip)
    if not _check_rate_limit(client_ip):
        return AuthResult(False, None, None, "rate_limited")
    if not _check_rate_limit(username):
        return AuthResult(False, None, None, "rate_limited_user")
    if len(username) > 64 or not username.replace("_", "").replace("-", "").isalnum():
        logger.warning("Invalid username format: %s", username)
        return AuthResult(False, None, None, "invalid_username")
    from sqlalchemy import text
    row = db.execute(
        text("SELECT id, password_hash, salt, locked FROM users WHERE username = :u"),
        {"u": username},
    ).fetchone()
    if not row:
        time.sleep(0.1)
        logger.warning("User not found: %s", username)
        return AuthResult(False, None, None, "invalid_credentials")
    if row.locked:
        return AuthResult(False, None, None, "account_locked")
    expected = _hash_password(password, row.salt)
    if not hmac.compare_digest(row.password_hash, expected):
        logger.warning("Bad password for user: %s", username)
        return AuthResult(False, None, None, "invalid_credentials")
    token = _generate_token(row.id)
    _ISSUED_TOKENS[token] = {"user_id": row.id, "issued_at": time.time()}
    logger.info("Auth success: user_id=%s", row.id)
    return AuthResult(True, row.id, token, None)
"""

# Agent 1 (code_agent): simple, testable but SQL injection — low v4, high v6
_CODE_AGENT_AUTH = """\
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
    # B324: MD5 — weak hash
    pw_hash = hashlib.md5(password.encode()).hexdigest()
    if row.password_hash != pw_hash:
        return None
    return {"id": row.id}


def get_user_by_id(db: Session, user_id: int) -> dict | None:
    query = "SELECT id, username FROM users WHERE id=" + str(user_id)
    row = db.execute(text(query)).fetchone()
    return {"id": row.id, "username": row.username} if row else None


def logout(db: Session, user_id: int) -> bool:
    db.execute(
        text("UPDATE sessions SET active=0 WHERE user_id = :uid"),
        {"uid": user_id},
    )
    return True
"""


def get_artifacts(cycle_k: int = 0) -> list[dict]:
    base_context = "User authentication module. Stage: build. Scenario: S5."
    return [
        {
            "id": "s5_auth_security_agent",
            "agent_id": "security_agent",
            "stage": "build",
            "content": _SECURITY_AGENT_AUTH,
            "artifact_type": "python_code",
            "context": (
                base_context + " Security-first implementation: JWT, rate limiting, "
                "pbkdf2 hashing. Expected: high security, low testability."
            ),
        },
        {
            "id": "s5_auth_code_agent",
            "agent_id": "code_agent",
            "stage": "build",
            "content": _CODE_AGENT_AUTH,
            "artifact_type": "python_code",
            "context": (
                base_context + " Clean-code implementation: minimal, testable. "
                "Expected: high testability, low security (SQL injection present)."
            ),
        },
    ]
