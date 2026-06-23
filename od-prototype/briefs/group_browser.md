# OpenDesign Brief — Functional Group Browser

Feature: Browse IR/IE functional group cards

Primary entity: functional_group_card

Screens:

1. Group list with filters
2. Group detail with vibrations, compounds, evidence
3. Right inspector for schema/version/quality metadata

Key fields:

- group_id
- name_zh / name_en
- smarts
- chemical_formula
- vibration_templates
- source_claims
- evidence_spans

States:

- loading
- empty search results
- forbidden
- read-only
- populated
