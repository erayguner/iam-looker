# Module: wif_github

Provision Workload Identity Federation (WIF) for GitHub Actions without service account keys.

## Inputs
- `project_id`: GCP project ID
- `project_number`: Numeric project number (for principalSet path)
- `pool_id`: Workload Identity Pool ID
- `provider_id`: Provider ID within the pool
- `repository`: GitHub `org/repo` string matched in OIDC token
- `ci_service_account_id`: Service account ID used for impersonation

## Outputs
- `service_account_email`
- `workload_identity_provider_name`

## Usage
```hcl
module "wif_github" {
  source = "./modules/wif_github"
  project_id             = var.project_id
  project_number         = var.project_number
  pool_id                = var.pool_id
  provider_id            = var.provider_id
  repository             = var.repository
  ci_service_account_id  = var.ci_service_account_id
}
```

## Notes
- No service account key resource is created.
- Attribute condition restricts usage to the specified repository.

