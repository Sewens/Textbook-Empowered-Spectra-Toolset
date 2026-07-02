# Scripts

Quick-start helpers for local demos and CLAS-GPU deployment.

## Local demo on Windows

Run from Windows Explorer or a terminal:

```bat
scripts\start_local_demo.bat
scripts\status_local_demo.bat
scripts\stop_local_demo.bat
```

Default local URLs:

- Frontend: http://127.0.0.1:5174/
- Backend health: http://127.0.0.1:8001/health
- Backend docs: http://127.0.0.1:8001/docs

`start_local_demo.bat` opens two tracked console windows: one for FastAPI and one for Vite. It also clears inherited `PYTHONPATH` / `VIRTUAL_ENV` so the backend uses `backend/.venv` instead of the Hermes agent environment.

## OpenDesign preview only

```bat
scripts\start_preview_static.bat
```

URL: http://127.0.0.1:5175/index.html

This serves `od-prototype/preview/index.html` as a static editable OpenDesign preview. It can fall back to built-in sample data if the backend is not running.

## Bash wrappers from Hermes/WSL

```bash
bash scripts/start_local_demo.sh
bash scripts/status_local_demo.sh
bash scripts/stop_local_demo.sh
```

The wrappers call the Windows `.bat` files because this project uses Windows Node/npm and Windows uv for the local demo.

## CLAS-GPU remote full-stack service

Run on CLAS-GPU from the repo root:

```bash
bash scripts/run_remote_20000.sh
bash scripts/status_remote_20000.sh
bash scripts/stop_remote_20000.sh
```

For durable deployment, run `run_remote_20000.sh` inside a `tmux` session such as `spectra_toolset_20000`. The full-stack app serves the built frontend from `frontend/dist` through FastAPI using `scripts/serve_fullstack.py`.
