variables {
  project_id = "test-project"
  project_number = "123456789"
  region = "us-central1"
  pool_id = "github-pool"
  provider_id = "github-provider"
  repository = "org/repo"
  ci_service_account_id = "ci-deployer"
  source_bucket = "dummy-bucket"
  source_object = "source.zip"
  looker_base_url = "https://looker.example.com:19999"
  looker_client_id = "client"
  looker_client_secret = "secret"
}

run "plan" {
  command = plan
  expect_failures = []
}
