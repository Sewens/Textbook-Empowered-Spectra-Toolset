# OpenDesign Brief — Spectrum Detail

Feature: Spectrum viewer and peak assignments

Primary entity: spectrum

Layout:

- Header: compound, group, source book, schema version
- Main: spectrum image/chart area
- Table: peaks and assignments
- Inspector: evidence spans and related source claims

Key fields:

- spectrum_id
- figure_id
- image_path
- peaks[].wavenumber_cm_1
- assignments[].assignment_text
- assignments[].assignment_confidence
- evidence_ids

RBAC:

- reader: view only
- curator: create/edit extracted assignment draft
- reviewer: approve/reject claims
