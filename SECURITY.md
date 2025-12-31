# Security Policy

## Reporting Security Vulnerabilities

We take the security of iam-looker seriously. If you discover a security vulnerability, please follow these steps:

### 🔒 Private Disclosure

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security issues by:

1. **Email:** Send details to the repository owner
2. **GitHub Security Advisories:** Use the [Security tab](../../security/advisories/new) to create a private security advisory

### 📝 What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if available)
- Your contact information

### ⏱️ Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 5 business days
- **Fix Timeline:** Varies by severity (critical issues prioritized)

## Security Measures

### Automated Security Scanning

This project uses multiple automated security scanning tools:

#### Secret Scanning
- **Gitleaks** - Detects hardcoded secrets, passwords, API keys
- **TruffleHog** - Scans for high-entropy strings and secrets
- **Detect-secrets** - Baseline-based secret detection
- **Pre-commit hooks** - Prevents secrets from being committed

#### Code Security
- **Bandit** - Python security linter
- **Semgrep** - Static analysis security testing (SAST)
- **CodeQL** - Advanced semantic code analysis
- **Ruff** - Security-focused linting rules

#### Dependency Security
- **pip-audit** - Scans Python dependencies for known vulnerabilities
- **Safety** - Checks Python packages against vulnerability databases
- **Dependabot** - Automated dependency updates and security patches

#### Infrastructure Security
- **Checkov** - Terraform/IaC security scanning
- **Trivy** - Comprehensive vulnerability scanner
- **Terraform validation** - Configuration validation

### CI/CD Security

All pull requests and commits undergo:

1. ✅ Secret scanning (multiple tools)
2. ✅ Code security analysis (Bandit, Semgrep, CodeQL)
3. ✅ Dependency vulnerability scanning
4. ✅ Infrastructure security checks (Checkov)
5. ✅ Type safety checks (MyPy)
6. ✅ Code quality linting (Ruff)

### Continuous Monitoring

- **Weekly Security Scans:** Comprehensive security audit every Monday
- **Daily Secret Scanning:** Checks for exposed secrets daily
- **Dependabot:** Monitors dependencies and creates PRs for security updates

## Security Best Practices

### For Contributors

1. **Never commit secrets:**
   - Use `.env` files (excluded from git)
   - Use Google Secret Manager for production secrets
   - Use pre-commit hooks to prevent accidental commits

2. **Follow secure coding practices:**
   - Input validation and sanitization
   - Use type hints and static type checking
   - Avoid SQL injection, XSS, command injection
   - Use parameterized queries and safe APIs

3. **Keep dependencies updated:**
   - Review and merge Dependabot PRs promptly
   - Pin dependency versions in requirements.txt
   - Use only trusted packages

4. **Use Workload Identity Federation:**
   - Never create service account JSON keys
   - Use WIF for all external authentication
   - Follow least privilege principle

### Infrastructure Security

1. **Encryption:**
   - Use CMEK (Customer-Managed Encryption Keys) for production
   - Enable encryption at rest and in transit
   - Rotate encryption keys regularly

2. **Network Security:**
   - Use VPC and private endpoints
   - Configure firewall rules (least access)
   - Use `ALLOW_INTERNAL_ONLY` for Cloud Functions

3. **Access Control:**
   - Follow principle of least privilege
   - Use service accounts for applications
   - Regularly audit IAM permissions
   - Enable audit logging

4. **Secret Management:**
   - Store all secrets in Google Secret Manager
   - Never hardcode secrets in code or config
   - Use `secret_environment_variables` in Cloud Functions
   - Rotate secrets regularly

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Security Checklist for Deployment

Before deploying to production:

- [ ] All secrets stored in Secret Manager
- [ ] CMEK encryption enabled for Pub/Sub topics
- [ ] Workload Identity Federation configured
- [ ] VPC and network security configured
- [ ] IAM policies follow least privilege
- [ ] Audit logging enabled
- [ ] All dependencies up to date
- [ ] Security scans passing
- [ ] Pre-commit hooks installed

## Security Features

### Current Implementation

✅ **Secret Management**
- Google Secret Manager integration
- No hardcoded credentials
- Environment variable validation

✅ **Authentication**
- Workload Identity Federation (WIF)
- No service account JSON keys
- OIDC-based authentication

✅ **Encryption**
- Optional CMEK for Pub/Sub topics
- TLS/HTTPS for all communications
- Encrypted secrets at rest

✅ **Network Security**
- Internal-only Cloud Functions
- VPC integration
- Firewall rules

✅ **Code Security**
- Type safety (MyPy)
- Security linting (Bandit, Semgrep)
- Input validation (Pydantic)
- SQL injection prevention

✅ **CI/CD Security**
- Automated security scanning
- Secret detection
- Dependency vulnerability checks
- Infrastructure security validation

### Planned Improvements

🔜 **Enhanced Monitoring**
- Cloud Security Command Center integration
- Real-time anomaly detection
- Security incident response automation

🔜 **Advanced Protection**
- Binary Authorization for Cloud Functions
- VPC Service Controls
- Organization policy constraints

🔜 **Compliance**
- SOC 2 compliance documentation
- GDPR data handling procedures
- Audit trail improvements

## Security Contacts

For security-related questions or concerns:

- **Security Issues:** Use GitHub Security Advisories
- **General Security Questions:** Create a discussion in the repository

## Acknowledgments

We appreciate security researchers and contributors who help keep this project secure. Responsible disclosure of vulnerabilities is greatly valued.

## Updates to This Policy

This security policy may be updated from time to time. Please check back regularly for updates.

**Last Updated:** 2025-11-27
