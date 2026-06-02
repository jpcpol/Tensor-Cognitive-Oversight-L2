# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-030 — H3 (scalability) was ABSORBED into H_OBS.

Under the causal-observability reframing (CAL_Benchmark_v1.md), the original
H3 "the TCO advantage grows with system complexity" is the special case of
H_OBS where complexity is operationalized as the Causal Complexity Index (CCI).
There is no separate H3 analysis: the moderation test (Group x CCI) and the
pre-registered high-CCI vs low-CCI contrast live in h_obs_causal.py.

Run instead:
    python analysis/h_obs_causal.py --dry-run
"""
from __future__ import annotations

import sys


def main() -> None:
    print("H3 is absorbed into H_OBS - run: python analysis/h_obs_causal.py")
    sys.exit(2)


if __name__ == "__main__":
    main()
