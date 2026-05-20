# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""Pipeline state shared across all LangGraph nodes."""
from __future__ import annotations

from typing import Any, TypedDict


class ArtifactDict(TypedDict):
    id: str
    agent_id: str
    stage: str          # design | build | test | deploy
    content: str
    artifact_type: str  # python_code | yaml_config | architecture_doc | ci_cd_config
    context: str


class PipelineState(TypedDict):
    session_id: str
    scenario_id: str
    cycle_k: int
    n_cycles: int
    artifacts: list[ArtifactDict]
    qa_evaluations: dict[str, Any]   # artifact_id → EvaluationMetrics
    vectors: list[dict[str, Any]]    # accumulated vector entries
    tensor_entries: list[Any]        # VectorEntry instances for TensorAggregator
    policy_context: str
    fault_injected: bool
    completed: bool
