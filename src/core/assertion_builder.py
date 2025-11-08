"""
Assertion builder for C2PA manifests.

Creates various types of assertions including actions, hash data,
schema.org metadata, and enterprise-specific assertions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.models import (
    Action,
    ActionType,
    Assertion,
    Author,
    ClassificationLevel,
    ComplianceCheck,
    DigitalSourceType,
    HashAlgorithm,
    HashData,
    OrganizationInfo,
    WorkflowAssertion,
    WorkflowStep,
)


class AssertionBuilder:
    """Build C2PA assertions for manifests."""

    def __init__(self, organization: Optional[str] = None):
        """
        Initialize assertion builder.

        Args:
            organization: Organization name for enterprise assertions
        """
        self.organization = organization

    def build_actions_assertion(
        self,
        action: ActionType,
        software_agent: Optional[str] = None,
        digital_source_type: Optional[DigitalSourceType] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Assertion:
        """
        Build c2pa.actions assertion.

        Args:
            action: Type of action performed
            software_agent: Software that performed the action
            digital_source_type: IPTC digital source type
            parameters: Additional action parameters

        Returns:
            Actions assertion
        """
        action_record = Action(
            action=action,
            when=datetime.utcnow(),
            software_agent=software_agent,
            digital_source_type=digital_source_type,
            parameters=parameters,
        )

        return Assertion(label="c2pa.actions", data={"actions": [action_record.dict()]})

    def build_hash_assertion(
        self, hash_algorithm: HashAlgorithm = HashAlgorithm.SHA256, hash_value: Optional[str] = None
    ) -> Assertion:
        """
        Build c2pa.hash.data assertion.

        Args:
            hash_algorithm: Hash algorithm to use
            hash_value: Pre-computed hash value (optional)

        Returns:
            Hash assertion
        """
        hash_data = HashData(name=hash_algorithm, alg=hash_algorithm, hash=hash_value)

        return Assertion(label="c2pa.hash.data", data=hash_data.dict(exclude_none=True))

    def build_creative_work_assertion(
        self,
        author_name: str,
        author_email: Optional[str] = None,
        author_credential: Optional[str] = None,
        title: Optional[str] = None,
        date_published: Optional[datetime] = None,
        organization_info: Optional[OrganizationInfo] = None,
    ) -> Assertion:
        """
        Build stds.schema-org.CreativeWork assertion.

        Args:
            author_name: Name of the content creator
            author_email: Email of the creator
            author_credential: Credential/employee ID
            title: Title of the work
            date_published: Publication date
            organization_info: Enterprise organization metadata

        Returns:
            CreativeWork assertion
        """
        author = Author(
            name=author_name, email=author_email, credential=author_credential
        ).dict(exclude_none=True, by_alias=True)

        data: Dict[str, Any] = {"author": [author]}

        if title:
            data["name"] = title

        if date_published:
            data["datePublished"] = date_published.isoformat()

        if organization_info:
            data["organizationInfo"] = organization_info.dict(exclude_none=True)

        return Assertion(label="stds.schema-org.CreativeWork", data=data)

    def build_workflow_assertion(
        self,
        workflow_id: str,
        creator_id: str,
        creator_name: str,
        classification: ClassificationLevel = ClassificationLevel.INTERNAL,
        department: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Assertion:
        """
        Build enterprise workflow assertion.

        Args:
            workflow_id: Unique workflow identifier
            creator_id: User ID of creator
            creator_name: Name of creator
            classification: Document classification level
            department: Department name
            project: Project name

        Returns:
            Workflow assertion
        """
        initial_step = WorkflowStep(
            role="creator",
            user_id=creator_id,
            user_name=creator_name,
            timestamp=datetime.utcnow(),
            status="created",
        )

        compliance = ComplianceCheck()

        workflow = WorkflowAssertion(
            workflow_id=workflow_id,
            approval_chain=[initial_step],
            compliance_check=compliance,
            classification=classification,
        )

        data = workflow.dict(exclude_none=True)

        # Add organizational context
        if department or project:
            data["organizational_context"] = {}
            if department:
                data["organizational_context"]["department"] = department
            if project:
                data["organizational_context"]["project"] = project

        return Assertion(label="org.enterprise.workflow", data=data)

    def build_thumbnail_assertion(self, thumbnail_format: str, thumbnail_data: bytes) -> Assertion:
        """
        Build c2pa.thumbnail assertion.

        Args:
            thumbnail_format: MIME type of thumbnail (e.g., 'image/jpeg')
            thumbnail_data: Binary thumbnail data

        Returns:
            Thumbnail assertion
        """
        import base64

        data = {
            "format": thumbnail_format,
            "thumbnail": base64.b64encode(thumbnail_data).decode("utf-8"),
        }

        return Assertion(label="c2pa.thumbnail.claim.jpeg", data=data)

    def build_ingredient_assertion(
        self, ingredient_path: str, relationship: str = "parentOf"
    ) -> Assertion:
        """
        Build c2pa.ingredient assertion for composite content.

        Args:
            ingredient_path: Path or URI to ingredient asset
            relationship: Relationship type (parentOf, componentOf, etc.)

        Returns:
            Ingredient assertion
        """
        data = {
            "relationship": relationship,
            "uri": ingredient_path,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return Assertion(label="c2pa.ingredient", data=data)

    def build_training_mining_assertion(
        self, allowed: bool = False, constraint_info: Optional[str] = None
    ) -> Assertion:
        """
        Build c2pa.training-mining assertion for AI/ML usage.

        Args:
            allowed: Whether training/mining is allowed
            constraint_info: Additional constraint information

        Returns:
            Training-mining assertion
        """
        data: Dict[str, Any] = {
            "use": {
                "allowed": allowed,
                "constraint_info": constraint_info,
            }
        }

        return Assertion(label="c2pa.training-mining", data=data)

    def add_approval_to_workflow(
        self,
        workflow_assertion: Assertion,
        approver_id: str,
        approver_name: str,
        role: str,
        status: str,
        comments: Optional[str] = None,
    ) -> None:
        """
        Add an approval step to an existing workflow assertion.

        Args:
            workflow_assertion: Existing workflow assertion
            approver_id: User ID of approver
            approver_name: Name of approver
            role: Role in workflow (reviewer, approver, etc.)
            status: Approval status (approved, rejected, etc.)
            comments: Optional comments
        """
        if workflow_assertion.label != "org.enterprise.workflow":
            raise ValueError("Not a workflow assertion")

        approval_step = WorkflowStep(
            role=role,
            user_id=approver_id,
            user_name=approver_name,
            timestamp=datetime.utcnow(),
            status=status,
            comments=comments,
        )

        workflow_assertion.data["approval_chain"].append(approval_step.dict(exclude_none=True))

    def update_compliance_check(
        self,
        workflow_assertion: Assertion,
        pdpa_approved: Optional[bool] = None,
        trademark_cleared: Optional[bool] = None,
        legal_review: Optional[str] = None,
    ) -> None:
        """
        Update compliance checks in workflow assertion.

        Args:
            workflow_assertion: Existing workflow assertion
            pdpa_approved: PDPA compliance status
            trademark_cleared: Trademark clearance status
            legal_review: Legal review result
        """
        if workflow_assertion.label != "org.enterprise.workflow":
            raise ValueError("Not a workflow assertion")

        compliance = workflow_assertion.data.get("compliance_check", {})

        if pdpa_approved is not None:
            compliance["pdpa_approved"] = pdpa_approved
        if trademark_cleared is not None:
            compliance["trademark_cleared"] = trademark_cleared
        if legal_review is not None:
            compliance["legal_review"] = legal_review

        workflow_assertion.data["compliance_check"] = compliance
