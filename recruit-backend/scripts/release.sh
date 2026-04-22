#!/usr/bin/env bash
# One-off migration runner. Idempotent.
# Railway calls this via preDeployCommand (see railway.toml).
# Manual invocation: `railway run ./scripts/release.sh`
set -euo pipefail

echo "[release] Python: $(python --version)"
echo "[release] alembic current:"
alembic current
echo "[release] alembic upgrade head"
alembic upgrade head
echo "[release] done"
