# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
DT-032 — SID Study: Semantic Information Decomposition over S1–S5.

Computes SID_C*(R) for three representations:
  R_raw : raw artifact text (bag-of-chars TF-IDF)
  R_V   : 11-dimensional evaluation vector φ(artifact)
  R_T   : tensor slice T[d,i,j,k] (multi-cycle joint representation)

The output — SID_C*(s) per scenario — is the pre-registration artifact
for H_cross before the RCT n=40 data collection begins.

Usage (full pipeline):
  python analysis/sid_study/benchmark_s1s5.py --corpus src/experiment/phi_calibration/corpus/corpus.json
"""
