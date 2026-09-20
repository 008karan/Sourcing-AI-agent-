# Build status - Sourcing Decision Room

## North-star flow

RFx creation -> vendor response collection -> extraction -> normalization -> exception review -> evidence-backed comparison -> scenario analysis

Supplier Discovery and Negotiation are deliberately deferred until this path is trustworthy end to end.

## Stage 1 - Domain harness and adversarial test data - DONE

- 30-line FY27 corrugated-packaging RFx, ~INR 4.1 Cr baseline spend.
- 8-question qualification questionnaire.
- Five fictional supplier responses in XLSX, PDF, DOCX, angled JPG and EML.
- Designed edge cases: USD/INR, per-piece/per-100/per-carton/per-bundle/per-kg, partial 27/30 quote, conditional footnote rebate, certificate expiry, failed mandatory quality gate, visual ambiguity, `same as last year`, freight included vs extra.
- Canonical ground truth and evidence pointers for regression testing.

## Stage 2 - Product/UI harness - DONE

Four buyer-facing spaces:
1. RFx Builder
2. Response Inbox
3. Review & Compare + Exception Inbox
4. Analysis Room

Trust is contextual rather than hidden in an audit page. Every comparison/scenario quote cell can open an Evidence Drawer showing source, confidence and normalization trace.

## Stage 3 - Hybrid extraction and deterministic normalization - DONE for native paths

Native parsers implemented for:
- XLSX: sheets/cells preserved.
- PDF: tables + narrative/footnotes parsed with `pdfplumber`.
- DOCX: table rows + narrative parsed.
- EML: body parsed and line claims extracted.
- JPG: deliberately routes to multimodal model path.

117 supplier-line quote cells are natively parsed and normalized. `verify_demo.py` checks every one against the generated truth within INR 0.02.

Normalization owns arithmetic:
- USD -> INR
- /100 -> /piece
- carton/bundle pack-size conversion
- INR/kg × RFx unit weight -> INR/piece
- freight additions
- prior-year baseline resolution

## Stage 4 - AI contracts - CODED, model execution requires API key

- RFx Copilot: buyer intent -> structured RFx draft + buyer-review points.
- Extraction/Mapping Specialist: supplier artifact -> structured quote lines, commercial terms, questionnaire answers and unresolved ambiguities.
- Scenario Analyst: natural-language question -> strict ScenarioSpec only.

Model outputs never calculate award values. With no API key, the demo uses transparent local fallbacks and seeded truth; with `OPENAI_API_KEY`, the structured model loops are enabled.

## Stage 5 - Deterministic award scenario engine - DONE

SciPy MILP solver supports:
- minimize landed cost
- qualification filter
- maximum supplier award-spend share
- max delivery days
- excluded/required suppliers
- missing-quote policy

Tests prove a 45% supplier cap is respected and that constrained scenarios cannot be cheaper than the unconstrained optimum.

## Stage 6 - Workflow persistence / human resolution - NEXT

- Wire the existing LangGraph blueprint into execution.
- Persist event/fact/evidence/scenario versions in Postgres/Supabase.
- Buyer actions on exceptions: accept, edit, remap, exclude, request clarification.
- Recompute only impacted normalization/scenarios after a correction.

## Stage 7 - Supplier clarification loop - NEXT

For missing/ambiguous commercial facts:
- system drafts supplier clarification
- buyer approves send
- incoming reply links to the open exception
- extraction reruns only for that supplier/field

## Later

- Supplier Discovery
- Negotiation Agent
- ERP/PO integrations
