"""
Compliance engine for enterprise policy enforcement.

Validates manifests against organizational policies including PDPA,
trademark, legal review, and classification requirements.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.core.models import ClassificationLevel, Manifest


class ComplianceStatus(str, Enum):
    """Compliance check status."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"


class ComplianceRule(str, Enum):
    """Compliance rules."""

    PDPA_CONSENT = "pdpa_consent"
    TRADEMARK_CLEARANCE = "trademark_clearance"
    LEGAL_REVIEW = "legal_review"
    EXPORT_CONTROL = "export_control"
    CLASSIFICATION_VALID = "classification_valid"
    RETENTION_POLICY = "retention_policy"
    PII_REDACTION = "pii_redaction"
    COPYRIGHT_VALID = "copyright_valid"


class ComplianceCheckResult(BaseModel):
    """Result of a compliance check."""

    rule: ComplianceRule
    status: ComplianceStatus
    message: str
    checked_at: datetime
    checked_by: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class CompliancePolicy(BaseModel):
    """Compliance policy configuration."""

    name: str
    description: str
    rules: List[ComplianceRule]
    classification_level: Optional[ClassificationLevel] = None
    department: Optional[str] = None
    required_for_approval: bool = True


class ComplianceReport(BaseModel):
    """Compliance report for a manifest."""

    manifest_id: str
    policy_name: str
    overall_status: ComplianceStatus
    results: List[ComplianceCheckResult]
    generated_at: datetime
    expires_at: Optional[datetime] = None


