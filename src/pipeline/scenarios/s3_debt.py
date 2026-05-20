# SPDX-License-Identifier: AGPL-3.0
# Copyright (C) 2026 Juan Pablo Chancay
"""
S3 — Gradual technical debt accumulation (4 cycles)

Fault: cyclomatic complexity and maintainability index degrade over 4 cycles.
INDETECTABLE with raw artifact review — requires temporal tensor slicing:
  T[d8, :, :, k] - T[d8, :, :, k-3] > 0.20 to trigger alert.

Target v8 (technical_debt) trajectory per paper:
  k=0: ~0.68  (MI ≈ 68, CC ≈ 2)
  k=1: ~0.60  (MI ≈ 60, CC ≈ 5)
  k=2: ~0.52  (MI ≈ 52, CC ≈ 8)
  k=3: ~0.44  (MI ≈ 44, CC ≈ 12)

The individual delta per cycle (~0.08) is within evaluation noise.
Only the 3-cycle cumulative drop (~0.24) crosses the Δ alert threshold.
This is the core proof that tensor temporal indexing is a mathematical necessity.
"""
from __future__ import annotations

SCENARIO_ID = "S3"
DESCRIPTION = "Order processor — gradual technical debt accumulation over 4 cycles"
FAULT_TYPE = "debt_accumulation"
N_CYCLES = 4

GROUND_TRUTH: dict[str, dict] = {
    "s3_processor_k0": {"v8_approx": 0.68, "mi_approx": 68, "cc_approx": 2},
    "s3_processor_k1": {"v8_approx": 0.60, "mi_approx": 60, "cc_approx": 5},
    "s3_processor_k2": {"v8_approx": 0.52, "mi_approx": 52, "cc_approx": 8},
    "s3_processor_k3": {"v8_approx": 0.44, "mi_approx": 44, "cc_approx": 12},
}

# k=0: Clean, minimal cyclomatic complexity. MI ≈ 65-72.
_CODE_K0 = """\
import logging

logger = logging.getLogger(__name__)


def process_order(order: dict) -> dict:
    logger.info("Processing order %s", order.get("id"))
    if not order.get("items"):
        logger.warning("Order %s has no items", order.get("id"))
        return {"status": "error", "reason": "no_items"}
    total = sum(item["price"] * item["qty"] for item in order["items"])
    logger.info("Order %s total: %.2f", order.get("id"), total)
    return {"order_id": order["id"], "total": total, "status": "processed"}
"""

# k=1: Added edge-case conditionals and discount logic. MI ≈ 57-63.
_CODE_K1 = """\
import logging

logger = logging.getLogger(__name__)


def process_order(order: dict) -> dict:
    logger.info("Processing order %s", order.get("id"))
    if not order:
        return {"status": "error", "reason": "empty_order"}
    if not order.get("items"):
        logger.warning("Order %s has no items", order.get("id"))
        return {"status": "error", "reason": "no_items"}
    if not order.get("customer_id"):
        return {"status": "error", "reason": "missing_customer"}
    total = 0.0
    for item in order["items"]:
        price = item["price"]
        qty = item["qty"]
        if item.get("discount"):
            price = price * (1 - item["discount"])
        if item.get("tax"):
            price = price * (1 + item["tax"])
        total += price * qty
    status = "processed"
    if total > 1000:
        status = "requires_review"
    logger.info("Order %s total: %.2f status: %s", order["id"], total, status)
    return {"order_id": order["id"], "total": total, "status": status}
"""

