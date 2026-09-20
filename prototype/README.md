# Aerchain Sourcing Decision Room - v0.3

Runnable evidence-backed procurement prototype for the Aerchain take-home assignment.

## Implemented flow

**RFx creation -> vendor response collection -> hybrid extraction -> deterministic normalization -> exceptions + evidence -> deterministic scenario analysis**

The bundled demo is a realistic 30-line corrugated-packaging sourcing event with ~INR 4.1 Cr baseline annual spend and five deliberately inconsistent supplier responses.

## Run

```bash
cd aerchain-sourcing-decision-room
pip install -r requirements.txt
python run_demo.py
```

Open `http://127.0.0.1:8000`.

The UI works without an API key using transparent local fallbacks plus the generated truth dataset. To enable the actual structured AI loops for RFx drafting, supplier extraction and scenario-intent compilation:

```bash
export GOOGLE_API_KEY="..."
python run_demo.py
# or, without leaving the key in your shell history:
python run_demo.py --prompt-key
```

## Verify the harness

```bash
python verify_demo.py
```

Current checks:
- 117 quote lines parsed natively across XLSX/PDF/DOCX/EML.
- All 117 normalize to within INR 0.02 of generated ground truth.
- 45% maximum supplier-spend constraint is enforced by the MILP solver.
- Constrained award cost is not lower than the unconstrained optimum.

## Supplier test set

| Supplier | Source | Coverage | What it tests |
|---|---|---:|---|
| PackRight Industries | XLSX | 30/30 | multi-sheet workbook; per-piece and per-100-piece |
| CorrPro International | PDF | 30/30 | USD; /100 pcs; DDP; conditional rebate buried in footnote |
| BoxWorks India Pvt Ltd | DOCX | 27/30 | missing lines; carton packs; freight extra; expiring certificate |
| AlphaPack Solutions | angled JPG | 30/30 | vision path; obscured rate; bundle units; mandatory quality failure |
| GreenCarton Co. | EML | 30/30 | INR/kg; prior-year references; percentage freight |

## What is real vs deliberately stubbed

Real:
- actual supplier artifacts in five formats
- native XLSX/PDF/DOCX/EML parsing
- multimodal/structured OpenAI extraction contract for ambiguous/visual inputs
- RFx Copilot structured-output contract
- deterministic normalization and evidence traces
- risk-prioritized exception UX
- evidence drawer back to original source
- mixed-integer award optimization
- natural-language -> ScenarioSpec AI contract
- buyer-facing UI

Stubbed for the take-home:
- SMTP/inbox plumbing
- production Postgres/Supabase persistence
- authentication
- ERP/PO integration

The LangGraph workflow blueprint remains in `backend/app/graph.py`; persistence + human-review execution is the next implementation stage.

## Useful docs

- `docs/architecture.md` - system boundaries and trust rules
- `docs/data-model.md` - canonical facts/evidence/scenario model
- `docs/build-status.md` - step-by-step build status
- `docs/one-page-note.md` - assignment decision note
- `docs/demo-walkthrough.md` - recommended live-demo sequence
- `demo-data/README.md` - adversarial supplier dataset
