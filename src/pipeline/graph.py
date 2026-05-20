# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
TCO Pipeline — LangGraph StateGraph

Nodes (in order per cycle):
  load_artifacts  — fetches scenario artifacts for the current cycle
  qa_evaluate     — runs QAAgent (LLM semantic evaluation)
  vectorize       — runs Vectorizer φ (static + LLM → V ∈ [0,1]¹¹)
  aggregate       — updates TensorAggregator with new VectorEntries
  infer           — runs InferenceEngine I: T → {Ω, Δ, Ρ, Ξ}
  next_cycle      — increments cycle_k; routes back to load_artifacts or END

Usage:
  from pipeline.graph import build_graph, run_scenario
  result = run_scenario("S3", session_id="exp_001", n_cycles=4)
"""
from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path
from typing import Any

# Ensure src/ is on the path when running as a script
_SRC = Path(__file__).parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import END, StateGraph
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    _LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph not available — graph.py running in stub mode")

from pipeline.scenarios import get_scenario
from pipeline.state import PipelineState

try:
    from tco_engine.core.aggregator import STAGE_INDEX, TensorAggregator, VectorEntry
    from tco_engine.core.inference_engine import InferenceEngine, InferenceResult
    from tco_engine.core.vectorizer import Artifact, Vectorizer
    from tco_engine.schemas.vector import EvaluationVector
    _TCO_ENGINE_AVAILABLE = True
except ImportError:
    _TCO_ENGINE_AVAILABLE = False
    logger.warning("tco_engine not available — pipeline will run in dry-run mode")


# ─── LangGraph node functions ────────────────────────────────────────────────

def _node_load_artifacts(state: PipelineState) -> PipelineState:
    scenario_mod = get_scenario(state["scenario_id"])
    cycle_k = state["cycle_k"]
    artifacts = scenario_mod.get_artifacts(cycle_k)
    logger.info(
        "Loaded %d artifacts for %s cycle_k=%d",
        len(artifacts), state["scenario_id"], cycle_k,
    )
    return {**state, "artifacts": artifacts, "qa_evaluations": {}}


def _node_qa_evaluate(state: PipelineState) -> PipelineState:
    artifacts = state["artifacts"]
    policy_context = state.get("policy_context", "")

    if not _TCO_ENGINE_AVAILABLE:
        logger.info("dry-run: skipping QA evaluation")
        evaluations = {a["id"]: {"dry_run": True} for a in artifacts}
        return {**state, "qa_evaluations": evaluations}

    from pipeline.agents.qa_agent import QAAgent
    agent = QAAgent()
    updated = agent.run({**state, "artifacts": artifacts, "policy_context": policy_context})
    return {**state, "qa_evaluations": updated.get("qa_evaluations", {})}


def _node_vectorize(state: PipelineState) -> PipelineState:
    artifacts = state["artifacts"]
    cycle_k = state["cycle_k"]

    if not _TCO_ENGINE_AVAILABLE:
        logger.info("dry-run: skipping vectorization")
        return {**state, "vectors": state.get("vectors", []), "tensor_entries": state.get("tensor_entries", [])}

    vectorizer = Vectorizer()
    vectors: list[dict[str, Any]] = list(state.get("vectors", []))
    tensor_entries: list[Any] = list(state.get("tensor_entries", []))

    for art_dict in artifacts:
        artifact = Artifact(
            artifact_id=art_dict["id"],
            agent_id=art_dict["agent_id"],
            stage=art_dict["stage"],
            cycle_k=cycle_k,
            code=art_dict["content"],
            artifact_type=art_dict["artifact_type"],
            context=art_dict.get("context", ""),
        )
        try:
            vector = vectorizer.vectorize(artifact)
        except Exception as exc:
            logger.error("Vectorization failed for %s: %s", art_dict["id"], exc)
            continue

        stage_idx = STAGE_INDEX.get(art_dict["stage"], 0)
        # Assign a stable agent index from the agent_id string
        agent_ids: list[str] = [
            a["agent_id"] for a in artifacts
        ]
        unique_agents = list(dict.fromkeys(agent_ids))
        agent_idx = unique_agents.index(art_dict["agent_id"])

        entry = VectorEntry(
            vector=vector,
            stage_idx=stage_idx,
            agent_idx=agent_idx,
            time_idx=cycle_k,
        )
        tensor_entries.append(entry)

        vectors.append({
            "artifact_id": art_dict["id"],
            "agent_id": art_dict["agent_id"],
            "stage": art_dict["stage"],
            "cycle_k": cycle_k,
            "vector": vector.model_dump(),
        })
        logger.info(
            "Vectorized %s: v4=%.2f v6=%.2f v7=%.2f v8=%.2f conf=%.2f",
            art_dict["id"],
            vector.security_risk,
            vector.testability,
            vector.maintainability,
            vector.technical_debt,
            vector.confidence,
        )

    return {**state, "vectors": vectors, "tensor_entries": tensor_entries}


def _node_aggregate(state: PipelineState) -> PipelineState:
    if not _TCO_ENGINE_AVAILABLE:
        return state
    tensor_entries = state.get("tensor_entries", [])
    if not tensor_entries:
        return state
    aggregator = TensorAggregator()
    T = aggregator.aggregate(tensor_entries)
    return {**state, "_tensor": T}


def _node_infer(state: PipelineState) -> PipelineState:
    if not _TCO_ENGINE_AVAILABLE:
        return state
    T = state.get("_tensor")
    if T is None:
        return state
    cycle_k = state["cycle_k"]
    engine = InferenceEngine()
    result = engine.infer(T, cycle_k)
    logger.info(
        "Inference cycle_k=%d: Ω=%s (%.2f) Δ=%d trends Ρ=%d conflicts Ξ=%d recs",
        cycle_k, result.omega, result.omega_score,
        len(result.delta), len(result.rho), len(result.xi),
    )
    return {**state, "_inference": result}


def _node_next_cycle(state: PipelineState) -> PipelineState:
    new_k = state["cycle_k"] + 1
    logger.info("Advancing to cycle_k=%d", new_k)
    return {**state, "cycle_k": new_k}


def _should_continue(state: PipelineState) -> str:
    if state["cycle_k"] < state["n_cycles"] - 1:
        return "continue"
    return "done"


# ─── Graph builder ────────────────────────────────────────────────────────────

def build_graph():
    if not _LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph unavailable — returning None")
        return None

    graph: StateGraph = StateGraph(dict)  # type: ignore[type-var]

    graph.add_node("load_artifacts", _node_load_artifacts)
    graph.add_node("qa_evaluate", _node_qa_evaluate)
    graph.add_node("vectorize", _node_vectorize)
    graph.add_node("aggregate", _node_aggregate)
    graph.add_node("infer", _node_infer)
    graph.add_node("next_cycle", _node_next_cycle)

    graph.set_entry_point("load_artifacts")
    graph.add_edge("load_artifacts", "qa_evaluate")
    graph.add_edge("qa_evaluate", "vectorize")
    graph.add_edge("vectorize", "aggregate")
    graph.add_edge("aggregate", "infer")
    graph.add_conditional_edges(
        "infer",
        _should_continue,
        {"continue": "next_cycle", "done": END},
    )
    graph.add_edge("next_cycle", "load_artifacts")

    return graph.compile()


# ─── High-level runner ────────────────────────────────────────────────────────

def run_scenario(
    scenario_id: str,
    session_id: str | None = None,
    policy_context: str = "",
) -> dict[str, Any]:
    """
    Run a full scenario through the pipeline.

    Returns the final PipelineState with vectors, tensor, and inference results.
    """
    scenario_mod = get_scenario(scenario_id)
    n_cycles: int = getattr(scenario_mod, "N_CYCLES", 1)
    sid = session_id or str(uuid.uuid4())

    initial_state: PipelineState = {
        "session_id": sid,
        "scenario_id": scenario_id,
        "cycle_k": 0,
        "n_cycles": n_cycles,
        "artifacts": [],
        "qa_evaluations": {},
        "vectors": [],
        "tensor_entries": [],
        "policy_context": policy_context,
        "fault_injected": False,
        "completed": False,
    }

    compiled = build_graph()
    if compiled is None:
        logger.error("Graph not available — cannot run scenario")
        return initial_state

    logger.info("Running scenario %s (%d cycles) session=%s", scenario_id, n_cycles, sid)
    final_state = compiled.invoke(initial_state)
    final_state["completed"] = True
    return final_state
