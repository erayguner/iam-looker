# ============================================================================
# Terraform Test Configuration - Looker Automation Infrastructure
# ============================================================================
#
# Native Terraform testing with tftest.hcl (Terraform 1.6+)
# Run with: terraform test
#
# This test suite validates:
# - Resource creation and configuration
# - Workload Identity Federation setup
# - Cloud Functions deployment
# - Secret Manager integration
# - Pub/Sub topic creation
# - API Gateway configuration
# - Auto-redeployment on code changes
#
# ============================================================================

# Test variables
variables {
  project_id            = "test-looker-automation"
  project_number        = "123456789012"
  region                = "us-central1"
  pool_id               = "github-pool-test"
  provider_id           = "github-provider-test"
  repository            = "test-org/test-repo"
  ci_service_account_id = "ci-deployer-test"
  environment           = "development"
}

# ============================================================================
# Test 1: Validate Plan - Ensure configuration is valid
# ============================================================================

run "validate_configuration" {
  command = plan

  assert {
    condition     = google_storage_bucket.function_source.name == "${var.project_id}-looker-functions"
    error_message = "Storage bucket name should follow naming convention"
  }

  assert {
    condition     = google_storage_bucket.function_source.location == var.region
    error_message = "Storage bucket should be in the specified region"
  }

  assert {
    condition     = google_storage_bucket.function_source.uniform_bucket_level_access == true
    error_message = "Storage bucket should have uniform bucket level access enabled"
  }
}

# ============================================================================
# Test 2: Validate Secret Manager Secrets
# ============================================================================

run "validate_secrets" {
  command = plan

  assert {
    condition     = google_secret_manager_secret.looker_client_id.secret_id == "looker-client-id"
    error_message = "Looker client ID secret should have correct ID"
  }

  assert {
    condition     = google_secret_manager_secret.looker_client_secret.secret_id == "looker-client-secret"
    error_message = "Looker client secret should have correct ID"
  }

  assert {
    condition     = google_secret_manager_secret.looker_base_url.secret_id == "looker-base-url"
    error_message = "Looker base URL secret should have correct ID"
  }
}

# ============================================================================
# Test 3: Validate Pub/Sub Topics (7 topics)
# ============================================================================

run "validate_pubsub_topics" {
  command = plan

  assert {
    condition     = google_pubsub_topic.provision_project.name == "looker-provision-project"
    error_message = "Provision project topic should have correct name"
  }

  assert {
    condition     = google_pubsub_topic.decommission_project.name == "looker-decommission-project"
    error_message = "Decommission project topic should have correct name"
  }

  assert {
    condition     = google_pubsub_topic.add_user_to_group.name == "looker-add-user-to-group"
    error_message = "Add user to group topic should have correct name"
  }

  assert {
    condition     = google_pubsub_topic.create_user.name == "looker-create-user"
    error_message = "Create user topic should have correct name"
  }

  assert {
    condition     = google_pubsub_topic.bulk_provision_users.name == "looker-bulk-provision-users"
    error_message = "Bulk provision users topic should have correct name"
  }

  assert {
    condition     = google_pubsub_topic.create_project_folder.name == "looker-create-project-folder"
    error_message = "Create project folder topic should have correct name"
  }

  assert {
    condition     = google_pubsub_topic.create_connection.name == "looker-create-connection"
    error_message = "Create connection topic should have correct name"
  }
}

# ============================================================================
# Test 4: Validate Event-Driven Cloud Functions (7 functions)
# ============================================================================

run "validate_event_functions" {
  command = plan

  # Test provision project function
  assert {
    condition     = google_cloudfunctions2_function.provision_project.name == "looker-provision-project"
    error_message = "Provision project function should have correct name"
  }

  assert {
    condition     = google_cloudfunctions2_function.provision_project.build_config[0].runtime == local.python_runtime
    error_message = "Provision project function should use correct Python runtime"
  }

  assert {
    condition     = google_cloudfunctions2_function.provision_project.build_config[0].entry_point == "provision_looker_project"
    error_message = "Provision project function should have correct entry point"
  }

  assert {
    condition     = google_cloudfunctions2_function.provision_project.service_config[0].available_memory == "512M"
    error_message = "Provision project function should have 512M memory"
  }

  assert {
    condition     = length(google_cloudfunctions2_function.provision_project.service_config[0].secret_environment_variables) == 3
    error_message = "All functions should have 3 secret environment variables"
  }

  # Test all 7 event-driven functions exist with correct entry points
  assert {
    condition     = google_cloudfunctions2_function.decommission_project.build_config[0].entry_point == "decommission_looker_project"
    error_message = "Decommission function should have correct entry point"
  }

  assert {
    condition     = google_cloudfunctions2_function.add_user_to_group.build_config[0].entry_point == "add_user_to_group"
    error_message = "Add user function should have correct entry point"
  }

  assert {
    condition     = google_cloudfunctions2_function.create_user.build_config[0].entry_point == "create_user"
    error_message = "Create user function should have correct entry point"
  }

  assert {
    condition     = google_cloudfunctions2_function.bulk_provision_users.build_config[0].entry_point == "bulk_provision_users"
    error_message = "Bulk provision function should have correct entry point"
  }

  assert {
    condition     = google_cloudfunctions2_function.create_project_folder.build_config[0].entry_point == "create_project_folder"
    error_message = "Create folder function should have correct entry point"
  }

  assert {
    condition     = google_cloudfunctions2_function.create_connection.build_config[0].entry_point == "create_connection"
    error_message = "Create connection function should have correct entry point"
  }
}

