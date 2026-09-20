from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .store import load_demo
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class ValidatedSpec(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    objective: Literal['minimize_landed_cost'] = 'minimize_landed_cost'
    qualified_suppliers_only: bool = True
    max_supplier_spend_share: float | None = Field(default=None, gt=0, le=1)
    max_delivery_days: int | None = Field(default=None, gt=0)
    allocation_granularity: Literal['line_item'] = 'line_item'
    missing_quote_policy: Literal['disallow','allow_uncovered'] = 'disallow'
    required_supplier_ids: list[str] = []
    excluded_supplier_ids: list[str] = []


def _fmt_cr(value: float) -> float:
    return round(value / 10_000_000, 3)


def _eligible_quotes(row: dict[str, Any], spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    required = set(spec.get("required_supplier_ids") or [])
    excluded = set(spec.get("excluded_supplier_ids") or [])
    for vendor_id, quote in row["vendors"].items():
        if vendor_id in excluded:
            continue
        if quote.get('blocking_exception'):
            continue
        if quote.get("status") != "quoted" or quote.get("landed_unit_cost") is None:
            continue
        if spec.get("qualified_suppliers_only", True) and quote.get("qualification") != "pass":
            continue
        if spec.get("max_delivery_days") and (quote.get("lead_days") or 999) > spec["max_delivery_days"]:
            continue
        out[vendor_id] = quote
    return out


def solve_scenario(spec: dict[str, Any], data: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = ValidatedSpec.model_validate(spec).model_dump()
    data = data if data is not None else load_demo()
    ids=set(data['vendors']); required=set(spec['required_supplier_ids']); excluded=set(spec['excluded_supplier_ids'])
    if (required | excluded)-ids: raise ValueError('Unknown supplier ID in scenario constraints')
    if required & excluded: raise ValueError('A supplier cannot be both required and excluded')
    comparison = data["comparison"]
    baseline = sum(row["qty"] * row["baseline_unit_price_inr"] for row in comparison)

    variables: list[tuple[int, str, float]] = []
    item_to_vars: dict[int, list[int]] = defaultdict(list)
    vendor_to_vars: dict[str, list[int]] = defaultdict(list)
    uncovered: list[int] = []

    for row in comparison:
        eligible = _eligible_quotes(row, spec)
        if not eligible:
            uncovered.append(row["line_no"])
            continue
        for vendor_id, quote in eligible.items():
            idx = len(variables)
            total_cost = quote["landed_unit_cost"] * row["qty"]
            variables.append((row["line_no"], vendor_id, total_cost))
            item_to_vars[row["line_no"]].append(idx)
            vendor_to_vars[vendor_id].append(idx)

    if uncovered and spec.get("missing_quote_policy", "disallow") == "disallow":
        return {
            "status": "infeasible",
            "reason": "No eligible quote exists for one or more lines under the selected constraints.",
            "uncovered_lines": uncovered,
            "spec": spec,
        }
    if not variables:
        return {"status": "infeasible", "reason": "No eligible quotations remain.", "spec": spec}

    if required-set(vendor_to_vars):
        return {'status':'infeasible','reason':'A required supplier has no eligible quotes.','spec':spec}

    n = len(variables)
    c = np.array([v[2] for v in variables], dtype=float)
    integrality = np.ones(n, dtype=int)
    bounds = Bounds(np.zeros(n), np.ones(n))
    constraints = []

    # Exactly one supplier per line for every line that has eligible quotes.
    Aeq = []
    beq = []
    for line_no, idxs in item_to_vars.items():
        row = np.zeros(n)
        row[idxs] = 1
        Aeq.append(row)
        beq.append(1)
    if Aeq:
        Aeq = np.vstack(Aeq)
        constraints.append(LinearConstraint(Aeq, np.array(beq), np.array(beq)))

    # Supplier award-spend share: vendor_cost <= share * total_award_cost.
    for vid in required:
        row=np.zeros(n); row[vendor_to_vars[vid]]=1
        constraints.append(LinearConstraint(row,1,np.inf))

    share = spec.get("max_supplier_spend_share")
    if share:
        rows = []
        for vendor_id, idxs in vendor_to_vars.items():
            row = -share * c.copy()
            row[idxs] += c[idxs]
            rows.append(row)
        if rows:
            A = np.vstack(rows)
            constraints.append(LinearConstraint(A, -np.inf * np.ones(len(rows)), np.zeros(len(rows))))

    result = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints, options={"time_limit": 15.0,'mip_rel_gap':0.0})
    if not result.success or result.x is None:
        return {
            "status": "infeasible",
            "reason": result.message or "No feasible allocation found for these constraints.",
            "solver_status": "infeasible" if result.status==2 else "limit_or_error",
            "spec": spec,
            "uncovered_lines": uncovered,
        }

    allocation = []
    vendor_spend = defaultdict(float)
    selected = np.where(result.x > 0.5)[0]
    for idx in selected:
        line_no, vendor_id, total_cost = variables[idx]
        row = comparison[line_no - 1]
        quote = row["vendors"][vendor_id]
        vendor_spend[vendor_id] += total_cost
        allocation.append(
            {
                "line_no": line_no,
                "sku": row["sku"],
                "description": row["description"],
                "qty": row["qty"],
                "vendor_id": vendor_id,
                "vendor_name": data["vendors"][vendor_id]["name"],
                "landed_unit_cost": quote["landed_unit_cost"],
                "total_cost": round(total_cost, 2),
                "evidence_id": quote.get("evidence_id"),
            }
        )
    allocation.sort(key=lambda x: x["line_no"])
    total = float(sum(x["total_cost"] for x in allocation))
    vendor_mix = [
        {
            "vendor_id": vid,
            "vendor_name": data["vendors"][vid]["name"],
            "spend": round(spend, 2),
            "share": round(spend / total, 4) if total else 0,
            "lines": sum(1 for x in allocation if x["vendor_id"] == vid),
        }
        for vid, spend in sorted(vendor_spend.items(), key=lambda kv: kv[1], reverse=True)
    ]
    covered_baseline=sum(row['qty']*row['baseline_unit_price_inr'] for row in comparison if row['line_no'] not in uncovered)
    return {
        "status": "ok",
        "spec": spec,
        "dataset_version": data.get("dataset_version", 1),
        "assumptions": [
            f"FX: USD/INR {data['rfx']['commercial_rules']['fx_rate_usd_inr']}",
            "GST excluded from comparison",
            "Conditional rebates are not applied unless explicitly resolved into normalized commercial terms",
            "Pending/failed suppliers are excluded when qualified_suppliers_only=true",
        ],
        "baseline_total_inr": round(baseline, 2),
        "award_total_inr": round(total, 2),
        "award_total_cr": _fmt_cr(total),
        "savings_inr": round(covered_baseline - total, 2),
        "savings_pct": round((covered_baseline - total) / covered_baseline * 100, 2),
        'covered_baseline_inr':round(covered_baseline,2),
        'complete_award':not uncovered,
        'solver_gap':float(result.mip_gap),
        "supplier_count": len(vendor_spend),
        "uncovered_lines": uncovered,
        "vendor_mix": vendor_mix,
        "allocation": allocation,
    }
