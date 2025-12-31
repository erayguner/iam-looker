# Terraform Infrastructure Documentation

This directory contains Terraform configurations for deploying the iam-looker infrastructure on Google Cloud Platform.

## Overview

The infrastructure includes:
- Google Cloud Functions (Gen2) for Looker automation
- Pub/Sub topics for event-driven triggers
- Workload Identity Federation for keyless CI/CD
- API Gateway for HTTP-based internal access
- VPC networking and security controls

## Security Features (2025 Best Practices)

### 1. Customer-Managed Encryption Keys (CMEK)

All Pub/Sub topics support optional CMEK encryption for enhanced security:

```hcl
variable "kms_key_name" {
  type        = string
  description = "Customer-managed encryption key for PubSub topics"
  default     = null  # Optional, uses Google-managed keys if not provided
}
```

**Recommendation:** For production environments, create a Cloud KMS key and provide it via this variable.

### 2. Workload Identity Federation (WIF)

GitHub Actions and other external identities can authenticate without service account keys:

- **No JSON keys**: All authentication uses short-lived OIDC tokens
- **Attribute mapping**: Restricts access to specific repository
- **Audit trail**: All operations logged in Cloud Logging

See `modules/wif_github/` for the WIF module.

### 3. Secret Management

- Secrets stored in Google Secret Manager
- Cloud Functions reference secrets via `secret_environment_variables`
- No secrets in Terraform variables or state

### 4. Network Security

- Cloud Functions use `ALLOW_INTERNAL_ONLY` ingress
- API Gateway attached to VPC for internal access only
- No public endpoints exposed

## Prerequisites

- Terraform 1.10.3 or higher
- Google Cloud SDK (`gcloud`)
- Authenticated GCP account with appropriate permissions
- Checkov (for security scanning)

## Project Structure

```
terraform/
├── providers.tf          # Provider configuration
├── variables.tf          # Input variables
├── main.tf              # Main resources (WIF, storage)
├── functions.tf         # Pub/Sub-triggered functions
├── http_functions.tf    # HTTP-triggered functions + API Gateway
├── modules/
│   └── wif_github/      # Workload Identity Federation module
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
└── TERRAFORM.md         # This file
```

## Setup and Deployment

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Create terraform.tfvars

**Example `terraform.tfvars`:**

```hcl
project_id      = "my-analytics-prod"
project_number  = "123456789012"
region          = "us-central1"
repository      = "myorg/my-repo"  # For GitHub WIF
source_bucket   = "cf-source-artifacts"
source_object   = "placeholder.zip"
vpc_network     = "projects/123456789012/global/networks/shared-vpc"
looker_base_url = "https://looker.company.com:19999"

# Optional: CMEK for Pub/Sub topics (recommended for production)
# kms_key_name = "projects/my-project/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-key"
```

**Important:** Never commit `terraform.tfvars` with sensitive values.

### 3. Configure Secrets

Create secrets in Google Secret Manager (do this before deploying):

```bash
# Create Looker API credentials in Secret Manager
echo -n "your-client-id" | gcloud secrets create looker-client-id \
  --data-file=- \
  --replication-policy=automatic

echo -n "your-client-secret" | gcloud secrets create looker-client-secret \
  --data-file=- \
  --replication-policy=automatic
```

### 4. Validate Configuration

```bash
# Format Terraform files
terraform fmt -recursive

# Validate configuration
terraform validate

# Run security scan
make terraform-checkov
# Or: checkov -d .
```

### 5. Plan and Apply

```bash
# Preview changes
terraform plan

# Apply changes
terraform apply
```

## Security Scanning

Run Checkov to scan for security issues:

```bash
# From project root
make terraform-checkov

# Or from terraform directory
checkov -d . --compact
```

### Common Checkov Findings

| Check ID | Description | Resolution |
|----------|-------------|------------|
| CKV_GCP_83 | PubSub topics should use CMEK | Set `kms_key_name` variable |
| CKV_GCP_125 | GitHub OIDC should have attribute mapping | ✅ Already configured |
| CKV_SECRET_6 | High entropy strings detected | False positive (base64 encoding) |

## Variables Reference

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `project_id` | string | GCP project ID |
| `project_number` | string | GCP project number |
| `repository` | string | GitHub repository for WIF (org/repo) |
| `source_bucket` | string | GCS bucket for Cloud Function source |
| `vpc_network` | string | VPC network for API Gateway |
| `looker_base_url` | string | Looker instance URL |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `region` | string | `us-central1` | GCP region for resources |
| `pool_id` | string | `github-pool` | Workload Identity Pool ID |
| `provider_id` | string | `github-provider` | WIF Provider ID |
| `ci_service_account_id` | string | `ci-deployer` | Service account for CI/CD |
| `kms_key_name` | string | `null` | CMEK key for encryption |

See `variables.tf` for complete list.

## Workload Identity Federation

### GitHub Actions Setup

1. Deploy Terraform with WIF module (creates pool, provider, service account)

2. Update GitHub Actions workflow:

```yaml
name: Deploy
on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/${{ secrets.GCP_PROJECT_NUMBER }}/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
          service_account: 'ci-deployer@${{ secrets.GCP_PROJECT_ID }}.iam.gserviceaccount.com'

      - name: Deploy
        run: |
          # Your deployment commands here
```

### Security Best Practices

✅ **DO:**
- Use WIF for all external identity authentication
- Store secrets in Secret Manager
- Enable CMEK encryption for production
- Use VPC for network isolation
- Regular security scans with Checkov
- Least privilege IAM policies

❌ **DON'T:**
- Create service account JSON keys
- Store secrets in Terraform variables
- Commit `terraform.tfvars` with sensitive data
- Use public endpoints unnecessarily
- Skip security scans

## Troubleshooting

### Error: Cannot find source bucket

```bash
# Create the source bucket first
gcloud storage buckets create gs://cf-source-artifacts \
  --location=us-central1 \
  --project=my-project
```

### Error: Secret not found

```bash
# Verify secrets exist
gcloud secrets list --project=my-project

# Create missing secrets
gcloud secrets create looker-client-id --replication-policy=automatic
```

### Checkov fails with network error

This is expected when running behind a proxy. Checkov will still scan locally but can't fetch remote guidelines. The scan results are still valid.

## Maintenance

### Updating Cloud Functions

Cloud Functions use automatic source hashing. Any code change triggers:
1. New archive created with different MD5 hash
2. New GCS object uploaded
3. Terraform detects change and redeploys function

No manual version bumps needed.

### Rotating Secrets

```bash
# Update secret version
echo -n "new-secret-value" | gcloud secrets versions add looker-client-secret \
  --data-file=-

# Cloud Functions automatically use "latest" version
```

### Upgrading Terraform

```bash
# Update Terraform version
terraform version

# If needed, upgrade providers
terraform init -upgrade
```

## Cost Optimization

- Cloud Functions use minimal instances (max 3-5)
- Pub/Sub message retention: 1 day
- Automatic scaling based on load
- Internal-only endpoints (no egress costs)

## Compliance and Auditing

- All resources tagged with project metadata
- Cloud Logging captures all function executions
- Cloud Audit Logs track infrastructure changes
- VPC Flow Logs for network monitoring (if enabled)

## Additional Resources

- [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Cloud Functions Best Practices](https://cloud.google.com/functions/docs/bestpractices)
- [Checkov Documentation](https://www.checkov.io/)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
