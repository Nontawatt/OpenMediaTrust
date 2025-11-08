# OpenMediaTrust Architecture

## System Overview

OpenMediaTrust is an enterprise-grade C2PA (Coalition for Content Provenance and Authenticity) manifest system designed for organizations that require robust content authentication with post-quantum cryptographic protection.

## Architecture Layers

### 1. Manifest Creation Layer

The manifest creation layer handles content ingestion and metadata extraction:

**Components:**
- **Content Ingestion Service**: Accepts files from various sources (upload, API, DAM integration)
- **Metadata Extractor**: Extracts EXIF, XMP, IPTC, and technical metadata from content
- **Assertion Builder**: Constructs C2PA assertions based on content type and organizational requirements
- **Signing Service**: Signs manifests using quantum-safe cryptographic algorithms

**Supported Algorithms:**
- **ML-DSA (Dilithium)**: NIST-standardized post-quantum signature scheme
  - ML-DSA-44 (Category 2 security)
  - ML-DSA-65 (Category 3 security) - Default
  - ML-DSA-87 (Category 5 security)
- **SLH-DSA (SPHINCS+)**: Hash-based signature scheme for long-term security
- **Hybrid Modes**: Classical + PQC for transitional deployments

### 2. Enterprise Features Layer

**Access Control:**
- Role-Based Access Control (RBAC)
- LDAP/Active Directory integration
- Permission-based operations
- Multi-tenant support

**Workflow Management:**
- State machine for approval workflows
- Multi-stage approval chains
- Role-based transitions
- Audit trail for all state changes

**Compliance Engine:**
- PDPA compliance checking
- Trademark clearance verification
- Legal review tracking
- Export control validation
- Classification level enforcement

### 3. Verification Layer

**Manifest Validator:**
- Structure validation
- Signature verification
- Assertion consistency checks
- Certificate chain validation
- Trust level determination

**Policy Engine:**
- Organizational policy enforcement
- Custom validation rules
- Classification constraints
- Required/forbidden assertions
- Custom validation functions

### 4. Storage Infrastructure

**Database (PostgreSQL):**
- Manifest metadata indexing
- Workflow state tracking
- User and role management
- Audit logs
- Search and filtering

**Object Storage (S3-compatible):**
- **Hot Tier**: Active manifests and content
- **Warm Tier**: Archived manifests (90+ days)
- **Cold Tier**: Long-term retention (365+ days)
- Automatic lifecycle management
- Pre-signed URL generation

### 5. API Layer

**REST API (FastAPI):**
- Manifest CRUD operations
- Verification endpoints
- Workflow management
- Compliance checking
- User administration
- Metrics and monitoring

**Integration Points:**
- DAM (Digital Asset Management) systems
- CMS (Content Management Systems)
- Production tools (Adobe CC, etc.)
- Archive systems
- SSO/LDAP providers

## Data Flow

### Manifest Creation Flow

```
┌─────────────┐
│   Content   │
│   Upload    │
└──────┬──────┘
       │
       v
┌─────────────────┐
│    Metadata     │
│   Extraction    │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│   Assertion     │
│    Building     │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│   Manifest      │
│   Creation      │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│    Signing      │
│  (ML-DSA/PQC)   │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│    Storage      │
│ (DB + Object)   │
└─────────────────┘
```

### Verification Flow

```
┌─────────────┐
│  Manifest   │
│  Retrieval  │
└──────┬──────┘
       │
       v
┌─────────────────┐
│   Structure     │
│  Validation     │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│   Signature     │
│  Verification   │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│  Certificate    │
│  Trust Check    │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│  Chain of       │
│  Custody        │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│   Policy        │
│  Evaluation     │
└──────┬──────────┘
       │
       v
┌─────────────────┐
│  Verification   │
│    Result       │
└─────────────────┘
```

## Security Architecture

### Cryptographic Security

**Key Management:**
- Hardware Security Module (HSM) integration for private keys
- Key ceremony procedures for root CA
- Automatic key rotation
- Secure key storage with encryption at rest

**Quantum-Safe Transition:**
1. **Phase 1**: Hybrid mode (Classical + PQC)
2. **Phase 2**: Pure PQC with classical backup
3. **Phase 3**: Pure PQC only

**Certificate Management:**
- Internal PKI for enterprise certificates
- Trust list management
- Certificate revocation checking
- Timestamp authority integration

### Access Security

**Authentication:**
- JWT-based API authentication
- LDAP/AD integration
- Multi-factor authentication support
- Session management

**Authorization:**
- Role-based access control
- Permission inheritance
- Department/project-based isolation
- Multi-tenant support

**Audit:**
- Immutable audit logs
- User action tracking
- System event logging
- Compliance reporting

## Scalability Architecture

### Horizontal Scaling

**API Servers:**
- Stateless design
- Load balancer distribution
- Auto-scaling based on load

**Background Workers:**
- Celery task queue
- Multiple worker processes
- Priority-based task execution

**Database:**
- Read replicas for queries
- Connection pooling
- Query optimization
- Partitioning for large tables

**Storage:**
- S3-compatible object storage
- CDN integration for content delivery
- Geographic replication

### Performance Optimization

**Caching:**
- Redis for session and data caching
- Manifest metadata caching
- Policy evaluation caching
- Pre-computed verification results

**Async Processing:**
- Asynchronous API endpoints
- Background job processing
- Webhook notifications
- Batch operations

## Deployment Architecture

### Production Deployment

```
┌─────────────────────────────────────┐
│         Load Balancer (HAProxy)     │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───v───┐     ┌───v───┐
│ API 1 │     │ API 2 │  ... API N
└───┬───┘     └───┬───┘
    │             │
    └──────┬──────┘
           │
    ┌──────v──────┐
    │             │
┌───v────┐  ┌────v────┐
│ DB     │  │ Redis   │
│Primary │  │ Cluster │
└────────┘  └─────────┘
    │
┌───v────┐
│ DB     │
│Replica │
└────────┘
```

### Container Orchestration

**Kubernetes Deployment:**
- API pods with auto-scaling
- Worker pods for background tasks
- StatefulSets for databases
- ConfigMaps for configuration
- Secrets for sensitive data
- Persistent volumes for storage

## Monitoring and Observability

**Metrics:**
- Prometheus for metrics collection
- Grafana for visualization
- Custom dashboards for:
  - Manifest creation rate
  - Verification success rate
  - API response times
  - Storage usage
  - Error rates

**Logging:**
- Structured logging (JSON)
- Centralized log aggregation
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Audit log retention

**Tracing:**
- Distributed tracing support
- Request correlation IDs
- Performance profiling

## Disaster Recovery

**Backup Strategy:**
- Daily database backups
- Object storage replication
- Configuration backups
- Key material backup (encrypted)

**Recovery Procedures:**
- Database restore procedures
- Storage recovery from replicas
- Service failover
- RTO: 4 hours
- RPO: 1 hour

## Compliance and Governance

**Data Protection:**
- Encryption at rest and in transit
- PII handling and redaction
- Right to be forgotten support
- Data retention policies

**Regulatory Compliance:**
- PDPA compliance
- Export control adherence
- Legal review workflows
- Audit trail requirements
