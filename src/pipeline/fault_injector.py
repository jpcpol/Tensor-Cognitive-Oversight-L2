# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
FaultInjector — programmatic artifact-level fault transformation.

Used by graph.py to dynamically inject known faults into clean baseline artifacts.
Each scenario module pre-defines faulty artifact variants; the FaultInjector
provides an additional mechanism for controlled fault injection at runtime.

Supported fault types:
  sql_injection       — replaces parameterized query with string concatenation
  circular_import     — injects a circular import statement
  missing_resource    — removes resource limits block from K8s YAML
  debt_increment      — adds a known-bad code pattern to a Python artifact
  agent_security_bias — modifies artifact to produce a low security score
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FaultSpec:
    fault_type: str
    target_artifact_id: str
    description: str = ""
    # Optional intensity parameter (0.0=minimal, 1.0=maximal)
    intensity: float = 1.0


class FaultInjector:
    """
    Transforms a clean artifact dict by injecting a specified fault.

    Returns a new artifact dict (does not mutate in place).
    """

    def inject(self, artifact: dict, spec: FaultSpec) -> dict:
        handler = self._HANDLERS.get(spec.fault_type)
        if handler is None:
            logger.warning("Unknown fault type %r — returning artifact unchanged", spec.fault_type)
            return artifact

        content = artifact.get("content", "")
        try:
            new_content = handler(self, content, spec)
        except Exception as exc:
            logger.error("Fault injection failed for %r: %s", spec.fault_type, exc)
            return artifact

        logger.info(
            "Injected fault %r into artifact %s",
            spec.fault_type,
            artifact.get("id", "unknown"),
        )
        return {**artifact, "content": new_content, "_fault_injected": spec.fault_type}

    # ─── Fault handlers ──────────────────────────────────────────────────────

    def _inject_sql_injection(self, code: str, spec: FaultSpec) -> str:
        """Replace :param parameterized query with string concatenation."""
        # Replace text("... :param ...", {param: value}) with direct concat
        code = re.sub(
            r'text\("(SELECT[^"]+WHERE\s+\w+\s*=\s*):(\w+)"[^)]*\)',
            lambda m: f'"{ m.group(1) }" + str(username)',
            code,
        )
        # Also replace sha256 with md5 for additional bandit finding
        code = code.replace("hashlib.sha256", "hashlib.md5")
        code = code.replace("hmac.compare_digest(", "# insecure: (")
        return code

    def _inject_circular_import(self, code: str, spec: FaultSpec) -> str:
        """Add a circular import statement to YAML or Python code."""
        if "depends_on" in code:
            # YAML service dep — inject a back-reference
            lines = code.splitlines()
            result = []
            for line in lines:
                result.append(line)
                if "depends_on: []" in line:
                    # Add a dependency on a service that will create a cycle
                    result.append(line.replace("depends_on: []", "depends_on: [order_service]"))
            return "\n".join(result)
        # Python — inject a circular import comment
        return f"# FAULT: circular import introduced\nfrom __future__ import annotations\n{code}"

    def _inject_missing_resource(self, code: str, spec: FaultSpec) -> str:
        """Remove resource limits block from K8s YAML."""
        # Remove the resources: block (requests + limits)
        code = re.sub(
            r'\s+resources:\s*\n(?:\s+\w+:[^\n]*\n)+(?:\s+\w+:[^\n]*\n)*',
            "\n          # FAULT: resource limits removed\n",
            code,
        )
        # Remove probe definitions
        code = re.sub(r'\s+\w+Probe:[^\n]*(?:\n(?:\s{12}[^\n]+))*', "", code)
        return code

    def _inject_debt_increment(self, code: str, spec: FaultSpec) -> str:
        """Append a known-bad code pattern that increases cyclomatic complexity."""
        debt_suffix = """

# FAULT: debt injected — redundant validation with magic numbers
def _validate_order_legacy(order: dict) -> bool:
    if not order:
        return False
    if order.get("total", 0) < 0:
        return False
    if order.get("total", 0) > 999999:
        return False
    if order.get("items") is None:
        return False
    if len(order.get("items", [])) == 0:
        return False
    if len(order.get("items", [])) > 500:
        return False
    if not order.get("customer_id"):
        return False
    if order.get("customer_id") == 0:
        return False
    if order.get("currency") not in ["USD", "EUR", "GBP", None]:
        return False
    if order.get("status") not in ["pending", "processing", "completed", None]:
        return False
    return True
"""
        return code + debt_suffix

    def _inject_security_bias(self, code: str, spec: FaultSpec) -> str:
        """Insert SQL injection pattern to force a low security score."""
        injection = (
            "\n\n# FAULT: insecure fallback added\n"
            "def _legacy_lookup(db, uid):\n"
            "    return db.execute('SELECT * FROM users WHERE id=' + str(uid)).fetchone()\n"
        )
        return code + injection

    _HANDLERS: dict = {
        "sql_injection":       _inject_sql_injection,
        "circular_import":     _inject_circular_import,
        "missing_resource":    _inject_missing_resource,
        "debt_increment":      _inject_debt_increment,
        "agent_security_bias": _inject_security_bias,
    }


# Pre-defined fault specs aligned with each scenario

FAULT_SPECS: dict[str, FaultSpec] = {
    "S1": FaultSpec(
        fault_type="sql_injection",
        target_artifact_id="s1_auth_clean",
        description="SQL injection via string concatenation + MD5 hash",
    ),
    "S2": FaultSpec(
        fault_type="circular_import",
        target_artifact_id="s2_arch_clean",
        description="Circular dependency in service graph",
    ),
    "S3": FaultSpec(
        fault_type="debt_increment",
        target_artifact_id="s3_processor_k0",
        description="Gradual technical debt accumulation",
    ),
    "S4": FaultSpec(
        fault_type="missing_resource",
        target_artifact_id="s4_deploy_clean",
        description="Missing resource limits and observability probes",
    ),
    "S5": FaultSpec(
        fault_type="agent_security_bias",
        target_artifact_id="s5_auth_code_agent",
        description="Code agent produces insecure implementation (conflict with security_agent)",
    ),
}
