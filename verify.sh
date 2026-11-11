#!/usr/bin/env bash
# Rebuilds your service, sends it traffic and inspects its logs, metrics and traces. Run with: ./verify.sh
cd "$(dirname "$0")" || exit 1
command -v docker >/dev/null || { echo "docker is not installed." >&2; exit 1; }
exec python3 .lab/instrcheck.py
