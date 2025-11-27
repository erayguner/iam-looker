# iam-looker
Looker user onboarding automation

## Project Objectives
- Automate onboarding of Google Cloud projects into a Looker instance.
- Provision access for Google Workspace groups via Looker SAML configuration updates.
- Create project-scoped Looker folders and clone dashboard templates with project context (project ID / ancestry path).
- Ensure idempotent, observable, secure operations driven by a spec-first workflow.
- Enforce keyless security posture (no long-lived service account keys) via Workload Identity Federation (WIF) for CI/CD.

## High-Level Goal
Given a Cloud Pub/Sub event (or HTTP trigger) containing a GCP project ID (and optional ancestry path) plus the associated Google Workspace group email, automatically:
1. Validate and normalize the incoming payload.
2. Provision or map the Workspace group inside Looker (create Looker Group if missing).
3. Update SAML settings to include the group with correct role/folder access.
4. Create (or find) a project folder in Looker.
5. Clone a set of template dashboards into that folder, performing token substitution (e.g. {{PROJECT_ID}}, {{ANCESTRY_PATH}}).
6. Emit a structured result + metrics / logs for observability.

## Spec-Driven Development
A living specification file (`SPEC.md`) defines:
- Data contracts for the triggering event.
- API interactions with Looker SDK.
- Idempotency rules and reconciliation logic.
- Error taxonomy & retry semantics.
- Non-functional requirements (security, performance, auditing).
- Workload Identity Federation requirements (no service account keys).

All implementation MUST conform to the spec. Changes begin by updating `SPEC.md` then implementing code & tests.

See `SPEC.md` for the authoritative detailed specification.

## Architecture Overview
- Trigger: Cloud Function (Pub/Sub or HTTP) receives onboarding request.
- Core Modules:
  - `config.py` loads environment & static config.
  - `looker_provisioner.py` encapsulates Looker API interactions.
  - `dashboard_template.py` handles template retrieval & cloning logic.
  - `main.py` orchestration entrypoint.
- External Services:
  - Looker API via `looker_sdk` (API 4.0).
  - Google Workspace group (email provided; optional validation via Admin SDK in future).
- Security: CI/CD uses Workload Identity Federation (GitHub OIDC or Cloud Build) – no JSON keys checked in or distributed.
- Observability: Structured logging (JSON), metrics hooks (extensible), correlation ID propagation.

## Event Payload Contract (Summary)
```
{
  "projectId": "my-gcp-project",
  "ancestryPath": "organization/12345 -> folder/67890 -> project/abcdef",
  "groupEmail": "data-analysts@company.com",
  "templateDashboardIds": [101, 202],
  "templateFolderId": 55,
  "tokens": {"EXTRA_KEY": "value"}
}
```
Base64-encoded in `data` for Pub/Sub; raw JSON for HTTP.

## Idempotency Strategy
- Looker group looked up by name/email before creation.
- Folder looked up by convention: `Project: <projectId>`.
- Dashboard clones searched by slug/title pattern before cloning.
- SAML config merged, not overwritten.

## Security Posture (Keyless / WIF)
We DO NOT create or use long-lived service account JSON keys.
Instead, we rely on Workload Identity Federation (WIF) so external identities (e.g. GitHub Actions runners) can obtain short-lived credentials.

### Why Avoid Keys?
- Keys are static, hard to rotate, and prone to leakage.
- WIF provides ephemeral tokens, audited in Cloud Logging.

### CI/CD Pattern (GitHub OIDC Example)
Terraform snippet (see `terraform/` directory for full example):
```hcl
module "ci_wif" {
  source = "./modules/wif_github"
  project_id = var.project_id
  pool_id    = var.pool_id            # e.g. "github-pool"
  provider_id = var.provider_id       # e.g. "github-provider"
  repository  = var.repository        # e.g. "org/repo"
  sa_id       = var.ci_service_account_id  # e.g. "ci-deployer"
}
```
GitHub workflow excerpt (identity only; no key):
```yaml
permissions:
  id-token: write
  contents: read

steps:
  - name: Auth via WIF
    uses: google-github-actions/auth@v2
    with:
      workload_identity_provider: "projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/<POOL_ID>/providers/<PROVIDER_ID>"
      service_account: "ci-deployer@<PROJECT_ID>.iam.gserviceaccount.com"
  - name: Terraform Apply
    run: |
      terraform init
      terraform apply -auto-approve
```

### Cloud Function Runtime
Cloud Functions / Cloud Run uses its attached service account (no key) and Application Default Credentials (ADC) automatically. No manual key creation required.

## Error Handling (Brief)
- Invalid payload: 400 / logged error.
- Looker API transient (HTTP 429/5xx): retry with exponential backoff (to be added).
- Permanent errors escalate to dead-letter / alerting.

## Local Development

### Prerequisites
- Python 3.12 or higher
- Terraform 1.10.3 or higher (for infrastructure)
- Make (optional, for convenience commands)

### Quick Start

