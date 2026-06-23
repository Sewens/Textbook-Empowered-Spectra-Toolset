# AGENTS.md — Repository Agent Entry Point

Read this file first. Then read `docs/dev_docs/agent_skill/SKILL.md`.

## Repo layout

```text
docs/dev_docs/     internal development docs, architecture, API notes, agent skill
docs/site_docs/    public/user-facing website docs and help content
od-prototype/      OpenDesign workspace only; not production React code
raw_data/          immutable extracted source data and schema summaries
backend/           Python/FastAPI backend, if present
frontend/          React/TypeScript frontend, if present
infra/             deployment files, if present
```

## Context budget rule

Default context is only:

1. `AGENTS.md`
2. `docs/dev_docs/agent_skill/SKILL.md`
3. task template provided by user
4. `docs/dev_docs/agent_skill/data_contract.min.json` only when data entities are involved

Do not load full `raw_data/*.md` or full source JSON files unless the task explicitly requires schema/database/API import details.

## Non-negotiable rules

- Backend authorization is the security boundary. Frontend RBAC only hides/disables UI.
- Raw extracted data is immutable. Never edit files in `raw_data/`; create derived migrations/import scripts instead.
- Schema changes must propagate: data contract -> DB migration -> ORM -> DTO -> API -> OpenAPI -> TS client -> React UI -> tests.
- OpenDesign prototypes stay in `od-prototype/`; production React code stays in `frontend/`.
- Use small diffs. Before coding, write a short plan; after coding, list changed files and tests.
