# EmergencyPulse

EmergencyPulse is a production-shaped emergency ambulance routing and dispatch API. It optimizes ambulance assignment using patient severity, ambulance capability, traffic proxy, signal-delay proxy, and spatial distance, with clean service and repository boundaries so the routing engine can later be swapped for a full road-network engine.

## Assumptions

- GCP is the target cloud, using Cloud Run, Cloud SQL for PostgreSQL, Secret Manager, and Terraform.
- Local development uses Docker Compose with PostGIS.
- The included routing heuristic is intentionally deterministic and sub-second. Real traffic feeds, signal phase APIs, and road-network engines are future integrations.
- Default local credentials are for development only. Production secrets must be set through CI/GCP Secret Manager.

## Architecture Overview

- **API:** FastAPI, async SQLAlchemy, OpenAPI 3.0.3, JSON structured logging, global error handlers.
- **Domain:** Pydantic models for incidents, ambulances, coordinates, route plans, and dispatch decisions.
- **Service:** `RoutingService` scores available ambulances and persists the selected dispatch.
- **Repository:** SQLAlchemy repository isolates database access from dispatch logic.
- **Data:** PostgreSQL 16 + PostGIS, generated geography columns, GIST indexes.
- **Infrastructure:** Terraform modules for `network`, `database`, and `compute`.

Decision log:

- **FastAPI over Go:** faster team iteration, automatic OpenAPI, strong Pydantic validation, and sufficient latency headroom for async request handling.
- **PostGIS over plain PostgreSQL:** native spatial indexing and future route proximity queries.
- **Cloud Run over GKE initially:** lower operational overhead, fast autoscaling, and easy path to containerized microservices.
- **Terraform modules:** environment parity and safer review boundaries.

See [docs/architecture.md](/Users/aayush/Documents/Codex/2026-07-04/this-is-a-comprehensive-production-grade/docs/architecture.md) for the system diagram.

## Local Setup

Prerequisites:

- Python 3.12
- Docker and Docker Compose
- Terraform 1.7+
- GCP CLI for cloud deployments

Start the full local environment:

```bash
cp .env.example .env
make up
docker compose exec api alembic upgrade head
curl http://localhost:8080/healthz
```

Run locally without Docker for the API:

```bash
make install
docker compose up -d db
export DATABASE_URL=postgresql+asyncpg://emergencypulse:emergencypulse@localhost:5432/emergencypulse
make migrate
make run
```

Useful commands:

```bash
make lint
make test
make test-integration
make docker-build
make terraform-validate
```

## API Usage

The service exposes interactive Swagger/OpenAPI docs at:

- `http://localhost:8080/docs`
- `http://localhost:8080/swagger`
- Raw OpenAPI JSON: `http://localhost:8080/openapi.json`

The checked-in export lives at [docs/openapi.json](/Users/aayush/Documents/Codex/2026-07-04/this-is-a-comprehensive-production-grade/docs/openapi.json). Regenerate it after API changes:

```bash
make openapi
```

Swagger testing flow:

1. Open `http://localhost:8080/swagger`.
2. Expand `POST /api/v1/auth/token`.
3. Click **Try it out** and submit `dispatcher` / `local-password`.
4. Copy the returned `access_token`.
5. Click **Authorize**, paste the bearer token, and test secured dispatch APIs.

Issue a token:

```bash
curl -X POST http://localhost:8080/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dispatcher&password=local-password"
```

The default local dispatcher password is `local-password`. Replace `ADMIN_PASSWORD_HASH` in `.env` before using shared or production-like environments.

Dispatch an incident:

```bash
curl -X POST http://localhost:8080/api/v1/dispatch/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_location": {"latitude": 40.7584, "longitude": -73.9857},
    "destination": {"latitude": 40.7648, "longitude": -73.9808},
    "severity": "critical",
    "notes": "Chest pain with shortness of breath"
  }'
```

Calculate a public healthcare route without creating a dispatch:

```bash
curl -X POST http://localhost:8080/api/v1/routes/best \
  -H "Content-Type: application/json" \
  -d '{
    "origin": {"latitude": 40.7584, "longitude": -73.9857},
    "destination": {"latitude": 40.7648, "longitude": -73.9808},
    "priority": "emergency",
    "include_alternatives": true,
    "use_signal_priority": true,
    "traffic_level": 1.35
  }'
```

