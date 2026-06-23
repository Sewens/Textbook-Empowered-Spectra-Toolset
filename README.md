# IR-IE Spectra Platform Repository Skill

This package is a minimal repo-aligned skill for a React + Python IR/IE spectroscopy data platform.
It is designed for the current root layout:

```text
.git/
docs/
  dev_docs/
  site_docs/
od-prototype/
raw_data/
```

## Install

Unzip this package at the repository root. It is safe to merge with existing `docs/`, `od-prototype/`, and `raw_data/` directories.

Then tell your local coding agent:

```text
Read AGENTS.md first. Then read docs/dev_docs/agent_skill/SKILL.md only.
Do not load full raw_data unless the task is a schema/database/API task.
```

For OpenDesign, run it from `od-prototype/` so it reads `od-prototype/SKILL.md`.

## Minimal workflow

1. Prototype UI in `od-prototype/`.
2. Store internal design/dev notes in `docs/dev_docs/`.
3. Store user-facing site content in `docs/site_docs/`.
4. Keep raw extracted data immutable in `raw_data/`.
5. Implement production code in `backend/` and `frontend/` when those folders are created.

## Important

The compact data contract lives at:

```text
docs/dev_docs/agent_skill/data_contract.min.json
```

The full source data model files should stay in:

```text
raw_data/ir_ie_v07_core_data_model_v20260622.md
raw_data/ir_ie_v07_core_data_model_v20260622.summary.json
```
