# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
S2 — Architecture circular dependency

Fault: service dependency graph with A→B→A cycle.
Structurally undetectable at artifact level — requires architectural overview.
Target: v2 (architectural_alignment) drops from ~0.85 to ~0.20.

LLM-scored dimension — static analysis cannot detect circular deps in YAML.
This scenario validates the LLM's ability to reason about architectural patterns.
"""
from __future__ import annotations

SCENARIO_ID = "S2"
DESCRIPTION = "Service architecture — circular dependency fault"
FAULT_TYPE = "circular_dependency"
N_CYCLES = 1

GROUND_TRUTH: dict[str, dict] = {
    "s2_arch_clean": {
        "v2_architectural_alignment_approx": 0.85,
        "fault_present": False,
        "expected_llm_detection": "No circular deps; proper DAG",
    },
    "s2_arch_faulty": {
        "v2_architectural_alignment_approx": 0.20,
        "fault_present": True,
        "fault_description": "user_service ↔ order_service mutual dependency (circular)",
        "expected_llm_detection": "Circular: user_service→order_service→user_service",
    },
}

_CLEAN_ARCH = """\
# service_architecture.yaml — clean version
# Dependency graph is a valid DAG (no cycles).

services:
  database_service:
    provides: [connect, query, pool]
    depends_on: []

  cache_service:
    provides: [get, set, invalidate]
    depends_on: [database_service]

  user_service:
    provides: [authenticate, get_profile, update_profile]
    depends_on: [database_service, cache_service]

  order_service:
    provides: [create_order, get_orders, cancel_order]
    depends_on: [user_service, database_service]

  notification_service:
    provides: [send_email, send_push]
    depends_on: [user_service]

  api_gateway:
    provides: [route, auth_middleware, rate_limit]
    depends_on: [user_service, order_service, notification_service]

dependency_checks:
  max_depth: 4
  cycles_allowed: false
  validation: strict
"""

_FAULTY_ARCH = """\
# service_architecture.yaml — CIRCULAR DEPENDENCY FAULT
# user_service and order_service mutually depend on each other.

services:
  database_service:
    provides: [connect, query, pool]
    depends_on: []

  cache_service:
    provides: [get, set, invalidate]
    depends_on: [database_service]

  user_service:
    provides: [authenticate, get_profile, update_profile]
    # FAULT: user_service depends on order_service
    depends_on: [database_service, cache_service, order_service]

  order_service:
    provides: [create_order, get_orders, cancel_order]
    # FAULT: order_service depends on user_service — creates cycle
    depends_on: [user_service, database_service]

  notification_service:
    provides: [send_email, send_push]
    depends_on: [user_service]

  api_gateway:
    provides: [route, auth_middleware, rate_limit]
    depends_on: [user_service, order_service, notification_service]

dependency_checks:
  max_depth: 4
  cycles_allowed: false
  validation: strict
"""


def get_artifacts(cycle_k: int = 0) -> list[dict]:
    base_context = "Microservice dependency architecture. Stage: design. Scenario: S2."
    return [
        {
            "id": "s2_arch_clean",
            "agent_id": "arch_agent",
            "stage": "design",
            "content": _CLEAN_ARCH,
            "artifact_type": "yaml_config",
            "context": base_context + " No circular dependencies present.",
        },
        {
            "id": "s2_arch_faulty",
            "agent_id": "arch_agent",
            "stage": "design",
            "content": _FAULTY_ARCH,
            "artifact_type": "yaml_config",
            "context": base_context + " Circular dependency fault injected.",
        },
    ]
