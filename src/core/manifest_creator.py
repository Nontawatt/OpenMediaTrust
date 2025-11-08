"""
Manifest creator for C2PA content provenance.

Creates complete C2PA manifests with assertions and metadata.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.core.assertion_builder import AssertionBuilder
from src.core.metadata_extractor import MetadataExtractor
from src.core.models import (
    ActionType,
    Assertion,
    ClassificationLevel,
    ClaimGeneratorInfo,
    DigitalSourceType,
    HashAlgorithm,
    Manifest,
)


class ManifestCreator:
    """Create C2PA manifests for content."""

    def __init__(
        self,
        claim_generator: str = "OpenMediaTrust/1.0.0",
        organization: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize manifest creator.

        Args:
            claim_generator: Name and version of the claim generator
            organization: Organization name
            tenant_id: Multi-tenant identifier
        """
        self.claim_generator = claim_generator
        self.organization = organization
        self.tenant_id = tenant_id
        self.metadata_extractor = MetadataExtractor()
        self.assertion_builder = AssertionBuilder(organization=organization)

    def create(
        self,
        file_path: str,
        creator: str,
        title: Optional[str] = None,
        department: Optional[str] = None,
        project: Optional[str] = None,
        classification: ClassificationLevel = ClassificationLevel.INTERNAL,
        digital_source_type: Optional[DigitalSourceType] = None,
        action: ActionType = ActionType.CREATED,
        software_agent: Optional[str] = None,
        extract_metadata: bool = True,
    ) -> Manifest:
        """
        Create a C2PA manifest for a file.

        Args:
            file_path: Path to the content file
            creator: Creator's email or identifier
            title: Title of the content
            department: Department name
            project: Project name
            classification: Security classification level
            digital_source_type: IPTC digital source type
            action: Action being performed
            software_agent: Software used to create content
            extract_metadata: Whether to extract file metadata

        Returns:
            Complete C2PA manifest
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Extract file metadata
        file_metadata = {}
        if extract_metadata:
            file_metadata = self.metadata_extractor.extract(file_path)

        # Determine format
        mime_type = file_metadata.get("mime_type", "application/octet-stream")

        # Create manifest
        manifest = Manifest(
            claim_generator=self.claim_generator,
            format=mime_type,
            title=title or file_metadata.get("title", path.name),
            organization=self.organization,
            tenant_id=self.tenant_id,
        )

        # Add claim generator info
        manifest.claim_generator_info = [
            ClaimGeneratorInfo(
                name="OpenMediaTrust Enterprise C2PA System", version="1.0.0"
            )
        ]

        # Build and add assertions
        self._add_core_assertions(
            manifest=manifest,
            file_path=file_path,
            creator=creator,
            action=action,
            software_agent=software_agent or file_metadata.get("software"),
            digital_source_type=digital_source_type,
            file_metadata=file_metadata,
        )

        # Add enterprise workflow assertion
        if department or project or classification != ClassificationLevel.PUBLIC:
            workflow_id = f"WF-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8]}"
            workflow_assertion = self.assertion_builder.build_workflow_assertion(
                workflow_id=workflow_id,
                creator_id=creator,
                creator_name=file_metadata.get("artist", creator),
                classification=classification,
                department=department,
                project=project,
            )
            manifest.assertions.append(workflow_assertion)

        return manifest

    def _add_core_assertions(
        self,
        manifest: Manifest,
        file_path: str,
        creator: str,
        action: ActionType,
        software_agent: Optional[str],
        digital_source_type: Optional[DigitalSourceType],
        file_metadata: Dict[str, Any],
    ) -> None:
        """Add core C2PA assertions to manifest."""
        # Actions assertion
        actions_assertion = self.assertion_builder.build_actions_assertion(
            action=action,
            software_agent=software_agent,
            digital_source_type=digital_source_type,
        )
        manifest.assertions.append(actions_assertion)

        # Hash assertion
        hash_value = self._compute_file_hash(file_path)
        hash_assertion = self.assertion_builder.build_hash_assertion(
            hash_algorithm=HashAlgorithm.SHA256, hash_value=hash_value
        )
        manifest.assertions.append(hash_assertion)

        # CreativeWork assertion with author info
        from src.core.models import OrganizationInfo

        org_info = None
        if file_metadata or self.organization:
            org_info = OrganizationInfo()

        creative_work_assertion = self.assertion_builder.build_creative_work_assertion(
            author_name=file_metadata.get("artist", creator),
            author_email=creator if "@" in creator else None,
            author_credential=creator if "@" not in creator else None,
            title=manifest.title,
            date_published=datetime.utcnow(),
            organization_info=org_info,
        )
        manifest.assertions.append(creative_work_assertion)

    def _compute_file_hash(
        self, file_path: str, algorithm: HashAlgorithm = HashAlgorithm.SHA256
    ) -> str:
        """Compute hash of file content."""
        hash_func = hashlib.new(algorithm.value)

        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def add_assertion(self, manifest: Manifest, assertion: Assertion) -> None:
        """
        Add a custom assertion to manifest.

        Args:
            manifest: Target manifest
            assertion: Assertion to add
        """
        manifest.assertions.append(assertion)
        manifest.updated_at = datetime.utcnow()

    def add_ingredient(
        self, manifest: Manifest, ingredient_path: str, relationship: str = "parentOf"
    ) -> None:
        """
        Add an ingredient assertion for composite content.

        Args:
            manifest: Target manifest
            ingredient_path: Path to ingredient asset
            relationship: Relationship type
        """
        ingredient_assertion = self.assertion_builder.build_ingredient_assertion(
            ingredient_path=ingredient_path, relationship=relationship
        )
        manifest.assertions.append(ingredient_assertion)
        manifest.updated_at = datetime.utcnow()

    def add_approval(
        self,
        manifest: Manifest,
        approver_id: str,
        approver_name: str,
        role: str,
        status: str,
        comments: Optional[str] = None,
    ) -> None:
        """
        Add approval step to workflow.

        Args:
            manifest: Target manifest
            approver_id: Approver's user ID
            approver_name: Approver's name
            role: Role in approval chain
            status: Approval status
            comments: Optional comments
        """
        # Find workflow assertion
        workflow_assertion = manifest.get_assertion("org.enterprise.workflow")
        if not workflow_assertion:
            raise ValueError("No workflow assertion found in manifest")

        self.assertion_builder.add_approval_to_workflow(
            workflow_assertion=workflow_assertion,
            approver_id=approver_id,
            approver_name=approver_name,
            role=role,
            status=status,
            comments=comments,
        )
        manifest.updated_at = datetime.utcnow()

    def update_compliance(
        self,
        manifest: Manifest,
        pdpa_approved: Optional[bool] = None,
        trademark_cleared: Optional[bool] = None,
        legal_review: Optional[str] = None,
    ) -> None:
        """
        Update compliance checks.

        Args:
            manifest: Target manifest
            pdpa_approved: PDPA compliance
            trademark_cleared: Trademark clearance
            legal_review: Legal review status
        """
        workflow_assertion = manifest.get_assertion("org.enterprise.workflow")
        if not workflow_assertion:
            raise ValueError("No workflow assertion found in manifest")

        self.assertion_builder.update_compliance_check(
            workflow_assertion=workflow_assertion,
            pdpa_approved=pdpa_approved,
            trademark_cleared=trademark_cleared,
            legal_review=legal_review,
        )
        manifest.updated_at = datetime.utcnow()

    def to_json(self, manifest: Manifest, pretty: bool = True) -> str:
        """
        Convert manifest to JSON string.

        Args:
            manifest: Manifest to convert
            pretty: Whether to format JSON

        Returns:
            JSON string representation
        """
        data = manifest.to_dict()
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    def save_manifest(self, manifest: Manifest, output_path: str) -> None:
        """
        Save manifest to JSON file.

        Args:
            manifest: Manifest to save
            output_path: Path to output file
        """
        json_data = self.to_json(manifest)
        with open(output_path, "w") as f:
            f.write(json_data)
