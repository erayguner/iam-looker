# Development Guide

This guide covers development setup, coding standards, and workflows for the iam-looker project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Code Quality Tools](#code-quality-tools)
- [Testing](#testing)
- [Terraform](#terraform)
- [CI/CD](#cicd)

## Prerequisites

- Python 3.12 or higher
- Terraform 1.10.3 or higher
- Make (for running common commands)
- Git

## Development Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd iam-looker
```

### 2. Install Python dependencies

```bash
# Install development dependencies
make install-dev

# Or manually:
pip install -e ".[dev]"
```

### 3. Set up pre-commit hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually on all files
make pre-commit
```

### 4. Configure environment

Copy `.env.example` to `.env` and fill in your configuration:

```bash
cp .env.example .env
```

## Code Quality Tools

This project uses modern Python tooling following 2025 best practices.

### Ruff (Linter & Formatter)

Ruff is an extremely fast Python linter and formatter that replaces multiple tools (black, isort, flake8, etc.).

```bash
# Run linter
make lint

# Auto-fix issues
make lint-fix

# Format code
make format

# Check formatting without changes
make format-check
```

**Configuration:** See `[tool.ruff]` in `pyproject.toml`

### MyPy (Type Checking)

MyPy performs static type checking to catch type-related errors before runtime.

```bash
# Run type checking
make type-check
```

**Configuration:** See `[tool.mypy]` in `pyproject.toml`

### Bandit (Security Scanning)

Bandit scans for common security issues in Python code.

```bash
# Run security scan
make security
```

**Configuration:** See `[tool.bandit]` in `pyproject.toml`

### Run All Checks

```bash
# Run all checks (lint, format-check, type-check, security)
make check

# Run all checks + tests (CI simulation)
make ci
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=src --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names: `test_<functionality>_<scenario>`
- Use fixtures from `tests/conftest.py`
- Follow AAA pattern: Arrange, Act, Assert

Example:

```python
def test_provisioner_creates_user_successfully():
    # Arrange
    provisioner = Provisioner()
    user_data = {"email": "test@example.com"}

    # Act
    result = provisioner.create_user(user_data)

    # Assert
    assert result.status == "success"
```

## Terraform

### Setup

```bash
# Initialize Terraform
make terraform-init

# Validate configuration
make terraform-validate

# Plan changes
make terraform-plan
```

### Security Scanning

```bash
# Run Checkov security scan
make terraform-checkov
```

### Best Practices

1. **Encryption:** Use customer-managed encryption keys (CMEK) for sensitive resources
2. **Least Privilege:** Grant minimal necessary permissions
3. **Network Security:** Use VPC, private endpoints, and firewall rules
4. **Secrets Management:** Use Google Secret Manager, never commit secrets
5. **Resource Naming:** Use consistent, descriptive names with project prefix

## CI/CD

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

- Ruff linting and formatting
- MyPy type checking
- Bandit security scanning
- Terraform formatting and validation
- YAML/JSON/TOML validation
- Trailing whitespace removal
- Private key detection

### GitHub Actions

The CI pipeline runs:

1. All linters and formatters
2. Type checking
3. Security scanning
4. Unit tests
5. Terraform validation

## Common Commands

All common development tasks are available via the Makefile:

```bash
make help              # Show all available commands
make install           # Install production dependencies
make install-dev       # Install development dependencies
make test              # Run tests
make lint              # Run linter
make lint-fix          # Auto-fix linting issues
make format            # Format code
make security          # Run security checks
make type-check        # Run type checking
make check             # Run all checks
make pre-commit        # Run pre-commit hooks
make clean             # Clean cache files
make ci                # Run CI checks locally
```

## Coding Standards

### Python Style Guide

- Follow PEP 8 (enforced by Ruff)
- Use type hints for all functions
- Maximum line length: 100 characters
- Use double quotes for strings
- Import order: stdlib → third-party → local (enforced by Ruff)

### Naming Conventions

- **Variables/Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_CASE`
- **Private methods:** `_leading_underscore`

### Type Hints

All functions should have type hints:

```python
from typing import Dict, List, Optional

def process_user(user_id: str, options: Optional[Dict[str, str]] = None) -> bool:
    """Process a user with optional configuration."""
    ...
```

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Keep comments concise and meaningful

Example:

```python
def create_looker_user(email: str, role: str) -> Dict[str, Any]:
    """Create a new Looker user with specified role.

    Args:
        email: User's email address
        role: Role to assign (e.g., "Developer", "Viewer")

    Returns:
        Dictionary containing user details and creation status

    Raises:
        LookerAPIError: If user creation fails
    """
    ...
```

## Troubleshooting

### Pre-commit hooks failing

```bash
# Update hooks to latest version
pre-commit autoupdate

# Clear cache and reinstall
pre-commit clean
pre-commit install
```

### Type checking errors

```bash
# Ignore specific line
result = api_call()  # type: ignore[no-untyped-call]

# Add type stub for missing imports
pip install types-<package>
```

### Terraform validation fails

```bash
# Ensure you're authenticated
gcloud auth application-default login

# Set project
gcloud config set project <project-id>
```

## Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Checkov Documentation](https://www.checkov.io/)
