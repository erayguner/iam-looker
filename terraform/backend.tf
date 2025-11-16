# Backend configuration for Terraform state
# Uncomment and configure after creating the state bucket
#
# terraform {
#   backend "gcs" {
#     bucket  = "YOUR_PROJECT_ID-terraform-state"
#     prefix  = "terraform/state"
#   }
# }
#
# To create the state bucket:
# gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_PROJECT_ID-terraform-state
# gsutil versioning set on gs://YOUR_PROJECT_ID-terraform-state
