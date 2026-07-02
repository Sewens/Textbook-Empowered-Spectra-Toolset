from pathlib import Path
import sys

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DIST = ROOT / "frontend" / "dist"

sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402

if not DIST.exists():
    raise RuntimeError(f"Frontend dist not found: {DIST}")

# Keep API/static routes from backend first, then serve the built React app.
app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="frontend-assets")

@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    candidate = DIST / full_path
    if full_path and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(DIST / "index.html")