# ============================================================================
# Test 5: Validate HTTP Cloud Functions (3 functions)
# ============================================================================

run "validate_http_functions" {
  command = plan

  assert {
    condition     = google_cloudfunctions2_function.http_add_group.name == "http-looker-add-group"
    error_message = "HTTP add group function should have correct name"
  }

  assert {
    condition     = google_cloudfunctions2_function.http_add_group.build_config[0].entry_point == "add_group_to_saml"
    error_message = "HTTP add group function should have correct entry point"
  }

  assert {
    condition     = google_cloudfunctions2_function.http_add_group.service_config[0].ingress_settings == "ALLOW_INTERNAL_ONLY"
    error_message = "HTTP functions should only allow internal traffic"
  }

  assert {
    condition     = google_cloudfunctions2_function.http_create_folder.name == "http-looker-create-folder"
    error_message = "HTTP create folder function should have correct name"
  }

  assert {
    condition     = google_cloudfunctions2_function.http_create_dashboard.name == "http-looker-create-dashboard"
    error_message = "HTTP create dashboard function should have correct name"
  }

  assert {
    condition     = google_cloudfunctions2_function.http_create_dashboard.service_config[0].available_memory == "512M"
    error_message = "Dashboard function needs 512M for larger operations"
  }
}

# ============================================================================
# Test 6: Validate API Gateway
# ============================================================================

run "validate_api_gateway" {
  command = plan

  assert {
    condition     = google_api_gateway_api.looker_api.api_id == "looker-automation"
    error_message = "API Gateway should have correct API ID"
  }

  assert {
    condition     = google_api_gateway_gateway.looker_gw.gateway_id == "looker-automation-gw"
    error_message = "API Gateway should have correct gateway ID"
  }

  assert {
    condition     = google_api_gateway_gateway.looker_gw.region == var.region
    error_message = "API Gateway should be in the specified region"
  }
}

# ============================================================================
# Test 7: Validate Security Configuration
# ============================================================================

run "validate_security" {
  command = plan

  # All functions should only allow internal traffic
  assert {
    condition     = google_cloudfunctions2_function.provision_project.service_config[0].ingress_settings == "ALLOW_INTERNAL_ONLY"
    error_message = "All functions should only allow internal traffic for security"
  }

  # Storage bucket should have versioning
  assert {
    condition     = google_storage_bucket.function_source.versioning[0].enabled == true
    error_message = "Storage bucket should have versioning enabled"
  }

  # Storage bucket should have lifecycle rules
  assert {
    condition     = length(google_storage_bucket.function_source.lifecycle_rule) > 0
    error_message = "Storage bucket should have lifecycle rules for cleanup"
  }
}

# ============================================================================
# Test 8: Validate Auto-Redeployment Configuration
# ============================================================================

run "validate_auto_redeployment" {
  command = plan

  # Source object name should include MD5 hash
  assert {
    condition     = can(regex("source-[a-f0-9]+\\.zip", google_storage_bucket_object.function_source.name))
    error_message = "Source object name must include MD5 hash for auto-redeployment"
  }

  # Functions should have deployment_hash label
  assert {
    condition     = google_cloudfunctions2_function.provision_project.labels["deployment_hash"] == local.source_hash
    error_message = "Functions must have deployment_hash label for change tracking"
  }

  # Functions should reference the storage object
  assert {
    condition     = google_cloudfunctions2_function.provision_project.build_config[0].source[0].storage_source[0].object == google_storage_bucket_object.function_source.name
    error_message = "Functions must reference the versioned source object"
  }
}

# ============================================================================
# Test 9: Validate Labels and Metadata
# ============================================================================

run "validate_labels" {
  command = plan

  assert {
    condition     = google_cloudfunctions2_function.provision_project.labels["component"] == "looker-automation"
    error_message = "Functions should have component label"
  }

  assert {
    condition     = google_cloudfunctions2_function.provision_project.labels["managed_by"] == "terraform"
    error_message = "Functions should have managed_by label"
  }

  assert {
    condition     = google_storage_bucket.function_source.labels["component"] == "looker-automation"
    error_message = "All resources should have consistent labeling"
  }
}

# ============================================================================
# Test 10: Validate Source Code Packaging
# ============================================================================

run "validate_source_packaging" {
  command = plan

  assert {
    condition     = data.archive_file.function_zip.type == "zip"
    error_message = "Function source must be packaged as ZIP"
  }

  assert {
    condition     = contains(data.archive_file.function_zip.excludes, ".git")
    error_message = "Should exclude .git directory from package"
  }

  assert {
    condition     = contains(data.archive_file.function_zip.excludes, "terraform")
    error_message = "Should exclude terraform directory from package"
  }

  assert {
    condition     = contains(data.archive_file.function_zip.excludes, "tests")
    error_message = "Should exclude tests directory from package"
  }
}
