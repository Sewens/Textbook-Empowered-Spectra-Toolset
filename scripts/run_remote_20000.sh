#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.pyenv/shims:$HOME/.pyenv/bin:$PATH"
cd /share/lawbda/Textbook-Empowered-Spectra-Toolset/backend
exec uv run python -m uvicorn scripts.serve_fullstack:app --app-dir .. --host 0.0.0.0 --port 20000
