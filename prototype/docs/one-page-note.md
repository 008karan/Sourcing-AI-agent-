# Product note - Kill the Quote Spreadsheet

## What I built

A buyer-facing **Sourcing Decision Room** for a 30-line, five-supplier corrugated-packaging RFx worth ~INR 4.1 Cr annually. Suppliers are not forced into a portal/template: the demo ingests an Excel workbook, a letterhead PDF, a Word quote, an angled phone photo and a terse email, then presents a normalized comparison and lets the buyer run award scenarios in natural language.

## Product thesis

The spreadsheet is not the hard problem. **Trustworthy normalization is.** Extraction alone is commodity functionality; the buyer needs to know which facts are reliable, how a number was transformed, what is still unknown, and whether a sourcing scenario is reproducible.

## Key decisions

**1. Supplier convenience over input conformity.** The system absorbs heterogeneous formats instead of requiring suppliers to adopt the buyer's template.

**2. Hybrid extraction rather than LLM-everything.** Excel, Word, email and parseable PDF tables are preserved natively; multimodal AI is used where semantic/layout ambiguity requires it. This reduces cost and preserves better source coordinates.

**3. Source fact != normalized fact.** Every commercial value retains the raw source evidence and an explicit transformation trace. A buyer can click any price and see the exact source plus steps such as `USD 23.51 / 100 pcs -> /100 -> × INR 83.20 = INR 19.56/piece`.

**4. The system is allowed to say “I don't know.”** Missing quote lines remain missing, not zero. Low-confidence visual fields, unresolved freight, prior-period references and conditional rebates become exceptions instead of silent assumptions.

**5. Review is risk-based.** Exceptions are prioritized by uncertainty × financial exposure × decision relevance rather than by confidence score alone.

**6. AI interprets; deterministic software decides.** AI drafts RFx content, maps messy supplier language and compiles plain-language questions into structured constraints. Currency/unit arithmetic, qualification gates and award optimization run in deterministic code.

**7. Evidence lives where the decision happens.** There is no separate “trust dashboard.” Evidence is one click away from a comparison value or scenario allocation.

## Deliberately left out

Real SMTP/inbox infrastructure, authentication, ERP/PO integrations, supplier discovery, autonomous negotiation and production persistence. The assignment permits plumbing to be stubbed; I spent the time on the risky loop: messy input -> auditable facts -> exceptions -> defensible sourcing decision.

## What I would build next

Persist versioned facts/evidence/scenarios, wire human-review interrupts into LangGraph, then add a supplier-clarification loop that resolves missing or ambiguous fields without forcing the buyer to manually chase and re-key responses.
