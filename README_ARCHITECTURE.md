# Architecture Deep Dive

Refer to `SPEC.md` for authoritative definitions. This document elaborates internal design rationale.

## Module Responsibilities
- `src/config.py`: Centralized environment & defaults parsing.
- `src/looker_provisioner.py`: Imperative orchestration of Looker API calls. Maintains idempotency rules.
- `src/dashboard_template.py`: Concerned solely with token substitution logic; future expansion to element-level modifications.
- `cloud_function/main.py`: Transport adapter translating Cloud event model to internal calls.

## Sequence Diagram (Textual)
1. Cloud Function trigger -> parse payload.
2. Load configuration.
3. Initialize Looker SDK client.
4. ensure_group -> search_groups / create_group.
5. ensure_saml_group_mapping -> saml_config / update_saml_config.
6. ensure_project_folder -> search_folders / create_folder.
7. For each template dashboard -> dashboard -> search_dashboards -> dashboard_copy.
8. Token substitution (future) -> update_dashboard (not yet implemented in code).
9. Log completion and return JSON result.

## Idempotency Details
- Group & folder reuse avoid duplicates.
- Dashboard clone check on desired title; collision prevention.

## Observability
Logging fields structured for ingestion into centralized logging with correlationId. Future enhancement: tracing context injection.

## Security Model (Keyless)
- CI/CD and automation MUST use Workload Identity Federation (WIF) – no service account keys.
- Enforce via organisation policy `constraints/iam.disableServiceAccountKeyCreation` where possible.
- Monitor Cloud Audit Logs for `google.iam.admin.v1.CreateServiceAccountKey` – alert if triggered.
- Runtime (Cloud Functions) relies on attached service account & short-lived tokens (ADC), never static keys.

### WIF Flow
GitHub Action Runner -> OIDC Token -> Workload Identity Pool Provider -> Impersonate Service Account -> Terraform / deploy.

## Extensibility Points
- Replace title-based dashboard reuse with metadata tags.
- Add exponential backoff wrapper around API calls.
- Introduce metrics exporter module.
- Enhance WIF provider attribute conditions (e.g. branch protection, workflow reference).

## Risk & Mitigation
| Risk | Mitigation |
|------|------------|
| Incorrect SAML update overwrites config | Merge-only logic, verify model fields before prod deployment |
| Title collision for dashboards | Use unique suffix pattern `(project: <projectId>)` |
| Missing template IDs cause failure | Validate IDs exist earlier (future preflight) |
| Accidental key creation | Org policy + audit log alert + Terraform scanning (OPA/Rego) |

## Pending Verification
Actual Looker SDK method signatures for copying dashboards & SAML config field names; placeholders used until integration test.

## Compliance Controls
- Keyless provisioning documented in `README.md` and `SPEC.md`.
- Periodic (daily) audit job to scan for service account keys (future).

## Performance Considerations
Minimal API calls; can batch dashboard operations later.

## 2025 Python Project Structure Enhancements
- Adopt `src/iam_looker` package for clear boundaries & namespacing.
- Pydantic models (`models.py`) for strict payload validation (type-safety & error clarity).
- Centralised settings via Pydantic `BaseSettings` (`settings.py`) supporting `.env` and environment overrides.
- JSON structured logging with custom formatter (`logging.py`).
- Thin Cloud Function entrypoint delegating to `handler.handle_event` for testability.
- Legacy modules retained temporarily for backward compatibility; plan removal after migration.

# Specification: iam-looker

Version: 0.1.0
Status: Draft
Owner: Data Platform Engineering
Last Updated: 2025-11-15

## 1. Purpose
Automate onboarding of a Google Cloud project into Looker by provisioning group-based access, creating project folder(s), and cloning template dashboards with project-specific substitutions.

## 2. Scope
In Scope:
- Single project onboarding per event.
- Looker group ensure/create.
- SAML config update to include group (non-destructive merge).
- Folder creation following naming convention.
- Dashboard cloning from predefined template folder / list.
- Idempotent operations.
- Structured logging.

Out of Scope (initial version):
- Multi-project batch requests.
- Advanced role assignment logic.
- Dashboard content transformation beyond token substitution.
- Secret lifecycle management.
- Retry/backoff (will be added later).

## 3. Stakeholders
- Requesters: Platform team automation pipeline.
- Consumers: Looker users (analysts, engineers).
- Operators: Data platform / governance.

## 4. Triggers & Entry Points
Two supported triggers:
1. Pub/Sub message (Cloud Functions): Event contains base64 encoded JSON.
2. HTTP (optional future): Raw JSON body.

