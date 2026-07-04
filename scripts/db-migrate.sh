#!/usr/bin/env bash
set -Eeuo pipefail

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
}

require_env DATABASE_URL

if ! command -v alembic >/dev/null 2>&1; then
  echo "alembic is not installed; run 'make install' first." >&2
  exit 1
fi

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."
