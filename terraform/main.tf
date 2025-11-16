module "wif_github" {
  source                = "./modules/wif_github"
  project_id            = var.project_id
  project_number        = var.project_number
  pool_id               = var.pool_id
  provider_id           = var.provider_id
  repository            = var.repository
  ci_service_account_id = var.ci_service_account_id
}

# Package Python source
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = path.root
  excludes    = [".git", "terraform", "tests", "*.tfstate", "*.tfstate.backup", "__pycache__"]
  output_path = "${path.root}/build/function_source.zip"
}

resource "google_storage_bucket_object" "function_source" {
  name         = "function-source-${data.archive_file.function_zip.output_md5}.zip"
  bucket       = var.source_bucket
  source       = data.archive_file.function_zip.output_path
  content_type = "application/zip"
}

locals {
  openapi_spec = templatefile("${path.module}/openapi_template.yaml", {
    add_group_uri        = google_cloudfunctions2_function.http_add_group.service_config[0].uri
    create_folder_uri    = google_cloudfunctions2_function.http_create_folder.service_config[0].uri
    create_dashboard_uri = google_cloudfunctions2_function.http_create_dashboard.service_config[0].uri
  })
}

resource "google_api_gateway_api" "looker_api" {
  api_id       = "looker-automation"
  project      = var.project_id
  display_name = "Looker Automation API"
}

resource "google_api_gateway_api_config" "looker_api_cfg" {
  api           = google_api_gateway_api.looker_api.api_id
  project       = var.project_id
  api_config_id = "v1"

  openapi_documents {
    document {
      path     = "generated-openapi.yaml"
      contents = local.openapi_spec
    }
  }

  depends_on = [
    google_cloudfunctions2_function.http_add_group,
    google_cloudfunctions2_function.http_create_folder,
    google_cloudfunctions2_function.http_create_dashboard
  ]
}

resource "google_api_gateway_gateway" "looker_gw" {
  project    = var.project_id
  api_config = google_api_gateway_api_config.looker_api_cfg.id
  gateway_id = "looker-gw"
  location   = var.region

  gateway_config {
    network = var.vpc_network
  }
}
