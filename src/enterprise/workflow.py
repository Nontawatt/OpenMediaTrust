"""
Workflow engine for enterprise content approval processes.

Manages multi-stage approval workflows with state transitions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from src.core.models import Manifest


class WorkflowState(str, Enum):
    """Workflow states."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WorkflowAction(str, Enum):
    """Workflow actions."""

    SUBMIT = "submit"
    REVIEW = "review"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    RECALL = "recall"


class WorkflowTransition(BaseModel):
    """Workflow state transition."""

    from_state: WorkflowState
    to_state: WorkflowState
    action: WorkflowAction
    required_role: str


class WorkflowHistory(BaseModel):
    """Workflow history entry."""

    timestamp: datetime
    user_id: str
    user_name: str
    from_state: WorkflowState
    to_state: WorkflowState
    action: WorkflowAction
    comments: Optional[str] = None


class WorkflowInstance(BaseModel):
    """Workflow instance for a manifest."""

    workflow_id: str
    manifest_id: str
    current_state: WorkflowState
    created_by: str
    created_at: datetime
    updated_at: datetime
    history: List[WorkflowHistory]
    metadata: Dict[str, Any] = {}


class WorkflowEngine:
    """Workflow engine for content approval."""

    def __init__(self):
        """Initialize workflow engine."""
        self.workflows: Dict[str, WorkflowInstance] = {}
        self.transitions: List[WorkflowTransition] = []
        self._initialize_transitions()

    def _initialize_transitions(self) -> None:
        """Initialize allowed state transitions."""
        self.transitions = [
            # Draft → Submitted
            WorkflowTransition(
                from_state=WorkflowState.DRAFT,
                to_state=WorkflowState.SUBMITTED,
                action=WorkflowAction.SUBMIT,
                required_role="creator",
            ),
            # Submitted → In Review
            WorkflowTransition(
                from_state=WorkflowState.SUBMITTED,
                to_state=WorkflowState.IN_REVIEW,
                action=WorkflowAction.REVIEW,
                required_role="reviewer",
            ),
            # In Review → Approved
            WorkflowTransition(
                from_state=WorkflowState.IN_REVIEW,
                to_state=WorkflowState.APPROVED,
                action=WorkflowAction.APPROVE,
                required_role="approver",
            ),
            # In Review → Rejected
            WorkflowTransition(
                from_state=WorkflowState.IN_REVIEW,
                to_state=WorkflowState.REJECTED,
                action=WorkflowAction.REJECT,
                required_role="reviewer",
            ),
            # Approved → Published
            WorkflowTransition(
                from_state=WorkflowState.APPROVED,
                to_state=WorkflowState.PUBLISHED,
                action=WorkflowAction.PUBLISH,
                required_role="approver",
            ),
            # Published → Archived
            WorkflowTransition(
                from_state=WorkflowState.PUBLISHED,
                to_state=WorkflowState.ARCHIVED,
                action=WorkflowAction.ARCHIVE,
                required_role="manager",
            ),
            # Rejected → Draft (recall)
            WorkflowTransition(
                from_state=WorkflowState.REJECTED,
                to_state=WorkflowState.DRAFT,
                action=WorkflowAction.RECALL,
                required_role="creator",
            ),
        ]

    def create_workflow(
        self, manifest: Manifest, creator_id: str, creator_name: str
    ) -> WorkflowInstance:
        """
        Create a new workflow instance.

        Args:
            manifest: Manifest to track
            creator_id: Creator user ID
            creator_name: Creator name

        Returns:
            New workflow instance
        """
        workflow = WorkflowInstance(
            workflow_id=manifest.instance_id,
            manifest_id=manifest.instance_id,
            current_state=WorkflowState.DRAFT,
            created_by=creator_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            history=[],
        )

        self.workflows[workflow.workflow_id] = workflow
        return workflow

    def transition(
        self,
        workflow_id: str,
        action: WorkflowAction,
        user_id: str,
        user_name: str,
        user_role: str,
        comments: Optional[str] = None,
    ) -> WorkflowInstance:
        """
        Perform a workflow transition.

        Args:
            workflow_id: Workflow instance ID
            action: Action to perform
            user_id: User performing action
            user_name: User's name
            user_role: User's role
            comments: Optional comments

        Returns:
            Updated workflow instance

        Raises:
            ValueError: If transition is not allowed
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Find valid transition
        valid_transition = None
        for transition in self.transitions:
            if (
                transition.from_state == workflow.current_state
                and transition.action == action
            ):
                valid_transition = transition
                break

        if not valid_transition:
            raise ValueError(
                f"Invalid transition: {action} from state {workflow.current_state}"
            )

        # Check role permission
        if user_role != valid_transition.required_role and user_role != "administrator":
            raise PermissionError(
                f"Role '{user_role}' cannot perform action '{action}'. "
                f"Required role: '{valid_transition.required_role}'"
            )

        # Record history
        history_entry = WorkflowHistory(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_name=user_name,
            from_state=workflow.current_state,
            to_state=valid_transition.to_state,
            action=action,
            comments=comments,
        )
        workflow.history.append(history_entry)

        # Update state
        workflow.current_state = valid_transition.to_state
        workflow.updated_at = datetime.utcnow()

        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """
        Get workflow instance.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow instance or None
        """
        return self.workflows.get(workflow_id)

    def get_available_actions(
        self, workflow_id: str, user_role: str
    ) -> List[WorkflowAction]:
        """
        Get available actions for a workflow based on user role.

        Args:
            workflow_id: Workflow ID
            user_role: User's role

        Returns:
            List of available actions
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return []

        available = []
        for transition in self.transitions:
            if transition.from_state == workflow.current_state:
                if user_role == transition.required_role or user_role == "administrator":
                    available.append(transition.action)

        return available

    def get_workflows_by_state(self, state: WorkflowState) -> List[WorkflowInstance]:
        """
        Get all workflows in a specific state.

        Args:
            state: Workflow state

        Returns:
            List of workflow instances
        """
        return [wf for wf in self.workflows.values() if wf.current_state == state]

    def get_workflows_by_user(self, user_id: str) -> List[WorkflowInstance]:
        """
        Get all workflows created by a user.

        Args:
            user_id: User ID

        Returns:
            List of workflow instances
        """
        return [wf for wf in self.workflows.values() if wf.created_by == user_id]
