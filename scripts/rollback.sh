#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:-staging}"
ROLLBACK_IMAGE="${ROLLBACK_IMAGE:-}"

if [[ "${ENVIRONMENT}" != "dev" && "${ENVIRONMENT}" != "staging" && "${ENVIRONMENT}" != "prod" ]]; then
  echo "Usage: $0 [dev|staging|prod]" >&2
  exit 1
fi

if [[ -z "${ROLLBACK_IMAGE}" ]]; then
  echo "Missing ROLLBACK_IMAGE. Set it to the known-good container image digest." >&2
  exit 1
fi

if [[ "${ENVIRONMENT}" == "prod" && "${CONFIRM_PRODUCTION_ROLLBACK:-}" != "yes" ]]; then
  echo "Refusing production rollback without CONFIRM_PRODUCTION_ROLLBACK=yes" >&2
  exit 1
fi

echo "TODO: Wire Cloud Run rollback to ${ROLLBACK_IMAGE} for ${ENVIRONMENT}."
echo "Rollback preflight passed."
