# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
Bootstrap / promote a CAL admin account.

Usage (from src/, with PYTHONPATH=.):
    python -m tco_engine.scripts.create_admin --email admin@x.com --password secret123 --name "Admin"

If the email already exists, the account is promoted to role=admin (password
left unchanged). Otherwise a new admin participant is created.
"""
from __future__ import annotations

import argparse
import sys

from tco_engine.core.auth import hash_password
from tco_engine.db.database import Base, SessionLocal, engine
from tco_engine.db.models import CalParticipant


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or promote a CAL admin")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", help="required when creating a new account")
    parser.add_argument("--name", default="Admin")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(CalParticipant).filter(
            CalParticipant.email == args.email
        ).first()
        if existing:
            existing.role = "admin"
            db.commit()
            print(f"Promoted existing account to admin: {args.email}")
            return 0

        if not args.password:
            print("ERROR: --password is required to create a new admin", file=sys.stderr)
            return 2

        admin = CalParticipant(
            email=args.email,
            hashed_password=hash_password(args.password),
            role="admin",
            name=args.name,
            years_experience=0,
        )
        db.add(admin)
        db.commit()
        print(f"Created admin account: {args.email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
