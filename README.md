# iam-looker

[![CI](https://github.com/erayguner/iam-looker/actions/workflows/ci.yml/badge.svg)](https://github.com/erayguner/iam-looker/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Terraform](https://img.shields.io/badge/terraform-1.11.0-623CE4.svg)](https://www.terraform.io/)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](http://mypy-lang.org/)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

> Automated Looker user onboarding and project provisioning for Google Cloud Platform

## Overview

**iam-looker** automates the onboarding of Google Cloud projects into Looker instances, handling group provisioning, folder creation, and dashboard cloning with complete observability and security.

### Key Features

- **Automated Group Provisioning**: Sync Google Workspace groups to Looker via SAML configuration
- **Project Folder Management**: Create and manage project-scoped Looker folders with naming conventions
- **Dashboard Templating**: Clone template dashboards with dynamic token substitution (PROJECT_ID, ANCESTRY_PATH)
- **Idempotent Operations**: Safe to run repeatedly without duplicates
- **Keyless Security**: Workload Identity Federation for all CI/CD (no service account keys)
- **Observable**: Structured JSON logging with correlation IDs
- **Cloud Native**: Google Cloud Functions Gen2 with Pub/Sub and HTTP triggers

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Terraform 1.11.0+
- Google Cloud Platform project
- Looker instance with API access

### Installation

```bash
# Clone the repository
git clone https://github.com/erayguner/iam-looker.git
cd iam-looker

# Install dependencies
pip install -r requirements.txt

# Or install with development tools
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Configuration

Create a `.env` file or export environment variables:

```bash
export LOOKERSDK_BASE_URL="https://your.looker.instance:19999"
export LOOKERSDK_CLIENT_ID="your_client_id"
export LOOKERSDK_CLIENT_SECRET="your_client_secret"
export LOOKERSDK_VERIFY_SSL=true
```

**⚠️ Security Note**: Never commit real credentials. Use Secret Manager in production.

### Local Testing

```bash
# Run tests
make test

# Run tests with coverage
make test-cov

# Lint code
make lint

# Format code
make format

# Run all checks (CI simulation)
make ci

# Simulate an event locally
python functions/main.py '{"projectId":"demo","groupEmail":"demo-group@company.com"}'
```

## Project Structure

```
iam-looker/
├── src/iam_looker/          # Main package (2025 src layout)
│   ├── handler.py           # Cloud Function entrypoint handler
│   ├── models.py            # Pydantic models for validation
│   ├── settings.py          # Centralized configuration
│   ├── provisioner.py       # Looker API orchestration
│   ├── logging.py           # Structured logging
│   ├── exceptions.py        # Custom exceptions
│   └── cli.py               # CLI commands
├── functions/               # Cloud Function entry points
│   └── main.py              # All function handlers
├── terraform/               # Infrastructure as Code
│   ├── main.tf              # Main Terraform config
│   ├── functions.tf         # Cloud Functions deployment
│   └── modules/wif_github/  # Workload Identity Federation
├── tests/                   # Test suite
├── .github/workflows/       # GitHub Actions CI/CD
└── pyproject.toml           # Project metadata and config
```

## Event Payload Contract

### Pub/Sub Event

```json
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

### Field Descriptions

- **projectId** (required): GCP project ID (RFC1034 label format)
- **groupEmail** (required): Google Workspace group email
- **ancestryPath** (optional): Organization/folder hierarchy path
- **templateDashboardIds** (optional): Dashboard IDs to clone (uses defaults if absent)
- **templateFolderId** (optional): Source folder for templates
- **tokens** (optional): Additional key-value pairs for substitution

## Architecture

### High-Level Flow

```
┌─────────────┐      ┌──────────────────┐      ┌──────────────┐
│  Pub/Sub    │─────▶│ Cloud Function   │─────▶│   Looker     │
│  / HTTP     │      │  (Gen2)          │      │   API 4.0    │
└─────────────┘      └──────────────────┘      └──────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Secret Manager   │
                     │ (credentials)    │
                     └──────────────────┘
```

### Operations

1. **Validate Payload**: Pydantic model validation with clear error messages
2. **Ensure Group**: Lookup or create Looker group (idempotent)
3. **Update SAML**: Add group to SAML configuration (merge, not overwrite)
4. **Create Folder**: Find or create project folder with naming convention
5. **Clone Dashboards**: Copy templates with token substitution
6. **Log Results**: Structured JSON logging with correlation ID

### Cloud Functions

| Function Name | Entry Point | Trigger | Description |
|--------------|-------------|---------|-------------|
| `looker-provision-all` | `provision_looker_project` | Pub/Sub | Complete provisioning workflow |
| `looker-add-group-saml` | `add_group_to_saml` | Pub/Sub | Add group to SAML only |
| `looker-create-folder` | `create_project_folder` | Pub/Sub | Create project folder only |
| `looker-clone-dashboard` | `create_dashboard_from_template` | Pub/Sub | Clone dashboard only |
| `looker-http-provision` | `http_provision` | HTTP | HTTP endpoint for provisioning |

## Deployment

### Terraform Deployment

```bash
cd terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id     = "my-analytics-prod"
project_number = "123456789012"
region         = "us-central1"
source_bucket  = "cf-source-artifacts"
vpc_network    = "projects/123456789012/global/networks/shared-vpc"
EOF

# Plan deployment
terraform plan -var-file=terraform.tfvars

# Apply infrastructure
terraform apply -var-file=terraform.tfvars
```

### Manual Cloud Function Deployment

```bash
gcloud functions deploy looker-provision-all \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=provision_looker_project \
  --trigger-topic=looker-onboard-topic \
  --service-account=looker-onboard-sa@PROJECT_ID.iam.gserviceaccount.com \
  --set-secrets=LOOKERSDK_BASE_URL=looker-base-url:latest,LOOKERSDK_CLIENT_ID=looker-client-id:latest,LOOKERSDK_CLIENT_SECRET=looker-client-secret:latest
```

### CI/CD with GitHub Actions

The project includes comprehensive GitHub Actions workflows:

- **CI**: Linting, testing, security scanning, Terraform validation
- **Deploy Cloud Functions**: Automated deployment to dev/staging/prod
- **Deploy Terraform**: Infrastructure deployment with plan/apply/destroy
- **Release**: Automated releases with changelog and Docker images
- **PR Comments**: Automated CI results and coverage reports on pull requests

See [.github/WORKFLOWS.md](.github/WORKFLOWS.md) for complete documentation.

## Security

### Keyless Architecture (Workload Identity Federation)

**⚠️ We DO NOT use service account JSON keys.**

Instead, we use Workload Identity Federation (WIF) for all external authentication:

- **GitHub Actions**: OIDC token exchange for short-lived GCP credentials
- **Cloud Functions**: Attached service account with Application Default Credentials
- **No Keys**: Enforced via organization policy when possible

### Security Features

- **Secret Manager**: All credentials stored in GCP Secret Manager
- **Least Privilege**: Service accounts have minimal required permissions
- **Input Validation**: Pydantic models validate all inputs
- **Audit Logging**: All operations logged to Cloud Logging
- **No Secrets in Code**: Never commit credentials to repository

### CI/CD Pattern (GitHub OIDC)

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - name: Authenticate to Google Cloud
    uses: google-github-actions/auth@v2
    with:
      workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
      service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
```

## Development

### Setup Development Environment

```bash
# Using make
make dev-setup

# Or manually
pip install -e ".[dev,terraform,all]"
pre-commit install

# Using Docker
docker-compose up -d dev
docker-compose exec dev bash
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src/iam_looker --cov-report=html

# Specific test file
pytest tests/test_handler.py -v

# Using make
make test-cov
```

### Code Quality

```bash
# Lint with Ruff
ruff check .

# Format code
ruff format .

# Type check with mypy
mypy src/

# Security scan
bandit -r src/

# All checks
make ci
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

- Trailing whitespace removal
- YAML/JSON validation
- Ruff linting and formatting
- MyPy type checking
- Bandit security scan
- Terraform formatting and validation
- Secret detection
- Commit message linting (Conventional Commits)

Run manually: `pre-commit run --all-files`

## Idempotency

All operations are designed to be idempotent and safe to run repeatedly:

| Operation | Lookup Strategy | Idempotent Behavior |
|-----------|----------------|---------------------|
| **Group** | Search by name/email | Reuse existing or create new |
| **SAML Config** | Fetch current config | Merge group, don't overwrite |
| **Folder** | Search by pattern `Project: <projectId>` | Reuse existing or create new |
| **Dashboard** | Search by title pattern | Skip if exists, else clone |

## Error Handling

- **Invalid Payload**: 400 error with validation details
- **Looker API Transient**: Retry with exponential backoff (future)
- **Permanent Errors**: Logged and escalated to dead-letter queue
- **Correlation IDs**: Track requests across distributed systems

## Observability

### Structured Logging

All logs are JSON-formatted for easy ingestion:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "event": "group.ensure",
  "projectId": "my-project",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Looker group ensured",
  "details": {"groupId": 123}
}
```

### Metrics (Future)

Planned metrics exporter for:
- Request duration (P50, P95, P99)
- Success/failure rates
- Resource creation counts
- Looker API call latency

## 2025 Python Best Practices

This project follows modern Python development standards:

1. **src/ Layout**: Explicit package structure (`iam_looker`)
2. **Pydantic v2**: Type-safe models for validation and settings
3. **Structured Logging**: JSON logs with correlation IDs
4. **Thin Handlers**: Business logic separated from transport layer
5. **Type Hints**: Full mypy strict mode compliance
6. **Modern Tools**: Ruff (linting), pytest (testing), pre-commit (quality gates)
7. **Dependency Pinning**: Major version pinning for stability

## Roadmap

- [x] Core provisioning workflow
- [x] Idempotent operations
- [x] Structured logging
- [x] Terraform deployment
- [x] CI/CD with GitHub Actions
- [x] Workload Identity Federation
- [x] Pre-commit hooks
- [ ] Retry/backoff wrapper
- [ ] Metrics exporter (Prometheus/OpenTelemetry)
- [ ] Workspace group validation via Admin SDK
- [ ] Dashboard metadata tagging (replace title-based matching)
- [ ] Multi-project batch processing
- [ ] Advanced role assignment logic

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code of conduct
- Development setup
- Testing requirements
- Pull request process
- Coding standards

## Documentation

- [SPEC.md](SPEC.md) - Authoritative technical specification
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](SECURITY.md) - Security policy and vulnerability reporting
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [.github/WORKFLOWS.md](.github/WORKFLOWS.md) - GitHub Actions workflows documentation

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/erayguner/iam-looker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/erayguner/iam-looker/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for vulnerability reporting

---

**Built with ❤️ for the data platform engineering community**
