# Implementation Plan

This plan is ordered for demo risk, not engineering perfection.

## Phase 0 - Baseline safety

- [ ] Run `python verify_demo.py` successfully.
- [ ] Run app and verify RFx, Responses, Review & Compare, Evidence Drawer, Analysis Room.
- [ ] Create a small regression test for any bug fixed from this point onward.

Exit: current functionality remains intact.

## Phase 1 - Buyer exception resolution

Implement write APIs and UI controls.

Suggested API surface:

- `POST /api/exceptions/{id}/accept`
- `POST /api/exceptions/{id}/correct-value`
- `POST /api/exceptions/{id}/remap-line`
- `POST /api/exceptions/{id}/mark-not-quoted`
- `POST /api/exceptions/{id}/exclude`
- `POST /api/exceptions/{id}/clarification-draft`

Each action must:
1. preserve original fact
2. create a new fact/version or resolution object
3. write audit event
4. recompute impacted normalized record(s)
5. increment dataset version if comparison truth changed
6. mark impacted scenario results stale

Exit: resolve one seeded high-impact exception from UI and see comparison change with evidence/history preserved.

## Phase 2 - Persistence

Prefer SQLite for take-home speed unless Postgres is already trivial to add. Hide DB access behind repository functions so production Postgres/Supabase remains a clean migration.

Tables/entities:
- events
- rfx_versions
- suppliers
- responses
- documents
- extracted_facts
- evidence_refs
- normalized_lines
- exceptions
- resolutions
- dataset_versions
- scenarios
- scenario_results
- audit_events
- workflow_runs

Exit: restart server and previous buyer resolution/scenario still exists.

## Phase 3 - LangGraph execution

Wire the existing graph blueprint rather than inventing a second orchestration system.

Nodes:
- draft_rfx
- buyer_rfx_approval interrupt
- dispatch_invitations stub
- await_responses stub
- per-supplier ingest subgraph
- exception gate
- buyer exception review interrupt
- build comparison
- ready_for_analysis

Graph state should contain IDs/status/version only.

Exit: workflow can pause for buyer review and resume without losing state.

## Phase 4 - Real AI extraction

Mandatory: run the photo fixture through a multimodal structured-output loop.

Expected behavior:
- extract 30-line attempt
- retain low confidence for obscured high-value line
- preserve bundle basis / pack size
- detect FSC fail from source if present
- produce unresolved ambiguity rather than inventing a rate

Recommended additional test:
- have AI identify CorrPro's conditional rebate footnote as a term with conditions, but do not apply it automatically.

Exit: at least one ugly source is genuinely interpreted by the model and produces reviewable evidence/confidence.

## Phase 5 - Clarification loop

When a fact is missing/unclear:
- generate a concise supplier clarification draft
- buyer approves
- fake the send
- capture a simulated reply
- link reply evidence to exception
- re-run only affected extraction/normalization

Demo candidate: BoxWorks missing item or AlphaPack obscured rate.

Exit: show closed-loop exception resolution without reprocessing the whole event.

## Phase 6 - Evidence preview

Enhance evidence drawer by artifact type:
- XLSX: sheet/cell range + source text
- PDF: page + source text; highlighted page crop if feasible
- DOCX: paragraph/table/cell location
- EML: body excerpt/span
- JPG: bounding box/crop if feasible

Exit: every decision-relevant number has an understandable route back to source.

## Phase 7 - Scenario hardening

- validate ScenarioSpec before solver
- return explicit `infeasible` result when constraints conflict
- never auto-relax constraints
- persist scenario input + dataset version + result
- expose vendor shares and per-line award
- mark stale after data correction
- add recompute action

Exit: four demo questions work reliably and one infeasible scenario fails gracefully.

## Phase 8 - Product polish

- loading states
- empty/error states
- clear qualification legends
- comparison filters
- exception counts
- dataset/scenario version indicators where helpful
- consistent INR formatting
- accessible click targets
- no raw JSON shown to buyer unless intentionally in a technical inspector

Exit: 5-7 minute demo works without explaining implementation details.

## Phase 9 - Final deliverables

Only after app is stable:
- hosted live link
- recorded Loom/Drive walkthrough
- 1-page note or 5-7 slide PPT
- README setup instructions
- architecture diagram
- deliberately-left-out section
- known limitations / next step
