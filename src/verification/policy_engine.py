"""
Policy engine for organizational manifest validation rules.

Enforces custom organizational policies beyond standard C2PA validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel

from src.core.models import ClassificationLevel, Manifest


class PolicyRuleType(str, Enum):
    """Types of policy rules."""

    REQUIRED_ASSERTION = "required_assertion"
    FORBIDDEN_ASSERTION = "forbidden_assertion"
    REQUIRED_FIELD = "required_field"
    VALUE_CONSTRAINT = "value_constraint"
    CLASSIFICATION_CONSTRAINT = "classification_constraint"
    CUSTOM_FUNCTION = "custom_function"


class PolicyRuleSeverity(str, Enum):
    """Severity of policy violations."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class PolicyRule(BaseModel):
    """Policy rule definition."""

    name: str
    description: str
    rule_type: PolicyRuleType
    severity: PolicyRuleSeverity
    enabled: bool = True

    # Rule parameters
    assertion_label: Optional[str] = None
    field_path: Optional[str] = None
    required_value: Optional[Any] = None
    allowed_values: Optional[List[Any]] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    classification_levels: Optional[List[ClassificationLevel]] = None

    # Custom validation function name
    custom_function: Optional[str] = None


class PolicyViolation(BaseModel):
    """Policy violation record."""

    rule_name: str
    severity: PolicyRuleSeverity
    message: str
    location: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation."""

    manifest_id: str
    policy_name: str
    passed: bool
    violations: List[PolicyViolation]
    evaluated_at: datetime


class OrganizationalPolicy(BaseModel):
    """Complete organizational policy."""

    name: str
    description: str
    version: str
    rules: List[PolicyRule]
    department: Optional[str] = None
    classification_level: Optional[ClassificationLevel] = None


class PolicyEngine:
    """Policy evaluation engine."""

    def __init__(self):
        """Initialize policy engine."""
        self.policies: Dict[str, OrganizationalPolicy] = {}
        self.custom_functions: Dict[str, Callable] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        """Initialize default organizational policies."""
        # Marketing content policy
        marketing_policy = OrganizationalPolicy(
            name="marketing_content",
            description="Policy for marketing and public relations content",
            version="1.0",
            department="Marketing",
            rules=[
                PolicyRule(
                    name="require_creative_work",
                    description="Must have CreativeWork assertion with author",
                    rule_type=PolicyRuleType.REQUIRED_ASSERTION,
                    severity=PolicyRuleSeverity.ERROR,
                    assertion_label="stds.schema-org.CreativeWork",
                ),
                PolicyRule(
                    name="require_workflow",
                    description="Must have enterprise workflow",
                    rule_type=PolicyRuleType.REQUIRED_ASSERTION,
                    severity=PolicyRuleSeverity.ERROR,
                    assertion_label="org.enterprise.workflow",
                ),
                PolicyRule(
                    name="public_classification",
                    description="Marketing content must be classified as public",
                    rule_type=PolicyRuleType.CLASSIFICATION_CONSTRAINT,
                    severity=PolicyRuleSeverity.ERROR,
                    classification_levels=[ClassificationLevel.PUBLIC],
                ),
            ],
        )
        self.policies["marketing_content"] = marketing_policy

        # Legal document policy
        legal_policy = OrganizationalPolicy(
            name="legal_documents",
            description="Policy for legal and compliance documents",
            version="1.0",
            department="Legal",
            rules=[
                PolicyRule(
                    name="require_hash",
                    description="Must have hash assertion for integrity",
                    rule_type=PolicyRuleType.REQUIRED_ASSERTION,
                    severity=PolicyRuleSeverity.ERROR,
                    assertion_label="c2pa.hash.data",
                ),
                PolicyRule(
                    name="require_actions",
                    description="Must have complete action history",
                    rule_type=PolicyRuleType.REQUIRED_ASSERTION,
                    severity=PolicyRuleSeverity.ERROR,
                    assertion_label="c2pa.actions",
                ),
                PolicyRule(
                    name="confidential_or_higher",
                    description="Legal docs must be confidential or higher",
                    rule_type=PolicyRuleType.CLASSIFICATION_CONSTRAINT,
                    severity=PolicyRuleSeverity.ERROR,
                    classification_levels=[
                        ClassificationLevel.CONFIDENTIAL,
                        ClassificationLevel.SECRET,
                        ClassificationLevel.TOP_SECRET,
                    ],
                ),
            ],
        )
        self.policies["legal_documents"] = legal_policy

    def add_policy(self, policy: OrganizationalPolicy) -> None:
        """
        Add a custom policy.

        Args:
            policy: Policy to add
        """
        self.policies[policy.name] = policy

    def register_custom_function(
        self, name: str, function: Callable[[Manifest], bool]
    ) -> None:
        """
        Register a custom validation function.

        Args:
            name: Function name
            function: Callable that takes manifest and returns bool
        """
        self.custom_functions[name] = function

    def evaluate(self, manifest: Manifest, policy_name: str) -> PolicyEvaluationResult:
        """
        Evaluate manifest against a policy.

        Args:
            manifest: Manifest to evaluate
            policy_name: Name of policy to apply

        Returns:
            Evaluation result

        Raises:
            ValueError: If policy not found
        """
        policy = self.policies.get(policy_name)
        if not policy:
            raise ValueError(f"Policy not found: {policy_name}")

        violations: List[PolicyViolation] = []

        for rule in policy.rules:
            if not rule.enabled:
                continue

            rule_violations = self._evaluate_rule(manifest, rule)
            violations.extend(rule_violations)

        # Determine if passed (no ERROR severity violations)
        passed = not any(v.severity == PolicyRuleSeverity.ERROR for v in violations)

        return PolicyEvaluationResult(
            manifest_id=manifest.instance_id,
            policy_name=policy_name,
            passed=passed,
            violations=violations,
            evaluated_at=datetime.utcnow(),
        )

    def _evaluate_rule(
        self, manifest: Manifest, rule: PolicyRule
    ) -> List[PolicyViolation]:
        """Evaluate a single rule."""
        if rule.rule_type == PolicyRuleType.REQUIRED_ASSERTION:
            return self._check_required_assertion(manifest, rule)
        elif rule.rule_type == PolicyRuleType.FORBIDDEN_ASSERTION:
            return self._check_forbidden_assertion(manifest, rule)
        elif rule.rule_type == PolicyRuleType.REQUIRED_FIELD:
            return self._check_required_field(manifest, rule)
        elif rule.rule_type == PolicyRuleType.VALUE_CONSTRAINT:
            return self._check_value_constraint(manifest, rule)
        elif rule.rule_type == PolicyRuleType.CLASSIFICATION_CONSTRAINT:
            return self._check_classification_constraint(manifest, rule)
        elif rule.rule_type == PolicyRuleType.CUSTOM_FUNCTION:
            return self._check_custom_function(manifest, rule)
        else:
            return []

    def _check_required_assertion(
        self, manifest: Manifest, rule: PolicyRule
    ) -> List[PolicyViolation]:
        """Check if required assertion exists."""
        if not rule.assertion_label:
            return []

        assertion = manifest.get_assertion(rule.assertion_label)
        if not assertion:
            return [
                PolicyViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"Required assertion '{rule.assertion_label}' not found",
                    location=f"assertions[{rule.assertion_label}]",
                    expected=rule.assertion_label,
                    actual="missing",
                )
            ]

        return []

    def _check_forbidden_assertion(
        self, manifest: Manifest, rule: PolicyRule
    ) -> List[PolicyViolation]:
        """Check if forbidden assertion exists."""
        if not rule.assertion_label:
            return []

        assertion = manifest.get_assertion(rule.assertion_label)
        if assertion:
            return [
                PolicyViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"Forbidden assertion '{rule.assertion_label}' found",
                    location=f"assertions[{rule.assertion_label}]",
                    expected="not present",
                    actual="present",
                )
            ]

        return []

    def _check_required_field(
        self, manifest: Manifest, rule: PolicyRule
    ) -> List[PolicyViolation]:
        """Check if required field exists."""
        if not rule.field_path:
            return []

        # Simple field path resolution (e.g., "title", "organization")
        value = getattr(manifest, rule.field_path, None)
        if value is None:
            return [
                PolicyViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"Required field '{rule.field_path}' not found",
                    location=rule.field_path,
                    expected="value",
                    actual="null",
                )
            ]

        return []

    def _check_value_constraint(
        self, manifest: Manifest, rule: PolicyRule
    ) -> List[PolicyViolation]:
        """Check value constraints."""
        if not rule.field_path:
            return []

        value = getattr(manifest, rule.field_path, None)
        if value is None:
            return []

        violations = []

        # Check allowed values
        if rule.allowed_values and value not in rule.allowed_values:
            violations.append(
                PolicyViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"Field '{rule.field_path}' has invalid value",
                    location=rule.field_path,
                    expected=f"one of {rule.allowed_values}",
                    actual=str(value),
                )
            )

        # Check min/max values
        if rule.min_value is not None and value < rule.min_value:
            violations.append(
                PolicyViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"Field '{rule.field_path}' below minimum",
                    location=rule.field_path,
                    expected=f">= {rule.min_value}",
                    actual=str(value),
                )
            )

        if rule.max_value is not None and value > rule.max_value:
            violations.append(
                PolicyViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=f"Field '{rule.field_path}' above maximum",
                    location=rule.field_path,
                    expected=f"<= {rule.max_value}",
                    actual=str(value),
                )
            )

        return violations

    def _check_classification_constraint(
        self, manifest: Manifest, rule: PolicyRule
    ) -> List[PolicyViolation]:
        """Check classification level constraints."""
        workflow = manifest.get_assertion("org.enterprise.workflow")
        if not workflow or not isinstance(workflow.data, dict):
            return [
                PolicyViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message="No workflow assertion to check classification",
                    location="assertions[org.enterprise.workflow]",
                )
            ]

        classification = workflow.data.get("classification")
        if not classification:
            return [
                PolicyViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message="No classification specified",
                    location="workflow.classification",
                )
            ]

        if rule.classification_levels:
            allowed = [level.value for level in rule.classification_levels]
            if classification not in allowed:
                return [
                    PolicyViolation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"Invalid classification level",
                        location="workflow.classification",
                        expected=f"one of {allowed}",
                        actual=classification,
                    )
                ]

        return []

    def _check_custom_function(
        self, manifest: Manifest, rule: PolicyRule
    ) -> List[PolicyViolation]:
        """Check custom validation function."""
        if not rule.custom_function:
            return []

        func = self.custom_functions.get(rule.custom_function)
        if not func:
            return [
                PolicyViolation(
                    rule_name=rule.name,
                    severity=PolicyRuleSeverity.ERROR,
                    message=f"Custom function '{rule.custom_function}' not found",
                )
            ]

        try:
            result = func(manifest)
            if not result:
                return [
                    PolicyViolation(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"Custom validation '{rule.custom_function}' failed",
                    )
                ]
        except Exception as e:
            return [
                PolicyViolation(
                    rule_name=rule.name,
                    severity=PolicyRuleSeverity.ERROR,
                    message=f"Custom validation error: {str(e)}",
                )
            ]

        return []
