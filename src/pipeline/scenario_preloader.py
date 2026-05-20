# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
scenario_preloader — generates the phi calibration corpus from all 5 scenarios.

The corpus is a JSON file consumed by phi_calibration.py. It contains raw
artifact code strings (not scores). phi_calibration.py runs radon/bandit and
the QAEvaluator on each artifact to compute Spearman ρ between static and LLM scores.

Output: src/experiment/phi_calibration/corpus/corpus.json
         ~20-25 entries covering all fault types across S1-S5

Usage:
  python scenario_preloader.py
  python scenario_preloader.py --output path/to/corpus.json
  python scenario_preloader.py --dry-run   (print summary, no file write)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure src/ is importable
_SRC = Path(__file__).parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pipeline.scenarios import ALL_SCENARIOS

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT = (
    Path(__file__).parent.parent
    / "experiment"
    / "phi_calibration"
    / "corpus"
    / "corpus.json"
)


def collect_corpus() -> list[dict]:
    """
    Iterate all scenarios and all cycles. Return one corpus entry per artifact.

    Each entry contains:
      artifact_id, scenario, cycle, artifact_type, code, context,
      fault_present (from ground_truth), ground_truth metadata
    """
    corpus: list[dict] = []

    for scenario_mod in ALL_SCENARIOS:
        scenario_id = scenario_mod.SCENARIO_ID
        n_cycles: int = getattr(scenario_mod, "N_CYCLES", 1)
        ground_truth: dict = getattr(scenario_mod, "GROUND_TRUTH", {})

        for k in range(n_cycles):
            artifacts = scenario_mod.get_artifacts(cycle_k=k)
            for art in artifacts:
                artifact_id = art["id"]
                gt = ground_truth.get(artifact_id, {})
                corpus.append({
                    "artifact_id":   artifact_id,
                    "scenario":      scenario_id,
                    "cycle":         k,
                    "artifact_type": art["artifact_type"],
                    "code":          art["content"],
                    "context":       art.get("context", ""),
                    "fault_present": gt.get("fault_present", None),
                    "ground_truth":  gt,
                })

        logger.debug(
            "Scenario %s: %d cycles × artifacts = %d entries added",
            scenario_id,
            n_cycles,
            sum(1 for e in corpus if e["scenario"] == scenario_id),
        )

    return corpus


def write_corpus(corpus: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version":      "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_artifacts":  len(corpus),
        "scenarios":    sorted({e["scenario"] for e in corpus}),
        "corpus":       corpus,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    logger.info("Corpus written to %s (%d entries)", output_path, len(corpus))


def print_summary(corpus: list[dict]) -> None:
    from collections import Counter
    by_scenario = Counter(e["scenario"] for e in corpus)
    by_type     = Counter(e["artifact_type"] for e in corpus)
    faulty      = sum(1 for e in corpus if e.get("fault_present") is True)
    clean       = sum(1 for e in corpus if e.get("fault_present") is False)

    print(f"\nCorpus summary — {len(corpus)} artifacts total")
    print(f"  By scenario:      {dict(sorted(by_scenario.items()))}")
    print(f"  By type:          {dict(sorted(by_type.items()))}")
    print(f"  Fault present:    {faulty}")
    print(f"  Clean baseline:   {clean}")
    print(f"  Unknown/n-a:      {len(corpus) - faulty - clean}")

    python_count = by_type.get("python_code", 0)
    print(f"\n  phi_calibration eligible (python_code): {python_count}")
    print(
        "  -> These will be scored by radon/bandit + QAEvaluator for Spearman rho.\n"
        "     YAML artifacts contribute to LLM calibration on v2/v5 only."
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s  %(name)s  %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Generate phi calibration corpus from TCO experimental scenarios"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help=f"Output path for corpus.json (default: {_DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without writing corpus.json",
    )
    args = parser.parse_args()

    corpus = collect_corpus()
    print_summary(corpus)

    if args.dry_run:
        print("\n[dry-run] No file written.")
        return

    write_corpus(corpus, args.output)
    print(f"\nCorpus written -> {args.output}")
    print("Next step: run phi_calibration.py --corpus <path> to compute Spearman ρ")


if __name__ == "__main__":
    main()
