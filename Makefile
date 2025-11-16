.PHONY: help install install-dev clean lint format test test-cov security docker-build docker-up docker-down terraform-init terraform-plan terraform-validate pre-commit-install pre-commit-run build release

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Configuration
PYTHON := python3
PIP := pip
DOCKER_COMPOSE := docker-compose
TERRAFORM := terraform
PRE_COMMIT := pre-commit

# Directories
SRC_DIR := src/iam_looker
TEST_DIR := tests
TERRAFORM_DIR := terraform
COVERAGE_DIR := htmlcov

help: ## Show this help message
	@echo "$(BLUE)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}'

# Installation targets
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev,terraform,all]"
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

# Cleaning targets
clean: ## Remove build artifacts, cache files, and test reports
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf $(COVERAGE_DIR)
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# Code quality targets
lint: ## Run linters (ruff, mypy, bandit)
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR)
	mypy $(SRC_DIR) || true
	bandit -r $(SRC_DIR) -c pyproject.toml
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff format $(SRC_DIR) $(TEST_DIR)
	ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Formatting complete$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	ruff format --check $(SRC_DIR) $(TEST_DIR)
	ruff check $(SRC_DIR) $(TEST_DIR)

# Testing targets
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest -v

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest -v --cov --cov-report=html --cov-report=term --cov-report=xml
	@echo "$(GREEN)✓ Coverage report generated in $(COVERAGE_DIR)$(NC)"

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -v -m unit

test-integration: ## Run only integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -v -m integration

test-parallel: ## Run tests in parallel
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	pytest -v -n auto

# Security targets
security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	bandit -r $(SRC_DIR) -c pyproject.toml
	safety check --json || true
	@echo "$(GREEN)✓ Security scan complete$(NC)"

security-full: ## Run comprehensive security scan
	@echo "$(BLUE)Running comprehensive security scan...$(NC)"
	bandit -r $(SRC_DIR) -c pyproject.toml
	safety check --json || true
	pip-audit || true
	@echo "$(GREEN)✓ Comprehensive security scan complete$(NC)"

# Docker targets
docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-build-prod: ## Build production Docker image
	@echo "$(BLUE)Building production Docker image...$(NC)"
	docker build -t iam-looker:latest -f Dockerfile .
	@echo "$(GREEN)✓ Production Docker image built$(NC)"

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Docker containers started$(NC)"

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Docker containers stopped$(NC)"

docker-shell: ## Open shell in development container
	@echo "$(BLUE)Opening shell in development container...$(NC)"
	$(DOCKER_COMPOSE) run --rm dev /bin/bash

docker-test: ## Run tests in Docker container
	@echo "$(BLUE)Running tests in Docker container...$(NC)"
	$(DOCKER_COMPOSE) run --rm test

docker-logs: ## View Docker container logs
	$(DOCKER_COMPOSE) logs -f

# Terraform targets
terraform-init: ## Initialize Terraform
	@echo "$(BLUE)Initializing Terraform...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) init
	@echo "$(GREEN)✓ Terraform initialized$(NC)"

terraform-validate: ## Validate Terraform configuration
	@echo "$(BLUE)Validating Terraform configuration...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) fmt -check
	cd $(TERRAFORM_DIR) && $(TERRAFORM) validate
	@echo "$(GREEN)✓ Terraform validation complete$(NC)"

terraform-plan: ## Create Terraform plan
	@echo "$(BLUE)Creating Terraform plan...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) plan
	@echo "$(GREEN)✓ Terraform plan created$(NC)"

terraform-fmt: ## Format Terraform files
	@echo "$(BLUE)Formatting Terraform files...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) fmt -recursive
	@echo "$(GREEN)✓ Terraform files formatted$(NC)"

terraform-security: ## Run Checkov security scan on Terraform
	@echo "$(BLUE)Running Checkov security scan...$(NC)"
	checkov -d $(TERRAFORM_DIR) --framework terraform --quiet
	@echo "$(GREEN)✓ Terraform security scan complete$(NC)"

# Pre-commit targets
pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	$(PRE_COMMIT) install
	$(PRE_COMMIT) install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

pre-commit-run: ## Run pre-commit on all files
	@echo "$(BLUE)Running pre-commit on all files...$(NC)"
	$(PRE_COMMIT) run --all-files
	@echo "$(GREEN)✓ Pre-commit checks complete$(NC)"

pre-commit-update: ## Update pre-commit hooks
	@echo "$(BLUE)Updating pre-commit hooks...$(NC)"
	$(PRE_COMMIT) autoupdate
	@echo "$(GREEN)✓ Pre-commit hooks updated$(NC)"

# Build targets
build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Distribution packages built$(NC)"

build-check: build ## Build and check distribution packages
	@echo "$(BLUE)Checking distribution packages...$(NC)"
	twine check dist/*
	@echo "$(GREEN)✓ Distribution packages are valid$(NC)"

# Release targets
release-test: build-check ## Upload to Test PyPI
	@echo "$(YELLOW)Uploading to Test PyPI...$(NC)"
	twine upload --repository testpypi dist/*
	@echo "$(GREEN)✓ Uploaded to Test PyPI$(NC)"

release: build-check ## Upload to PyPI
	@echo "$(RED)Uploading to PyPI...$(NC)"
	@read -p "Are you sure you want to upload to PyPI? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		twine upload dist/*; \
		echo "$(GREEN)✓ Uploaded to PyPI$(NC)"; \
	else \
		echo "$(YELLOW)Upload cancelled$(NC)"; \
	fi

# Development workflow targets
dev-setup: install-dev pre-commit-install ## Complete development environment setup
	@echo "$(GREEN)✓ Development environment setup complete!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. Copy .env.example to .env and configure"
	@echo "  2. Run 'make test' to verify everything works"
	@echo "  3. Run 'make pre-commit-run' to check code quality"

ci: clean lint test-cov security ## Run all CI checks locally
	@echo "$(GREEN)✓ All CI checks passed!$(NC)"

check: lint test-cov ## Quick check (lint + test with coverage)
	@echo "$(GREEN)✓ Quick checks passed!$(NC)"

all: clean install-dev lint test-cov security build ## Run complete build pipeline
	@echo "$(GREEN)✓ Complete build pipeline finished!$(NC)"

# Utility targets
show-coverage: test-cov ## Open coverage report in browser
	@echo "$(BLUE)Opening coverage report...$(NC)"
	@$(PYTHON) -m webbrowser -t "file://$(PWD)/$(COVERAGE_DIR)/index.html" 2>/dev/null || \
	echo "Please open $(COVERAGE_DIR)/index.html in your browser"

version: ## Show project version
	@echo "$(BLUE)Project version:$(NC)"
	@grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'

deps-update: ## Update dependencies (use with caution)
	@echo "$(YELLOW)Updating dependencies...$(NC)"
	pip install --upgrade pip setuptools wheel
	pip list --outdated
	@echo "$(YELLOW)Review outdated packages above and update requirements.txt manually$(NC)"

.DEFAULT_GOAL := help
