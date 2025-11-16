resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = var.pool_id
  project                   = var.project_id
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = var.provider_id
  project                            = var.project_id
  display_name                       = "GitHub Provider"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  attribute_condition = "assertion.repository == \"${var.repository}\""
}

resource "google_service_account" "ci" {
  account_id   = var.ci_service_account_id
  project      = var.project_id
  display_name = "CI Deployer"
}

resource "google_service_account_iam_binding" "ci_wif" {
  service_account_id = google_service_account.ci.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/projects/${var.project_number}/locations/global/workloadIdentityPools/${var.pool_id}/attribute.repository/${var.repository}"
  ]
}
