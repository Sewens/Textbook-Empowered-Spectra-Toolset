# Textbook Materials v1.0.0

This is the versioned precision-screened textbook material release used by the `materials` API.

## Scope

- 31 MinerU-parsed infrared spectroscopy textbooks
- `accepted/`: only candidates with direct naming evidence in a figure or table context
- `quarantine/`: excluded candidates with machine-readable rejection reasons
- Every accepted source record retains textbook title, page/locator, bounding box, original evidence text, and relative image path.

## Layout

- `accepted/_compound_catalog.json`: deduplicated material browse catalog
- `accepted/_group_catalog.json`: deduplicated related-group catalog
- `accepted/_spectrum_catalog.json`: deduplicated spectrum catalog
- `accepted/<book>/material_spectra.json`: book-native records and evidence
- `quarantine/rejected_material_candidates.json`: audit partition
- `manifest.json`: release contract and counts
- `SHA256SUMS.txt`: integrity checksums

## Reproduce

Run `python scripts/build_accepted_material_catalog.py`, then
`python scripts/package_textbook_material_release.py` from the repository root.

Source textbook images remain in the configured MinerU output root and are referenced by validated relative paths; this release does not redistribute the original textbook assets.