## 5. Event Payload Contract
```
{
  "projectId": "string (GCP project ID, RFC1034 label)",
  "groupEmail": "string (GSuite/Workspace group email)",
  "ancestryPath": "string (optional; organization/folder chain)",
  "templateDashboardIds": [int, ...] (optional; if absent, default set),
  "templateFolderId": int (optional; overrides default),
  "tokens": {"KEY": "value"} (optional; extra substitutions)
}
```
Validation Rules:
- projectId: required, matches `^[a-z][a-z0-9-]{4,61}[a-z0-9]$`.
- groupEmail: required, must contain `@`.
- templateDashboardIds: all positive integers.
- tokens: keys alphanumeric/underscore only.

## 6. Configuration
Environment variables:
- LOOKERSDK_BASE_URL
- LOOKERSDK_CLIENT_ID
- LOOKERSDK_CLIENT_SECRET
- LOOKERSDK_VERIFY_SSL (default true)
- DEFAULT_TEMPLATE_FOLDER_ID (optional)
- DEFAULT_TEMPLATE_DASHBOARD_IDS (comma-separated ints)

## 7. Idempotency Rules
Operation outcomes:
- Group: If Looker group with `name == groupEmail` OR `name == <prefix><groupEmail>` exists, reuse; else create.
- SAML Config: Fetch current SAML settings; if group already mapped, skip; else append.
- Folder: Search for folder with name `Project: <projectId>`; if exists, reuse; else create under root or configured parent folder.
- Dashboards: For each template ID, search in target folder for existing clone with title pattern `<original_title> (project: <projectId>)`; if exists, skip; else copy.

## 8. Token Substitution
Dashboard elements, description, and title may contain placeholders:
- `{{PROJECT_ID}}`
- `{{ANCESTRY_PATH}}`
- Additional `{{KEY}}` for keys in payload tokens.
Applied after cloning via update dashboard call.

## 9. API Interactions (Looker SDK 4.0)
- List groups: `sdk.search_groups(name=...)`.
- Create group: `sdk.create_group(body=GroupWrite(name=...))`.
- Get / Update SAML config: `sdk.saml_config()` / `sdk.update_saml_config(body=SamlConfig(saml_idp_metadata=..., groups=...))` (NOTE: actual field names may require refinement; placeholder in code).
- Search folders: `sdk.search_folders(name=...)`.
- Create folder: `sdk.create_folder(body=Folder(name=..., parent_id=...))`.
- Get dashboard: `sdk.dashboard(dashboard_id)`.
- Copy dashboard: `sdk.dashboard_copy(dashboard_id, body=DashboardCopy(name=..., folder_id=...))` (actual write model may differ; code will abstract behind provisioner methods with TODOs to refine).
- Update dashboard: `sdk.update_dashboard(dashboard_id, body=Dashboard())`.

All write interactions must check success & raise `ProvisioningError` on failure.

## 10. Errors & Exceptions
Custom Exceptions:
- `ValidationError` (400)
- `ProvisioningError` (Dependency failure)

Retryable Classes (future): network, 429, 5xx.

## 11. Logging Format
JSON lines with fields:
- `timestamp`
- `level`
- `event` (e.g., group.ensure, dashboard.clone)
- `projectId`
- `correlationId` (UUID per request)
- `message`
- `details` (object)

## 12. Security
- Credentials only via env vars or Secret Manager references.
- Minimal scopes for Looker API user.
- No persistence of secrets in logs.

## 13. Performance Targets
- P50 < 3s for 3 dashboards.
- P95 < 8s.

## 14. Testing Strategy
Unit Tests:
- Payload validation.
- Idempotent provisioning (mock existing resources).
Integration (future):
- Sandbox Looker instance.
Contract:
- Schema validation using regex/unit tests.

## 15. Deployment
GCP Cloud Functions Gen2 .
Single artifact built from repo root. Python 3.12 runtime.

## 16. Future Enhancements
- Backoff/retry wrapper.
- Metric emission (Prometheus/OpenTelemetry).
- Group role mapping matrix.
- Template registry service.
- Multiple project batch ingestion.

## 17. Open Questions
- Exact field names for SAML config group mapping (verify with API model).
- Preferred folder parent location (root vs shared parent).

## 18. Acceptance Criteria
- Given valid payload, function returns success result including created/reused resource IDs.
- Re-running with same payload produces no duplicates.
- Invalid payload returns structured error.

For adopted best practices see README section '2025 Python Best Practices Adopted'.

---
This spec governs implementation; modifications require version bump & stakeholder review.

## Single-Task Functions
Granular functions reduce blast radius and allow targeted IAM:
- add_group_to_saml
- create_project_folder
- create_dashboard_from_template
Internal-only via Cloud Functions Gen2 + Pub/Sub triggers + API Gateway.
