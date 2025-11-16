# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to the repository maintainers. You should receive a response within 48 hours. If for some reason you do not, please follow up to ensure we received your original message.

### What to Include

Please include the following information in your report:

- **Description**: A clear description of the vulnerability
- **Impact**: What kind of vulnerability is it? (e.g., remote code execution, information disclosure)
- **Affected Components**: Which parts of the codebase are affected?
- **Reproduction Steps**: Step-by-step instructions to reproduce the issue
- **Proof of Concept**: If applicable, provide a PoC
- **Suggested Fix**: If you have ideas on how to fix it (optional)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity and complexity
  - Critical: 1-7 days
  - High: 7-30 days
  - Medium: 30-90 days
  - Low: 90+ days

## Security Best Practices

### For Users

1. **Never Commit Secrets**
   - Use environment variables or Secret Manager
   - Never commit `.env` files with real credentials
   - Use `.env.example` as a template only

2. **Use Workload Identity Federation**
   - Avoid service account JSON keys
   - Implement keyless authentication
   - Follow the WIF setup in our documentation

3. **Keep Dependencies Updated**
   - Regularly update dependencies
   - Enable Dependabot alerts
   - Monitor security advisories

4. **Secure Your Environment**
   - Use principle of least privilege
   - Enable Cloud Audit Logs
   - Implement network security controls

### For Contributors

1. **Code Security**
   - Run security linters (Bandit) before committing
   - Use type hints to prevent type-related bugs
   - Validate all inputs using Pydantic models
   - Sanitize user inputs

2. **Dependency Management**
   - Pin dependency versions
   - Review dependency security alerts
   - Use `safety` to scan for known vulnerabilities
   - Minimize dependency count

3. **Infrastructure as Code**
   - Run Checkov scans on Terraform code
   - Follow GCP security best practices
   - Use secure defaults
   - Document security assumptions

4. **Testing**
   - Include security test cases
   - Test authentication and authorization
   - Test input validation
   - Test error handling

## Security Features

### Authentication & Authorization

- **Workload Identity Federation**: Keyless authentication for CI/CD
- **Service Account Impersonation**: Principle of least privilege
- **API Key Rotation**: Support for credential rotation

### Data Protection

- **Secret Management**: Integration with GCP Secret Manager
- **Encryption**: Use of TLS for all network communications
- **Audit Logging**: Structured logging of all operations

### Infrastructure Security

- **Network Isolation**: VPC-attached resources
- **IAM Policies**: Granular access controls
- **Security Scanning**: Automated vulnerability detection

### CI/CD Security

- **Dependency Scanning**: Safety, pip-audit
- **Code Scanning**: Bandit, CodeQL
- **Secret Detection**: detect-secrets, TruffleHog
- **SARIF Reports**: Security findings uploaded to GitHub

## Security Scanning

This project uses multiple security tools:

### Python Code
- **Bandit**: Security linter for Python code
- **Safety**: Checks dependencies for known vulnerabilities
- **pip-audit**: Audits Python packages for security issues

### Terraform
- **Checkov**: Infrastructure as Code security scanner
- **tflint**: Terraform linting and security checks

### Secrets
- **detect-secrets**: Prevents secrets from being committed
- **TruffleHog**: Scans for secrets in git history

### General
- **CodeQL**: Semantic code analysis
- **Dependabot**: Automated dependency updates

## Known Security Considerations

### 1. Looker API Credentials

Looker API credentials (`LOOKERSDK_CLIENT_ID` and `LOOKERSDK_CLIENT_SECRET`) must be:
- Stored in Secret Manager
- Never committed to version control
- Rotated regularly
- Scoped to minimum required permissions

### 2. Workload Identity Federation

When using WIF:
- Verify repository claims in attribute conditions
- Use specific branch/tag restrictions
- Audit identity pool usage regularly
- Document pool configuration

### 3. Cloud Function Security

Cloud Functions should:
- Use internal-only ingress
- Attach to VPC networks
- Use service accounts with minimal permissions
- Enable Cloud Armor (if using HTTP)

### 4. Terraform State

Terraform state files may contain sensitive data:
- Use remote state with encryption
- Enable state locking
- Restrict state file access
- Never commit state files

## Compliance

This project aims to comply with:

- **OWASP Top 10**: Web application security risks
- **CIS Benchmarks**: For GCP and Terraform
- **Principle of Least Privilege**: Minimal necessary permissions
- **Defense in Depth**: Multiple layers of security

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 0.1.3)
- Documented in CHANGELOG.md
- Announced via GitHub Security Advisories
- Tagged with security labels

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
- [Terraform Security Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Acknowledgments

We appreciate the security research community and will acknowledge researchers who responsibly disclose vulnerabilities (unless they prefer to remain anonymous).

---

Last Updated: 2025-11-16
