variable "project_id" { type = string }
variable "project_number" { type = string }
variable "region" { type = string  default = "us-central1" }
variable "pool_id" { type = string  default = "github-pool" }
variable "provider_id" { type = string  default = "github-provider" }
variable "repository" { type = string  description = "GitHub org/repo for OIDC" }
variable "ci_service_account_id" { type = string  default = "ci-deployer" }
variable "source_bucket" { type = string }
variable "source_object" { type = string }
variable "vpc_network" { type = string description = "Full self_link of VPC network for internal API Gateway" }
