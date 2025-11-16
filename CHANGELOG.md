# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive development tooling and CI/CD setup
- Pre-commit hooks for code quality
- GitHub Actions workflows for CI/CD
- Docker support with multi-stage builds
- Makefile for common development tasks
- Comprehensive testing setup with pytest and coverage
- Security scanning with Bandit, Checkov, and Safety
- Type checking with mypy
- Code formatting with Ruff
- Dependabot configuration for automated dependency updates
- EditorConfig for consistent coding styles
- CONTRIBUTING.md with detailed contribution guidelines
- Terraform validation and security scanning in CI

### Changed
- Modernized pyproject.toml with comprehensive tool configurations
- Updated Python dependencies to latest versions
- Enhanced .gitignore with modern patterns
- Improved documentation structure

### Security
- Added Workload Identity Federation (WIF) support
- Implemented secret scanning in CI/CD
- Added security scanning with multiple tools
- Enforced keyless authentication patterns

## [0.1.2] - 2025-11-15

### Added
- Initial implementation for Looker provisioning automation
- Pydantic models for data validation
- Structured logging support
- Basic test coverage

### Changed
- Adopted src/ layout structure
- Migrated to Python 3.12+
- Updated to use modern Python best practices

## [0.1.1] - Previous

### Added
- Basic provisioning functionality
- Terraform infrastructure code
- Legacy modules

---

[Unreleased]: https://github.com/erayguner/iam-looker/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/erayguner/iam-looker/releases/tag/v0.1.2
[0.1.1]: https://github.com/erayguner/iam-looker/releases/tag/v0.1.1
