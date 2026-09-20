# Aerchain evaluation report

Mode: offline; model: none; run: 2026-09-19T15:42:14.311721+00:00.

Checks: 35/35 passed. Runtime: 0.8 seconds.

## Extraction quality

Rates compared to `demo-data/generated/normalized_truth.csv`, tolerance INR 0.02 per piece. Four buyer-approved prior-year references are included.

| Supplier | Compared | Within tolerance | Withheld | Maximum error |
|---|---:|---:|---|---:|
| packright | 30 | 30 | [] | 0.0 |
| corrpro | 30 | 30 | [] | 0.0 |
| boxworks | 27 | 27 | [] | 0.0 |
| alphapack | 0 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30] | None |
| greencarton | 30 | 30 | [] | 0.010000000000001563 |

## Scenarios

| Question | Result | Award INR | Dataset |
|---|---|---:|---:|
| Cheapest qualified supplier per line | ok | 39195860.0 | 23 |
| Qualified only, no supplier above 45% of award spend | ok | 39377480.0 | 23 |
| Qualified only, no supplier above 55% of award spend | ok | 39310450.0 | 23 |
| Qualified suppliers with delivery within 14 days | ok | 39195860.0 | 23 |
| Qualified suppliers with delivery within 1 day | infeasible | — | 23 |

## Checks

- PASS: RFx structured draft
- PASS: RFx approval interrupt
- PASS: Response collection precedes extraction
- PASS: Real processing progress recorded
- PASS: Five vendor ingestion branches
- PASS: Human review interrupt
- PASS: Native fixture coverage
- PASS: Partial quote stays missing
- PASS: Prior-year assumptions held for review
- PASS: packright normalization
- PASS: corrpro normalization
- PASS: boxworks normalization
- PASS: alphapack normalization
- PASS: greencarton normalization
- PASS: Scenario intent: Cheapest qualified supplier per line
- PASS: Scenario outcome: Cheapest qualified supplier per line
- PASS: Allocation integrity: Cheapest qualified supplier per line
- PASS: Scenario intent: Qualified only, no supplier above 45% of award spend
- PASS: Scenario outcome: Qualified only, no supplier above 45% of award spend
- PASS: Allocation integrity: Qualified only, no supplier above 45% of award spend
- PASS: Spend cap: Qualified only, no supplier above 45% of award spend
- PASS: Scenario intent: Qualified only, no supplier above 55% of award spend
- PASS: Scenario outcome: Qualified only, no supplier above 55% of award spend
- PASS: Allocation integrity: Qualified only, no supplier above 55% of award spend
- PASS: Spend cap: Qualified only, no supplier above 55% of award spend
- PASS: Scenario intent: Qualified suppliers with delivery within 14 days
- PASS: Scenario outcome: Qualified suppliers with delivery within 14 days
- PASS: Allocation integrity: Qualified suppliers with delivery within 14 days
- PASS: Scenario intent: Qualified suppliers with delivery within 1 day
- PASS: Scenario outcome: Qualified suppliers with delivery within 1 day
- PASS: Independent cheapest-line oracle
- PASS: Clarification changes only reviewed price
- PASS: Historical scenario marked stale
- PASS: Historical award reproducible
- PASS: CSV export includes all lines

## Limits and interpretation

- SMTP and demo replies are simulated; extraction and analysis run at request time.
- Qualification checks declarations, not certificate authenticity.
- Conditional rebates are surfaced but excluded from optimization.
- Whole-line allocation only.
- Four prior-year references require explicit buyer approval.
- Obscured photo line 18 is correctly withheld; full 147-price recall would be unsafe.
- Scenario staleness is conservative: every persisted business change creates a version.
- RFx retains baseline line specifications and qualification IDs; proposed questionnaire edits are advisory.
