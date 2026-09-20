# Architecture v0.1 - Sourcing Decision Room

## Product thesis

The product is not a quote extractor. It is a procurement decision system that converts unstructured supplier responses into auditable, normalized facts and defensible award scenarios.

## Primary flow

1. RFx Copilot drafts scope, line items, questionnaire, and commercial terms.
2. Buyer reviews and approves the RFx.
3. Supplier invitations are dispatched through a stubbed channel.
4. Responses arrive as Excel, PDF, DOCX, image, email text, and attachments.
5. Intake router chooses the safest extraction path for each artifact.
6. Extractor converts source content into canonical facts with evidence anchors.
7. Validator checks completeness, arithmetic, item matching, units, currencies, and commercial terms.
8. Normalizer converts comparable facts into a common unit/currency/basis.
9. Exception engine prioritizes uncertain or commercially material facts for human review.
10. Comparison view presents normalized offers alongside questionnaire results and source evidence.
11. Analyst converts buyer questions into a structured ScenarioSpec.
12. Deterministic scenario engine evaluates constraints and allocation.
13. Explanation layer returns text/tables/charts with evidence and assumptions.

## Orchestration

Use LangGraph for the workflow because the process has explicit stages, retries, branching, parallel supplier ingestion, and human-review pauses.

Graph state contains orchestration state only:
- event_id
- current_stage
- supplier_response_ids
- pending_exception_ids
- dataset_version
- last_error
- run metadata

The graph state MUST NOT contain entire uploaded files or become the procurement system of record.

## High-level graph

START
  -> draft_rfx
  -> buyer_rfx_approval [interrupt]
  -> dispatch_invitations
  -> await_responses
  -> ingest_response_subgraph [parallel per supplier]
      -> classify_artifacts
      -> parse_artifacts
      -> extract_facts
      -> validate_facts
      -> normalize_facts
      -> create_exceptions
  -> material_exception_gate
      -> human_exception_review [interrupt, only if required]
  -> build_comparison
  -> READY_FOR_ANALYSIS

Analysis subgraph:

buyer_question
  -> interpret_question
  -> compile_scenario_spec
  -> validate_scenario_spec
  -> run_deterministic_scenario
  -> explain_result
  -> attach_evidence
  -> answer

## Agent boundaries

### 1. RFx Copilot
Uses the buyer's natural-language requirement plus category configuration to draft:
- event scope
- line items
- questionnaire
- commercial terms
- response deadline

It does not autonomously send anything without buyer approval.

### 2. Extraction & Mapping Specialist
Purpose: transform heterogeneous response artifacts into canonical procurement facts.

This is a specialist with deterministic tools, not a free-form autonomous agent.
It may use:
- native XLSX parser
- DOCX parser
- EML parser
- Docling for PDF/layout/table extraction
- multimodal model for scans/photos/layout ambiguity
- canonical-schema structured output

### 3. Verification Specialist
Re-checks low-confidence or commercially material extracted facts against the source. It never invents a missing value.

### 4. Scenario Analyst
Converts plain-language questions into a validated ScenarioSpec. It cannot directly calculate or award. The deterministic scenario engine performs the calculation.

Future subgraphs:
- Supplier Discovery
- Negotiation Agent

## Extraction strategy by format

### XLSX
1. Read workbook natively.
2. Preserve sheet, row, column, merged-cell, and formula metadata.
3. Identify likely quote tables and commercial-term regions.
4. Use the model only for semantic mapping to the canonical schema.
5. Evidence anchor: workbook + sheet + cell/range.

### DOCX
1. Extract paragraphs and tables natively.
2. Preserve paragraph/table/cell indexes.
3. Use model for semantic mapping and ambiguous commercial language.
4. Evidence anchor: document + paragraph/table/cell index.

### Email
1. Parse subject/body/attachments deterministically.
2. Extract direct price/term claims from body.
3. Process attachments independently.
4. Evidence anchor: message + body character span or attachment anchor.

### PDF
1. Run layout-aware parsing/table extraction with Docling.
2. Preserve page geometry and table structure.
3. Render pages/regions when visual interpretation is needed.
4. Send ambiguous page/region plus structural context to multimodal model.
5. Evidence anchor: page + bounding box + text/table element ID.

### Photo / scanned quote
1. Render/normalize image.
2. Multimodal extraction into canonical schema.
3. Capture bounding boxes where practical.
4. Lower confidence if the image is skewed/blurred or values are ambiguous.
5. Evidence anchor: image + bounding box/crop.

