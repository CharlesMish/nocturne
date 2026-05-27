#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 install.py "$@"
echo
echo "Done. You can close this window."
read -r -p "Press Return to exit… " _ || true
