# Aerchain — Sourcing Decision Room

## Snapshot and status

Packaged on 20 September 2026 at the user's request: **the whole implemented project as it stands**, not a claim that every planned feature or live test is complete. Start with this document. It supersedes older setup/status statements in the original handoff documents.

The current application uses **Google Gemini**, not OpenAI, for its AI operations. The configured default is `gemini-3.8-flash`. Native document parsing, normalization and award calculations remain deterministic code. The model interprets language and document ambiguity; it does not calculate the award.

No API keys, active runtime databases, uploaded session files, virtual environments or caches are included. The packaged app starts with a fresh event. Original fictional supplier fixtures, buyer reference, evaluation truth and source code are included.

## Start locally

Use Python 3.12 (the tested version), an internet connection for installation/live AI, and a Google Gemini API key with access to the configured model.

From the extracted project folder:

```sh
cd prototype
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_demo.py --prompt-key --port 8018
```

On Windows, activate with `.venv\Scripts\activate` instead. Enter the key at the hidden terminal prompt. It is held in the process environment, not saved by the application. Open **http://127.0.0.1:8018/**. If the port is occupied, choose another `--port`.

`requirements-snapshot.txt` records exact installed versions in the development environment; `requirements.txt` is the normal installation entry point. There is no Node build step: FastAPI serves the JavaScript/CSS frontend.

To run without AI, omit `--prompt-key` and ensure `GOOGLE_API_KEY` is unset. The UI explicitly identifies offline fallback. Native fixture extraction and structured optimization work; photo interpretation, generic document AI and voice transcription require Gemini. Offline operation is not a substitute for a live AI evaluation.

Configuration:

- `GOOGLE_API_KEY`: runtime secret; prefer the hidden prompt. Never commit a key or place one in source, screenshots, reports or a ZIP.
- `GEMINI_MODEL`: optional model override; defaults to `gemini-3.8-flash`. Model access and output compatibility depend on the account.
- `AERCHAIN_DATA_DIR`: optional data directory. Default is `prototype/runtime/`, created on first use.
- `.env.example` contains blank/example settings only. The launcher does **not** automatically load `.env` files.

This is a local single-user prototype, without production authentication or multi-tenant isolation. Keep it on localhost; do not expose it publicly.

## Implemented workflow

1. **RFx drafting:** a conversational text composer sends buyer intent to Gemini and displays structured scope, quality questions, commercial terms and review points. Buyer approval is required before simulated release.
2. **Supplier inbox:** load five demo messages, or paste a message and attach XLSX, DOCX, PDF, email/text or image files. Receipt and extraction are separate actions. Replacing a response invalidates its old facts.
3. **Extraction:** native parsers handle the known fixtures; non-template documents use native text blocks plus Gemini, with multimodal image/PDF support. Background jobs expose supplier-level processing stages.
4. **Normalization:** explicit currency, per-piece/per-100/carton/bundle/kg conversions, buyer item weights and freight rules produce landed INR rates excluding GST. Unknown or uncertain inputs are withheld.
5. **Evidence:** price cells open source excerpts, locations, transformation traces and original documents. PDF/image previews are inline; workbook/Word originals can be downloaded.
6. **Exception review:** approve justified prior-year assumptions, correct raw values, remap or exclude quotes, and record buyer identity/reason. Clarification drafts and simulated replies link to a review; replies do not silently alter an award.
7. **Scenario analysis:** Gemini turns a natural-language question into validated constraints. A deterministic whole-line optimizer computes costs, qualification/delivery eligibility and supplier-spend caps. Results include allocations, supplier mix, evidence references, history and CSV export.
8. **Persistence:** SQLite stores immutable dataset snapshots, audit records, scenarios and jobs. Changed data marks historical scenarios stale; historical versions can be replayed.
9. **Orchestration:** LangGraph with SQLite checkpoints enforces RFx approval, response collection, parallel supplier ingestion and human review interruptions.
10. **Voice:** browser recording and Gemini transcription populate a composer for user review. Microphone permission/browser support is required; this path has not been fully end-to-end tested.

## Try the demo

1. Build the RFx using the prefilled packaging brief; review it and choose **Approve & release RFx**. No external invitations are sent.
2. In **Responses**, choose **Load demo messages**, then **Extract & normalize**. Alternatively, use each supplier's **Add supplier response** and attach the corresponding file from `vendor-test-pack/`.
3. In **Review & Compare**, inspect a price and its source. Review the four GreenCarton prior-year references explicitly; missing values are not zeros. AlphaPack's obscured photo price must stay unresolved, and its mandatory FSC failure must exclude it from qualified-only awards.
4. In **Analysis Room**, ask “Cheapest qualified supplier per line”, “Qualified only, no supplier above 45% of award spend”, or “Qualified suppliers with delivery within 1 day”. The last should be infeasible.
5. Correct a quote with a reason, then open scenario history and recompute the stale scenario. Old versions remain available.

Only upload the actual supplier offer files, not `normalized_truth.csv` or `demo_state.json`. The latter are evaluation/legacy reference assets, not supplier evidence. The current runtime comparison is built from ingested facts, not loaded from the truth file.

### Five fictional supplier fixtures

| Supplier | Offer | Main test cases |
|---|---|---|
| PackRight | `vendor_a_packright_offer.xlsx` | 30 lines; piece and per-100 pricing |
| CorrPro | `vendor_b_corrpro_quote.pdf` | 30 lines; USD; conditional 3% rebate |
| BoxWorks | `vendor_c_boxworks_offer.docx` | 27 lines; carton pricing; freight extra; certificate renewal |
| AlphaPack | `vendor_d_alphapack_rate_card_photo.jpg` | Angled photo; bundle units; obscured price; FSC failure |
| GreenCarton | `vendor_e_greencarton_reply.eml` | INR/kg; freight 2%; four prior-year references |

