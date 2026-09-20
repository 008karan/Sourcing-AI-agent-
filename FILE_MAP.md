# Bundle File Map

## Root
- `00_START_HERE.md` - first file to read
- `CODEX_MASTER_PROMPT.md` - paste/use as continuation instructions in Codex
- `FILE_MAP.md` - this map

## assignment/
- `Aerchain-Product-Assignment.pdf` - original two-page take-home brief

## prototype/
Current runnable v0.3 source.

Key files:
- `README.md` - setup/current capabilities
- `run_demo.py` - starts FastAPI app
- `verify_demo.py` - deterministic regression checks
- `backend/app/main.py` - API routes
- `backend/app/ai.py` - structured AI contracts
- `backend/app/native_extractors.py` - native extraction
- `backend/app/normalize.py` - deterministic normalization
- `backend/app/scenario.py` - award optimization
- `backend/app/graph.py` - LangGraph blueprint
- `frontend/` - current UI
- `demo-data/generated/` - full test event and ground truth
- `docs/` - architecture, data model, build status and demo notes

## product/
- `PRODUCT_SPEC.md` - product behavior and UX contract
- `IMPLEMENTATION_PLAN.md` - prioritized build plan
- `ACCEPTANCE_CRITERIA.md` - definition of done
- `DELIVERY_CHECKLIST.md` - final assignment submission checklist

## vendor-test-pack/
A standalone adversarial dataset containing:
- five supplier responses
- RFx reference workbook + JSON
- canonical demo state
- normalized truth CSV
- manifest

Use this to regression-test extraction/normalization independently of the UI.

## reference/screenshots/
Current UI reference images:
- RFx Builder
- Review & Compare
- Evidence Drawer
- Analysis Room

## reference/research/
- `COMPETITOR_NOTES.md` - market research and product implications
