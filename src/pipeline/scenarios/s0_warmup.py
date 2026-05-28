# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
S0 — Warm-up Pipeline (no fault injection).

A healthy notification microservice used exclusively for participant
onboarding. Designed to:
  1. Familiarize both groups with the interface (TCO Dashboard or ControlGroupViewer)
  2. Demonstrate a normal, non-degraded pipeline state
  3. NOT be learnable as a hint for S1–S5 (different domain, different patterns)

Domain: async notification service (email/webhook delivery).
No injected faults. All quality dimensions in [0.70, 0.92].

Used in: Warm-up phase (15 min) before the experimental block.
Not included in corpus.json calibration (no ground truth fault).
"""
from __future__ import annotations

SCENARIO_ID = "S0"
N_CYCLES = 1
DOMAIN = "notification_service"

# ── Artifacts ─────────────────────────────────────────────────────────────────

_PYTHON_ARTIFACT = '''\
"""Async notification dispatcher — email and webhook delivery."""
import asyncio
import hashlib
import hmac
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Channel(Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class Notification:
    recipient: str
    channel: Channel
    subject: str
    body: str
    correlation_id: Optional[str] = None


class NotificationDispatcher:
    """Dispatches notifications across email and webhook channels."""

    def __init__(self, smtp_host: str, webhook_secret: str) -> None:
        self._smtp_host = smtp_host
        self._secret = webhook_secret.encode()

    async def dispatch(self, notification: Notification) -> bool:
        logger.info(
            "dispatching notification",
            extra={
                "channel": notification.channel.value,
                "recipient": notification.recipient,
                "correlation_id": notification.correlation_id,
            },
        )
        try:
            if notification.channel == Channel.EMAIL:
                return await self._send_email(notification)
            return await self._send_webhook(notification)
        except Exception as exc:
            logger.error("dispatch_failed", extra={"error": str(exc)})
            return False

    async def _send_email(self, n: Notification) -> bool:
        # Placeholder: integrate with smtp_host in production
        await asyncio.sleep(0)
        return True

    async def _send_webhook(self, n: Notification) -> bool:
        payload = f"{n.recipient}:{n.body}".encode()
        signature = hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
        logger.debug("webhook_signature_computed", extra={"sig_prefix": signature[:8]})
        await asyncio.sleep(0)
        return True


async def batch_dispatch(
    dispatcher: NotificationDispatcher,
    notifications: list[Notification],
) -> dict[str, int]:
    """Dispatch a batch; returns {sent: n, failed: n}."""
    results = await asyncio.gather(
        *[dispatcher.dispatch(n) for n in notifications],
        return_exceptions=False,
    )
    sent = sum(1 for r in results if r)
    return {"sent": sent, "failed": len(results) - sent}
'''

_YAML_ARTIFACT = '''\
# notification-service — Docker Compose configuration
version: "3.9"

services:
  notification-api:
    image: notification-service:latest
    environment:
      - SMTP_HOST=${SMTP_HOST}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080"
    resources:
      limits:
        cpu: "0.5"
        memory: 256M
      requests:
        cpu: "0.1"
        memory: 128M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      prometheus.io/scrape: "true"
      prometheus.io/port: "8080"
      prometheus.io/path: "/metrics"

  redis:
    image: redis:7-alpine
    resources:
      limits:
        memory: 64M
'''

# ── Warm-up artifacts ─────────────────────────────────────────────────────────

_ARTIFACTS = [
    {
        "id": "s0_notification_service",
        "agent_id": "code_agent",
        "stage": "generation",
        "content": _PYTHON_ARTIFACT,
        "artifact_type": "python_code",
        "context": (
            "Notification dispatcher for async email and webhook delivery. "
            "Uses hmac-sha256 for webhook signatures. Async batch dispatch. "
            "Expected quality: all dimensions healthy (no faults injected). "
            "Purpose: warm-up practice — familiarize with interface."
        ),
    },
    {
        "id": "s0_docker_compose",
        "agent_id": "deploy_agent",
        "stage": "deployment",
        "content": _YAML_ARTIFACT,
        "artifact_type": "ci_cd",
        "context": (
            "Docker Compose config for notification service. "
            "Resource limits, health checks, and Prometheus annotations present. "
            "Expected quality: observability and deployment dims healthy. "
            "Purpose: warm-up practice — familiarize with interface."
        ),
    },
]

# Expected quality profile — healthy, no faults.
# Used only for facilitator reference, NOT for scoring or corpus.json.
EXPECTED_QUALITY_PROFILE = {
    "v1_functional_correctness": 0.85,
    "v2_architectural_alignment": 0.82,
    "v3_scalability_projection": 0.78,
    "v4_security_risk": 0.88,       # hmac-sha256, no SQL, env vars for secrets
    "v5_observability_coverage": 0.87,  # Prometheus annotations, health checks
    "v6_testability": 0.75,
    "v7_maintainability": 0.80,
    "v8_technical_debt": 0.82,
    "v9_performance": 0.76,
    "v10_confidence": 0.84,
    "v11_anomaly_score": 0.90,      # no anomalies expected
}

WARM_UP_FACILITATOR_NOTES = """
WARM-UP FACILITATOR SCRIPT (15 min)

Goal: participant understands the interface, makes at least one assessment,
      asks questions. No performance pressure. No scoring of warm-up results.

[Experimental group — TCO Dashboard]
  "You'll see a radar chart showing 11 quality dimensions, a system state
   indicator (Omega), and a trend panel (Delta). The pipeline has no faults —
   everything should look healthy. Your job is to read the state and, if you
   wish, write a policy injection in the text box. There are no wrong answers
   in this warm-up. Take your time to explore."

[Control group — ControlGroupViewer]
  "You'll see the raw source code and configuration for a notification service.
   Your job is to review it and note any observations in the correction form.
   The pipeline has no injected faults — it's a clean baseline. Take your time
   to explore the interface."

After 10 min: "Do you have any questions about the interface?
Any part that was unclear or unexpected?"

Transition: "Great. The next 5 scenarios will follow the same structure but
with actual quality issues injected. You'll have a timer for each task."
"""


# ── Public interface (same as S1–S5) ──────────────────────────────────────────

def get_artifacts(cycle_k: int = 0) -> list[dict]:
    """Return warm-up artifacts. Single cycle, no fault injection."""
    return list(_ARTIFACTS)
