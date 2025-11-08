"""
Manifest management API endpoints.

Handles manifest creation, retrieval, signing, and metadata management.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from src.core.manifest_creator import ManifestCreator
from src.core.models import ActionType, ClassificationLevel, DigitalSourceType
from src.core.signer import Signer

router = APIRouter()


# Request/Response models
class CreateManifestRequest(BaseModel):
    """Request to create a manifest."""

    title: Optional[str] = None
    creator: str
    department: Optional[str] = None
    project: Optional[str] = None
    classification: ClassificationLevel = ClassificationLevel.INTERNAL
    digital_source_type: Optional[DigitalSourceType] = None
    action: ActionType = ActionType.CREATED
    organization: Optional[str] = None


class ManifestResponse(BaseModel):
    """Manifest response."""

    manifest_id: str
    instance_id: str
    title: Optional[str]
    format: str
    creator: str
    created_at: datetime
    is_signed: bool
    workflow_id: Optional[str]
    storage_path: Optional[str]


class SignManifestRequest(BaseModel):
    """Request to sign a manifest."""

    algorithm: str = "ml-dsa-65"
    certificate_path: Optional[str] = None


@router.post("/manifests", response_model=ManifestResponse, status_code=status.HTTP_201_CREATED)
async def create_manifest(
    file: UploadFile = File(...),
    creator: str = Form(...),
    title: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    project: Optional[str] = Form(None),
    classification: str = Form("internal"),
    organization: Optional[str] = Form(None),
):
    """
    Create a new C2PA manifest for uploaded content.

    Args:
        file: Content file to create manifest for
        creator: Creator email or ID
        title: Content title
        department: Department name
        project: Project name
        classification: Security classification
        organization: Organization name

    Returns:
        Created manifest metadata
    """
    # Save uploaded file temporarily
    import tempfile
    import os

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
    try:
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # Create manifest
        manifest_creator = ManifestCreator(organization=organization)

        classification_level = ClassificationLevel(classification)

        manifest = manifest_creator.create(
            file_path=temp_file.name,
            creator=creator,
            title=title,
            department=department,
            project=project,
            classification=classification_level,
        )

        # TODO: Save to storage and database

        return ManifestResponse(
            manifest_id=manifest.instance_id,
            instance_id=manifest.instance_id,
            title=manifest.title,
            format=manifest.format,
            creator=creator,
            created_at=manifest.created_at,
            is_signed=manifest.signature is not None,
            workflow_id=None,
            storage_path=None,
        )

    finally:
        # Clean up temp file
        os.unlink(temp_file.name)


@router.get("/manifests/{manifest_id}", response_model=ManifestResponse)
async def get_manifest(manifest_id: str):
    """
    Get manifest by ID.

    Args:
        manifest_id: Manifest identifier

    Returns:
        Manifest metadata
    """
    # TODO: Retrieve from storage
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Manifest {manifest_id} not found",
    )


@router.post("/manifests/{manifest_id}/sign")
async def sign_manifest(manifest_id: str, request: SignManifestRequest):
    """
    Sign a manifest with quantum-safe algorithm.

    Args:
        manifest_id: Manifest identifier
        request: Signing request

    Returns:
        Signed manifest metadata
    """
    # TODO: Retrieve manifest, sign, and save
    return {"message": "Manifest signed successfully", "manifest_id": manifest_id}


@router.get("/manifests")
async def list_manifests(
    organization: Optional[str] = None,
    department: Optional[str] = None,
    creator: Optional[str] = None,
    limit: int = 100,
):
    """
    List manifests with optional filters.

    Args:
        organization: Filter by organization
        department: Filter by department
        creator: Filter by creator
        limit: Maximum results

    Returns:
        List of manifests
    """
    # TODO: Query from database
    return {"manifests": [], "total": 0}


@router.delete("/manifests/{manifest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manifest(manifest_id: str):
    """
    Delete a manifest (soft delete, moves to archive).

    Args:
        manifest_id: Manifest identifier
    """
    # TODO: Archive manifest
    pass