## Test results and commands

Latest local verification at packaging:

- **21 automated tests passed** in 4.91 seconds; one dependency deprecation warning from Starlette/AnyIO.
- Legacy fixture regression passed: **117 native rates within INR 0.02** of truth; baseline approximately **INR 3.920 Cr** and 45% supplier-cap scenario approximately **INR 3.938 Cr**. The legacy script is a regression check, not proof of the current live UI workflow.
- Current **offline end-to-end evaluation: 35/35 checks passed**. See `prototype/evaluation-offline/EVALUATION_REPORT.md` and its JSON details. Photo extraction is deliberately not tested in offline mode.
- Latest **live Gemini run was incomplete**. Seventeen checks passed through RFx drafting, five ingestion branches, normalization, photo abstention, mandatory FSC failure and bundle extraction. The run then stopped during the additional direct PDF AI evaluation with an incomplete HTTP response (`http.client.IncompleteRead`). It did not reach live scenario/clarification checks and did not produce a complete Gemini report. Its saved AlphaPack output is in `prototype/evaluation-gemini/`. Do not interpret the partial output as a full pass.
- The redesigned UI was opened and RFx generation initiated, but complete browser acceptance testing of the new guided UI was not finished before this snapshot.
- `prototype/evaluation/` is a **historical OpenAI evaluation** from before the provider migration. It is retained for project completeness, not evidence that Gemini passed the same checks.

Run tests from `prototype/` with the virtual environment activated:

```sh
python -m pytest -q
python verify_demo.py
python evaluate.py --out evaluation-offline-new
python evaluate.py --live --prompt-key --out evaluation-gemini-new
```

The end-to-end evaluator uses an isolated temporary database and compares rates to `demo-data/generated/normalized_truth.csv`. Live tests make paid API calls and can take several minutes. Use a new output directory per run so partial outputs cannot be confused with an older complete report.

## Known gaps and next work

- Add retry/controlled error handling for truncated Gemini HTTP bodies (`IncompleteRead`); the current retry logic covers HTTP 429/selected 5xx, not this failure. Then rerun the complete live evaluation.
- Finish browser tests for manual attachments, processing/retry, exception correction, source previews, scenario errors/history, responsive layouts and voice recording/transcription.
- RFx drafting retains the supplied 30-item baseline and qualification IDs. Proposed questionnaire edits are advisory, not a general RFx schema editor.
- Native exact-fixture paths are tested more thoroughly than arbitrary supplier templates. Qualification checks supplier declarations, not certificate authenticity.
- Conditional rebates are displayed but not incorporated in optimization. Allocation is whole-line only. FX is a fixed buyer comparison assumption, not a live market rate.
- SMTP/invitations and supplier clarification replies are simulated. There is no live mailbox connector.
- All business writes conservatively create a new dataset version and may mark scenarios stale. Storage is a prototype snapshot implementation, not a production data platform.
- Correction validation, conflicting multi-attachment responses and generic document edge cases need broader hardening. Unknown freight can keep a quote blocked.
- Production security, user management, deployment, load testing and operational monitoring remain outside this delivered snapshot.

## Project map

```text
PROJECT.md                         Current setup/status (read first)
MANIFEST_SHA256.txt                 Fresh checksums for this package
assignment/                        Original assignment PDF
product/                           Original specification and plans
reference/                         Original research and historical screenshots
vendor-test-pack/                  Buyer workbook, five offers and evaluation truth
prototype/
  run_demo.py                      Local server; hidden runtime-key prompt
  requirements.txt                 App/test dependencies
  requirements-snapshot.txt        Installed dependency version snapshot
  backend/app/main.py              API and source-file endpoints
  backend/app/ai.py                Gemini structured output and transcription
  backend/app/pipeline.py          Intake, normalization, evidence and resolution
  backend/app/native_extractors.py Native fixture parsers
  backend/app/scenario.py          Validated constraints and optimizer
  backend/app/repository.py        Versioned SQLite business storage
  backend/app/graph.py             Durable LangGraph workflow
  backend/app/jobs.py              Background processing/progress
  frontend/                       Guided UI, comparison and evidence screens
  tests/test_workflow.py           Automated regression tests
  evaluate.py                     End-to-end evaluation and report generation
  verify_demo.py                  Original native-fixture regression
  demo-data/generated/            Runtime fixtures and evaluation references
  evaluation-offline/              Complete current offline evaluation
  evaluation-gemini/               Partial Gemini extraction artifact
  evaluation/                     Historical pre-migration OpenAI evaluation
  docs/ and _qa/                  Historical architecture notes/screenshots
```

`00_START_HERE.md`, `CODEX_MASTER_PROMPT.md`, `FILE_MAP.md`, original product documents, `prototype/README.md` and older architecture screenshots are preserved as historical context. Some still mention OpenAI, older version numbers or unfinished work that has since been implemented. Use this `PROJECT.md` and the actual source for current behavior. Install using `prototype/requirements.txt`, not the older backend `pyproject.toml` or optional-workflow list.

For a new clean test event, set `AERCHAIN_DATA_DIR` to a new directory rather than deleting an existing database. Preserve both SQLite databases and original uploads together if backing up a running instance. Do not share real supplier files without authorization; live extraction sends the selected content to Google Gemini.
