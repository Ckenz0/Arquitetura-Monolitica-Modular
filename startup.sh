#!/usr/bin/env bash
set -euo pipefail

exec python -m waitress \
  --host=0.0.0.0 \
  --port="${PORT:-8000}" \
  --threads=4 \
  --max-request-body-size=1048576 \
  --call server.app:create_app
