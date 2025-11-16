# Specification: iam-looker

Version: 0.1.2
Status: Draft
Owner: Data Platform Engineering
Last Updated: 2025-01-15

## 1. Purpose
Automate onboarding of a Google Cloud project into Looker by provisioning group-based access, creating project folder(s), and cloning template dashboards with project-specific substitutions.

## 2. Scope
...existing code...

## 6. Configuration
Environment variables:
- LOOKERSDK_BASE_URL
- LOOKERSDK_CLIENT_ID
- LOOKERSDK_CLIENT_SECRET
- LOOKERSDK_VERIFY_SSL (default true)
- DEFAULT_TEMPLATE_FOLDER_ID (optional)
- DEFAULT_TEMPLATE_DASHBOARD_IDS (comma-separated ints)

Infrastructure identity (CI/CD) MUST use Workload Identity Federation (WIF). No service account JSON keys may be created or stored. Terraform code MUST NOT include `google_service_account_key` resources.

## 7. Idempotency Rules
...existing code...

## 12. Security
- Credentials only via env vars or Secret Manager references.
- Minimal scopes for Looker API user.
- No long-lived service account keys; adopt Workload Identity Federation for external identity (e.g. GitHub OIDC, Cloud Build).
- Enforce via policy: Org Policy `constraints/iam.disableServiceAccountKeyCreation` (if permissible) or project-level monitoring for key creation events.

### Workload Identity Federation Pattern
GitHub OIDC -> Workload Identity Pool -> Service Account (no key). Terraform example stub:
```hcl
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
```
No `google_service_account_key` usage permitted.

### Keyless Authentication Requirement
To further enhance security, all configurations and deployments must utilize keyless authentication methods. This is in alignment with the best practices for using Workload Identity Federation. Ensure that no service account keys are used or stored in any part of the infrastructure or application code.

## 13. Performance Targets
...existing code...

## 14. Testing Strategy
...existing code...

## 15. Deployment
...existing code...

## 16. Future Enhancements
- Backoff/retry wrapper.
- Metric emission (Prometheus/OpenTelemetry).
- Group role mapping matrix.
- Template registry service.
- Multiple project batch ingestion.
- Org policy enforcement / automated audit for key creation events.

## 17. Open Questions
- Exact field names for SAML config group mapping (verify with API model).
- Preferred folder parent location (root vs shared parent).
- Need for additional attribute filters on WIF provider (e.g. workflow ref).

## 18. Acceptance Criteria
...existing code...

## 19. Implementation Notes (2025 Structure)
- `iam_looker.models.ProvisionPayload` enforces schema & regex validation.
- `iam_looker.handler.handle_event` is the single integration entrypoint.
- Legacy flat modules will be deprecated in a future version (>0.2.0).

Refer to README '2025 Python Best Practices Adopted' for structural rationale.

## 20. Function Decomposition
Tasks split into discrete Cloud Functions (Pub/Sub triggered):
- add_group_to_saml
- create_project_folder
- create_dashboard_from_template
Composite orchestration retained separately; API Gateway provides internal access paths. All functions internal-only ingress.

## 21. Invocation Model
Each task exposed via two paths:
- Pub/Sub event function for asynchronous automation.
- HTTP internal function for on-demand invocation via API Gateway (VPC attached, no public ingress).
Security relies on IAM + network attachment; no service account keys.

## 22. Secret Management Policy
- All sensitive Looker credentials (client_id, client_secret) stored in Secret Manager.
- Cloud Functions use `secret_environment_variables` to fetch latest version.
- `terraform.tfvars` limited to non-secret infra identifiers (project_id, project_number, region, source_bucket, vpc_network).
- No plaintext secrets in Terraform state or code.
- Secret rotation strategy: update Secret Manager version; functions pick up new version tag (e.g. `latest`).

---
This spec governs implementation; modifications require version bump & stakeholder review.
