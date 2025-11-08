"""
Database storage for manifest metadata and indexing.

Uses SQLAlchemy for database abstraction with PostgreSQL support.
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

from src.core.models import ClassificationLevel
from src.enterprise.workflow import WorkflowState

Base = declarative_base()


class ManifestRecord(Base):
    """Manifest metadata record."""

    __tablename__ = "manifests"

    id = Column(Integer, primary_key=True)
    manifest_id = Column(String(255), unique=True, index=True, nullable=False)
    instance_id = Column(String(255), unique=True, index=True, nullable=False)

    # Content metadata
    title = Column(String(500))
    format = Column(String(100))
    file_path = Column(String(1000))
    file_hash = Column(String(128))

    # Creator info
    creator_id = Column(String(255), index=True)
    creator_name = Column(String(255))

    # Organization
    organization = Column(String(255), index=True)
    tenant_id = Column(String(255), index=True)
    department = Column(String(255), index=True)
    project = Column(String(255), index=True)

    # Classification
    classification = Column(Enum(ClassificationLevel))

    # Workflow
    workflow_id = Column(String(255), index=True)
    workflow_state = Column(Enum(WorkflowState))

    # Signature
    is_signed = Column(Boolean, default=False)
    signature_algorithm = Column(String(50))
    signature_timestamp = Column(DateTime)

    # Storage
    storage_tier = Column(String(20))  # hot, warm, cold
    storage_path = Column(String(1000))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at = Column(DateTime)

    # Metadata JSON
    metadata = Column(JSON)

    # Relationships
    assertions = relationship(
        "AssertionRecord", back_populates="manifest", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="manifest", cascade="all, delete-orphan"
    )


class AssertionRecord(Base):
    """Assertion record for indexing."""

    __tablename__ = "assertions"

    id = Column(Integer, primary_key=True)
    manifest_id = Column(Integer, ForeignKey("manifests.id"), nullable=False)
    assertion_id = Column(String(255))
    label = Column(String(255), index=True, nullable=False)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    manifest = relationship("ManifestRecord", back_populates="assertions")


class AuditLog(Base):
    """Audit log for manifest operations."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    manifest_id = Column(Integer, ForeignKey("manifests.id"), nullable=False)

    # Operation details
    operation = Column(
        String(50), nullable=False
    )  # create, update, sign, verify, approve, etc.
    user_id = Column(String(255), nullable=False, index=True)
    user_name = Column(String(255))
    user_role = Column(String(100))

    # Context
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Details
    details = Column(JSON)
    status = Column(String(20))  # success, failed, error
    error_message = Column(Text)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    manifest = relationship("ManifestRecord", back_populates="audit_logs")


class DatabaseStorage:
    """Database storage manager."""

    def __init__(self, connection_string: str):
        """
        Initialize database storage.

        Args:
            connection_string: SQLAlchemy connection string
        """
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create database tables."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(self.engine)

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def save_manifest(
        self,
        manifest_id: str,
        instance_id: str,
        title: Optional[str] = None,
        format: Optional[str] = None,
        creator_id: Optional[str] = None,
        creator_name: Optional[str] = None,
        organization: Optional[str] = None,
        tenant_id: Optional[str] = None,
        department: Optional[str] = None,
        project: Optional[str] = None,
        classification: Optional[ClassificationLevel] = None,
        workflow_id: Optional[str] = None,
        workflow_state: Optional[WorkflowState] = None,
        storage_path: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ManifestRecord:
        """
        Save manifest metadata to database.

        Args:
            manifest_id: Manifest identifier
            instance_id: Instance identifier
            title: Content title
            format: Content format
            creator_id: Creator user ID
            creator_name: Creator name
            organization: Organization name
            tenant_id: Tenant identifier
            department: Department
            project: Project name
            classification: Classification level
            workflow_id: Workflow ID
            workflow_state: Workflow state
            storage_path: Path in object storage
            metadata: Additional metadata

        Returns:
            Saved manifest record
        """
        session = self.get_session()
        try:
            record = ManifestRecord(
                manifest_id=manifest_id,
                instance_id=instance_id,
                title=title,
                format=format,
                creator_id=creator_id,
                creator_name=creator_name,
                organization=organization,
                tenant_id=tenant_id,
                department=department,
                project=project,
                classification=classification,
                workflow_id=workflow_id,
                workflow_state=workflow_state,
                storage_path=storage_path,
                storage_tier="hot",
                metadata=metadata,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def get_manifest(self, manifest_id: str) -> Optional[ManifestRecord]:
        """Get manifest by ID."""
        session = self.get_session()
        try:
            return (
                session.query(ManifestRecord)
                .filter(ManifestRecord.manifest_id == manifest_id)
                .first()
            )
        finally:
            session.close()

    def search_manifests(
        self,
        organization: Optional[str] = None,
        department: Optional[str] = None,
        creator_id: Optional[str] = None,
        workflow_state: Optional[WorkflowState] = None,
        classification: Optional[ClassificationLevel] = None,
        limit: int = 100,
    ) -> List[ManifestRecord]:
        """Search manifests with filters."""
        session = self.get_session()
        try:
            query = session.query(ManifestRecord)

            if organization:
                query = query.filter(ManifestRecord.organization == organization)
            if department:
                query = query.filter(ManifestRecord.department == department)
            if creator_id:
                query = query.filter(ManifestRecord.creator_id == creator_id)
            if workflow_state:
                query = query.filter(ManifestRecord.workflow_state == workflow_state)
            if classification:
                query = query.filter(ManifestRecord.classification == classification)

            return query.order_by(ManifestRecord.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def add_audit_log(
        self,
        manifest_id: str,
        operation: str,
        user_id: str,
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        status: str = "success",
        details: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Add audit log entry."""
        session = self.get_session()
        try:
            # Get manifest record
            manifest_record = (
                session.query(ManifestRecord)
                .filter(ManifestRecord.manifest_id == manifest_id)
                .first()
            )
            if not manifest_record:
                return

            log = AuditLog(
                manifest_id=manifest_record.id,
                operation=operation,
                user_id=user_id,
                user_name=user_name,
                user_role=user_role,
                status=status,
                details=details,
                error_message=error_message,
            )
            session.add(log)
            session.commit()
        finally:
            session.close()

    def get_audit_logs(
        self, manifest_id: str, limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a manifest."""
        session = self.get_session()
        try:
            manifest_record = (
                session.query(ManifestRecord)
                .filter(ManifestRecord.manifest_id == manifest_id)
                .first()
            )
            if not manifest_record:
                return []

            return (
                session.query(AuditLog)
                .filter(AuditLog.manifest_id == manifest_record.id)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()
