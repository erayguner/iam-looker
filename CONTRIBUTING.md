# Contributing to iam-looker

Thank you for your interest in contributing to iam-looker! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Security](#security)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- Docker and Docker Compose (optional but recommended)
- Terraform 1.11.0+ (for infrastructure changes)

### Development Environment Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/erayguner/iam-looker.git
   cd iam-looker
   ```

2. **Set up development environment**

   ```bash
   make dev-setup
   ```

   This command will:
   - Install all development dependencies
   - Set up pre-commit hooks
   - Configure the development environment

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Verify installation**

   ```bash
   make test
   ```

### Using Docker (Recommended)

For a consistent development environment:

```bash
# Build development container
make docker-build

# Start development environment
make docker-up

# Access development shell
make docker-shell
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

### 2. Make Your Changes

- Write clean, well-documented code
- Follow the code standards (see below)
- Add or update tests as needed
- Update documentation if necessary

### 3. Run Quality Checks

Before committing, ensure your code passes all checks:

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test-cov

# Run security checks
make security

# Or run everything at once
make ci
```

### 4. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add new dashboard provisioning feature"
git commit -m "fix: resolve authentication timeout issue"
git commit -m "docs: update README with new examples"
```

Commit types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Standards

### Python Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

- **Line length**: 100 characters
- **Style guide**: PEP 8 compliant
- **Import sorting**: Automatically handled by Ruff
- **Type hints**: Required for all public functions

### Type Checking

We use `mypy` for static type checking:

```bash
make lint  # Includes mypy check
```

### Docstrings

Use Google-style docstrings:

```python
def provision_looker_project(project_id: str, group_email: str) -> ProvisionResult:
    """Provision a Looker project for the given GCP project.

    Args:
        project_id: The GCP project identifier.
        group_email: The Google Workspace group email.

    Returns:
        ProvisionResult containing the operation status and details.

    Raises:
        ProvisionError: If provisioning fails.
    """
    ...
```

### Code Organization

- Keep functions small and focused
- Use meaningful variable and function names
- Follow SOLID principles
- Prefer composition over inheritance
- Use Pydantic models for data validation

## Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_handler.py      # Handler tests
└── test_provisioner.py  # Provisioner tests
```

### Writing Tests

```python
import pytest
from iam_looker.provisioner import LookerProvisioner


@pytest.mark.unit
def test_create_folder_success(mock_looker_client):
    """Test successful folder creation."""
    provisioner = LookerProvisioner(mock_looker_client)
    result = provisioner.create_folder("test-project")

    assert result.success
    assert result.folder_id is not None


@pytest.mark.integration
def test_end_to_end_provisioning(integration_config):
    """Test complete provisioning workflow."""
    # Integration test implementation
    ...
```

### Test Coverage

- Maintain minimum 80% code coverage
- Write tests for all new features
- Include edge cases and error scenarios
- Use markers for test categorization:
  - `@pytest.mark.unit` - Unit tests
  - `@pytest.mark.integration` - Integration tests
  - `@pytest.mark.slow` - Slow-running tests

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test types
make test-unit
make test-integration

# Run in parallel
make test-parallel
```

## Terraform Guidelines

### Code Style

- Use consistent naming conventions
- Document all variables and outputs
- Use modules for reusable components
- Follow the [Terraform Style Guide](https://www.terraform.io/docs/language/syntax/style.html)

### Security

- Never commit `.tfvars` files
- Use variables for all sensitive data
- Enable Checkov security scanning
- Follow least privilege principle

### Terraform Workflow

```bash
# Format code
make terraform-fmt

# Validate configuration
make terraform-validate

# Run security scan
make terraform-security

# Plan changes
make terraform-plan
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Examples:

```
feat(provisioner): add support for custom dashboard templates

- Add template_ids parameter to provisioner
- Update documentation with examples
- Add tests for template provisioning

Closes #123
```

```
fix(auth): resolve WIF token expiration issue

The workload identity federation tokens were expiring prematurely.
Updated the token refresh logic to proactively renew tokens.

Fixes #456
```

## Pull Request Process

1. **Update Documentation**
   - Update README.md if adding features
   - Add docstrings to new functions/classes
   - Update SPEC.md if changing specifications

2. **Pass All Checks**
   - All CI checks must pass
   - Code coverage must not decrease
   - No security vulnerabilities introduced

3. **Request Review**
   - Assign at least one reviewer
   - Address all review comments
   - Keep PR scope focused and manageable

4. **PR Description Template**

   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   Describe testing performed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] All CI checks pass
   ```

5. **Merge Requirements**
   - At least one approval required
   - All conversations resolved
   - Branch up to date with main
   - No merge conflicts

## Security

### Reporting Security Issues

**Do not** create public issues for security vulnerabilities. Instead:

1. Email security concerns to the maintainers
2. Provide detailed description of the vulnerability
3. Include steps to reproduce if applicable
4. Allow time for fix before public disclosure

### Security Best Practices

- Never commit secrets, keys, or credentials
- Use environment variables for sensitive data
- Follow Workload Identity Federation for GCP
- Keep dependencies updated
- Run security scans regularly

### Pre-commit Security Checks

The pre-commit hooks include:

- Secret detection (detect-secrets)
- Security linting (Bandit)
- Dependency scanning (Safety)

## Additional Resources

- [Project README](README.md)
- [Architecture Documentation](README_ARCHITECTURE.md)
- [Specification](SPEC.md)
- [Issue Tracker](https://github.com/erayguner/iam-looker/issues)

## Questions?

If you have questions:

1. Check existing documentation
2. Search closed issues
3. Open a new issue with the `question` label

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

---

Thank you for contributing to iam-looker! 🎉