# k=2: Nested conditional blocks, duplicated validation, poor naming. MI ≈ 49-55.
_CODE_K2 = """\
import logging

logger = logging.getLogger(__name__)


def process_order(order: dict) -> dict:
    logger.info("Processing order %s", order.get("id"))
    if not order:
        return {"status": "error", "reason": "empty_order"}
    if not order.get("items"):
        return {"status": "error", "reason": "no_items"}
    if not order.get("customer_id"):
        return {"status": "error", "reason": "missing_customer"}
    total = 0.0
    discount_total = 0.0
    tax_total = 0.0
    for item in order["items"]:
        p = item["price"]
        q = item["qty"]
        if item.get("discount"):
            d = item["discount"]
            if d > 0.5:
                d = 0.5
            p2 = p * (1 - d)
            discount_total += (p - p2) * q
            p = p2
        if item.get("tax"):
            t = item["tax"]
            if t < 0:
                t = 0
            p3 = p * (1 + t)
            tax_total += (p3 - p) * q
            p = p3
        if item.get("bundle_discount") and q >= 3:
            p = p * 0.9
        total += p * q
    st = "processed"
    if total > 1000:
        st = "requires_review"
    if total > 5000:
        st = "manager_approval"
    if order.get("priority") == "express":
        if total < 50:
            st = "error_min_express"
    return {
        "order_id": order["id"],
        "total": total,
        "discount_total": discount_total,
        "tax_total": tax_total,
        "status": st,
    }
"""

# k=3: Deeply nested, magic numbers, duplicated logic, no abstraction. MI ≈ 42-47.
_CODE_K3 = """\
import logging

logger = logging.getLogger(__name__)


def process_order(order: dict) -> dict:
    if not order:
        return {"status": "error", "reason": "empty_order"}
    if not order.get("items"):
        return {"status": "error", "reason": "no_items"}
    if not order.get("customer_id"):
        return {"status": "error", "reason": "missing_customer"}
    if not order.get("id"):
        return {"status": "error", "reason": "missing_id"}
    t = 0.0
    dt = 0.0
    tt = 0.0
    fc = 0
    for item in order["items"]:
        p = item.get("price", 0)
        q = item.get("qty", 0)
        if p < 0:
            p = 0
        if q < 0:
            q = 0
        if item.get("discount"):
            dv = item["discount"]
            if dv > 0.5:
                dv = 0.5
            if dv < 0:
                dv = 0
            p2 = p * (1 - dv)
            dt += (p - p2) * q
            p = p2
        if item.get("tax"):
            tv = item["tax"]
            if tv < 0:
                tv = 0
            if tv > 0.3:
                tv = 0.3
            p3 = p * (1 + tv)
            tt += (p3 - p) * q
            p = p3
        if item.get("bundle_discount"):
            if q >= 3:
                p = p * 0.9
            elif q >= 5:
                p = p * 0.85
            elif q >= 10:
                p = p * 0.80
        if item.get("member_price") and order.get("is_member"):
            mp = item["member_price"]
            if mp < p:
                p = mp
        t += p * q
        fc += 1
    s = "processed"
    if t > 1000:
        s = "requires_review"
    if t > 5000:
        s = "manager_approval"
    if t > 10000:
        s = "finance_approval"
    if order.get("priority") == "express":
        if t < 50:
            s = "error_min_express"
        elif t > 500:
            s = "express_surcharge"
    if order.get("region") == "international":
        if t < 100:
            s = "error_min_international"
        t = t * 1.15
    if fc == 0:
        s = "error_no_valid_items"
    logger.info("order=%s total=%.2f items=%d status=%s", order["id"], t, fc, s)
    return {
        "order_id": order["id"],
        "total": t,
        "discount_total": dt,
        "tax_total": tt,
        "item_count": fc,
        "status": s,
    }
"""

_VERSIONS = {0: _CODE_K0, 1: _CODE_K1, 2: _CODE_K2, 3: _CODE_K3}


def get_artifacts(cycle_k: int = 0) -> list[dict]:
    k = max(0, min(cycle_k, 3))
    code = _VERSIONS[k]
    gt = GROUND_TRUTH[f"s3_processor_k{k}"]
    return [
        {
            "id": f"s3_processor_k{k}",
            "agent_id": "code_agent",
            "stage": "build",
            "content": code,
            "artifact_type": "python_code",
            "context": (
                f"Order processor module. Stage: build. Scenario: S3. "
                f"Cycle {k}/3. Expected MI≈{gt['mi_approx']}, "
                f"CC≈{gt['cc_approx']}."
            ),
        }
    ]