## Evidence contract

Every extracted commercial fact must include an EvidenceRef.

EvidenceRef fields:
- evidence_id
- document_id
- artifact_type
- page_number (optional)
- bounding_box (optional)
- sheet_name (optional)
- cell_range (optional)
- paragraph_index (optional)
- body_span (optional)
- source_text
- source_preview_uri

Every normalized fact also records a TransformationTrace:
- raw value
- raw unit/currency
- conversion rule IDs
- formula
- normalized value
- normalized unit/currency
- assumptions
- evidence IDs

This powers the UI interaction: "Why this number?"

## Trust rules

Hard product invariants:

1. Missing is never converted to zero.
2. No normalized numeric commercial fact without evidence.
3. No unit conversion without an explicit conversion rule or buyer-approved assumption.
4. Unknown freight/tax/discount stays unknown until clarified or explicitly excluded.
5. Every AI-extracted fact carries confidence and extraction method.
6. High-impact uncertain facts become review exceptions.
7. Scenario computation is deterministic and stores its exact constraints.
8. A scenario stores the dataset version it ran on.
9. Editing a source fact creates a new version/audit event; prior scenario results remain reproducible.
10. Any buyer override is visible and attributed as a human override.

## Exception priority

Do not prioritize only by model confidence.

priority_score = uncertainty_score * estimated_financial_exposure * decision_relevance

Examples:
- 75% confidence on a Rs 20k line may be low priority.
- 92% confidence on a Rs 1.2 crore line may still require review.

Exception states:
- AUTO_VERIFIED
- NEEDS_REVIEW
- BLOCKING
- RESOLVED_BY_BUYER
- CLARIFICATION_REQUIRED

Buyer actions:
- Accept extraction
- Edit value
- Change item mapping
- Change unit conversion
- Mark not quoted
- Exclude from comparison
- Draft supplier clarification

## Scenario architecture

Natural-language request example:
"Give me the cheapest split award among quality-approved vendors, no vendor above 50% of spend, and prefer delivery within 14 days."

The Scenario Analyst outputs structured JSON, not a result:

- objective: minimize_landed_cost
- eligibility: quality_status == PASS
- max_supplier_spend_share: 0.50
- delivery_days_lte: 14
- allocation_granularity: line_item
- missing_quote_policy: disallow

The backend validates this spec. A deterministic solver (mixed-integer programming (SciPy `milp` in the prototype; replaceable behind the solver interface)) computes the allocation.

The explanation layer then describes:
- total landed cost
- savings vs baseline
- supplier allocation
- constraints applied
- exceptions/assumptions
- evidence links

## UI information architecture

### Global event header
RFx name | category | expected spend | status | invited/replied | unresolved exceptions

### 1. RFx Builder
Two-pane design:
- left: conversational/copilot input
- right: structured RFx preview

Sections: Scope / Line items / Questionnaire / Terms.

### 2. Response Inbox
Supplier cards/table with:
- response status
- source formats
- line coverage
- extraction status
- exception count
- data-quality indicator

### 3. Review & Normalize Workspace
Main comparison grid plus right-side exception queue.

Click any value -> Evidence Drawer:
- source preview with highlighted region
- extracted raw value
- normalization formula
- confidence
- buyer override history

### 4. Analysis Room
Left/center: conversational analyst.
Right: scenario cards and constraint summary.
Responses can render narrative, tables, charts, and export actions.

## Suggested stack

Prototype frontend:
- dependency-light HTML/CSS/JS served by FastAPI for one-service deployment and lower take-home risk

Production direction:
- Next.js + TypeScript
- Tailwind + shadcn/ui
- TanStack Table for large comparison grids
- Recharts for scenario visuals

Backend:
- FastAPI + Pydantic
- LangGraph for orchestration
- direct structured model calls inside graph nodes
- Docling for document/layout/table parsing
- native parsers for XLSX/DOCX/EML where useful
- OR-Tools for constrained scenario optimization

Data:
- Supabase Postgres
- Supabase Storage for source documents and previews
- pgvector only if semantic retrieval later becomes necessary

Deployment:
- Vercel frontend
- Railway/Render backend
- Supabase database/storage

## Why not a large multi-agent swarm?

The procurement workflow is mostly known. We should encode known control flow deterministically and use agents only where ambiguity genuinely exists. This improves trust, debugging, latency, and demo reliability.
