# OpenMediaTrust API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API requests require authentication using JWT tokens.

```http
Authorization: Bearer <token>
```

## Manifests API

### Create Manifest

Create a new C2PA manifest for content.

**Endpoint:** `POST /manifests`

**Request (multipart/form-data):**

```http
POST /api/v1/manifests
Content-Type: multipart/form-data

file: <binary>
creator: john.doe@company.com
title: Product Photo Q4 2025
department: Marketing
project: Campaign-2025-Q4
classification: internal
organization: Acme Corporation
```

**Response:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "instance_id": "xmp:iid:abc123...",
  "title": "Product Photo Q4 2025",
  "format": "image/jpeg",
  "creator": "john.doe@company.com",
  "created_at": "2025-11-08T10:00:00Z",
  "is_signed": false,
  "workflow_id": null,
  "storage_path": "hot/manifests/abc123.json"
}
```

### Get Manifest

Retrieve manifest by ID.

**Endpoint:** `GET /manifests/{manifest_id}`

**Response:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "instance_id": "xmp:iid:abc123...",
  "title": "Product Photo Q4 2025",
  "format": "image/jpeg",
  "creator": "john.doe@company.com",
  "created_at": "2025-11-08T10:00:00Z",
  "is_signed": true,
  "workflow_id": "WF-20251108-abc",
  "storage_path": "hot/manifests/abc123.json"
}
```

### Sign Manifest

Sign a manifest with quantum-safe algorithm.

**Endpoint:** `POST /manifests/{manifest_id}/sign`

**Request:**

```json
{
  "algorithm": "ml-dsa-65",
  "certificate_path": "/keys/signing-cert.pem"
}
```

**Response:**

```json
{
  "message": "Manifest signed successfully",
  "manifest_id": "xmp:iid:abc123...",
  "signature": {
    "algorithm": "ml-dsa-65",
    "timestamp": "2025-11-08T10:05:00Z"
  }
}
```

### List Manifests

List manifests with optional filters.

**Endpoint:** `GET /manifests`

**Query Parameters:**
- `organization`: Filter by organization
- `department`: Filter by department
- `creator`: Filter by creator
- `limit`: Maximum results (default: 100)

**Response:**

```json
{
  "manifests": [
    {
      "manifest_id": "xmp:iid:abc123...",
      "title": "Product Photo Q4 2025",
      "creator": "john.doe@company.com",
      "created_at": "2025-11-08T10:00:00Z"
    }
  ],
  "total": 1
}
```

## Verification API

### Verify Manifest

Verify a manifest's authenticity and integrity.

**Endpoint:** `POST /verify`

**Request:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "strict": true
}
```

**Response:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "valid": true,
  "trust_level": "enterprise",
  "signature_valid": true,
  "certificate_trusted": true,
  "chain_complete": true,
  "assertions_verified": [
    {
      "label": "c2pa.actions",
      "verified": true,
      "message": "Actions assertion valid (1 actions)"
    },
    {
      "label": "c2pa.hash.data",
      "verified": true,
      "message": "Hash assertion valid"
    }
  ],
  "issues": [],
  "warnings": [],
  "organizational_compliance": {
    "pdpa_compliant": true,
    "workflow_approved": true,
    "department_authorized": true
  }
}
```

### Check Policy

Check manifest against organizational policy.

**Endpoint:** `POST /verify/policy`

**Request:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "policy_name": "marketing_content"
}
```

**Response:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "policy_name": "marketing_content",
  "passed": true,
  "violations": []
}
```

### Get Chain of Custody

Get complete chain of custody for a manifest.

**Endpoint:** `GET /verify/{manifest_id}/chain-of-custody`

