# Spectroscopy Backend

FastAPI backend for the Textbook-Empowered-Spectra-Toolset repository.

## Local uv workflow

Run from the repository root or backend directory:

    cd backend
    uv sync
    uv run pytest -q
    uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

The default data source is the repository-local immutable release:

    ../raw_data/basic_groups_v07_20260619
    ../raw_data/docs/ir_ie_v07_core_data_model_v20260622.summary.json

Override with environment variables when needed:

    RELEASE_PATH=/path/to/basic_groups_v07_20260619     DOCS_SUMMARY_PATH=/path/to/ir_ie_v07_core_data_model_v20260622.summary.json     uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

## Local RBAC

This migration includes a development RBAC boundary driven by the X-User-Role request header.
If no header is supplied, requests run as ordinary_user.

| Role | Header value | Scope |
| --- | --- | --- |
| 普通用户 | ordinary_user | Read-only knowledge browsing and search |
| 数据管理员 | data_admin | Read access plus analysis/extraction data operations |
| 网站管理员 | site_admin | Data admin plus user/role/site management |

Examples:

    curl http://127.0.0.1:8000/api/user/me
    curl -H 'X-User-Role: site_admin' http://127.0.0.1:8000/api/user/roles
