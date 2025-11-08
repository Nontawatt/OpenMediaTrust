"""
Verification API endpoints.

Handles manifest validation, signature verification, and policy checking.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.verification.validator import ValidationLevel

router = APIRouter()


# Request/Response models
class VerificationRequest(BaseModel):
    """Verification request."""

    manifest_id: str
    strict: bool = True


class AssertionVerificationResult(BaseModel):
    """Assertion verification result."""

    label: str
    verified: bool
    message: str


class VerificationResponse(BaseModel):
    """Verification response."""

    manifest_id: str
    valid: bool
    trust_level: ValidationLevel
    signature_valid: bool
    certificate_trusted: bool
    chain_complete: bool
    assertions_verified: List[AssertionVerificationResult]
    issues: List[dict]
    warnings: List[dict]
    organizational_compliance: Optional[dict] = None


class PolicyCheckRequest(BaseModel):
    """Policy check request."""

    manifest_id: str
    policy_name: str


class PolicyCheckResponse(BaseModel):
    """Policy check response."""

    manifest_id: str
    policy_name: str
    passed: bool
    violations: List[dict]


@router.post("/verify", response_model=VerificationResponse)
async def verify_manifest(request: VerificationRequest):
    """
    Verify a C2PA manifest.

    Validates manifest structure, signature, assertions, and trust chain.

    Args:
        request: Verification request

    Returns:
        Verification result
    """
    # TODO: Load manifest and verify
    return VerificationResponse(
        manifest_id=request.manifest_id,
        valid=False,
        trust_level=ValidationLevel.INVALID,
        signature_valid=False,
        certificate_trusted=False,
        chain_complete=False,
        assertions_verified=[],
        issues=[],
        warnings=[],
    )


@router.post("/verify/policy", response_model=PolicyCheckResponse)
async def check_policy(request: PolicyCheckRequest):
    """
    Check manifest against organizational policy.

    Args:
        request: Policy check request

    Returns:
        Policy check result
    """
    # TODO: Load manifest and evaluate policy
    return PolicyCheckResponse(
        manifest_id=request.manifest_id,
        policy_name=request.policy_name,
        passed=False,
        violations=[],
    )


@router.get("/verify/{manifest_id}/history")
async def get_verification_history(manifest_id: str, limit: int = 50):
    """
    Get verification history for a manifest.

    Args:
        manifest_id: Manifest identifier
        limit: Maximum results

    Returns:
        List of verification records
    """
    # TODO: Query verification history from database
    return {"manifest_id": manifest_id, "verifications": []}


@router.get("/verify/{manifest_id}/chain-of-custody")
async def get_chain_of_custody(manifest_id: str):
    """
    Get complete chain of custody for a manifest.

    Args:
        manifest_id: Manifest identifier

    Returns:
        Chain of custody information
    """
    # TODO: Extract and return action history
    return {"manifest_id": manifest_id, "actions": [], "ingredients": []}
