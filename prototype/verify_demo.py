from __future__ import annotations

from collections import defaultdict

from backend.app.native_extractors import extract_native
from backend.app.normalize import normalize_fact
from backend.app.store import load_demo
from backend.app.scenario import solve_scenario


def main() -> None:
    data = load_demo()
    expected_coverage = {"packright": 30, "corrpro": 30, "boxworks": 27, "greencarton": 30}
    failures = []
    checked = 0
    for vendor_id, expected in expected_coverage.items():
        result = extract_native(vendor_id)
        assert result["coverage"] == expected, (vendor_id, result["coverage"], expected)
        truth_by_line = {x["line_no"]: x for x in data["vendors"][vendor_id]["lines"]}
        for fact in result["facts"]:
            norm = normalize_fact(vendor_id, fact, result["terms"])
            truth = truth_by_line[fact["line_no"]]
            checked += 1
            if abs(norm["landed_unit_cost_inr"] - truth["landed_piece_price_inr"]) > 0.02:
                failures.append((vendor_id, fact["line_no"], norm["landed_unit_cost_inr"], truth["landed_piece_price_inr"]))
    assert not failures, failures[:10]

    base = solve_scenario({
        "objective": "minimize_landed_cost", "qualified_suppliers_only": True,
        "max_supplier_spend_share": None, "max_delivery_days": None,
        "allocation_granularity": "line_item", "missing_quote_policy": "disallow",
        "required_supplier_ids": [], "excluded_supplier_ids": [],
    })
    capped = solve_scenario({
        "objective": "minimize_landed_cost", "qualified_suppliers_only": True,
        "max_supplier_spend_share": 0.45, "max_delivery_days": None,
        "allocation_granularity": "line_item", "missing_quote_policy": "disallow",
        "required_supplier_ids": [], "excluded_supplier_ids": [],
    })
    assert base["status"] == "ok"
    assert capped["status"] == "ok"
    assert max(v["share"] for v in capped["vendor_mix"]) <= 0.4501
    assert capped["award_total_inr"] >= base["award_total_inr"]
    print(f"PASS: {checked} native quote lines parsed + normalized within ₹0.02 of truth")
    print(f"PASS: baseline scenario ₹{base['award_total_cr']} Cr; 45% cap scenario ₹{capped['award_total_cr']} Cr")
    print("PASS: max supplier share constraint respected")


if __name__ == "__main__":
    main()
