# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive GitHub Actions workflows for CI/CD
  - CI workflow with linting, testing, security scanning, Terraform validation
  - Deploy Cloud Functions workflow for automated deployments
  - Deploy Terraform workflow with plan/apply/destroy actions
  - Release workflow with automated changelog generation
  - CodeQL security analysis workflow
  - PR comment workflows for CI results, coverage reports, and status summaries
- Comprehensive development tooling
  - Pre-commit hooks with 15+ checks (Ruff, MyPy, Bandit, Terraform, etc.)
  - Docker support with development and production Dockerfiles
  - Docker Compose for local development
  - Makefile with 30+ development commands
- Testing and quality infrastructure
  - Pytest with coverage, asyncio, mock, and xdist support
  - Type checking with MyPy in strict mode
  - Code formatting and linting with Ruff 0.9.2
  - Security scanning with Bandit, Checkov, and Safety
- Documentation
  - README.md modernized with badges and comprehensive documentation
  - WORKFLOWS.md with complete CI/CD documentation
  - CONTRIBUTING.md with detailed contribution guidelines
  - SECURITY.md with vulnerability reporting process
  - CODE_OF_CONDUCT.md for community standards
  - Issue and pull request templates
- Development infrastructure
  - EditorConfig for consistent coding styles
  - Dependabot for automated dependency updates
  - .gitignore with modern patterns

### Changed

- Updated all tool versions to latest 2025 releases
  - Terraform: 1.11.0
  - Ruff: 0.9.2
  - MyPy: 1.14.1
  - Pytest: 8.3.0
  - Bandit: 1.8.0
  - Checkov: 3.2.0
  - Pre-commit hooks updated to latest versions
- Modernized pyproject.toml with comprehensive tool configurations
- Enhanced GitHub Actions workflows with improved features
  - PR comments with CI results and coverage reports
  - Enhanced Terraform plan comments with change summaries
  - Multi-environment deployment support (dev/staging/prod)
- Improved documentation structure and clarity

### Removed

- Unnecessary AI agent instruction files (.github/*.instructions.md)
- README_ARCHITECTURE.md (content consolidated into SPEC.md and README.md)
- NOTICE.md (redundant with LICENSE)

### Security

- Enforced Workload Identity Federation (WIF) for all CI/CD (no service account keys)
- Added secret scanning in CI/CD workflows
- Implemented multi-layer security scanning (Bandit, Checkov, Safety, CodeQL)
- Added secret detection in pre-commit hooks

## [0.1.2] - 2025-01-15

### Added

- Initial implementation for Looker provisioning automation
- Pydantic models for data validation
- Structured logging support with JSON formatting
- Basic test coverage
- Cloud Functions entry points for all operations
- Terraform infrastructure with modules

### Changed

- Adopted src/ layout structure (iam_looker package)
- Migrated to Python 3.12+ as minimum version
- Updated to use modern Python best practices
- Centralized configuration with Pydantic settings

### Security

- Implemented keyless authentication patterns
- Added Workload Identity Federation module

## [0.1.1] - 2024-12-01

### Added

- Basic provisioning functionality
- Terraform infrastructure code
- Legacy modules (config.py, looker_provisioner.py, dashboard_template.py)
- Initial Cloud Functions deployment

---

[Unreleased]: https://github.com/erayguner/iam-looker/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/erayguner/iam-looker/releases/tag/v0.1.2
[0.1.1]: https://github.com/erayguner/iam-looker/releases/tag/v0.1.1
