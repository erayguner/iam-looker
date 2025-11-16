# Terraform Outputs for Looker Automation

# Workload Identity Federation
output "wif_provider_name" {
  description = "Workload Identity Pool Provider resource name"
  value       = module.wif_github.provider_name
}

output "wif_service_account_email" {
  description = "Service account email for GitHub Actions"
  value       = module.wif_github.service_account_email
}

# Storage
output "source_bucket_name" {
  description = "GCS bucket containing Cloud Function source code"
  value       = google_storage_bucket.function_source.name
}

output "source_object_name" {
  description = "Latest Cloud Function source archive"
  value       = google_storage_bucket_object.function_source.name
}

output "source_code_md5" {
  description = "MD5 hash of source code (triggers redeployment on change)"
  value       = data.archive_file.function_zip.output_md5
}

# Pub/Sub Topics
output "pubsub_topics" {
  description = "Pub/Sub topics for event-driven functions"
  value = {
    provision_project      = google_pubsub_topic.provision_project.name
    decommission_project   = google_pubsub_topic.decommission_project.name
    add_user_to_group      = google_pubsub_topic.add_user_to_group.name
    create_user            = google_pubsub_topic.create_user.name
    bulk_provision_users   = google_pubsub_topic.bulk_provision_users.name
    create_project_folder  = google_pubsub_topic.create_project_folder.name
    create_connection      = google_pubsub_topic.create_connection.name
  }
}

# Event-Driven Cloud Functions
output "event_functions" {
  description = "Event-driven Cloud Functions (Pub/Sub triggered)"
  value = {
    provision_project = {
      name = google_cloudfunctions2_function.provision_project.name
      url  = google_cloudfunctions2_function.provision_project.service_config[0].uri
    }
    decommission_project = {
      name = google_cloudfunctions2_function.decommission_project.name
      url  = google_cloudfunctions2_function.decommission_project.service_config[0].uri
    }
    add_user_to_group = {
      name = google_cloudfunctions2_function.add_user_to_group.name
      url  = google_cloudfunctions2_function.add_user_to_group.service_config[0].uri
    }
    create_user = {
      name = google_cloudfunctions2_function.create_user.name
      url  = google_cloudfunctions2_function.create_user.service_config[0].uri
    }
    bulk_provision_users = {
      name = google_cloudfunctions2_function.bulk_provision_users.name
      url  = google_cloudfunctions2_function.bulk_provision_users.service_config[0].uri
    }
    create_project_folder = {
      name = google_cloudfunctions2_function.create_project_folder.name
      url  = google_cloudfunctions2_function.create_project_folder.service_config[0].uri
    }
    create_connection = {
      name = google_cloudfunctions2_function.create_connection.name
      url  = google_cloudfunctions2_function.create_connection.service_config[0].uri
    }
  }
}

# HTTP Cloud Functions
output "http_functions" {
  description = "HTTP-triggered Cloud Functions"
  value = {
    add_group_to_saml = {
      name = google_cloudfunctions2_function.http_add_group.name
      url  = google_cloudfunctions2_function.http_add_group.service_config[0].uri
    }
    create_folder = {
      name = google_cloudfunctions2_function.http_create_folder.name
      url  = google_cloudfunctions2_function.http_create_folder.service_config[0].uri
    }
    create_dashboard = {
      name = google_cloudfunctions2_function.http_create_dashboard.name
      url  = google_cloudfunctions2_function.http_create_dashboard.service_config[0].uri
    }
  }
}

# API Gateway
output "api_gateway_url" {
  description = "API Gateway URL for Looker Automation API"
  value       = google_api_gateway_gateway.looker_gw.default_hostname
}

output "api_gateway_managed_service" {
  description = "Managed service endpoint for API Gateway"
  value       = google_api_gateway_gateway.looker_gw.default_hostname
}

# Secret Manager
output "secret_ids" {
  description = "Secret Manager secret IDs"
  value = {
    looker_client_id     = google_secret_manager_secret.looker_client_id.secret_id
    looker_client_secret = google_secret_manager_secret.looker_client_secret.secret_id
    looker_base_url      = google_secret_manager_secret.looker_base_url.secret_id
  }
}

# Deployment Information
output "deployment_info" {
  description = "Deployment metadata and helpful information"
  value = {
    project_id     = var.project_id
    region         = var.region
    python_runtime = local.python_runtime
    terraform_version = ">=  1.11.0"
    last_updated   = timestamp()
  }
}

# Quick Start Commands
output "quick_start_commands" {
  description = "Commands to interact with deployed infrastructure"
  value = <<-EOT
    # Publish message to provision project:
    gcloud pubsub topics publish ${google_pubsub_topic.provision_project.name} \
      --project=${var.project_id} \
      --message='{"projectId":"test-proj","groupEmail":"team@example.com","templateDashboardIds":[1,2]}'

    # Invoke HTTP function:
    curl -X POST ${google_cloudfunctions2_function.http_add_group.service_config[0].uri} \
      -H "Content-Type: application/json" \
      -d '{"groupEmail":"team@example.com","groupId":123}'

    # View function logs:
    gcloud functions logs read ${google_cloudfunctions2_function.provision_project.name} \
      --project=${var.project_id} --region=${var.region} --limit=50

    # Update Looker credentials:
    echo -n "your-client-id" | gcloud secrets versions add ${google_secret_manager_secret.looker_client_id.secret_id} --data-file=-
    echo -n "your-client-secret" | gcloud secrets versions add ${google_secret_manager_secret.looker_client_secret.secret_id} --data-file=-
    echo -n "https://your-instance.looker.com:19999" | gcloud secrets versions add ${google_secret_manager_secret.looker_base_url.secret_id} --data-file=-
  EOT
}
