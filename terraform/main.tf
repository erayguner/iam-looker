# ============================================================================
# Looker Automation Infrastructure - Complete Terraform Configuration
# ============================================================================
#
# This file defines all resources needed for Looker automation including:
# - Workload Identity Federation for GitHub Actions
# - Cloud Storage for function source code
# - Secret Manager for Looker credentials
# - Cloud Functions (event-driven and HTTP)
# - Pub/Sub topics for event routing
# - API Gateway for unified API access
#
# Prerequisites:
# 1. GCP project with billing enabled
# 2. APIs enabled: cloudfunctions, cloudbuild, secretmanager, pubsub, apigateway
# 3. Looker instance URL, client ID, and client secret
#
# ============================================================================

locals {
  python_runtime = "python312"
  function_timeout = 180
  max_instances  = 10

  # Source code hash - triggers redeployment when Python code changes
  source_hash = data.archive_file.function_zip.output_md5
}

# ============================================================================
# Workload Identity Federation for GitHub Actions
# ============================================================================

module "wif_github" {
  source                = "./modules/wif_github"
  project_id            = var.project_id
  project_number        = var.project_number
  pool_id               = var.pool_id
  provider_id           = var.provider_id
  repository            = var.repository
  ci_service_account_id = var.ci_service_account_id
}

# ============================================================================
# Cloud Storage - Function Source Code
# ============================================================================

# GCS bucket for Cloud Function source code
resource "google_storage_bucket" "function_source" {
  name                        = "${var.project_id}-looker-functions"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
      age                = 30
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    component = "looker-automation"
    managed_by = "terraform"
  }
}

# Package Python source code into ZIP archive
# Excludes unnecessary files to reduce package size
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.root}/.."
  output_path = "${path.root}/build/function_source.zip"

  excludes = [
    ".git",
    ".github",
    "terraform",
    "tests",
    "*.tfstate",
    "*.tfstate.backup",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "dist",
    "build",
    "*.egg-info",
    ".venv",
    "venv",
    ".env",
    "*.md",
    "docs"
  ]
}

