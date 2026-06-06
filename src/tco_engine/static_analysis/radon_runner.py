# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
import re
from dataclasses import dataclass

try:
    import radon.complexity as rc
    import radon.metrics as rm
    _RADON_AVAILABLE = True
except ImportError:
    _RADON_AVAILABLE = False

MAX_CYCLOMATIC = 30.0
MAX_HALSTEAD_VOLUME = 8000.0
_LOG_CALL = re.compile(
    r'\b(logging|logger|log)\.(debug|info|warning|error|critical)\s*\(',
    re.IGNORECASE,
)


@dataclass
class RadonMetrics:
    cyclomatic_complexity: float  # [0,1] higher = more complex
    halstead_volume: float        # [0,1] higher = larger/denser
    debt_ratio: float             # [0,1] higher = more technical debt
    log_coverage: float           # [0,1] higher = more observable
    maintainability: float        # [0,1] higher = more maintainable
    testability: float            # [0,1] higher = more testable
    functional_correctness: float # proxy: 1.0 if parseable, 0.2 if syntax error


def _is_parseable(code: str) -> bool:
    import ast
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _log_density(code: str) -> float:
    sloc = max(1, sum(
        1 for line in code.splitlines()
        if line.strip() and not line.strip().startswith('#')
    ))
    calls = len(_LOG_CALL.findall(code))
    # Expect ~1 logging call per 20 SLOC for full coverage
    return min(1.0, calls / max(1.0, sloc / 20.0))


class RadonRunner:
    """Static metrics for v6 (testability), v7 (maintainability), v8 (technical_debt)."""

    def analyze(self, code: str) -> RadonMetrics:
        if not code or not code.strip():
            return RadonMetrics(0.0, 0.0, 0.5, 0.0, 0.5, 0.5, 0.0)

        parseable = _is_parseable(code)
        fc_proxy = 1.0 if parseable else 0.2

        if not parseable or not _RADON_AVAILABLE:
            return RadonMetrics(
                cyclomatic_complexity=0.5,
                halstead_volume=0.5,
                debt_ratio=0.7,
                log_coverage=_log_density(code),
                maintainability=0.3,
                testability=0.3,
                functional_correctness=fc_proxy,
            )

        try:
            blocks = rc.cc_visit(code)
            avg_cc = (sum(b.complexity for b in blocks) / len(blocks)) if blocks else 1.0
        except Exception:
            avg_cc = 5.0
        cc_norm = min(1.0, avg_cc / MAX_CYCLOMATIC)

        try:
            mi = float(rm.mi_visit(code, multi=True))
            mi_norm = max(0.0, min(1.0, mi / 100.0))
        except Exception:
            mi_norm = 0.5

        try:
            h_results = rm.h_visit(code)
            avg_vol = (
                sum(getattr(f, 'volume', 0) for f in h_results) / len(h_results)
                if h_results else 0.0
            )
        except Exception:
            avg_vol = 1000.0
        hv_norm = min(1.0, avg_vol / MAX_HALSTEAD_VOLUME)

        # Technical debt is multifactorial: it must NOT be a pure function of
        # the Maintainability Index, or it becomes algebraically identical to
        # `maintainability` (debt = 1 − mi ≡ maintainability), making the two
        # dimensions uncalibratable against distinct ground truth. We compose
        # debt from the structural drivers radon exposes — cyclomatic complexity
        # and Halstead volume — modulated by (1 − MI). A unit with high MI but
        # high branching/volume still accrues debt, which (1 − MI) alone misses.
        debt = 0.50 * cc_norm + 0.30 * hv_norm + 0.20 * max(0.0, 1.0 - mi_norm)

        return RadonMetrics(
            cyclomatic_complexity=cc_norm,
            halstead_volume=hv_norm,
            debt_ratio=min(1.0, max(0.0, debt)),
            log_coverage=_log_density(code),
            maintainability=mi_norm,
            testability=max(0.0, 1.0 - cc_norm),
            functional_correctness=fc_proxy,
        )
