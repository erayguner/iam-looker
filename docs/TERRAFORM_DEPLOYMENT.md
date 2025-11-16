# Terraform Deployment Guide

Complete guide for deploying the Looker Automation infrastructure using Terraform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Verification](#verification)
- [Auto-Redeployment](#auto-redeployment)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- Terraform >= 1.11.0
- Google Cloud SDK (`gcloud`)
- Git
- Python 3.12+

### Required GCP APIs

Enable the following APIs in your GCP project:

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  pubsub.googleapis.com \
  apigateway.googleapis.com \
  servicemanagement.googleapis.com \
  servicecontrol.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com
```

### Required Permissions

Your user/service account needs:
- `roles/owner` OR combination of:
  - `roles/cloudfunctions.admin`
  - `roles/iam.securityAdmin`
  - `roles/secretmanager.admin`
  - `roles/pubsub.admin`
  - `roles/storage.admin`
  - `roles/apigateway.admin`

## Quick Start

### 1. Set Up GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export REGION="us-central1"

# Configure gcloud
gcloud config set project $PROJECT_ID
```

### 2. Create State Bucket (Optional but Recommended)

```bash
# Create bucket for Terraform state
gsutil mb -p $PROJECT_ID -l $REGION gs://$PROJECT_ID-terraform-state

# Enable versioning
gsutil versioning set on gs://$PROJECT_ID-terraform-state

# Update terraform/backend.tf to use this bucket
```

### 3. Create terraform.tfvars

```bash
cd terraform

cat > terraform.tfvars <<EOF
project_id     = "$PROJECT_ID"
project_number = "$PROJECT_NUMBER"
region         = "$REGION"
repository     = "your-github-org/your-repo"
EOF
```

### 4. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply configuration
terraform apply
```

### 5. Configure Looker Credentials

```bash
# Add your Looker credentials to Secret Manager
echo -n "your-looker-client-id" | gcloud secrets versions add looker-client-id --data-file=-
echo -n "your-looker-client-secret" | gcloud secrets versions add looker-client-secret --data-file=-
echo -n "https://your-instance.looker.com:19999" | gcloud secrets versions add looker-base-url --data-file=-
```

## Detailed Setup

### Configuration Variables

Create `terraform.tfvars` with all required variables:

```hcl
# Required Variables
project_id     = "your-gcp-project-id"
project_number = "123456789012"  # Get with: gcloud projects describe PROJECT_ID --format='value(projectNumber)'
repository     = "github-org/repo-name"

# Optional Variables
region                = "us-central1"  # Default
pool_id               = "github-pool"  # Default
provider_id           = "github-provider"  # Default
ci_service_account_id = "ci-deployer"  # Default
environment           = "development"  # Options: development, staging, production

# Advanced Configuration
python_runtime    = "python312"  # Default
function_timeout  = 180  # Seconds, default
max_instances     = 10  # Default

# Custom Labels
labels = {
  team        = "data-platform"
  cost_center = "engineering"
  managed_by  = "terraform"
}
```

### Backend Configuration

For production deployments, enable remote state:

1. Create state bucket (see Quick Start)
2. Edit `terraform/backend.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket  = "your-project-id-terraform-state"
    prefix  = "terraform/state"
  }
}
```

3. Initialize backend:

```bash
terraform init -migrate-state
```

## Deployment

### Initial Deployment

```bash
cd terraform

# 1. Initialize
terraform init

# 2. Validate configuration
terraform validate

# 3. Format code
terraform fmt -recursive

# 4. Plan deployment
terraform plan -out=tfplan

# 5. Review plan output carefully
less tfplan.txt  # or terraform show tfplan

# 6. Apply changes
terraform apply tfplan

# 7. Save outputs
terraform output -json > outputs.json
```

### Deployment Output

After successful deployment, you'll see:

```
Outputs:

api_gateway_url = "looker-automation-gw-xxxxxx.apigateway.your-region.cloud.goog"
event_functions = {
  "provision_project" = {
    "name" = "looker-provision-project"
    "url" = "https://..."
  }
  # ... more functions
}
http_functions = {
  "add_group_to_saml" = {
    "name" = "http-looker-add-group"
    "url" = "https://..."
  }
  # ... more functions
}
pubsub_topics = {
  "provision_project" = "looker-provision-project"
  # ... more topics
}
quick_start_commands = <<EOT
  # Commands for common operations
EOT
```

## Verification

### 1. Verify Infrastructure

```bash
# List all Cloud Functions
gcloud functions list --project=$PROJECT_ID --region=$REGION

# List all Pub/Sub topics
gcloud pubsub topics list --project=$PROJECT_ID

# List secrets
gcloud secrets list --project=$PROJECT_ID

# Check API Gateway
gcloud api-gateway apis list --project=$PROJECT_ID
```

### 2. Run Terraform Tests

```bash
cd terraform

# Run native Terraform tests
terraform test

# Expected output: All tests passing
```

### 3. Test a Function

```bash
# Publish message to provision_project topic
gcloud pubsub topics publish looker-provision-project \
  --project=$PROJECT_ID \
  --message='{
    "projectId": "test-project",
    "groupEmail": "analysts@example.com",
    "templateDashboardIds": [1, 2]
  }'

# View function logs
gcloud functions logs read looker-provision-project \
  --project=$PROJECT_ID \
  --region=$REGION \
  --limit=50
