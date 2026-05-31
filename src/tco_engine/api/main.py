# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
TCO Engine API — FastAPI application.

Hosts the TCO core endpoints (φ / f / I / policy) and the CAL experiment
platform under `/cal/api`. Tables are created on startup; the platform
defaults to a local SQLite file so it runs without Docker/Postgres in dev.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tco_engine.api.routes import experiment, inference, policy, tensor, vector
from tco_engine.db.database import Base, engine
from tco_engine.db import models  # noqa: F401 — register models on Base before create_all

# Create all cal_* tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TCO Engine API",
    version="0.1.0",
    description="Tensor-Based Cognitive Oversight — REST API + CAL experiment platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# TCO core endpoints
app.include_router(vector.router,     prefix="/vector",     tags=["vector"])
app.include_router(tensor.router,     prefix="/tensor",     tags=["tensor"])
app.include_router(inference.router,  prefix="/inference",  tags=["inference"])
app.include_router(policy.router,     prefix="/policy",     tags=["policy"])

# CAL experiment platform
app.include_router(experiment.router, prefix="/cal/api",    tags=["cal"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