This route API is intentionally unauthenticated for open healthcare-service route
validation. Put it behind API Gateway, quotas, and abuse controls before exposing it
on the public internet.

## Terraform Deployment

1. Create or select GCP projects for dev, staging, and prod.
2. Enable required APIs: Cloud Run, Cloud SQL Admin, Secret Manager, Service Networking, IAM, Artifact Registry.
3. Copy the environment tfvars template:

```bash
cp infra/envs/staging/terraform.tfvars.example infra/envs/staging/terraform.tfvars
```

4. Edit `project_id`, `region`, `image`, and `database_tier`.
5. Plan and apply:

```bash
terraform -chdir=infra/envs/staging init
terraform -chdir=infra/envs/staging plan
terraform -chdir=infra/envs/staging apply
```

Production uses deletion protection, higher minimum Cloud Run instances, and regional Cloud SQL availability by default.

## CI/CD

`ci.yml` runs on pushes to `main` and pull requests:

- Install dependencies
- Lint with Ruff
- Start PostGIS
- Run Alembic migrations
- Run unit and integration tests
- Validate Terraform
- Build the Docker image
- Run Trivy dependency scanning

`deploy.yml` is manually triggered with `workflow_dispatch`.

- Choose `staging` or `prod`.
- Provide the image tag.
- GitHub Environment approvals should gate production.
- Required secrets: `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOY_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `ARTIFACT_REGISTRY`, `JWT_SECRET`.

## Automated Steps

- Dependency installation: `make install`
- Linting: `make lint`
- Unit tests: `make test`
- Integration tests: `make test-integration`
- Docker build: `make docker-build`
- Infrastructure validation: `make terraform-validate`
- Infrastructure provisioning: `scripts/deploy.sh`
- Database migration: `scripts/db-migrate.sh`
- Health verification: `curl /healthz` and `curl /readyz`

## Manual Steps Remaining

- Select and configure GCP projects.
- Register DNS and configure TLS/custom domains.
- Set initial CI/CD secrets and Workload Identity.
- Replace local JWT and admin password placeholders.
- Generate and store production `JWT_SECRET`.
- Approve final production deployment in GitHub Environments.
- Configure real Artifact Registry image names in tfvars and deployment workflow.
- Decide whether public Cloud Run invocation is acceptable or should sit behind API Gateway/IAP.

## Security Considerations

- No hardcoded production secrets are stored in source.
- JWT signing secrets must be rotated through Secret Manager and CI secrets.
- Runtime IAM is least-privilege for Cloud SQL and its database URL secret.
- Cloud SQL is private IP only.
- Input validation is enforced through Pydantic.
- Dependency scanning runs in CI.
- TODO: Add organization-specific audit logging sinks and alert policies.
- TODO: Replace public Cloud Run invoker with API Gateway, mTLS, or IAP if dispatch access is not public.
- TODO: Add API Gateway quotas and abuse protection for the open route-calculation endpoint.

Secret rotation outline:

1. Generate a new `JWT_SECRET`.
2. Store it in Secret Manager and GitHub Environment secrets.
3. Deploy staging and verify token issuance.
4. Deploy production during a maintenance window.
5. Revoke old tokens by reducing token TTL or changing issuer version.

## Troubleshooting

- **`/readyz` fails:** verify PostGIS container health and `DATABASE_URL`.
- **Migrations fail on PostGIS extension:** use the `postgis/postgis` image locally and enable PostGIS in Cloud SQL.
- **Terraform private service networking errors:** confirm `servicenetworking.googleapis.com` is enabled and the project has available private address ranges.
- **Token issuance fails locally:** replace `ADMIN_PASSWORD_HASH` with a bcrypt hash matching the password you submit.
- **Integration tests skip:** start the database and export `DATABASE_URL`.

## Future Improvements

- Integrate OSRM, GraphHopper, or Google Routes API behind the routing service.
- Add real-time traffic and signal phase feeds.
- Add ambulance telemetry ingestion via Pub/Sub.
- Add dispatch audit trails and immutable event storage.
- Add API Gateway, rate limiting, and WAF controls.
- Add load tests for sub-second p95/p99 dispatch latency targets.
- Add blue/green Cloud Run revisions and automated rollback hooks.
