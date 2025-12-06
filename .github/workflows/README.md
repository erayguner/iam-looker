# GitHub Actions Workflows

This directory contains CI/CD workflows for automated testing, security scanning, and quality checks.

## Workflows Overview

### 🔄 CI - Security & Quality Checks (`ci.yml`)

**Triggers:** Push to main/develop/claude branches, Pull Requests

**Jobs:**
1. **Secret Scanning** - Gitleaks
2. **Python Security** - Ruff, MyPy, Bandit
3. **Terraform Security** - Checkov, validation
4. **Dependency Scanning** - pip-audit
5. **Pre-commit Hooks** - All configured hooks
6. **Tests** - Pytest with coverage
7. **SAST** - Semgrep static analysis
8. **CodeQL** - Advanced code analysis
9. **Security Summary** - Consolidated report

**Runtime:** ~10-15 minutes

### 🔒 Secret Scanning (`secret-scanning.yml`)

**Triggers:** Push, Pull Requests, Daily (2:00 AM UTC), Manual

**Jobs:**
1. **Gitleaks** - High-performance secret detection
2. **TruffleHog** - Entropy-based secret scanning
3. **Detect-secrets** - Baseline comparison
4. **Custom Patterns** - Project-specific secret patterns

**Runtime:** ~3-5 minutes

### 📅 Weekly Security Scan (`security-scan.yml`)

**Triggers:** Weekly (Monday 9:00 AM UTC), Manual

**Jobs:**
- Comprehensive security audit with all tools
- Bandit (Python code security)
- Safety (dependency vulnerabilities)
- pip-audit (package vulnerabilities)
- Checkov (Terraform security)
- Trivy (comprehensive scanning)
- SARIF upload to GitHub Security

**Runtime:** ~8-12 minutes

## Security Tools Used

### Secret Detection
- **Gitleaks** - Fast, configurable secret scanner
- **TruffleHog** - High-entropy string detection
- **Detect-secrets** - Baseline-based detection
- **Pre-commit** - Pre-commit hook integration

### Code Security
- **Bandit** - Python security linter
- **Semgrep** - SAST with custom rules
- **CodeQL** - GitHub's semantic analysis
- **Ruff** - Fast linter with security rules

### Dependency Security
- **pip-audit** - OSV database vulnerability scanner
- **Safety** - Python package vulnerability checker
- **Dependabot** - Automated dependency updates

### Infrastructure Security
- **Checkov** - Terraform/IaC security scanner
- **Trivy** - Container and filesystem scanner
- **Terraform Validate** - Configuration validation

## Artifacts Generated

Each workflow produces artifacts for review:

- `bandit-security-report` - Python security findings
- `checkov-security-report` - Terraform security findings
- `pip-audit-report` - Dependency vulnerabilities
- `semgrep-results` - SAST findings
- `coverage-report` - Test coverage reports
- `secrets-baseline` - Secret detection baseline

## Required Secrets

Configure these in repository settings:

- `GITHUB_TOKEN` - Automatically provided
- `GITLEAKS_LICENSE` - Optional, for Gitleaks Pro features
- `CODECOV_TOKEN` - Optional, for Codecov integration

## Workflow Status Badges

Add these to your README:

```markdown
[![CI](https://github.com/erayguner/iam-looker/workflows/CI%20-%20Security%20&%20Quality%20Checks/badge.svg)](https://github.com/erayguner/iam-looker/actions?query=workflow%3A"CI+-+Security+%26+Quality+Checks")
[![Security Scan](https://github.com/erayguner/iam-looker/workflows/Weekly%20Security%20Scan/badge.svg)](https://github.com/erayguner/iam-looker/actions?query=workflow%3A"Weekly+Security+Scan")
[![Secret Scanning](https://github.com/erayguner/iam-looker/workflows/Secret%20Scanning/badge.svg)](https://github.com/erayguner/iam-looker/actions?query=workflow%3A"Secret+Scanning")
```

## Local Testing

Run checks locally before pushing:

```bash
# Install pre-commit hooks
pre-commit install

# Run all pre-commit checks
pre-commit run --all-files

# Run security checks
make security

# Run all checks
make check

# Run tests
make test
```

## Workflow Permissions

Each workflow uses minimal required permissions:

- `contents: read` - Read repository contents
- `security-events: write` - Upload security findings
- `pull-requests: write` - Comment on PRs
- `issues: write` - Create security issues

## Troubleshooting

### Workflow Fails on Secret Detection

1. Review the Gitleaks/TruffleHog output
2. Check `.gitleaks.toml` allowlist
3. Remove or encrypt the detected secret
4. Update `.secrets.baseline` if false positive

### Checkov Failures

1. Review Checkov output for failed checks
2. Fix security issues or add skip annotations
3. Update Terraform configuration
4. Re-run workflow

### Dependency Vulnerabilities

1. Review pip-audit/Safety output
2. Update vulnerable dependencies
3. Check for available patches
4. Consider alternative packages if needed

### CodeQL Timeouts

1. CodeQL can take 15-20 minutes on large repos
2. Consider using `queries: security-only` for faster scans
3. Check CodeQL documentation for optimization

## Maintenance

### Weekly Tasks
- ✅ Review security scan results
- ✅ Merge Dependabot PRs
- ✅ Update outdated dependencies

### Monthly Tasks
- ✅ Review and update workflow configurations
- ✅ Update security tool versions
- ✅ Review security policy
- ✅ Audit allowlisted patterns

### Quarterly Tasks
- ✅ Comprehensive security audit
- ✅ Review and update security documentation
- ✅ Security tool evaluation

## Contributing

When adding new workflows:

1. Test locally with `act` or similar tools
2. Use minimal required permissions
3. Add appropriate documentation
4. Include artifact uploads for debugging
5. Add failure notifications if needed

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Gitleaks Documentation](https://github.com/gitleaks/gitleaks)
- [Checkov Documentation](https://www.checkov.io/)
- [Semgrep Documentation](https://semgrep.dev/docs/)
- [CodeQL Documentation](https://codeql.github.com/docs/)