1. **Install Python dependencies:**
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (recommended)
make install-dev
# Or: pip install -e ".[dev]"
```

2. **Set up pre-commit hooks (recommended):**
```bash
pre-commit install
```

3. **Configure environment:**
Create & populate `.env` or export credentials:
```bash
export LOOKERSDK_BASE_URL="https://your.looker.instance:19999"
export LOOKERSDK_CLIENT_ID="client_id"
export LOOKERSDK_CLIENT_SECRET="client_secret"
export LOOKERSDK_VERIFY_SSL=true
```
(These are Looker API credentials – distinct from GCP identity. Never commit real secrets.)

4. **Run tests:**
```bash
make test
# Or: pytest -v
```

5. **Run linters and checks:**
```bash
# Run all checks (linting, formatting, type-checking, security)
make check

# Auto-fix linting issues
make lint-fix

# Format code
make format
```

6. **Simulate event:**
```bash
python cloud_function/main.py '{"projectId":"demo","groupEmail":"demo-group@company.com"}'
```

### Development Tools (2025 Best Practices)

This project uses modern Python tooling:

- **Ruff**: Fast linter and formatter (replaces black, isort, flake8)
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **Pytest**: Testing framework
- **Pre-commit**: Automated code quality checks
- **Checkov**: Infrastructure security scanning

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide.

### Common Commands

```bash
make help              # Show all available commands
make install-dev       # Install development dependencies
make test              # Run tests
make lint              # Run linter
make lint-fix          # Auto-fix linting issues
make format            # Format code
make security          # Run security checks
make type-check        # Run type checking
make check             # Run all checks
make clean             # Clean cache files
make ci                # Run CI checks locally
```

## Deployment (GCP Cloud Functions Gen2 example)
```
gcloud functions deploy lookerOnboard \
  --gen2 \
  --runtime=python310 \
  --region=us-central1 \
  --source=. \
  --entry-point=provision_looker_project \
  --trigger-topic=looker-onboard-topic \
  --service-account=looker-onboard-sa@<PROJECT_ID>.iam.gserviceaccount.com \
  --set-env-vars=LOOKERSDK_BASE_URL=...,LOOKERSDK_CLIENT_ID=...,LOOKERSDK_CLIENT_SECRET=...
```
Service account has only necessary roles (e.g. logging writer). No key created.

## Deployment Hashing
An `archive_file` data source packages source and names the object with its MD5 hash. Any code change -> new zip MD5 -> new GCS object name -> Terraform detects drift and recreates Cloud Functions (redeploy). No manual version bump needed.

## Single-Task Cloud Functions
Pub/Sub triggered functions:
- add_group_to_saml
- create_project_folder
- create_dashboard_from_template
HTTP internal functions (API Gateway backend) mirror the same tasks with `http-` prefixed names.
API Gateway attached to VPC network (`vpc_network`) for internal-only access.

### Terraform Testing
`tftest.hcl` defines variable inputs and a plan run for validation using native Terraform test framework.

## Repository Structure
```
/terraform
  providers.tf
  variables.tf
  main.tf
  functions.tf
  http_functions.tf
  /modules/wif_github
/src
  /iam_looker
    __init__.py
    handler.py
    models.py
    settings.py
    logging.py
    exceptions.py
    provisioner.py
    cli.py
  config.py (legacy)
  dashboard_template.py (legacy)
  looker_provisioner.py (legacy)
/functions
  main.py (all Cloud Function entry points)
```

## Security Considerations
- Secrets managed via Secret Manager (future improvement): reference them in env vars.
- Principle of least privilege for Looker API credentials.
- Input validation & sanitization for all template tokens.
- Keyless CI/CD with WIF; forbid `google_service_account_key` resources in Terraform.

## Testing Strategy
- Unit tests mock `looker_sdk` client.
- Contract tests ensure payload schema compliance.
- Future: Integration tests against Looker sandbox.

## Next Steps / Roadmap
- Implement retry/backoff wrapper.
- Add metrics exporter (Prometheus / Cloud Monitoring).
- Workspace group validation via Admin SDK.
- Secret Manager integration.
- Replace dashboard title uniqueness with metadata tagging.
- Terraform module to manage Looker-related IAM (no keys).

## 2025 Python Best Practices Adopted
1. src/ layout with explicit package (`iam_looker`).
2. Pydantic models for input validation & settings management.
3. JSON structured logging for better observability.
4. Thin handler entrypoint separated from business logic for testability.
5. Immutable result dataclasses replaced by pydantic models for consistent serialisation.
6. Dependency pinning (major versions) and pyproject classifiers for ecosystem clarity.
7. Backward compatibility layer (legacy modules) scheduled for deprecation.

## Secret Management
Sensitive values (Looker client id/secret) are injected via Cloud Functions `secret_environment_variables` referencing Secret Manager secrets (`looker-client-id`, `looker-client-secret`). Do not place them in `terraform.tfvars`. The only recommended tfvars are `project_id`, `project_number`, `region`, and possibly deployment artifact settings (bucket/object) which are not secrets.

### Example terraform.tfvars
```
project_id    = "my-analytics-prod"
project_number = "123456789012"
region        = "us-central1"
source_bucket = "cf-source-artifacts"
source_object = "placeholder.zip" # overwritten by archive_file object name
vpc_network   = "projects/123456789012/global/networks/shared-vpc"
```
All other secure values must reside in Secret Manager and referenced by name.

---
Refer to `SPEC.md` for the exhaustive specification.
