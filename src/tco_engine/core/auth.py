# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Authentication for the CAL experiment platform — JWT + bcrypt.

Two roles: `participant` and `admin`. Pattern mirrored from Research-Lab
(`app/auth.py`): python-jose for HS256 JWT, passlib for bcrypt hashing,
HTTPBearer dependency. Layer-agnostic — the same auth serves L2/L3/L4.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from tco_engine.db.database import get_db
from tco_engine.db.models import CalParticipant

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-min-32-chars!!")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "72"))

bearer = HTTPBearer(auto_error=False)


# ─── Password helpers ─────────────────────────────────────────────────────────
# bcrypt directly (not passlib) — passlib 1.7.x's backend detection is broken
# against bcrypt 4.x. bcrypt operates on the first 72 bytes; truncate explicitly.

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))


# ─── JWT helpers ──────────────────────────────────────────────────────────────

def create_token(participant_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": participant_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ─── FastAPI dependencies ─────────────────────────────────────────────────────

def get_current_participant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> CalParticipant:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated")
    participant_id = decode_token(credentials.credentials)
    if not participant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token")
    participant = db.query(CalParticipant).filter(
        CalParticipant.id == participant_id
    ).first()
    if not participant or not participant.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Participant not found or inactive")
    return participant


def get_current_admin(
    participant: CalParticipant = Depends(get_current_participant),
) -> CalParticipant:
    if participant.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Admin role required")
    return participant
