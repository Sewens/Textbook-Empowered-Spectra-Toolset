#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAT_WIN=$(python3 - <<'PY' "$SCRIPT_DIR/stop_local_demo.bat"
import sys
from pathlib import Path
p = Path(sys.argv[1]).resolve()
print(str(p).replace('/mnt/c/', 'C:/').replace('/', '\\'))
PY
)
/mnt/c/Windows/System32/cmd.exe /c "$BAT_WIN"
