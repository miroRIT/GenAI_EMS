#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:-staging}"
ROLLBACK_IMAGE="${ROLLBACK_IMAGE:-}"
GCP_PROJECT_ID="${GCP_PROJECT_ID:-}"
GCP_REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-emergencypulse-${ENVIRONMENT}-api}"

if [[ "${ENVIRONMENT}" != "dev" && "${ENVIRONMENT}" != "staging" && "${ENVIRONMENT}" != "prod" ]]; then
  echo "Usage: $0 [dev|staging|prod]" >&2
  exit 1
fi

if [[ -z "${ROLLBACK_IMAGE}" ]]; then
  echo "Missing ROLLBACK_IMAGE. Set it to the known-good container image digest." >&2
  exit 1
fi

if [[ -z "${GCP_PROJECT_ID}" ]]; then
  echo "Missing GCP_PROJECT_ID." >&2
  exit 1
fi

if [[ "${ENVIRONMENT}" == "prod" && "${CONFIRM_PRODUCTION_ROLLBACK:-}" != "yes" ]]; then
  echo "Refusing production rollback without CONFIRM_PRODUCTION_ROLLBACK=yes" >&2
  exit 1
fi

echo "Rolling ${SERVICE_NAME} in ${ENVIRONMENT} back to ${ROLLBACK_IMAGE}..."
gcloud run services update "${SERVICE_NAME}" \
  --project="${GCP_PROJECT_ID}" \
  --region="${GCP_REGION}" \
  --image="${ROLLBACK_IMAGE}"
echo "Rollback complete."
