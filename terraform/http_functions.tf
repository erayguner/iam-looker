resource "google_cloudfunctions2_function" "http_add_group" {
  name     = "http-looker-add-group"
  location = var.region
  project  = var.project_id

  build_config {
    runtime     = "python312"
    entry_point = "add_group_to_saml"

    source {
      storage_source {
        bucket = var.source_bucket
      }
    }
  }

  service_config {
    max_instance_count = 3
    available_memory   = "256M"
    timeout_seconds    = 60
    ingress_settings   = "ALLOW_INTERNAL_ONLY"

    environment_variables = {
      LOOKERSDK_BASE_URL      = var.looker_base_url
      LOOKERSDK_CLIENT_ID     = var.looker_client_id
      LOOKERSDK_CLIENT_SECRET = var.looker_client_secret
    }
  }
}

resource "google_cloudfunctions2_function" "http_create_folder" {
  name     = "http-looker-create-folder"
  location = var.region
  project  = var.project_id

  build_config {
    runtime     = "python312"
    entry_point = "create_project_folder"

    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count = 3
    available_memory   = "256M"
    timeout_seconds    = 60
    ingress_settings   = "ALLOW_INTERNAL_ONLY"

    environment_variables = {
      LOOKERSDK_BASE_URL      = var.looker_base_url
      LOOKERSDK_CLIENT_ID     = var.looker_client_id
      LOOKERSDK_CLIENT_SECRET = var.looker_client_secret
    }
  }
}

resource "google_cloudfunctions2_function" "http_create_dashboard" {
  name     = "http-looker-create-dashboard"
  location = var.region
  project  = var.project_id

  build_config {
    runtime     = "python312"
    entry_point = "create_dashboard_from_template"

    source {
      storage_source {
        bucket = var.source_bucket
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count = 5
    available_memory   = "512M"
    timeout_seconds    = 120
    ingress_settings   = "ALLOW_INTERNAL_ONLY"

    environment_variables = {
      LOOKERSDK_BASE_URL      = var.looker_base_url
      LOOKERSDK_CLIENT_ID     = var.looker_client_id
      LOOKERSDK_CLIENT_SECRET = var.looker_client_secret
    }
  }
}