**Response:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "actions": [
    {
      "action": "c2pa.created",
      "when": "2025-11-08T10:00:00Z",
      "software_agent": "Adobe Photoshop 2025"
    },
    {
      "action": "c2pa.edited",
      "when": "2025-11-08T10:30:00Z",
      "software_agent": "OpenMediaTrust/1.0.0"
    }
  ],
  "ingredients": []
}
```

## Workflow API

### Create Workflow

Create a new workflow for a manifest.

**Endpoint:** `POST /workflows`

**Request:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "creator_id": "john.doe",
  "creator_name": "John Doe"
}
```

**Response:**

```json
{
  "workflow_id": "WF-20251108-abc",
  "manifest_id": "xmp:iid:abc123...",
  "current_state": "draft",
  "created_by": "john.doe",
  "created_at": "2025-11-08T10:00:00Z",
  "updated_at": "2025-11-08T10:00:00Z",
  "history": [],
  "available_actions": ["submit"]
}
```

### Transition Workflow

Perform a workflow state transition.

**Endpoint:** `POST /workflows/{workflow_id}/transition`

**Request:**

```json
{
  "action": "approve",
  "user_id": "manager",
  "user_name": "Jane Manager",
  "user_role": "approver",
  "comments": "Approved for publication"
}
```

**Response:**

```json
{
  "workflow_id": "WF-20251108-abc",
  "manifest_id": "xmp:iid:abc123...",
  "current_state": "approved",
  "created_by": "john.doe",
  "created_at": "2025-11-08T10:00:00Z",
  "updated_at": "2025-11-08T11:00:00Z",
  "history": [
    {
      "timestamp": "2025-11-08T11:00:00Z",
      "user_id": "manager",
      "user_name": "Jane Manager",
      "from_state": "in_review",
      "to_state": "approved",
      "action": "approve",
      "comments": "Approved for publication"
    }
  ],
  "available_actions": ["publish"]
}
```

### Check Compliance

Check manifest compliance against policy.

**Endpoint:** `POST /compliance/check`

**Request:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "policy_name": "public_content",
  "checked_by": "compliance.officer"
}
```

**Response:**

```json
{
  "manifest_id": "xmp:iid:abc123...",
  "policy_name": "public_content",
  "overall_status": "passed",
  "results": [
    {
      "rule": "trademark_clearance",
      "status": "passed",
      "message": "Trademark clearance verified"
    },
    {
      "rule": "legal_review",
      "status": "passed",
      "message": "Legal review passed"
    }
  ]
}
```

## Admin API

### Create User

Create a new user account.

**Endpoint:** `POST /admin/users`

**Request:**

```json
{
  "user_id": "jane.smith",
  "username": "jane.smith",
  "email": "jane.smith@company.com",
  "full_name": "Jane Smith",
  "roles": ["creator", "reviewer"],
  "department": "Marketing",
  "is_active": true
}
```

**Response:**

```json
{
  "user_id": "jane.smith",
  "username": "jane.smith",
  "email": "jane.smith@company.com",
  "full_name": "Jane Smith",
  "roles": ["creator", "reviewer"],
  "department": "Marketing",
  "is_active": true
}
```

### Get System Metrics

Get system metrics and statistics.

**Endpoint:** `GET /admin/metrics`

**Response:**

```json
{
  "total_manifests": 15420,
  "total_users": 245,
  "manifests_today": 78,
  "verifications_today": 142,
  "storage_used_gb": 458.3
}
```

### Get Audit Logs

Get audit logs with filters.

**Endpoint:** `GET /admin/audit-logs`

**Query Parameters:**
- `manifest_id`: Filter by manifest
- `user_id`: Filter by user
- `operation`: Filter by operation
- `limit`: Maximum results

**Response:**

```json
{
  "logs": [
    {
      "id": 1234,
      "manifest_id": "xmp:iid:abc123...",
      "operation": "create",
      "user_id": "john.doe",
      "timestamp": "2025-11-08T10:00:00Z",
      "status": "success"
    }
  ],
  "total": 1
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_code": "INVALID_REQUEST"
}
```

**Common Status Codes:**
- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error
