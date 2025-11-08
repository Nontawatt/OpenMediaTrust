"""
Manifest validator for C2PA content verification.

Validates manifest structure, signatures, assertions, and trust chains.
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.core.models import Manifest
from src.core.signer import Signer


class ValidationLevel(str, Enum):
    """Validation trust levels."""

    INVALID = "invalid"
    BASIC = "basic"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"
    HIGH_ASSURANCE = "high_assurance"


class ValidationIssue(BaseModel):
    """Validation issue or warning."""

    severity: str  # error, warning, info
    code: str
    message: str
    location: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AssertionValidation(BaseModel):
    """Validation result for a single assertion."""

    label: str
    verified: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Complete validation result."""

    valid: bool
    trust_level: ValidationLevel
    signature_valid: bool
    certificate_trusted: bool
    chain_complete: bool
    assertions_verified: List[AssertionValidation]
    issues: List[ValidationIssue]
    warnings: List[ValidationIssue]
    verified_at: datetime
    manifest_id: str

    # Enterprise compliance
    organizational_compliance: Optional[Dict[str, bool]] = None


class ManifestValidator:
    """Validate C2PA manifests."""

    def __init__(self, trusted_certificates: Optional[List[str]] = None):
        """
        Initialize validator.

        Args:
            trusted_certificates: List of trusted certificate PEM strings
        """
        self.trusted_certificates = trusted_certificates or []

    def validate(
        self, manifest: Manifest, strict: bool = True
    ) -> ValidationResult:
        """
        Validate a manifest.

        Args:
            manifest: Manifest to validate
            strict: Whether to use strict validation

        Returns:
            Validation result
        """
        issues: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []
        assertion_validations: List[AssertionValidation] = []

        # Validate structure
        structure_valid = self._validate_structure(manifest, issues, warnings)

        # Validate assertions
        assertions_valid = self._validate_assertions(
            manifest, assertion_validations, issues, warnings
        )

        # Validate signature
        signature_valid = False
        certificate_trusted = False
        if manifest.signature:
            signature_valid = self._validate_signature(manifest, issues, warnings)
            certificate_trusted = self._validate_certificate_trust(
                manifest, issues, warnings
            )
        else:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="NO_SIGNATURE",
                    message="Manifest is not signed",
                )
            )

        # Validate chain of custody
        chain_complete = self._validate_chain_of_custody(manifest, issues, warnings)

        # Determine trust level
        trust_level = self._determine_trust_level(
            signature_valid, certificate_trusted, chain_complete, len(issues)
        )

        # Check enterprise compliance
        org_compliance = self._check_organizational_compliance(manifest)

        # Overall validity
        valid = structure_valid and assertions_valid and signature_valid
        if strict:
            valid = valid and certificate_trusted and chain_complete

        return ValidationResult(
            valid=valid,
            trust_level=trust_level,
            signature_valid=signature_valid,
            certificate_trusted=certificate_trusted,
            chain_complete=chain_complete,
            assertions_verified=assertion_validations,
            issues=issues,
            warnings=warnings,
            verified_at=datetime.utcnow(),
            manifest_id=manifest.instance_id,
            organizational_compliance=org_compliance,
        )

    def _validate_structure(
        self,
        manifest: Manifest,
        issues: List[ValidationIssue],
        warnings: List[ValidationIssue],
    ) -> bool:
        """Validate manifest structure."""
        valid = True

        # Check required fields
        if not manifest.claim_generator:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="MISSING_CLAIM_GENERATOR",
                    message="Manifest missing claim_generator",
                )
            )
            valid = False

        if not manifest.format:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="MISSING_FORMAT",
                    message="Manifest missing format",
                )
            )
            valid = False

        if not manifest.instance_id:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="MISSING_INSTANCE_ID",
                    message="Manifest missing instance_id",
                )
            )
            valid = False

        # Validate instance_id format
        if manifest.instance_id and not (
            manifest.instance_id.startswith("xmp:iid:")
            or manifest.instance_id.startswith("uuid:")
        ):
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="INVALID_INSTANCE_ID_FORMAT",
                    message="instance_id should start with 'xmp:iid:' or 'uuid:'",
                )
            )

        return valid

    def _validate_assertions(
        self,
        manifest: Manifest,
        assertion_validations: List[AssertionValidation],
        issues: List[ValidationIssue],
        warnings: List[ValidationIssue],
    ) -> bool:
        """Validate assertions."""
        if not manifest.assertions:
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="NO_ASSERTIONS",
                    message="Manifest has no assertions",
                )
            )
            return True

        # Check for required assertions
        has_actions = False
        has_hash = False

        for assertion in manifest.assertions:
            if assertion.label == "c2pa.actions":
                has_actions = True
                validation = self._validate_actions_assertion(assertion)
                assertion_validations.append(validation)
            elif assertion.label == "c2pa.hash.data":
                has_hash = True
                validation = self._validate_hash_assertion(assertion)
                assertion_validations.append(validation)
            else:
                # Other assertions
                assertion_validations.append(
                    AssertionValidation(
                        label=assertion.label,
                        verified=True,
                        message="Assertion present",
                    )
                )

        if not has_actions:
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="MISSING_ACTIONS_ASSERTION",
                    message="Recommended c2pa.actions assertion not found",
                )
            )

        if not has_hash:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="MISSING_HASH_ASSERTION",
                    message="Required c2pa.hash.data assertion not found",
                )
            )
            return False

        return True

    def _validate_actions_assertion(self, assertion: Any) -> AssertionValidation:
        """Validate actions assertion."""
        if not isinstance(assertion.data, dict):
            return AssertionValidation(
                label="c2pa.actions",
                verified=False,
                message="Invalid actions assertion format",
            )

        actions = assertion.data.get("actions", [])
        if not actions:
            return AssertionValidation(
                label="c2pa.actions",
                verified=False,
                message="Actions assertion has no actions",
            )

        return AssertionValidation(
            label="c2pa.actions",
            verified=True,
            message=f"Actions assertion valid ({len(actions)} actions)",
            details={"action_count": len(actions)},
        )

    def _validate_hash_assertion(self, assertion: Any) -> AssertionValidation:
        """Validate hash assertion."""
        if not isinstance(assertion.data, dict):
            return AssertionValidation(
                label="c2pa.hash.data",
                verified=False,
                message="Invalid hash assertion format",
            )

        if "name" not in assertion.data or "alg" not in assertion.data:
            return AssertionValidation(
                label="c2pa.hash.data",
                verified=False,
                message="Hash assertion missing required fields",
            )

        return AssertionValidation(
            label="c2pa.hash.data",
            verified=True,
            message="Hash assertion valid",
        )

    def _validate_signature(
        self,
        manifest: Manifest,
        issues: List[ValidationIssue],
        warnings: List[ValidationIssue],
    ) -> bool:
        """Validate manifest signature."""
        if not manifest.signature:
            return False

        try:
            # Create signer with same algorithm
            signer = Signer(algorithm=manifest.signature.alg)

            # Verify signature
            valid = signer.verify(manifest)

            if not valid:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="INVALID_SIGNATURE",
                        message="Manifest signature verification failed",
                    )
                )
                return False

            return True

        except Exception as e:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="SIGNATURE_VERIFICATION_ERROR",
                    message=f"Error verifying signature: {str(e)}",
                )
            )
            return False

    def _validate_certificate_trust(
        self,
        manifest: Manifest,
        issues: List[ValidationIssue],
        warnings: List[ValidationIssue],
    ) -> bool:
        """Validate certificate trust chain."""
        if not manifest.signature or not manifest.signature.certificate_chain:
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="NO_CERTIFICATE_CHAIN",
                    message="No certificate chain provided",
                )
            )
            return False

        # Check if certificates are in trusted list
        if not self.trusted_certificates:
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="NO_TRUSTED_CERTS",
                    message="No trusted certificates configured",
                )
            )
            return False

        # Simple trust check (in production, validate full chain)
        cert_chain = manifest.signature.certificate_chain
        for trusted_cert in self.trusted_certificates:
            if trusted_cert in cert_chain:
                return True

        warnings.append(
            ValidationIssue(
                severity="warning",
                code="UNTRUSTED_CERTIFICATE",
                message="Certificate not in trusted list",
            )
        )
        return False

    def _validate_chain_of_custody(
        self,
        manifest: Manifest,
        issues: List[ValidationIssue],
        warnings: List[ValidationIssue],
    ) -> bool:
        """Validate chain of custody."""
        # Check for actions assertion with complete history
        actions_assertion = manifest.get_assertion("c2pa.actions")
        if not actions_assertion:
            return False

        # In a full implementation, would check:
        # - Temporal consistency of actions
        # - Valid action transitions
        # - Ingredient manifests for composites
        # - Hash consistency through edits

        return True

    def _determine_trust_level(
        self,
        signature_valid: bool,
        certificate_trusted: bool,
        chain_complete: bool,
        issue_count: int,
    ) -> ValidationLevel:
        """Determine overall trust level."""
        if not signature_valid or issue_count > 0:
            return ValidationLevel.INVALID

        if certificate_trusted and chain_complete:
            return ValidationLevel.ENTERPRISE

        if certificate_trusted:
            return ValidationLevel.STANDARD

        if signature_valid:
            return ValidationLevel.BASIC

        return ValidationLevel.INVALID

    def _check_organizational_compliance(
        self, manifest: Manifest
    ) -> Dict[str, bool]:
        """Check organizational compliance."""
        compliance = {}

        workflow = manifest.get_assertion("org.enterprise.workflow")
        if workflow and isinstance(workflow.data, dict):
            compliance_check = workflow.data.get("compliance_check", {})
            compliance["pdpa_compliant"] = compliance_check.get("pdpa_approved", False)
            compliance["trademark_cleared"] = compliance_check.get(
                "trademark_cleared", False
            )
            compliance["legal_review_passed"] = (
                compliance_check.get("legal_review") == "passed"
            )

            # Check workflow approval
            approval_chain = workflow.data.get("approval_chain", [])
            compliance["workflow_approved"] = any(
                step.get("status") == "approved" for step in approval_chain
            )

            # Check department authorization
            org_context = workflow.data.get("organizational_context", {})
            compliance["department_authorized"] = bool(org_context.get("department"))

        return compliance
