# OpenMediaTrust

Enterprise-grade C2PA (Coalition for Content Provenance and Authenticity) Manifest System with Post-Quantum Cryptography support

## Overview

OpenMediaTrust is a comprehensive solution for creating, managing, and verifying C2PA manifests in enterprise environments. It provides:

- **Quantum-Safe Security**: ML-DSA (Dilithium) and SLH-DSA (SPHINCS+) support
- **Enterprise Integration**: LDAP/AD, DAM, CMS integration
- **Compliance**: PDPA, retention policies, audit trails
- **Workflow Management**: Multi-signature approval chains
- **Scalable Architecture**: Hot/warm/cold storage tiers

## Architecture

```
┌─────────────────────────────────────────────┐
│           Enterprise Network                │
│                                             │
│  ┌──────────────┐      ┌──────────────┐   │
│  │   Content    │──────│   Manifest   │   │
│  │   Sources    │      │   Creation   │   │
│  └──────────────┘      │   Service    │   │
│                        └───────┬──────┘   │
│                                │           │
│  ┌──────────────┐      ┌──────▼──────┐   │
│  │  Signing     │◄─────│   Manifest  │   │
│  │  Service     │      │   Store     │   │
│  │  (HSM)       │      └──────┬──────┘   │
│  └──────────────┘             │           │
│                                │           │
│  ┌──────────────┐      ┌──────▼──────┐   │
│  │ Verification │◄─────│   Policy    │   │
│  │  Service     │      │   Engine    │   │
│  └──────────────┘      └─────────────┘   │
│                                            │
│  ┌──────────────────────────────────┐    │
│  │     Management Dashboard          │    │
│  └──────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## Features

### Core Capabilities
- **Manifest Creation**: Automated assertion building with metadata extraction
- **Quantum-Safe Signing**: ML-DSA-65, SPHINCS+-256, hybrid classical+PQC modes
- **Chain of Custody**: Complete provenance tracking through asset lifecycle
- **Verification**: Multi-level validation with trust chain verification
- **Policy Enforcement**: Organizational compliance rules engine

### Enterprise Features
- **Access Control**: LDAP/AD integration, RBAC
- **Workflow**: Multi-stage approval processes
- **Compliance**: PDPA, export control, classification labels
- **Integration**: DAM, CMS, production tools
- **Audit**: Immutable audit trails, blockchain anchoring (optional)

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/OpenMediaTrust.git
cd OpenMediaTrust

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings

# Initialize database
python scripts/init_db.py

# Start services
docker-compose up -d
```

### Basic Usage

```python
from openmediatrust import ManifestCreator, Signer

# Create manifest
creator = ManifestCreator()
manifest = creator.create(
    file_path="image.jpg",
    creator="john.doe@company.com",
    department="Marketing",
    project="Campaign-2025-Q4"
)

# Sign with quantum-safe algorithm
signer = Signer(algorithm="ml-dsa-65")
signed_manifest = signer.sign(manifest)

# Embed in asset
creator.embed(signed_manifest, "image.jpg", "image_signed.jpg")
```

## Project Structure

```
OpenMediaTrust/
├── src/
│   ├── core/               # Core manifest functionality
│   ├── enterprise/         # Enterprise features
│   ├── verification/       # Verification layer
│   ├── storage/           # Storage backends
│   └── api/               # REST API
├── config/                # Configuration files
├── docs/                  # Documentation
├── tests/                 # Test suites
├── scripts/               # Utility scripts
└── deployment/            # Deployment configs
```

## Documentation

- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Security Model](docs/security.md)
- [Integration Guide](docs/integration.md)

## Use Cases

1. **Marketing Content**: Brand asset tracking with approval workflows
2. **Legal Documents**: Evidence chain with tampering detection
3. **Product Photography**: Authenticity verification for e-commerce
4. **News/PR**: Source verification for published content
5. **Internal Communications**: Executive announcement authentication
6. **Training Materials**: Version control and certification
7. **Security/Surveillance**: Chain of custody for evidence

## Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL, MongoDB
- **Storage**: MinIO/S3
- **Crypto**: PQCrypto, OpenSSL
- **Queue**: Redis, Celery
- **Frontend**: React, TypeScript (Dashboard)

## Security

This project implements:
- Post-quantum cryptographic algorithms (ML-DSA, SLH-DSA)
- Hardware Security Module (HSM) integration
- Zero-knowledge proofs for selective disclosure
- Secure key ceremony procedures
- FIPS 140-2 Level 3 compliance ready

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[SRAN License]

## Support

For enterprise support, contact: support@openmediatrust.org
