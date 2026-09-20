# Aerchain Take-Home - Codex Handoff

This bundle is the continuation package for the Aerchain Product Manager take-home: **"Kill the Quote Spreadsheet."**

## Objective

Finish a live-demo-ready prototype for this flow:

**RFx creation -> vendor response collection -> extraction -> normalization -> exceptions + evidence -> scenario analysis**

Supplier Discovery and Negotiation are explicitly **deferred until the core loop is excellent**.

The assignment rewards the ugly edges, trust, judgment and taste. It explicitly allows plumbing such as SMTP to be stubbed, but the AI extraction/reasoning loops must be real.

## Product thesis

Do not build a generic "upload documents and chat" demo.

Build a **Sourcing Decision Room** where suppliers can respond in whatever format they already use, while the buyer receives a normalized, auditable, decision-ready comparison.

The key differentiation is not extraction alone. It is:

1. **Source provenance** for every commercial fact.
2. **Explicit transformation trace** from raw quote to comparable landed price.
3. **Visible uncertainty** instead of silent assumptions.
4. **Risk-based exception handling**.
5. **Deterministic scenario calculations** after AI interprets the buyer's intent.
6. **Reproducible award decisions** tied to the dataset version and constraints.

## Start here in Codex

1. Read `CODEX_MASTER_PROMPT.md`.
2. Read the original brief in `assignment/Aerchain-Product-Assignment.pdf`.
3. Inspect `prototype/README.md`, `prototype/docs/architecture.md`, `prototype/docs/data-model.md`, and `product/IMPLEMENTATION_PLAN.md`.
4. Run the current app before changing architecture:

```bash
cd prototype
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python verify_demo.py
python run_demo.py
```

Open `http://127.0.0.1:8000`.

5. Set `OPENAI_API_KEY` only when testing the real model loops. The app is intentionally runnable without a key in transparent fallback mode.

## What already exists

- 30-line corrugated-packaging RFx (~INR 4.1 Cr baseline spend)
- 8-question qualification questionnaire
- five intentionally messy supplier response files
- native XLSX/PDF/DOCX/EML extraction paths
- multimodal extraction contract for the JPG/photo path
- deterministic unit/currency/freight normalization
- evidence trace and evidence drawer
- exception inbox concept
- qualification states
- mixed-integer award solver
- natural-language -> ScenarioSpec contract
- four-screen buyer UI
- regression truth dataset
- verification script

## Highest-priority remaining work

1. Human exception resolution and source-fact versioning.
2. Persistent workflow state / dataset versioning.
3. Wire LangGraph blueprint to actual execution + review interrupts.
4. Supplier clarification loop for missing/ambiguous fields.
5. Run and harden real AI extraction on the photo and at least one ambiguous text/PDF case.
6. Improve evidence preview so source regions are highlighted wherever practical.
7. Add scenario audit trail and stale-scenario detection after buyer corrections.
8. Final UI polish, error states and demo reliability.
9. Prepare the final one-page/PPT and Loom script only after the product loop is stable.

## Do not waste the take-home window on

- real SMTP infrastructure
- authentication / RBAC
- ERP/PO integration
- supplier discovery
- autonomous negotiation
- rebuilding the frontend framework solely for architectural purity
- excessive multi-agent choreography
- a graph database

The current app is a working FastAPI + lightweight frontend prototype. Improve it before considering a rewrite.
