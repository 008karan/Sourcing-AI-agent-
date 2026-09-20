# Canonical Data Model v0.1

## Core entities

### SourcingEvent
- id
- name
- category
- description
- base_currency
- comparison_uom_policy
- baseline_type
- status
- dataset_version

### RfxLineItem
- id
- event_id
- line_no
- buyer_sku
- description
- specification
- annual_quantity
- requested_uom
- delivery_location
- required_by_date

### QuestionnaireQuestion
- id
- event_id
- section
- question
- answer_type
- required
- qualification_rule

### Supplier
- id
- legal_name
- short_name

### SupplierResponse
- id
- event_id
- supplier_id
- received_at
- channel
- status

### SourceDocument
- id
- response_id
- file_name
- mime_type
- storage_uri
- checksum
- parser_used
- parse_status

### ExtractedFact
Append-only fact produced from source evidence.

- id
- event_id
- supplier_id
- response_id
- document_id
- fact_type
- rfx_line_item_id (nullable until mapped)
- raw_label
- raw_value
- parsed_value
- raw_unit
- raw_currency
- confidence
- extraction_method
- evidence_id
- verification_status
- created_at

Typical fact types:
- quoted_unit_price
- quoted_quantity
- uom
- pack_size
- currency
- freight_term
- freight_amount
- tax_term
- discount
- lead_time
- payment_term
- moq
- questionnaire_answer

### EvidenceRef
- id
- document_id
- page_number
- bbox_json
- sheet_name
- cell_range
- paragraph_index
- body_start
- body_end
- source_text
- preview_uri

### NormalizedQuoteLine
Derived/versioned comparison row per supplier and RFx line.

- id
- dataset_version
- event_id
- supplier_id
- rfx_line_item_id
- quote_status
- normalized_unit_price
- normalized_uom
- normalized_currency
- landed_unit_cost
- total_extended_cost
- freight_status
- qualification_status
- confidence
- blocking_exception
- transformation_trace_json

### Exception
- id
- event_id
- supplier_id
- rfx_line_item_id
- fact_id
- type
- severity
- uncertainty_score
- estimated_financial_exposure
- priority_score
- title
- explanation
- status
- recommended_action
- resolved_by
- resolution_json

### Scenario
- id
- event_id
- dataset_version
- question_text
- scenario_spec_json
- status
- total_cost
- savings_vs_baseline
- assumptions_json
- created_at

### ScenarioAllocation
- id
- scenario_id
- rfx_line_item_id
- supplier_id
- allocated_quantity
- unit_cost
- extended_cost
- rationale_code

### AuditEvent
- id
- event_id
- actor_type
- actor_id
- action
- entity_type
- entity_id
- previous_value_json
- new_value_json
- timestamp

## Key invariant

`NormalizedQuoteLine` must be reproducible from versioned `ExtractedFact` records + explicit conversion/normalization rules. UI edits create audited corrections instead of silently mutating source evidence.
