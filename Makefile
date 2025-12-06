# Makefile for iam-looker project
# 2025 Python best practices

.PHONY: help install install-dev test lint format security check clean pre-commit terraform-init terraform-plan terraform-apply

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests with pytest
	pytest tests/ -v --tb=short

lint: ## Run ruff linter
	ruff check .

lint-fix: ## Run ruff linter with auto-fix
	ruff check . --fix

format: ## Format code with ruff
	ruff format .

format-check: ## Check code formatting without changes
	ruff format --check .

security: ## Run security checks with bandit
	bandit -r src/ -c pyproject.toml

security-all: ## Run all security scanners (bandit, pip-audit, gitleaks)
	@echo "Running comprehensive security scan..."
	@echo "\n==> Bandit (Python code security)"
	bandit -r src/ -c pyproject.toml || true
	@echo "\n==> pip-audit (dependency vulnerabilities)"
	pip-audit --requirement requirements.txt || true
	@echo "\n==> Gitleaks (secret detection)"
	docker run --rm -v $(PWD):/path zricethezav/gitleaks:latest detect --source="/path" -v || true
	@echo "\nSecurity scan complete!"

secrets-scan: ## Scan for secrets using gitleaks
	@command -v gitleaks >/dev/null 2>&1 || { \
		echo "Gitleaks not found. Installing..."; \
		echo "Run: brew install gitleaks (macOS) or download from https://github.com/gitleaks/gitleaks/releases"; \
		exit 1; \
	}
	gitleaks detect --source . -v

check: lint format-check security ## Run all checks (lint, format, security)

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

clean: ## Clean up cache and temporary files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true

# Terraform commands
terraform-init: ## Initialize Terraform
	cd terraform && terraform init

terraform-validate: ## Validate Terraform configuration
	cd terraform && terraform validate

terraform-plan: ## Plan Terraform changes
	cd terraform && terraform plan

terraform-apply: ## Apply Terraform changes
	cd terraform && terraform apply

terraform-checkov: ## Run Checkov security scan on Terraform
	checkov -d terraform/ --compact

# Combined commands
ci: check test ## Run CI checks (all checks + tests)

ci-security: check test security-all ## Run CI with comprehensive security scans

all: install-dev check test ## Install, check, and test everything
