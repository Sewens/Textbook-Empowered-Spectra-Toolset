#!/usr/bin/env bash
set -euo pipefail
SESSION="${1:-spectra_toolset_20000}"
tmux kill-session -t "$SESSION" 2>/dev/null || true
echo "Stopped tmux session if it existed: $SESSION"
