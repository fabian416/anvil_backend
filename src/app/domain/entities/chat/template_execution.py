"""
Template Execution domain entity.

Enterprise-grade template workflow execution tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from uuid import UUID


@dataclass
class StepResult:
    """Result from executing a template step."""

    step_index: int
    agent_name: str
    response: str
    execution_time_seconds: int
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "step_index": self.step_index,
            "agent_name": self.agent_name,
            "response": self.response,
            "execution_time_seconds": self.execution_time_seconds,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class TemplateExecution:
    """
    Template execution entity.

    Tracks the execution of a multi-step conversation template
    with progress, results, and state management.
    """

    id: UUID
    template_id: UUID
    conversation_id: UUID
    user_id: UUID
    status: str  # "in_progress", "completed", "paused", "failed"

    # Progress tracking
    current_step_index: int = 0
    step_results: List[StepResult] = field(default_factory=list)

    # Metrics
    execution_time_seconds: Optional[int] = None
    completion_rate: float = 0.0  # 0.0 to 1.0

    # Timestamps
    started_at: datetime = None  # type: ignore
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize timestamps."""
        if self.started_at is None:
            self.started_at = datetime.now(UTC)

    def is_in_progress(self) -> bool:
        """Check if execution is in progress."""
        return self.status == "in_progress"

    def is_completed(self) -> bool:
        """Check if execution is completed."""
        return self.status == "completed"

    def is_paused(self) -> bool:
        """Check if execution is paused."""
        return self.status == "paused"

    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == "failed"

    def add_step_result(self, result: StepResult) -> None:
        """
        Add result for a completed step.

        Args:
            result: Step result to add
        """
        self.step_results.append(result)
        self.current_step_index = result.step_index + 1

        # Update completion rate
        # Assumes step_index is 0-based
        total_steps = max(
            result.step_index + 1,
            len(self.step_results),
        )
        self.completion_rate = len(self.step_results) / max(total_steps, 1)

    def pause(self) -> None:
        """Pause execution."""
        if self.status == "in_progress":
            self.status = "paused"
            self.paused_at = datetime.now(UTC)

    def resume(self) -> None:
        """Resume paused execution."""
        if self.status == "paused":
            self.status = "in_progress"
            self.paused_at = None

    def complete(self) -> None:
        """Mark execution as completed."""
        self.status = "completed"
        self.completed_at = datetime.now(UTC)
        self.completion_rate = 1.0

        # Calculate total execution time
        if self.started_at:
            self.execution_time_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )

    def fail(self, error_message: str) -> None:
        """
        Mark execution as failed.

        Args:
            error_message: Error description
        """
        self.status = "failed"
        self.completed_at = datetime.now(UTC)

        # Calculate execution time up to failure
        if self.started_at:
            self.execution_time_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )

        # Add failure as last step result
        self.step_results.append(
            StepResult(
                step_index=self.current_step_index,
                agent_name="system",
                response="",
                execution_time_seconds=0,
                success=False,
                error_message=error_message,
            )
        )

    def get_successful_steps(self) -> List[StepResult]:
        """Get all successful step results."""
        return [result for result in self.step_results if result.success]

    def get_failed_steps(self) -> List[StepResult]:
        """Get all failed step results."""
        return [result for result in self.step_results if not result.success]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "template_id": str(self.template_id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "status": self.status,
            "current_step_index": self.current_step_index,
            "step_results": [result.to_dict() for result in self.step_results],
            "execution_time_seconds": self.execution_time_seconds,
            "completion_rate": self.completion_rate,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
        }
