#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:-staging}"
IMAGE_TAG="${IMAGE_TAG:-}"
ARTIFACT_REGISTRY="${ARTIFACT_REGISTRY:-}"

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
}

case "${ENVIRONMENT}" in
  dev|staging|prod) ;;
  *) echo "Usage: $0 [dev|staging|prod]" >&2; exit 1 ;;
esac

require_env GCP_PROJECT_ID
require_env DATABASE_URL
require_env JWT_SECRET

if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]] && ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
  echo "No active gcloud credentials found. Set GOOGLE_APPLICATION_CREDENTIALS or authenticate via Workload Identity/gcloud." >&2
  exit 1
fi

if [[ "${ENVIRONMENT}" == "prod" && "${CONFIRM_PRODUCTION_DEPLOY:-}" != "yes" ]]; then
  echo "Refusing production deploy without CONFIRM_PRODUCTION_DEPLOY=yes" >&2
  exit 1
fi

if [[ -z "${IMAGE_TAG}" ]]; then
  IMAGE_TAG="$(git rev-parse --short HEAD)"
fi

export TF_VAR_project_id="${TF_VAR_project_id:-${GCP_PROJECT_ID}}"
if [[ -n "${ARTIFACT_REGISTRY}" ]]; then
  export TF_VAR_image="${TF_VAR_image:-${ARTIFACT_REGISTRY}/${IMAGE_TAG}}"
fi

echo "Deploying EmergencyPulse ${IMAGE_TAG} to ${ENVIRONMENT}..."
terraform -chdir="infra/envs/${ENVIRONMENT}" init
terraform -chdir="infra/envs/${ENVIRONMENT}" apply -auto-approve
./scripts/db-migrate.sh
echo "TODO: Configure Cloud Run deploy command with your Artifact Registry URL."
echo "Deployment preflight and infrastructure apply complete."