# Upload source code to GCS
# Filename includes MD5 hash to force redeployment on code changes
resource "google_storage_bucket_object" "function_source" {
  name         = "source-${data.archive_file.function_zip.output_md5}.zip"
  bucket       = google_storage_bucket.function_source.name
  source       = data.archive_file.function_zip.output_path
  content_type = "application/zip"

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================================================
# Secret Manager - Looker Credentials
# ============================================================================

# Looker SDK Client ID
resource "google_secret_manager_secret" "looker_client_id" {
  secret_id = "looker-client-id"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

# Looker SDK Client Secret
resource "google_secret_manager_secret" "looker_client_secret" {
  secret_id = "looker-client-secret"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

# Looker Base URL
resource "google_secret_manager_secret" "looker_base_url" {
  secret_id = "looker-base-url"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

# Note: Secret values must be added manually after creation:
# echo -n "your-client-id" | gcloud secrets versions add looker-client-id --data-file=-
# echo -n "your-client-secret" | gcloud secrets versions add looker-client-secret --data-file=-
# echo -n "https://your-instance.looker.com:19999" | gcloud secrets versions add looker-base-url --data-file=-

# ============================================================================
# Pub/Sub Topics for Event-Driven Functions
# ============================================================================

resource "google_pubsub_topic" "provision_project" {
  name    = "looker-provision-project"
  project = var.project_id

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

resource "google_pubsub_topic" "decommission_project" {
  name    = "looker-decommission-project"
  project = var.project_id

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

resource "google_pubsub_topic" "add_user_to_group" {
  name    = "looker-add-user-to-group"
  project = var.project_id

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

resource "google_pubsub_topic" "create_user" {
  name    = "looker-create-user"
  project = var.project_id

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

resource "google_pubsub_topic" "bulk_provision_users" {
  name    = "looker-bulk-provision-users"
  project = var.project_id

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

resource "google_pubsub_topic" "create_project_folder" {
  name    = "looker-create-project-folder"
  project = var.project_id

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

resource "google_pubsub_topic" "create_connection" {
  name    = "looker-create-connection"
  project = var.project_id

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

# ============================================================================
# Event-Driven Cloud Functions (Pub/Sub Triggered)
# ============================================================================

# Main provisioning orchestration function
resource "google_cloudfunctions2_function" "provision_project" {
  name        = "looker-provision-project"
  location    = var.region
  project     = var.project_id
  description = "Complete Looker project provisioning orchestration"

  build_config {
    runtime     = local.python_runtime
    entry_point = "provision_looker_project"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = local.max_instances
    min_instance_count    = 0
    available_memory      = "512M"
    timeout_seconds       = local.function_timeout
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
      LOG_LEVEL           = "INFO"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.provision_project.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# Decommission project function
resource "google_cloudfunctions2_function" "decommission_project" {
  name        = "looker-decommission-project"
  location    = var.region
  project     = var.project_id
  description = "Decommission Looker project resources"

  build_config {
    runtime     = local.python_runtime
    entry_point = "decommission_looker_project"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "256M"
    timeout_seconds       = local.function_timeout
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.decommission_project.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# Add user to group function
resource "google_cloudfunctions2_function" "add_user_to_group" {
  name        = "looker-add-user-to-group"
  location    = var.region
  project     = var.project_id
  description = "Add user to Looker group"

  build_config {
    runtime     = local.python_runtime
    entry_point = "add_user_to_group"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "256M"
    timeout_seconds       = 60
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.add_user_to_group.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# Create user function
resource "google_cloudfunctions2_function" "create_user" {
  name        = "looker-create-user"
  location    = var.region
  project     = var.project_id
  description = "Create Looker user"

  build_config {
    runtime     = local.python_runtime
    entry_point = "create_user"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "256M"
    timeout_seconds       = 60
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.create_user.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# Bulk provision users function
resource "google_cloudfunctions2_function" "bulk_provision_users" {
  name        = "looker-bulk-provision-users"
  location    = var.region
  project     = var.project_id
  description = "Provision multiple users at once"

  build_config {
    runtime     = local.python_runtime
    entry_point = "bulk_provision_users"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "512M"
    timeout_seconds       = local.function_timeout
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.bulk_provision_users.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# Create project folder function
resource "google_cloudfunctions2_function" "create_project_folder" {
  name        = "looker-create-project-folder"
  location    = var.region
  project     = var.project_id
  description = "Create Looker project folder"

  build_config {
    runtime     = local.python_runtime
    entry_point = "create_project_folder"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "256M"
    timeout_seconds       = 60
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.create_project_folder.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# Create connection function
resource "google_cloudfunctions2_function" "create_connection" {
  name        = "looker-create-connection"
  location    = var.region
  project     = var.project_id
  description = "Create Looker database connection"

  build_config {
    runtime     = local.python_runtime
    entry_point = "create_connection"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "256M"
    timeout_seconds       = 60
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.create_connection.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# ============================================================================
# HTTP Cloud Functions (Direct HTTP Triggers)
# ============================================================================

# HTTP function: Add group to SAML
resource "google_cloudfunctions2_function" "http_add_group" {
  name        = "http-looker-add-group"
  location    = var.region
  project     = var.project_id
  description = "HTTP endpoint to add group to SAML configuration"

  build_config {
    runtime     = local.python_runtime
    entry_point = "add_group_to_saml"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "256M"
    timeout_seconds       = 60
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# HTTP function: Create folder
resource "google_cloudfunctions2_function" "http_create_folder" {
  name        = "http-looker-create-folder"
  location    = var.region
  project     = var.project_id
  description = "HTTP endpoint to create Looker folder"

  build_config {
    runtime     = local.python_runtime
    entry_point = "create_project_folder"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "256M"
    timeout_seconds       = 60
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# HTTP function: Create dashboard
resource "google_cloudfunctions2_function" "http_create_dashboard" {
  name        = "http-looker-create-dashboard"
  location    = var.region
  project     = var.project_id
  description = "HTTP endpoint to clone dashboard from template"

  build_config {
    runtime     = local.python_runtime
    entry_point = "create_dashboard_from_template"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count    = 5
    available_memory      = "512M"
    timeout_seconds       = 120
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_id.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_client_secret.secret_id
      version    = "latest"
    }

    secret_environment_variables {
      key        = "LOOKERSDK_BASE_URL"
      project_id = var.project_id
      secret     = google_secret_manager_secret.looker_base_url.secret_id
      version    = "latest"
    }

    environment_variables = {
      LOOKERSDK_VERIFY_SSL = "true"
    }
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
    deployment_hash = local.source_hash
  }
}

# ============================================================================
# API Gateway - Unified API Access
# ============================================================================

# API Gateway API resource
resource "google_api_gateway_api" "looker_api" {
  api_id       = "looker-automation"
  project      = var.project_id
  display_name = "Looker Automation API"

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

# OpenAPI specification template
locals {
  openapi_spec = templatefile("${path.module}/openapi_template.yaml", {
    add_group_uri        = google_cloudfunctions2_function.http_add_group.service_config[0].uri
    create_folder_uri    = google_cloudfunctions2_function.http_create_folder.service_config[0].uri
    create_dashboard_uri = google_cloudfunctions2_function.http_create_dashboard.service_config[0].uri
  })
}

# API Gateway configuration with OpenAPI spec
resource "google_api_gateway_api_config" "looker_api_cfg" {
  api           = google_api_gateway_api.looker_api.api_id
  project       = var.project_id
  api_config_id = "v1-${substr(md5(local.openapi_spec), 0, 8)}"

  openapi_documents {
    document {
      path     = "openapi.yaml"
      contents = base64encode(local.openapi_spec)
    }
  }

  gateway_config {
    backend_config {
      google_service_account = module.wif_github.service_account_email
    }
  }

  depends_on = [
    google_cloudfunctions2_function.http_add_group,
    google_cloudfunctions2_function.http_create_folder,
    google_cloudfunctions2_function.http_create_dashboard
  ]

  lifecycle {
    create_before_destroy = true
  }

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}

# API Gateway deployment
resource "google_api_gateway_gateway" "looker_gw" {
  api_config   = google_api_gateway_api_config.looker_api_cfg.id
  gateway_id   = "looker-automation-gw"
  project      = var.project_id
  region       = var.region
  display_name = "Looker Automation Gateway"

  labels = {
    component  = "looker-automation"
    managed_by = "terraform"
  }
}