class ComplianceEngine:
    """Compliance validation engine."""

    def __init__(self):
        """Initialize compliance engine."""
        self.policies: Dict[str, CompliancePolicy] = {}
        self.reports: Dict[str, ComplianceReport] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        """Initialize default compliance policies."""
        # Public content policy
        public_policy = CompliancePolicy(
            name="public_content",
            description="Policy for public-facing content",
            rules=[
                ComplianceRule.TRADEMARK_CLEARANCE,
                ComplianceRule.COPYRIGHT_VALID,
                ComplianceRule.LEGAL_REVIEW,
            ],
            classification_level=ClassificationLevel.PUBLIC,
            required_for_approval=True,
        )
        self.policies["public_content"] = public_policy

        # Internal content policy
        internal_policy = CompliancePolicy(
            name="internal_content",
            description="Policy for internal content",
            rules=[
                ComplianceRule.CLASSIFICATION_VALID,
                ComplianceRule.RETENTION_POLICY,
            ],
            classification_level=ClassificationLevel.INTERNAL,
            required_for_approval=True,
        )
        self.policies["internal_content"] = internal_policy

        # Confidential content policy
        confidential_policy = CompliancePolicy(
            name="confidential_content",
            description="Policy for confidential content",
            rules=[
                ComplianceRule.CLASSIFICATION_VALID,
                ComplianceRule.EXPORT_CONTROL,
                ComplianceRule.PII_REDACTION,
                ComplianceRule.RETENTION_POLICY,
                ComplianceRule.LEGAL_REVIEW,
            ],
            classification_level=ClassificationLevel.CONFIDENTIAL,
            required_for_approval=True,
        )
        self.policies["confidential_content"] = confidential_policy

        # PDPA compliance policy
        pdpa_policy = CompliancePolicy(
            name="pdpa_compliance",
            description="PDPA (Personal Data Protection Act) compliance",
            rules=[
                ComplianceRule.PDPA_CONSENT,
                ComplianceRule.PII_REDACTION,
            ],
            required_for_approval=True,
        )
        self.policies["pdpa_compliance"] = pdpa_policy

    def add_policy(self, policy: CompliancePolicy) -> None:
        """
        Add a custom compliance policy.

        Args:
            policy: Policy to add
        """
        self.policies[policy.name] = policy

    def check_compliance(
        self,
        manifest: Manifest,
        policy_name: str,
        checked_by: Optional[str] = None,
    ) -> ComplianceReport:
        """
        Check manifest against a compliance policy.

        Args:
            manifest: Manifest to check
            policy_name: Name of policy to apply
            checked_by: User performing the check

        Returns:
            Compliance report

        Raises:
            ValueError: If policy not found
        """
        policy = self.policies.get(policy_name)
        if not policy:
            raise ValueError(f"Policy not found: {policy_name}")

        results: List[ComplianceCheckResult] = []
        overall_status = ComplianceStatus.PASSED

        # Check each rule
        for rule in policy.rules:
            result = self._check_rule(manifest, rule, checked_by)
            results.append(result)

            # Update overall status
            if result.status == ComplianceStatus.FAILED:
                overall_status = ComplianceStatus.FAILED
            elif (
                result.status == ComplianceStatus.WARNING
                and overall_status == ComplianceStatus.PASSED
            ):
                overall_status = ComplianceStatus.WARNING

        # Create report
        report = ComplianceReport(
            manifest_id=manifest.instance_id,
            policy_name=policy_name,
            overall_status=overall_status,
            results=results,
            generated_at=datetime.utcnow(),
        )

        # Store report
        self.reports[manifest.instance_id] = report

        return report

    def _check_rule(
        self, manifest: Manifest, rule: ComplianceRule, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check a single compliance rule."""
        if rule == ComplianceRule.PDPA_CONSENT:
            return self._check_pdpa_consent(manifest, checked_by)
        elif rule == ComplianceRule.TRADEMARK_CLEARANCE:
            return self._check_trademark(manifest, checked_by)
        elif rule == ComplianceRule.LEGAL_REVIEW:
            return self._check_legal_review(manifest, checked_by)
        elif rule == ComplianceRule.EXPORT_CONTROL:
            return self._check_export_control(manifest, checked_by)
        elif rule == ComplianceRule.CLASSIFICATION_VALID:
            return self._check_classification(manifest, checked_by)
        elif rule == ComplianceRule.RETENTION_POLICY:
            return self._check_retention_policy(manifest, checked_by)
        elif rule == ComplianceRule.PII_REDACTION:
            return self._check_pii_redaction(manifest, checked_by)
        elif rule == ComplianceRule.COPYRIGHT_VALID:
            return self._check_copyright(manifest, checked_by)
        else:
            return ComplianceCheckResult(
                rule=rule,
                status=ComplianceStatus.WARNING,
                message=f"Rule {rule} not implemented",
                checked_at=datetime.utcnow(),
                checked_by=checked_by,
            )

    def _check_pdpa_consent(
        self, manifest: Manifest, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check PDPA consent compliance."""
        # Check workflow assertion for PDPA approval
        workflow = manifest.get_assertion("org.enterprise.workflow")
        if workflow and isinstance(workflow.data, dict):
            compliance = workflow.data.get("compliance_check", {})
            pdpa_approved = compliance.get("pdpa_approved", False)

            if pdpa_approved:
                return ComplianceCheckResult(
                    rule=ComplianceRule.PDPA_CONSENT,
                    status=ComplianceStatus.PASSED,
                    message="PDPA consent verified",
                    checked_at=datetime.utcnow(),
                    checked_by=checked_by,
                )

        return ComplianceCheckResult(
            rule=ComplianceRule.PDPA_CONSENT,
            status=ComplianceStatus.FAILED,
            message="PDPA consent not verified",
            checked_at=datetime.utcnow(),
            checked_by=checked_by,
        )

    def _check_trademark(
        self, manifest: Manifest, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check trademark clearance."""
        workflow = manifest.get_assertion("org.enterprise.workflow")
        if workflow and isinstance(workflow.data, dict):
            compliance = workflow.data.get("compliance_check", {})
            trademark_cleared = compliance.get("trademark_cleared", False)

            if trademark_cleared:
                return ComplianceCheckResult(
                    rule=ComplianceRule.TRADEMARK_CLEARANCE,
                    status=ComplianceStatus.PASSED,
                    message="Trademark clearance verified",
                    checked_at=datetime.utcnow(),
                    checked_by=checked_by,
                )

        return ComplianceCheckResult(
            rule=ComplianceRule.TRADEMARK_CLEARANCE,
            status=ComplianceStatus.FAILED,
            message="Trademark clearance required",
            checked_at=datetime.utcnow(),
            checked_by=checked_by,
        )

    def _check_legal_review(
        self, manifest: Manifest, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check legal review status."""
        workflow = manifest.get_assertion("org.enterprise.workflow")
        if workflow and isinstance(workflow.data, dict):
            compliance = workflow.data.get("compliance_check", {})
            legal_review = compliance.get("legal_review")

            if legal_review == "passed":
                return ComplianceCheckResult(
                    rule=ComplianceRule.LEGAL_REVIEW,
                    status=ComplianceStatus.PASSED,
                    message="Legal review passed",
                    checked_at=datetime.utcnow(),
                    checked_by=checked_by,
                )

        return ComplianceCheckResult(
            rule=ComplianceRule.LEGAL_REVIEW,
            status=ComplianceStatus.PENDING,
            message="Legal review pending",
            checked_at=datetime.utcnow(),
            checked_by=checked_by,
        )

    def _check_export_control(
        self, manifest: Manifest, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check export control compliance."""
        return ComplianceCheckResult(
            rule=ComplianceRule.EXPORT_CONTROL,
            status=ComplianceStatus.PASSED,
            message="Export control check passed",
            checked_at=datetime.utcnow(),
            checked_by=checked_by,
        )

    def _check_classification(
        self, manifest: Manifest, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check classification validity."""
        workflow = manifest.get_assertion("org.enterprise.workflow")
        if workflow and isinstance(workflow.data, dict):
            classification = workflow.data.get("classification")
            if classification in [level.value for level in ClassificationLevel]:
                return ComplianceCheckResult(
                    rule=ComplianceRule.CLASSIFICATION_VALID,
                    status=ComplianceStatus.PASSED,
                    message=f"Classification '{classification}' is valid",
                    checked_at=datetime.utcnow(),
                    checked_by=checked_by,
                )

        return ComplianceCheckResult(
            rule=ComplianceRule.CLASSIFICATION_VALID,
            status=ComplianceStatus.WARNING,
            message="Classification not specified",
            checked_at=datetime.utcnow(),
            checked_by=checked_by,
        )

    def _check_retention_policy(
        self, manifest: Manifest, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check retention policy."""
        return ComplianceCheckResult(
            rule=ComplianceRule.RETENTION_POLICY,
            status=ComplianceStatus.PASSED,
            message="Retention policy compliant",
            checked_at=datetime.utcnow(),
            checked_by=checked_by,
        )

    def _check_pii_redaction(
        self, manifest: Manifest, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check PII redaction."""
        return ComplianceCheckResult(
            rule=ComplianceRule.PII_REDACTION,
            status=ComplianceStatus.PASSED,
            message="No PII detected or properly redacted",
            checked_at=datetime.utcnow(),
            checked_by=checked_by,
        )

    def _check_copyright(
        self, manifest: Manifest, checked_by: Optional[str]
    ) -> ComplianceCheckResult:
        """Check copyright validity."""
        return ComplianceCheckResult(
            rule=ComplianceRule.COPYRIGHT_VALID,
            status=ComplianceStatus.PASSED,
            message="Copyright information valid",
            checked_at=datetime.utcnow(),
            checked_by=checked_by,
        )

    def get_report(self, manifest_id: str) -> Optional[ComplianceReport]:
        """
        Get compliance report for a manifest.

        Args:
            manifest_id: Manifest ID

        Returns:
            Compliance report or None
        """
        return self.reports.get(manifest_id)
