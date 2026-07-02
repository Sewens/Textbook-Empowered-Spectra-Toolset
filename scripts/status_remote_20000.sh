#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-20000}"
echo "=== tmux ==="
tmux ls 2>/dev/null | grep spectra_toolset || true
echo "=== socket ==="
ss -ltnp 2>/dev/null | grep ":$PORT" || true
echo "=== health ==="
curl -sS -i --max-time 5 "http://127.0.0.1:$PORT/health" | sed -n '1,12p' || true
echo "=== home ==="
curl -sS -o /tmp/spectra_home_probe -w "HTTP %{http_code} %{content_type}\n" --max-time 5 "http://127.0.0.1:$PORT/" || true
head -c 160 /tmp/spectra_home_probe 2>/dev/null | tr '\n' ' '; echo
