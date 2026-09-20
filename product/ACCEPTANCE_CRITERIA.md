# Acceptance Criteria

## MUST - assignment-critical

### RFx creation
- [ ] Buyer can describe the sourcing need in natural language.
- [ ] System returns a structured RFx draft, questionnaire and commercial terms.
- [ ] Buyer approval is required before release/send.
- [ ] 30-line corrugated packaging event is preserved.

### Supplier response collection
- [ ] UI shows all five vendors and their response format/status.
- [ ] Source files are openable from the app.
- [ ] Supplier is not required to follow a common template.

### Extraction
- [ ] XLSX path reads source natively.
- [ ] DOCX path reads source natively.
- [ ] PDF path reads tables/narrative/footnote evidence.
- [ ] EML path reads email body and claims.
- [ ] JPG/photo uses a real multimodal extraction path in the final configured demo.
- [ ] Missing/unclear values are not invented.
- [ ] Extraction exposes confidence and source evidence.

### Normalization
- [ ] INR/USD conversion is deterministic and assumption is visible.
- [ ] `/100`, carton, bundle and kg conversions are deterministic.
- [ ] Freight treatment is explicit.
- [ ] Missing quote remains `Not quoted`, never zero.
- [ ] Raw values are retained separately from normalized values.

### Qualification
- [ ] Mandatory questionnaire failure can exclude a supplier.
- [ ] Pending/expired evidence is visible separately from pass/fail.
- [ ] Scenario filtering can require qualified suppliers only.

### Exceptions
- [ ] System visibly surfaces at least one low-confidence visual extraction.
- [ ] System visibly surfaces missing quote lines.
- [ ] System visibly surfaces a conditional commercial term/rebate.
- [ ] System visibly surfaces unresolved freight/prior-year/pack assumptions when applicable.
- [ ] Buyer can resolve at least one exception from UI.
- [ ] Original source fact remains auditable after a correction.

### Evidence / trust
- [ ] Clicking a comparison value opens a `Why this number?` view.
- [ ] Drawer shows source artifact and precise location when available.
- [ ] Drawer shows source text/value.
- [ ] Drawer shows normalization/conversion steps.
- [ ] Drawer shows confidence/extraction method.
- [ ] Human override is shown if applicable.

### Scenario analysis
- [ ] Buyer can ask a plain-language scenario question.
- [ ] AI returns a strict ScenarioSpec, not a numeric award.
- [ ] Deterministic solver computes award.
- [ ] `Cheapest qualified supplier per line` works.
- [ ] `No supplier above 45%/55% of spend` works.
- [ ] delivery-day constraint works.
- [ ] infeasible scenario is reported, not silently relaxed.
- [ ] result shows applied constraints, award total, vendor mix and per-line allocation.

### Reproducibility
- [ ] Scenario stores dataset version.
- [ ] A material buyer correction increments dataset version.
- [ ] Previous scenario remains viewable/reproducible.
- [ ] Previous scenario becomes `stale` against the new dataset and can be recomputed.

### Reliability
- [ ] `python verify_demo.py` passes.
- [ ] clean environment setup works from README.
- [ ] no API key is committed.
- [ ] app handles absent model key gracefully.

## SHOULD - strong differentiators

- [ ] Exception priority reflects commercial exposure, not confidence alone.
- [ ] Supplier clarification can be drafted and linked to an exception.
- [ ] Image/PDF evidence includes a highlighted region/crop.
- [ ] Scenario result notes unresolved assumptions that materially affect confidence.
- [ ] Analysis can export a decision-ready table/report.
- [ ] Buyer can filter comparison by qualified/unqualified/pending.

## NICE TO HAVE - only after MUST/SHOULD

- [ ] Supplier discovery.
- [ ] Negotiation agent.
- [ ] real email transport.
- [ ] authentication/RBAC.
- [ ] ERP integration.
