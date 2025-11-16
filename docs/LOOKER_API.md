# Looker Automation API Reference

Complete reference for all Looker automation functions available via Cloud Functions or direct SDK usage.

## Table of Contents

- [Core Provisioning](#core-provisioning)
- [User & Group Management](#user--group-management)
- [Connection Management](#connection-management)
- [LookML Project Operations](#lookml-project-operations)
- [Content Management](#content-management)
- [Decommissioning](#decommissioning)

---

## Core Provisioning

### `provision_looker_project`

Complete workflow for onboarding a GCP project into Looker.

**Payload:**

```json
{
  "projectId": "analytics-project-prod",
  "groupEmail": "data-analysts@company.com",
  "templateDashboardIds": [101, 102, 103]
}
```

**Returns:**

```json
{
  "status": "ok",
  "projectId": "analytics-project-prod",
  "groupEmail": "data-analysts@company.com",
  "groupId": 123,
  "folderId": 456,
  "dashboardIds": [201, 202, 203],
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**What it does:**

1. Creates/finds Looker group for the Google Workspace group
2. Adds group to SAML configuration
3. Creates project folder with naming convention `Project: {projectId}`
4. Clones template dashboards to the project folder
5. Returns IDs for all created/found resources

---

### `decommission_looker_project`

Safely decommission Looker project resources with configurable cleanup levels.

**Payload:**

```json
{
  "projectId": "old-analytics-project",
  "archiveFolder": true,
  "deleteDashboards": false,
  "deleteSchedules": true
}
```

**Parameters:**

- `archiveFolder` (bool, default `true`): Rename folder to "Archived: {name}"
- `deleteDashboards` (bool, default `false`): Permanently delete all dashboards
- `deleteSchedules` (bool, default `false`): Delete all scheduled deliveries

**Returns:**

```json
{
  "status": "ok",
  "projectId": "old-analytics-project",
  "archived_folder": true,
  "deleted_dashboards": 0,
  "deleted_schedules": 5
}
```

---

## User & Group Management

### `add_group_to_saml`

Add Google Workspace group to Looker SAML configuration.

**Payload:**

```json
{
  "groupEmail": "analysts@company.com"
}
```

**Returns:**

```json
{
  "status": "ok",
  "groupEmail": "analysts@company.com",
  "groupId": 123
}
```

---

### `create_user`

Create a new Looker user with optional role assignment.

**Payload:**

```json
{
  "email": "john.doe@company.com",
  "firstName": "John",
  "lastName": "Doe",
  "roleIds": [1, 5]  // optional
}
```

**Returns:**

```json
{
  "status": "ok",
  "userId": 789,
  "email": "john.doe@company.com"
}
```

---

### `add_user_to_group`

Add existing user to a Looker group.

**Payload:**

```json
{
  "groupId": 123,
  "userId": 789
}
```

**Returns:**

```json
{
  "status": "ok",
  "groupId": 123,
  "userId": 789,
  "added": true  // false if already in group
}
```

---

### `bulk_provision_users`

Provision multiple users at once, optionally adding them to a group.

**Payload:**

```json
{
  "users": [
    {
      "email": "user1@company.com",
      "firstName": "User",
      "lastName": "One",
      "roleIds": [1]
    },
    {
      "email": "user2@company.com",
      "firstName": "User",
      "lastName": "Two"
    }
  ],
  "groupId": 123  // optional
}
```

**Returns:**

```json
{
  "status": "ok",
  "userIds": [801, 802],
  "count": 2
}
```

---

## Connection Management

### `create_connection`

Create a new database connection in Looker.

**Payload (BigQuery):**

```json
{
  "name": "bigquery_prod",
  "host": "bigquery.googleapis.com",
  "database": "my-analytics-project",
  "dialectName": "bigquery_standard_sql",
  "serviceAccountJson": "{\"type\": \"service_account\", ...}"
}
```

**Payload (PostgreSQL):**

```json
{
  "name": "postgres_warehouse",
  "host": "db.company.com",
  "database": "analytics",
  "dialectName": "postgres",
  "username": "looker_user",
  "password": "secure_password",
  "port": 5432
}
```

**Returns:**

```json
{
  "status": "ok",
  "connectionName": "bigquery_prod"
}
```

---

### `test_connection`

Test an existing database connection.

**Payload:**

```json
{
  "connectionName": "bigquery_prod"
}
```

**Returns:**

```json
{
  "status": "ok",
  "status": "success",
  "message": "Connection successful",
  "success": true
}
```

---

### `delete_connection`

Delete a database connection.

**Payload:**

```json
{
  "connectionName": "old_connection"
}
```

**Returns:**

```json
{
  "status": "ok",
  "connectionName": "old_connection"
}
```

---

### `list_connections`

List all database connections.

**Payload:**

```json
{}
```

**Returns:**

```json
{
  "status": "ok",
  "connections": [
    {
      "name": "bigquery_prod",
      "dialect": "bigquery_standard_sql",
      "host": "bigquery.googleapis.com"
    },
    {
      "name": "postgres_warehouse",
      "dialect": "postgres",
      "host": "db.company.com"
    }
  ],
  "count": 2
}
```

---

## LookML Project Operations

### `create_lookml_project`

Create a new LookML project from a Git repository.

**Payload:**

```json
{
  "name": "analytics_project",
  "gitRemoteUrl": "https://github.com/company/looker-analytics.git",
  "gitServiceName": "github"  // or "gitlab", "bitbucket", etc.
}
```

**Returns:**

```json
{
  "status": "ok",
  "projectId": "analytics_project"
}
```

---

### `deploy_project_to_production`

Deploy LookML project to production.

**Payload:**

```json
{
  "projectId": "analytics_project"
}
```

**Returns:**

```json
{
  "status": "ok",
  "projectId": "analytics_project"
}
```

---

### `validate_project`

Validate LookML project for errors and warnings.

**Payload:**

```json
{
  "projectId": "analytics_project"
}
```

**Returns:**

```json
{
  "status": "ok",
  "valid": true,
  "errors": [],
  "warnings": [
    "Unused field: users.created_date"
  ]
}
```

**Error Response:**

```json
{
  "status": "ok",
  "valid": false,
  "errors": [
    "Syntax error in view 'orders': Line 15"
  ],
  "warnings": []
}
```

---

## Content Management

### `create_project_folder`

Create a Looker folder for a project.

**Payload:**

```json
{
  "projectId": "analytics-project",
  "parentId": "shared-folders-123"  // optional
}
```

**Returns:**

```json
{
  "status": "ok",
  "projectId": "analytics-project",
  "folderId": 456
}
```

---

### `create_dashboard_from_template`

Clone a dashboard template to a project folder.

**Payload:**

```json
{
  "templateDashboardId": 101,
  "folderId": 456,
  "projectId": "analytics-project"
}
```

**Returns:**

```json
{
  "status": "ok",
  "projectId": "analytics-project",
  "dashboardId": 789
}
```

---

### `move_dashboard_to_folder`

Move a dashboard to a different folder.

**Payload:**

```json
{
  "dashboardId": 789,
  "targetFolderId": 999
}
```

**Returns:**

```json
{
  "status": "ok",
  "dashboardId": 789,
  "targetFolderId": 999
}
```

---

### `create_scheduled_delivery`

Create a scheduled dashboard delivery via email.

**Payload:**

```json
{
  "dashboardId": 789,
  "name": "Weekly Executive Dashboard",
  "cronSchedule": "0 9 * * 1",  // Every Monday at 9 AM
  "destinationEmails": [
    "exec-team@company.com",
    "analytics-team@company.com"
  ],
  "pdfPaperSize": "letter"  // or "A4", optional
}
```

**Cron Schedule Examples:**

- `0 9 * * *` - Daily at 9 AM
- `0 9 * * 1` - Every Monday at 9 AM
- `0 9 1 * *` - First day of month at 9 AM
- `0 0 * * 0` - Every Sunday at midnight

**Returns:**

```json
{
  "status": "ok",
  "scheduledPlanId": 321
}
```

---

## Decommissioning

### `disable_user` (via provisioner SDK)

Disable a user account (soft delete).

```python
from iam_looker.provisioner import LookerProvisioner

provisioner = LookerProvisioner(sdk)
provisioner.disable_user(user_id=789)
```

---

### `delete_user` (via provisioner SDK)

Permanently delete a user account.

```python
provisioner.delete_user(user_id=789)
```

---

### `delete_group` (via provisioner SDK)

Delete a Looker group.

```python
provisioner.delete_group(group_id=123)
```

---

## Error Handling

All functions return consistent error responses:

```json
{
  "status": "error",
  "error": "Descriptive error message"
}
```

### Common Errors

- **SDK Unavailable**: Looker SDK not initialized

  ```json
  {"status": "sdk_unavailable"}
  ```

- **Validation Error**: Invalid payload

  ```json
  {
    "status": "validation_error",
    "error": "Missing required field: projectId"
  }
  ```

- **Provisioning Error**: Looker API operation failed

  ```json
  {
    "status": "error",
    "error": "create_connection failed: Connection name already exists"
  }
  ```

---

## Usage Examples

### Complete Project Onboarding

```python
# 1. Provision project
result = provision_looker_project({
    "projectId": "analytics-prod",
    "groupEmail": "analysts@company.com",
    "templateDashboardIds": [101, 102]
})

# 2. Add users to group
bulk_provision_users({
    "users": [
        {"email": "user1@company.com", "firstName": "User", "lastName": "One"},
        {"email": "user2@company.com", "firstName": "User", "lastName": "Two"}
    ],
    "groupId": result["groupId"]
})

# 3. Create database connection
create_connection({
    "name": "bigquery_analytics",
    "host": "bigquery.googleapis.com",
    "database": "analytics-prod",
    "dialectName": "bigquery_standard_sql"
})

# 4. Create scheduled delivery
create_scheduled_delivery({
    "dashboardId": result["dashboardIds"][0],
    "name": "Daily Analytics Report",
    "cronSchedule": "0 9 * * *",
    "destinationEmails": ["team@company.com"]
})
```

### Complete Project Decommissioning

```python
# 1. Decommission project resources
decommission_result = decommission_looker_project({
    "projectId": "old-analytics-project",
    "archiveFolder": True,
    "deleteDashboards": False,  # Keep dashboards archived
    "deleteSchedules": True      # Delete all schedules
})

# 2. Disable users (via SDK)
for user_id in [user1_id, user2_id]:
    provisioner.disable_user(user_id)

# 3. Delete group (via SDK)
provisioner.delete_group(group_id)

# 4. Delete connection
delete_connection({"connectionName": "old_connection"})
```

---

## Cloud Function Deployment

All functions can be deployed as individual Cloud Functions:

```bash
gcloud functions deploy looker-provision \
  --gen2 \
  --runtime=python312 \
  --entry-point=provision_looker_project \
  --trigger-topic=looker-provision-topic \
  --service-account=looker-automation@PROJECT_ID.iam.gserviceaccount.com \
  --set-secrets=LOOKERSDK_BASE_URL=looker-base-url:latest

gcloud functions deploy looker-create-connection \
  --gen2 \
  --runtime=python312 \
  --entry-point=create_connection \
  --trigger-topic=looker-connection-topic \
  --service-account=looker-automation@PROJECT_ID.iam.gserviceaccount.com

gcloud functions deploy looker-decommission \
  --gen2 \
  --runtime=python312 \
  --entry-point=decommission_looker_project \
  --trigger-topic=looker-decommission-topic \
  --service-account=looker-automation@PROJECT_ID.iam.gserviceaccount.com
```

---

## Direct SDK Usage

All functions are available via the `LookerProvisioner` class:

```python
from iam_looker.provisioner import LookerProvisioner
import looker_sdk

# Initialize SDK
sdk = looker_sdk.init40()
provisioner = LookerProvisioner(sdk)

# Use any provisioner method
result = provisioner.provision(
    project_id="my-project",
    group_email="team@company.com",
    template_dashboard_ids=[101, 102]
)

# Connection management
conn_name = provisioner.create_connection(
    name="my_connection",
    host="bigquery.googleapis.com",
    database="my-project"
)

# Project operations
project_id = provisioner.create_project(
    name="analytics",
    git_remote_url="https://github.com/company/looker.git"
)

# Decommissioning
decommission_result = provisioner.decommission_project(
    project_id="old-project",
    archive_folder=True,
    delete_dashboards=True
)
```

---

## Best Practices

1. **Idempotency**: All provisioning operations are idempotent - safe to run multiple times
2. **Error Handling**: Always check `status` field in responses
3. **Correlation IDs**: Use correlation IDs from provision responses for tracking
4. **Secret Management**: Store Looker credentials in Secret Manager, never in code
5. **Testing**: Test connection creation before deploying to production
6. **Decommissioning**: Always archive first, delete later after verification
7. **Bulk Operations**: Use bulk_provision_users for efficient user onboarding
8. **Validation**: Validate LookML projects before deploying to production

---

## Support

- **API Documentation**: See this file and [SPEC.md](../SPEC.md)
- **Issues**: [GitHub Issues](https://github.com/erayguner/iam-looker/issues)
- **Security**: See [SECURITY.md](../SECURITY.md)
