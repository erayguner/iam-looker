resource "google_pubsub_topic" "add_group_topic" {
  name    = "looker-add-group"
  project = var.project_id

  # Enable customer-managed encryption keys (CMEK) for enhanced security
  # Checkov: CKV_GCP_83
  kms_key_name = var.kms_key_name

  message_retention_duration = "86400s" # 1 day
}

resource "google_pubsub_topic" "create_folder_topic" {
  name    = "looker-create-folder"
  project = var.project_id

  # Enable customer-managed encryption keys (CMEK) for enhanced security
  # Checkov: CKV_GCP_83
  kms_key_name = var.kms_key_name

  message_retention_duration = "86400s" # 1 day
}

resource "google_pubsub_topic" "create_dashboard_topic" {
  name    = "looker-create-dashboard"
  project = var.project_id

  # Enable customer-managed encryption keys (CMEK) for enhanced security
  # Checkov: CKV_GCP_83
  kms_key_name = var.kms_key_name

  message_retention_duration = "86400s" # 1 day
}

resource "google_cloudfunctions2_function" "add_group" {
  name     = "looker-add-group"
  location = var.region
  project  = var.project_id

  build_config {
    runtime     = "python310"
    entry_point = "add_group_to_saml"

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

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      secret     = "looker-client-id"
      version    = "latest"
      project_id = var.project_id
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      secret     = "looker-client-secret"
      version    = "latest"
      project_id = var.project_id
    }

    environment_variables = {
      LOOKERSDK_BASE_URL = var.looker_base_url
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.add_group_topic.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }
}

resource "google_cloudfunctions2_function" "create_folder" {
  name     = "looker-create-folder"
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

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      secret     = "looker-client-id"
      version    = "latest"
      project_id = var.project_id
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      secret     = "looker-client-secret"
      version    = "latest"
      project_id = var.project_id
    }

    environment_variables = {
      LOOKERSDK_BASE_URL = var.looker_base_url
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.create_folder_topic.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }
}

resource "google_cloudfunctions2_function" "create_dashboard" {
  name     = "looker-create-dashboard"
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

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_ID"
      secret     = "looker-client-id"
      version    = "latest"
      project_id = var.project_id
    }

    secret_environment_variables {
      key        = "LOOKERSDK_CLIENT_SECRET"
      secret     = "looker-client-secret"
      version    = "latest"
      project_id = var.project_id
    }

    environment_variables = {
      LOOKERSDK_BASE_URL = var.looker_base_url
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.create_dashboard_topic.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }
}
