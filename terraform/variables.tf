variable "project_id" {
  type = string
}

variable "project_number" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "pool_id" {
  type    = string
  default = "github-pool"
}

variable "provider_id" {
  type    = string
  default = "github-provider"
}

variable "repository" {
  type        = string
  description = "GitHub org/repo for OIDC"
}

variable "ci_service_account_id" {
  type    = string
  default = "ci-deployer"
}

variable "source_bucket" {
  type = string
}

variable "source_object" {
  type = string
}

variable "vpc_network" {
  type        = string
  description = "Full self_link of VPC network for internal API Gateway"
}

variable "looker_base_url" {
  type        = string
  description = "Looker instance base URL"
}

variable "looker_client_id" {
  type        = string
  description = "Client ID (prefer Secret Manager, variable only for legacy)"
}

variable "looker_client_secret" {
  type        = string
  description = "Client Secret (prefer Secret Manager, variable only for legacy)"
}

variable "kms_key_name" {
  type        = string
  description = "Customer-managed encryption key for PubSub topics (optional, recommended for production)"
  default     = null
}
