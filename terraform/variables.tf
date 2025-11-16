# ============================================================================
# Terraform Variables - Looker Automation Infrastructure
# ============================================================================

# GCP Project Configuration
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "project_number" {
  description = "GCP Project Number (for Workload Identity Federation)"
  type        = string
}

variable "region" {
  description = "GCP region for resource deployment"
  type        = string
  default     = "us-central1"
}

# Workload Identity Federation
variable "pool_id" {
  description = "Workload Identity Pool ID for GitHub Actions"
  type        = string
  default     = "github-pool"
}

variable "provider_id" {
  description = "Workload Identity Provider ID"
  type        = string
  default     = "github-provider"
}

variable "repository" {
  description = "GitHub repository in format: owner/repo"
  type        = string
}

variable "ci_service_account_id" {
  description = "Service account ID for CI/CD operations"
  type        = string
  default     = "ci-deployer"
}

# Cloud Functions Configuration
variable "python_runtime" {
  description = "Python runtime version for Cloud Functions"
  type        = string
  default     = "python312"
}

variable "function_timeout" {
  description = "Default timeout for Cloud Functions (seconds)"
  type        = number
  default     = 180
}

variable "max_instances" {
  description = "Maximum number of function instances"
  type        = number
  default     = 10
}

# Environment Labels
variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "labels" {
  description = "Additional labels to apply to all resources"
  type        = map(string)
  default     = {}
}
