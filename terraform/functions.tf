resource "google_pubsub_topic" "add_group_topic" { name = "looker-add-group" }
resource "google_pubsub_topic" "create_folder_topic" { name = "looker-create-folder" }
resource "google_pubsub_topic" "create_dashboard_topic" { name = "looker-create-dashboard" }

resource "google_cloudfunctions2_function" "add_group" {
  name        = "looker-add-group"
  location    = var.region
  project     = var.project_id
  build_config {
    runtime     = "python310"
    entry_point = "add_group_to_saml"
    source { storage_source { bucket = var.source_bucket object = google_storage_bucket_object.function_source.name } }
  }
  service_config {
    max_instance_count = 3
    available_memory   = "256M"
    timeout_seconds    = 60
    ingress_settings   = "ALLOW_INTERNAL_ONLY"
    secret_environment_variables = [
      { key = "LOOKERSDK_CLIENT_ID", secret = "looker-client-id", version = "latest" },
      { key = "LOOKERSDK_CLIENT_SECRET", secret = "looker-client-secret", version = "latest" }
    ]
    environment_variables = {
      LOOKERSDK_BASE_URL = "${var.project_id}-looker-base-url" # placeholder; could also be secret if needed
    }
  }
  event_trigger { trigger_region = var.region event_type = "google.cloud.pubsub.topic.v1.messagePublished" pubsub_topic = google_pubsub_topic.add_group_topic.id retry_policy = "RETRY_POLICY_RETRY" }
}

resource "google_cloudfunctions2_function" "create_folder" {
  name        = "looker-create-folder"
  location    = var.region
  project     = var.project_id
  build_config { runtime = "python310" entry_point = "create_project_folder" source { storage_source { bucket = var.source_bucket object = google_storage_bucket_object.function_source.name } } }
  service_config {
    max_instance_count = 3
    available_memory   = "256M"
    timeout_seconds    = 60
    ingress_settings   = "ALLOW_INTERNAL_ONLY"
    secret_environment_variables = [
      { key = "LOOKERSDK_CLIENT_ID", secret = "looker-client-id", version = "latest" },
      { key = "LOOKERSDK_CLIENT_SECRET", secret = "looker-client-secret", version = "latest" }
    ]
    environment_variables = { LOOKERSDK_BASE_URL = "${var.project_id}-looker-base-url" }
  }
  event_trigger { trigger_region = var.region event_type = "google.cloud.pubsub.topic.v1.messagePublished" pubsub_topic = google_pubsub_topic.create_folder_topic.id retry_policy = "RETRY_POLICY_RETRY" }
}

resource "google_cloudfunctions2_function" "create_dashboard" {
  name        = "looker-create-dashboard"
  location    = var.region
  project     = var.project_id
  build_config { runtime = "python310" entry_point = "create_dashboard_from_template" source { storage_source { bucket = var.source_bucket object = google_storage_bucket_object.function_source.name } } }
  service_config {
    max_instance_count = 5
    available_memory   = "512M"
    timeout_seconds    = 120
    ingress_settings   = "ALLOW_INTERNAL_ONLY"
    secret_environment_variables = [
      { key = "LOOKERSDK_CLIENT_ID", secret = "looker-client-id", version = "latest" },
      { key = "LOOKERSDK_CLIENT_SECRET", secret = "looker-client-secret", version = "latest" }
    ]
    environment_variables = { LOOKERSDK_BASE_URL = "${var.project_id}-looker-base-url" }
  }
  event_trigger { trigger_region = var.region event_type = "google.cloud.pubsub.topic.v1.messagePublished" pubsub_topic = google_pubsub_topic.create_dashboard_topic.id retry_policy = "RETRY_POLICY_RETRY" }
}

resource "google_api_gateway_api" "looker_api" { api_id = "looker-automation" project = var.project_id display_name = "Looker Automation API" }

resource "google_api_gateway_api_config" "looker_api_cfg" {
  api      = google_api_gateway_api.looker_api.api_id
  project  = var.project_id
  api_config_id = "v1"
  openapi_documents { document { path = "openapi.yaml" contents = file("${path.module}/openapi.yaml") } }
  depends_on = [google_cloudfunctions2_function.add_group, google_cloudfunctions2_function.create_folder, google_cloudfunctions2_function.create_dashboard]
}

resource "google_api_gateway_gateway" "looker_gw" { project = var.project_id api_config = google_api_gateway_api_config.looker_api_cfg.id gateway_id = "looker-gw" location = var.region }
