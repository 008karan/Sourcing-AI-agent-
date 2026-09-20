# Product Spec - Sourcing Decision Room

## 1. Problem

Enterprise buyers send an RFx to several suppliers, but responses return in incompatible Excel, PDF, Word, image and email formats. Buyers manually re-key and normalize offers before they can answer simple award questions. This creates days of work and, more importantly, makes the decision difficult to audit.

The product must absorb supplier messiness without hiding uncertainty from the buyer.

## 2. Primary persona

### Category Buyer / Sourcing Manager
Owns the sourcing event end-to-end. Needs to turn heterogeneous proposals into a trusted commercial comparison and defensible award recommendation.

Jobs:
- define requirement
- invite suppliers
- understand response completeness
- compare prices/terms/qualification
- resolve ambiguity
- run scenarios
- defend recommendation

## 3. Supporting personas

### Supplier representative
Wants minimum friction. Can reply in their existing format instead of learning a portal/template.

### Quality / Technical evaluator
Owns mandatory qualification questions. A cheap vendor can still be ineligible.

### Procurement leader / approver
Wants questions answered at scenario level, not to inspect 150 cells manually.

## 4. In-scope workflow

1. RFx creation
2. Vendor response collection (plumbing may be stubbed)
3. Format-aware extraction
4. RFx-line matching
5. Unit/currency/commercial normalization
6. Questionnaire/qualification
7. Exception generation and review
8. Evidence and transformation trace
9. Side-by-side comparison
10. Natural-language scenario compilation
11. Deterministic award optimization
12. Explainable result / export-ready decision

## 5. Deferred workflow

- Supplier Discovery
- Negotiation Agent
- ERP/PO integration
- production identity/RBAC
- full supplier portal

## 6. Core data concepts

### Source document
Immutable supplier artifact: XLSX/PDF/DOCX/image/email/attachment.

### Extracted fact
A claim directly supported by source evidence, e.g. `USD 23.51 / 100 pcs`.

### Evidence reference
Location of the fact in source: page/bbox, sheet/cell, table/paragraph, email span, image crop.

### Normalized quote line
Comparable commercial representation for one RFx line and supplier, produced by deterministic transformations from facts.

### Transformation trace
Ordered list of conversions and assumptions: `/100 -> /piece`, `USD -> INR`, freight addition, pack-size conversion, prior-year baseline resolution.

### Exception
Something requiring review, clarification or explicit policy treatment.

### Dataset version
Immutable logical version of the sourcing facts used by a scenario.

### Scenario
A validated set of award constraints and a deterministic result.

## 7. Trust model

Trust is a contextual product feature, not a separate audit screen.

Every important displayed commercial value should be drillable to:

**Result -> normalized value -> transformation steps -> extracted fact -> exact source**

The UI must visibly distinguish:
- trusted/extracted
- normalized/derived
- human override
- missing
- low confidence
- qualification fail
- pending clarification

## 8. Exception model

Priority should consider:

`uncertainty × financial exposure × decision relevance`

Suggested statuses:
- AUTO_VERIFIED
- NEEDS_REVIEW
- BLOCKING
- CLARIFICATION_REQUIRED
- RESOLVED_BY_BUYER

Suggested buyer actions:
- accept
- correct
- remap
- adjust conversion
- mark not quoted
- exclude
- request clarification

## 9. Scenario contract

AI produces only a strict intent object, e.g.:

```json
{
  "objective": "minimize_landed_cost",
  "qualified_suppliers_only": true,
  "max_supplier_spend_share": 0.45,
  "max_delivery_days": 14,
  "allocation_granularity": "line_item",
  "missing_quote_policy": "disallow",
  "required_supplier_ids": [],
  "excluded_supplier_ids": []
}
```

Code validates the object. The deterministic solver calculates the award. AI may explain the result afterwards but does not invent or alter totals.

## 10. Primary UI

### RFx Builder
Buyer intent + draft RFx + line items + questionnaire + terms + explicit approval gate.

### Response Inbox
Supplier/format/coverage/status + issues detected + open source artifact + extraction mode.

### Review & Compare
Hero screen. Normalized matrix + qualification + exceptions + evidence drawer.

### Analysis Room
Question box + scenario constraints + KPIs + allocation + vendor mix + evidence/assumptions.

## 11. Category choice

Corrugated packaging is intentional because it naturally exercises:
- INR/kg
- INR/piece
- INR/100 pcs
- carton/bundle pack sizes
- USD conversion
- freight treatment
- line-level quality/technical attributes
- incomplete quotations
- annual-volume pricing/rebates
- supplier qualification

It is complex enough to demonstrate procurement judgment without freight/MRO domain complexity swallowing the build.
