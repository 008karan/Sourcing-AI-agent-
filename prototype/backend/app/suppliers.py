"""Supplier directory profiles and deterministic RFx-to-supplier matching.

Matching is explainable arithmetic over declared profile attributes: no model
decides who receives an RFx, and every score carries the reasons that produced it.
"""
from __future__ import annotations

from typing import Any

PROFILES: dict[str, dict[str, Any]] = {
    'packright': {
        'region': 'Bengaluru, Karnataka', 'distance_km': 18, 'relationship': 'incumbent',
        'capabilities': ['corrugated boxes', 'dividers', 'pads', 'sheets', 'sleeves'],
        'certifications': ['ISO 9001', 'FSC CoC'], 'past_awards': 7,
        'past_award_value_inr': 38_200_000, 'on_time_pct': 96, 'avg_response_hours': 18,
        'annual_capacity_pieces': 5_200_000, 'email': 'bids@packright.example',
    },
    'corrpro': {
        'region': 'Chennai, Tamil Nadu', 'distance_km': 310, 'relationship': 'approved',
        'capabilities': ['corrugated boxes', 'sheets', 'export packaging'],
        'certifications': ['ISO 9001', 'FSC CoC', 'ISO 14001'], 'past_awards': 4,
        'past_award_value_inr': 21_500_000, 'on_time_pct': 91, 'avg_response_hours': 26,
        'annual_capacity_pieces': 4_400_000, 'email': 'sales@corrpro.example',
    },
    'boxworks': {
        'region': 'Hosur, Tamil Nadu', 'distance_km': 42, 'relationship': 'approved',
        'capabilities': ['corrugated boxes', 'dividers', 'pads'],
        'certifications': ['ISO 9001'], 'past_awards': 2,
        'past_award_value_inr': 6_900_000, 'on_time_pct': 88, 'avg_response_hours': 34,
        'annual_capacity_pieces': 2_600_000, 'email': 'quotes@boxworks.example',
    },
    'alphapack': {
        'region': 'Pune, Maharashtra', 'distance_km': 840, 'relationship': 'approved',
        'capabilities': ['corrugated boxes', 'sleeves', 'sheets'],
        'certifications': ['ISO 9001', 'FSC CoC'], 'past_awards': 3,
        'past_award_value_inr': 12_400_000, 'on_time_pct': 84, 'avg_response_hours': 41,
        'annual_capacity_pieces': 3_100_000, 'email': 'rfq@alphapack.example',
    },
    'greencarton': {
        'region': 'Bengaluru, Karnataka', 'distance_km': 27, 'relationship': 'incumbent',
        'capabilities': ['corrugated boxes', 'dividers', 'pads', 'sheets', 'recycled packaging'],
        'certifications': ['ISO 9001', 'FSC CoC', 'PEFC'], 'past_awards': 6,
        'past_award_value_inr': 29_800_000, 'on_time_pct': 93, 'avg_response_hours': 21,
        'annual_capacity_pieces': 4_800_000, 'email': 'tenders@greencarton.example',
    },
}

NEW_SUPPLIER = {
    'region': 'Not on file', 'distance_km': None, 'relationship': 'new',
    'capabilities': [], 'certifications': [], 'past_awards': 0, 'past_award_value_inr': 0,
    'on_time_pct': None, 'avg_response_hours': None, 'annual_capacity_pieces': None,
}

MATCH_STAGES = [
    ('scan', 'Scanning the supplier directory', 'Reading every registered supplier in this category'),
    ('capability', 'Matching capability and capacity', 'Comparing declared product lines against your 30 requirement lines'),
    ('compliance', 'Checking certifications and compliance', 'Testing each supplier against the qualification gates you set'),
    ('mapping', 'Mapping your requirement to each supplier', 'Attaching line items, questionnaire and commercial terms'),
    ('share', 'Sharing the RFx', 'Releasing the event and opening the response inbox'),
]


