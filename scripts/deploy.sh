#!/usr/bin/env bash
set -Eeuo pipefail

ENVIRONMENT="${1:-staging}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

GCP_REGION="${GCP_REGION:-us-central1}"
ARTIFACT_REPOSITORY="${ARTIFACT_REPOSITORY:-emergencypulse}"
BUILD_STRATEGY="${BUILD_STRATEGY:-cloudbuild}"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "${ROOT_DIR}" rev-parse --short HEAD)}"
IMAGE_URI=""

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
}

require_command() {
  local name="$1"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "Missing required command: ${name}" >&2
    exit 1
  fi
}

case "${ENVIRONMENT}" in
  dev|staging|prod) ;;
  *) echo "Usage: $0 [dev|staging|prod]" >&2; exit 1 ;;
esac

require_env GCP_PROJECT_ID
require_env JWT_SECRET
require_env ADMIN_PASSWORD_HASH
require_command gcloud
require_command terraform
require_command curl

if [[ "${BUILD_STRATEGY}" == "docker" ]]; then
  require_command docker
fi

if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]] \
  && ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
  echo "No active gcloud credentials found. Authenticate with gcloud or Workload Identity." >&2
  exit 1
fi

if [[ "${ENVIRONMENT}" == "prod" && "${CONFIRM_PRODUCTION_DEPLOY:-}" != "yes" ]]; then
  echo "Refusing production deploy without CONFIRM_PRODUCTION_DEPLOY=yes" >&2
  exit 1
fi

export TF_VAR_project_id="${GCP_PROJECT_ID}"
export TF_VAR_region="${GCP_REGION}"
export TF_VAR_artifact_repository="${ARTIFACT_REPOSITORY}"
export TF_VAR_image_tag="${IMAGE_TAG}"
IMAGE_URI="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REPOSITORY}/api:${IMAGE_TAG}"

cd "${ROOT_DIR}"

echo "Deploying EmergencyPulse ${IMAGE_TAG} to ${ENVIRONMENT} in ${GCP_PROJECT_ID}/${GCP_REGION}"
echo "Image: ${IMAGE_URI}"

terraform -chdir="infra/envs/${ENVIRONMENT}" init

echo "Creating/enabling prerequisite GCP services and Artifact Registry..."
terraform -chdir="infra/envs/${ENVIRONMENT}" apply -auto-approve \
  -target=google_project_service.required \
  -target=google_artifact_registry_repository.api \
  -target=google_secret_manager_secret.jwt_secret \
  -target=google_secret_manager_secret.admin_password_hash

echo "Publishing runtime secret versions..."
printf "%s" "${JWT_SECRET}" | gcloud secrets versions add "emergencypulse-${ENVIRONMENT}-jwt-secret" \
  --project="${GCP_PROJECT_ID}" \
  --data-file=-
printf "%s" "${ADMIN_PASSWORD_HASH}" \
  | gcloud secrets versions add "emergencypulse-${ENVIRONMENT}-admin-password-hash" \
    --project="${GCP_PROJECT_ID}" \
    --data-file=-

echo "Building and pushing container image..."
if [[ "${BUILD_STRATEGY}" == "cloudbuild" ]]; then
  gcloud builds submit "${ROOT_DIR}" \
    --project="${GCP_PROJECT_ID}" \
    --tag="${IMAGE_URI}"
elif [[ "${BUILD_STRATEGY}" == "docker" ]]; then
  gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet
  docker build -t "${IMAGE_URI}" "${ROOT_DIR}"
  docker push "${IMAGE_URI}"
else
  echo "Unsupported BUILD_STRATEGY: ${BUILD_STRATEGY}. Use cloudbuild or docker." >&2
  exit 1
fi

echo "Applying Terraform infrastructure..."
terraform -chdir="infra/envs/${ENVIRONMENT}" apply -auto-approve

MIGRATION_JOB="$(terraform -chdir="infra/envs/${ENVIRONMENT}" output -raw migration_job_name)"
API_URL="$(terraform -chdir="infra/envs/${ENVIRONMENT}" output -raw api_url)"

echo "Running database migrations through Cloud Run Job: ${MIGRATION_JOB}"
gcloud run jobs execute "${MIGRATION_JOB}" \
  --project="${GCP_PROJECT_ID}" \
  --region="${GCP_REGION}" \
  --wait

echo "Verifying service health at ${API_URL}/healthz"
curl --fail --show-error --silent "${API_URL}/healthz"
echo
echo "Deployment complete: ${API_URL}"
