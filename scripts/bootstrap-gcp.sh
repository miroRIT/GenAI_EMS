#!/usr/bin/env bash
set -Eeuo pipefail

GCP_REGION="${GCP_REGION:-us-central1}"
ARTIFACT_REPOSITORY="${ARTIFACT_REPOSITORY:-emergencypulse}"

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

require_env GCP_PROJECT_ID
require_command gcloud

echo "Setting active project to ${GCP_PROJECT_ID}"
gcloud config set project "${GCP_PROJECT_ID}"

echo "Enabling required GCP APIs..."
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  compute.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  servicenetworking.googleapis.com \
  sqladmin.googleapis.com \
  --project="${GCP_PROJECT_ID}"

echo "Ensuring Artifact Registry repository exists..."
if ! gcloud artifacts repositories describe "${ARTIFACT_REPOSITORY}" \
  --project="${GCP_PROJECT_ID}" \
  --location="${GCP_REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${ARTIFACT_REPOSITORY}" \
    --project="${GCP_PROJECT_ID}" \
    --location="${GCP_REGION}" \
    --repository-format=DOCKER \
    --description="EmergencyPulse API container images"
fi

echo "Bootstrap complete."