def profile(vendor_id: str, vendor: dict[str, Any] | None = None) -> dict[str, Any]:
    base = dict(PROFILES.get(vendor_id) or NEW_SUPPLIER)
    if vendor and vendor.get('email'):
        base['email'] = vendor['email']
    base.setdefault('email', 'not on file')
    return base


def _needs(rfx: dict[str, Any], checklist: list[dict[str, Any]] | None) -> dict[str, Any]:
    wanted = {c.upper() for q in rfx['questionnaire'] for c in
              ('ISO 9001', 'FSC CoC', 'PEFC') if c.lower().split()[0] in q['question'].lower()}
    lead_rule = next((q.get('maximum') for q in rfx['questionnaire']
                      if q['type'] == 'number' and 'lead time' in q['question'].lower()), None)
    return {'category': rfx['category'].lower(), 'certifications': wanted,
            'lead_days': lead_rule, 'volume': sum(i['annual_quantity'] for i in rfx['items']),
            'checklist_items': [c['id'] for c in (checklist or []) if c.get('status') == 'captured']}


def match(rfx: dict[str, Any], vendors: dict[str, Any], checklist: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    need = _needs(rfx, checklist)
    keywords = [w for w in need['category'].replace('/', ' ').split() if len(w) > 3]
    matches = []
    for vid, vendor in vendors.items():
        p = profile(vid, vendor)
        score, reasons, gaps = 0, [], []

        capability = [c for c in p['capabilities'] if any(k in c.lower() for k in keywords)]
        if capability:
            score += 40
            reasons.append(f"Supplies {', '.join(capability[:3])} in {rfx['category'].lower()}")
        elif p['relationship'] == 'new':
            score += 25
            reasons.append('Added by you for this event; capability not yet on file')
        else:
            gaps.append('No declared capability in this category')

        held = {c.upper() for c in p['certifications']}
        covered = {c for c in need['certifications'] if any(c.split()[0] in h for h in held)}
        if need['certifications']:
            score += round(25 * len(covered) / len(need['certifications']))
            if covered:
                reasons.append('Holds ' + ', '.join(sorted(covered)))
            missing = need['certifications'] - covered
            if missing:
                gaps.append('Certification to verify: ' + ', '.join(sorted(missing)))
        else:
            score += 15

        if p['annual_capacity_pieces'] and need['volume']:
            ratio = p['annual_capacity_pieces'] / need['volume']
            score += 15 if ratio >= 1.5 else 10 if ratio >= 1 else 4
            reasons.append(f"Declared capacity covers {min(ratio, 9.9):.1f}× the annual volume")
        if p['distance_km'] is not None:
            score += 8 if p['distance_km'] <= 100 else 5 if p['distance_km'] <= 400 else 2
            reasons.append(f"{p['region']} · {p['distance_km']} km from the delivery plants")

        if p['past_awards']:
            score += min(12, p['past_awards'] * 2)
            reasons.append(f"{p['past_awards']} previous awards worth ₹{p['past_award_value_inr'] / 1e7:.2f} Cr")
        if p['on_time_pct'] is not None:
            score += round(p['on_time_pct'] / 20)
            reasons.append(f"{p['on_time_pct']}% on-time delivery on past orders")
        if p['relationship'] == 'new':
            gaps.append('No performance history on file yet')

        matches.append({
            'vendor_id': vid, 'name': vendor['name'], 'email': p['email'],
            'score': min(100, score), 'relationship': p['relationship'], 'region': p['region'],
            'certifications': p['certifications'], 'past_awards': p['past_awards'],
            'on_time_pct': p['on_time_pct'], 'avg_response_hours': p['avg_response_hours'],
            'reasons': reasons[:4], 'gaps': gaps,
            'fit': 'strong' if score >= 80 else 'good' if score >= 60 else 'possible',
        })
    matches.sort(key=lambda m: -m['score'])
    return {
        'pool_size': len(matches),
        'matched': matches,
        'requirement_lines': len(rfx['items']),
        'qualification_gates': sum(1 for q in rfx['questionnaire'] if q['mandatory']),
        'stages': [{'id': i, 'label': label, 'detail': detail} for i, label, detail in MATCH_STAGES],
    }
