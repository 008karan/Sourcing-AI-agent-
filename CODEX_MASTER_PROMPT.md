# Master continuation prompt for Codex

You are continuing an existing prototype for the Aerchain Product Manager take-home assignment. Do **not** start by redesigning or rewriting the project. Inspect and run the current repository first, preserve what works, and iterate in small verified steps.

## Assignment goal

Build a working live-demo prototype for:

**RFx creation -> vendor response collection -> heterogeneous supplier extraction -> canonical normalization -> exception review + provenance -> natural-language scenario analysis -> defensible award decision**

The supplier must not be forced into a buyer template. Five vendors respond in intentionally different formats. The assignment specifically values ugly edges such as partial quotes, different currencies/UOMs, angled photos and uncertainty.

## Product thesis

The product is not a quote extractor. It is an auditable procurement decision system.

Hard product rules:

1. Missing values are never converted to zero.
2. No normalized commercial value without a source evidence reference.
3. A raw source fact and its normalized fact are separate/versioned records.
4. No unit/currency/pack conversion without an explicit deterministic rule or buyer-approved assumption.
5. Unknown freight/tax/discount remains unknown or excluded explicitly; do not silently infer it.
6. Every AI-extracted fact has confidence + extraction method.
7. Important uncertain facts become exceptions based on uncertainty × financial exposure × decision relevance.
8. The application must be able to say "I don't know" and request review/clarification.
9. AI interprets ambiguity and buyer language; deterministic code performs arithmetic, qualification and award optimization.
10. Every scenario stores its exact constraints and dataset version.
11. Editing a fact creates a new version/audit event. Old scenarios remain reproducible and become visibly stale if the dataset changes.
12. Buyer overrides are explicit and attributable.

## Current technical baseline

- Backend: FastAPI + Pydantic
- Frontend: lightweight HTML/CSS/JS served by FastAPI
- Native parsers: openpyxl, python-docx, pdfplumber, email parser
- Optimization: SciPy MILP
- AI contracts: OpenAI Responses API structured JSON outputs
- Workflow blueprint: LangGraph file exists but is not yet wired to persisted execution
- Optional future extraction/layout dependency: Docling

Do not introduce multiple orchestration frameworks. If wiring workflow execution, use LangGraph as the one orchestration layer. It should carry orchestration IDs/status/retry/human-review state, not become the procurement database.

## Source of truth

Inspect:
- `assignment/Aerchain-Product-Assignment.pdf`
- `prototype/docs/architecture.md`
- `prototype/docs/data-model.md`
- `prototype/docs/build-status.md`
- `product/PRODUCT_SPEC.md`
- `product/IMPLEMENTATION_PLAN.md`
- `product/ACCEPTANCE_CRITERIA.md`
- `vendor-test-pack/manifest.json`
- `vendor-test-pack/normalized_truth.csv`

## Dataset

Category: corrugated packaging.

Five fictional vendors intentionally cover:
- XLSX: complete but ignores buyer template; mixed per-piece / per-100-piece pricing.
- PDF: USD / 100 pcs; conditional 3% rebate in a footnote.
- DOCX: 27/30 lines; mixed carton/each; freight extra; expiring certificate.
- JPG: angled phone photo; bundle units; obscured high-impact rate; mandatory FSC failure.
- EML: INR/kg; `same as last year`; percentage freight.

Do not sanitize these fixtures. They are the test harness.

## Build priorities - execute in this order

### P0 - preserve and verify current build
- Run `python verify_demo.py`.
- Run app and manually inspect the four main screens.
- Do not proceed if current regression checks fail.

### P1 - human exception resolution
Implement buyer actions on an exception:
- Accept extraction
- Correct value
- Remap RFx line
- Correct conversion/pack size
- Mark not quoted
- Exclude from comparison
- Request supplier clarification

Requirements:
- create a new fact/version rather than mutating historical truth invisibly
- write an audit event
- recompute only affected normalized values
- increment dataset version
- mark impacted scenarios stale
- retain prior scenario results for reproducibility

### P2 - persistence + workflow state
Use a lightweight local persistence layer first if needed (SQLite is acceptable for the take-home), with clean interfaces that can later map to Postgres/Supabase.
Persist:
- sourcing event
- RFx versions
- supplier responses/documents
- extracted fact versions
- evidence refs
- normalized quote-line versions
- exceptions
- buyer resolutions/overrides
- dataset versions
- scenarios/results
- workflow runs

Then wire the existing LangGraph blueprint for:
- RFx approval interrupt
- parallel supplier intake
- exception gate
- human-review interrupt
- ready-for-analysis state

### P3 - real extraction loop
Run real AI extraction with structured outputs for:
- the JPG/photo fixture (mandatory)
- at least one PDF/paragraph ambiguity or conditional term (recommended)

Keep native-first routing. Use multimodal AI only where it improves interpretation.
Do not let the model normalize prices or calculate awards.

### P4 - clarification loop
For missing/uncertain fields:
- draft a supplier clarification message
- buyer reviews/approves it
- simulate send
- simulate or capture reply
- link reply to the open exception
- re-extract only affected supplier/field
- close exception once evidence is sufficient

SMTP can remain fake/stubbed.

### P5 - evidence UX hardening
From every decision-relevant number:
- one-click evidence drawer
- source artifact name
- page/sheet/cell/paragraph/email span where available
- source text
- extraction confidence/method
- normalization steps
- buyer override if applicable
- original-source preview or highlighted crop where practical

### P6 - scenario reliability
Natural-language question -> strict ScenarioSpec -> validate -> deterministic MILP -> explanation.

Support at minimum:
- cheapest qualified supplier per line
- cheapest split award among qualified suppliers
- max supplier spend share (e.g. 45%, 55%)
- max delivery days
- explicit supplier exclusion/requirement if easy
- infeasible constraints with a clear explanation; never silently relax constraints

Scenario result should expose:
- award total
- savings vs buyer baseline
- vendor mix/share
- per-line allocation
- constraints applied
- dataset version
- qualification assumptions
- unresolved commercial assumptions/exceptions that affect confidence

### P7 - UI/demo polish
Keep the four primary spaces:
1. RFx Builder
2. Response Inbox
3. Review & Compare
4. Analysis Room

Focus on buyer comprehension, not enterprise UI density.
Ensure ugly states are visible and actionable.

## Final demo narrative

1. Buyer describes the sourcing event; AI drafts RFx, buyer remains approval gate.
2. Show five suppliers responding in completely different formats.
3. Show response ingestion and coverage, including partial/messy responses.
4. Open Review & Compare; demonstrate `Not quoted`, failed qualification, pending data.
5. Click a price and show exact source + transformation trace.
6. Resolve one high-impact exception or demonstrate clarification.
7. Ask a scenario question in natural language.
8. Show deterministic award result + constraints + evidence.
9. Change/correct a fact and show prior scenario becoming stale/recomputable if implemented.
10. Close with: extraction is becoming table stakes; the trust layer between extraction and award is the differentiator.

## Definition of done

The build is demo-ready only when every MUST criterion in `product/ACCEPTANCE_CRITERIA.md` passes, `python verify_demo.py` passes, the application runs from a clean setup, and there is a reliable 5-7 minute walkthrough without developer-only explanations.
