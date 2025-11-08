"""
Core data models for C2PA manifests.

This module defines the data structures for manifests, assertions, and signatures
following the C2PA specification with enterprise extensions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class SignatureAlgorithm(str, Enum):
    """Supported signature algorithms."""

    # Classical algorithms
    RSA_PSS_SHA256 = "ps256"
    RSA_PSS_SHA384 = "ps384"
    RSA_PSS_SHA512 = "ps512"
    ECDSA_SHA256 = "es256"
    ECDSA_SHA384 = "es384"
    ECDSA_SHA512 = "es512"

    # Post-quantum algorithms
    ML_DSA_44 = "ml-dsa-44"  # Dilithium2
    ML_DSA_65 = "ml-dsa-65"  # Dilithium3
    ML_DSA_87 = "ml-dsa-87"  # Dilithium5
    SLH_DSA_SHA2_128S = "slh-dsa-sha2-128s"  # SPHINCS+
    SLH_DSA_SHA2_256S = "slh-dsa-sha2-256s"

    # Hybrid modes
    HYBRID_RSA_ML_DSA = "hybrid-rsa-ml-dsa-65"
    HYBRID_ECDSA_ML_DSA = "hybrid-ecdsa-ml-dsa-65"


class HashAlgorithm(str, Enum):
    """Supported hash algorithms."""

    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
    SHA3_256 = "sha3-256"
    SHA3_512 = "sha3-512"


class ActionType(str, Enum):
    """C2PA action types."""

    CREATED = "c2pa.created"
    EDITED = "c2pa.edited"
    CROPPED = "c2pa.cropped"
    FILTERED = "c2pa.filtered"
    TRANSCODED = "c2pa.transcoded"
    PUBLISHED = "c2pa.published"
    REVIEWED = "c2pa.reviewed"
    APPROVED = "c2pa.approved"


class DigitalSourceType(str, Enum):
    """IPTC digital source types."""

    DIGITAL_CAPTURE = "http://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture"
    NEGATIVE_FILM = "http://cv.iptc.org/newscodes/digitalsourcetype/negativeFilm"
    POSITIVE_FILM = "http://cv.iptc.org/newscodes/digitalsourcetype/positiveFilm"
    PRINT_SCAN = "http://cv.iptc.org/newscodes/digitalsourcetype/print"
    MINOR_HUMAN_EDITS = "http://cv.iptc.org/newscodes/digitalsourcetype/minorHumanEdits"
    COMPOSITE_CAPTURE = "http://cv.iptc.org/newscodes/digitalsourcetype/compositeCapture"
    TRAINED_ALGORITHMIC = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"
    COMPOSITE_SYNTHETIC = "http://cv.iptc.org/newscodes/digitalsourcetype/compositeSynthetic"
    ALGORITHM_ENHANCED = "http://cv.iptc.org/newscodes/digitalsourcetype/algorithmicallyEnhanced"
    DATA_DRIVEN = "http://cv.iptc.org/newscodes/digitalsourcetype/dataDrivenMedia"
    VIRTUAL_RECORDING = "http://cv.iptc.org/newscodes/digitalsourcetype/virtualRecording"


class ClassificationLevel(str, Enum):
    """Document classification levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class Action(BaseModel):
    """C2PA action record."""

    action: ActionType
    when: datetime
    software_agent: Optional[str] = None
    digital_source_type: Optional[DigitalSourceType] = None
    parameters: Optional[Dict[str, Any]] = None
    changed: Optional[List[str]] = None
    instance_id: Optional[str] = None


class Author(BaseModel):
    """Content author information."""

    type: str = Field(default="Person", alias="@type")
    name: str
    identifier: Optional[str] = None
    credential: Optional[str] = None
    email: Optional[str] = None


class OrganizationInfo(BaseModel):
    """Enterprise organization metadata."""

    department: Optional[str] = None
    project: Optional[str] = None
    cost_center: Optional[str] = None
    approver: Optional[str] = None
    business_unit: Optional[str] = None


class WorkflowStep(BaseModel):
    """Workflow approval step."""

    role: str
    user_id: str
    user_name: Optional[str] = None
    timestamp: datetime
    status: str
    comments: Optional[str] = None


class ComplianceCheck(BaseModel):
    """Compliance validation results."""

    pdpa_approved: bool = False
    trademark_cleared: bool = False
    legal_review: Optional[str] = None
    export_control_passed: bool = True
    classification_verified: bool = True


class WorkflowAssertion(BaseModel):
    """Enterprise workflow assertion."""

    workflow_id: str
    approval_chain: List[WorkflowStep]
    compliance_check: ComplianceCheck
    classification: ClassificationLevel = ClassificationLevel.INTERNAL
    retention_policy: Optional[str] = None


class Assertion(BaseModel):
    """C2PA assertion."""

    label: str
    data: Union[Dict[str, Any], List[Any]]
    instance_id: Optional[str] = Field(default_factory=lambda: f"assertion:{uuid4()}")

    class Config:
        arbitrary_types_allowed = True


class HashData(BaseModel):
    """Hash assertion data."""

    exclusions: List[str] = Field(default_factory=list)
    name: HashAlgorithm = HashAlgorithm.SHA256
    alg: HashAlgorithm = HashAlgorithm.SHA256
    hash: Optional[str] = None


class Signature(BaseModel):
    """C2PA signature information."""

    alg: SignatureAlgorithm
    certificate_chain: List[str]
    timestamp: datetime
    tsa: Optional[str] = None  # Time Stamping Authority
    signature_value: Optional[bytes] = None

    class Config:
        arbitrary_types_allowed = True


class ClaimGeneratorInfo(BaseModel):
    """Information about the claim generator."""

    name: str
    version: str
    icon: Optional[str] = None


class Manifest(BaseModel):
    """C2PA Manifest structure."""

    # Required fields
    claim_generator: str
    format: str
    instance_id: str = Field(default_factory=lambda: f"xmp:iid:{uuid4()}")

    # Optional core fields
    claim_generator_info: Optional[List[ClaimGeneratorInfo]] = None
    title: Optional[str] = None
    assertions: List[Assertion] = Field(default_factory=list)
    signature: Optional[Signature] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Enterprise extensions
    organization: Optional[str] = None
    tenant_id: Optional[str] = None

    @validator("instance_id")
    def validate_instance_id(cls, v: str) -> str:
        """Ensure instance_id has proper format."""
        if not v.startswith(("xmp:iid:", "uuid:")):
            return f"xmp:iid:{v}"
        return v

    def add_assertion(self, label: str, data: Union[Dict[str, Any], List[Any]]) -> None:
        """Add an assertion to the manifest."""
        assertion = Assertion(label=label, data=data)
        self.assertions.append(assertion)

    def get_assertion(self, label: str) -> Optional[Assertion]:
        """Get an assertion by label."""
        for assertion in self.assertions:
            if assertion.label == label:
                return assertion
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary format."""
        return self.dict(exclude_none=True, by_alias=True)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: v.hex() if v else None,
        }
