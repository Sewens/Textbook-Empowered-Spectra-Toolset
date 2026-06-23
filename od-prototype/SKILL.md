---
name: ir-ie-data-console-prototype
description: Minimal OpenDesign prototype skill for IR/IE spectroscopy data platform screens.
od:
  mode: prototype
  preview: ./preview/index.html
  design_system: data-lab-console
  inputs:
    - name: feature
      type: string
      required: true
    - name: entity
      type: string
      required: false
    - name: role
      type: string
      required: false
    - name: schema_version
      type: string
      required: false
---

# IR-IE Data Console Prototype

Design admin/data-console screens for a spectroscopy knowledge platform.

## Visual direction

- Dense but readable data-lab console.
- Left navigation + top context bar + main table/workbench + right inspector.
- Prefer neutral cards, clear table hierarchy, compact metadata, explicit evidence links.
- Always include states: loading, empty, error, forbidden, read-only, populated.

## Must represent

- Role-aware actions: hidden/disabled for insufficient permission.
- Schema version on data records when relevant.
- Evidence traceability: source book, quote, image/asset link.
- Spectroscopy fields: group, compound, spectrum, peak, assignment, wavenumber cm^-1.

## Prototype only

Do not create production React code here. Accepted prototypes are later implemented under `frontend/`.