```

## Auto-Redeployment

### How It Works

The infrastructure automatically redeploys Cloud Functions when Python code changes:

1. **Source Code Hashing**:
   - Terraform packages source code into ZIP
   - MD5 hash calculated: `source-{md5}.zip`

2. **Change Detection**:
   - Any Python file change creates new MD5
   - New ZIP uploaded to GCS with new name
   - Terraform detects source object change

3. **Automatic Redeployment**:
   - Functions reference source object by name
   - Name change triggers function update
   - `create_before_destroy` ensures zero downtime

4. **Deployment Tracking**:
   - Each function labeled with `deployment_hash = {md5}`
   - Track which code version is deployed

### Triggering Redeployment

```bash
# Make any Python code change
echo "# Updated" >> src/iam_looker/provisioner.py

# Terraform will detect the change
terraform plan
# Output shows: google_storage_bucket_object.function_source will be created
#               google_cloudfunctions2_function.* will be updated

# Apply the change
terraform apply
```

### Excluded from Package

The following are automatically excluded from function packages:

- `.git/` - Git repository
- `.github/` - GitHub Actions workflows
- `terraform/` - Infrastructure code
- `tests/` - Test files
- `docs/` - Documentation
- `*.md` - Markdown files
- Python cache files (`__pycache__`, `.pyc`, `.pytest_cache`, etc.)
- Virtual environments (`.venv`, `venv`)
- Build artifacts (`dist`, `build`, `*.egg-info`)

## Maintenance

### Updating Infrastructure

```bash
# Update Terraform configuration
vim terraform/main.tf

# Plan changes
terraform plan

# Apply changes
terraform apply
```

### Updating Python Code

```bash
# Make changes to Python code
vim src/iam_looker/provisioner.py

# Terraform automatically handles redeployment
terraform apply
```

### Updating Looker Credentials

```bash
# Update client ID
echo -n "new-client-id" | gcloud secrets versions add looker-client-id --data-file=-

# Update client secret
echo -n "new-client-secret" | gcloud secrets versions add looker-client-secret --data-file=-

# Update base URL
echo -n "https://new-instance.looker.com:19999" | gcloud secrets versions add looker-base-url --data-file=-

# Functions will automatically use new versions
```

### Scaling Configuration

```bash
# Update max instances
cat >> terraform.tfvars <<EOF
max_instances = 20
EOF

terraform apply
```

### Monitoring

```bash
# View function metrics
gcloud monitoring dashboards list

# View logs
gcloud logging read "resource.type=cloud_function" \
  --project=$PROJECT_ID \
  --limit=100 \
  --format=json

# Set up alerts
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Function Errors" \
  --condition-display-name="Error rate > 1%" \
  --condition-threshold-value=0.01
```

## Troubleshooting

### Common Issues

#### 1. Terraform Init Fails

```bash
# Error: Failed to download providers
# Solution: Check internet connection and terraform version
terraform version  # Should be >= 1.11.0
```

#### 2. Permission Denied

```bash
# Error: Permission denied on project
# Solution: Ensure you have required IAM roles
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:YOUR_EMAIL"
```

#### 3. API Not Enabled

```bash
# Error: API [cloudfunctions.googleapis.com] not enabled
# Solution: Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
```

#### 4. Function Deployment Fails

```bash
# Check build logs
gcloud builds list --project=$PROJECT_ID --limit=5

# View specific build
gcloud builds describe BUILD_ID --project=$PROJECT_ID

# Common causes:
# - Missing dependencies in requirements.txt
# - Python syntax errors
# - Import errors
```

#### 5. Secret Access Denied

```bash
# Error: Permission denied accessing secret
# Solution: Grant secret access to service account

# Get function service account
SA_EMAIL=$(terraform output -json | jq -r '.wif_service_account_email.value')

# Grant secret accessor role
gcloud secrets add-iam-policy-binding looker-client-id \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

#### 6. Auto-Redeployment Not Working

```bash
# Verify source hash changed
terraform plan | grep deployment_hash

# Check if source object was created
gsutil ls gs://$PROJECT_ID-looker-functions/

# Force recreation
terraform taint google_storage_bucket_object.function_source
terraform apply
```

### Debug Mode

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform-debug.log

terraform apply

# Review logs
less terraform-debug.log
```

### Clean Up

To destroy all resources:

```bash
# WARNING: This will delete all infrastructure
terraform destroy

# Manually delete state bucket if needed
gsutil rm -r gs://$PROJECT_ID-terraform-state
```

## Advanced Topics

### Multi-Environment Setup

```bash
# Create environment-specific var files
cat > terraform/environments/dev.tfvars <<EOF
project_id = "project-dev"
environment = "development"
max_instances = 5
EOF

cat > terraform/environments/prod.tfvars <<EOF
project_id = "project-prod"
environment = "production"
max_instances = 20
EOF

# Deploy to specific environment
terraform apply -var-file=environments/dev.tfvars
```

### CI/CD Integration

The infrastructure includes Workload Identity Federation for GitHub Actions:

```yaml
# .github/workflows/deploy.yml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
    service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

- name: Deploy with Terraform
  run: |
    cd terraform
    terraform init
    terraform apply -auto-approve
```

### State Locking

For team environments, enable state locking:

```hcl
# terraform/backend.tf
terraform {
  backend "gcs" {
    bucket  = "your-project-terraform-state"
    prefix  = "terraform/state"
    # State locking is automatic with GCS backend
  }
}
```

## Support

- **Issues**: https://github.com/your-org/iam-looker/issues
- **Documentation**: See `/docs` directory
- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/google/latest/docs
