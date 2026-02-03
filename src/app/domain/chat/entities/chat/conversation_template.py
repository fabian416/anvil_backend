"""
Conversation template entity for workflow automation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, UTC


@dataclass
class AgentStep:
    """Single step in template execution."""

    agent_name: str
    prompt_template: str
    depends_on: List[int] = field(default_factory=list)  # Step indices
    parallel_execution: bool = False
    timeout_seconds: int = 30
    outputs: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "prompt_template": self.prompt_template,
            "depends_on": self.depends_on,
            "parallel_execution": self.parallel_execution,
            "timeout_seconds": self.timeout_seconds,
            "outputs": self.outputs,
        }


@dataclass
class InputSpec:
    """Input specification for template."""

    type: str  # "string", "number", "boolean", "wallet_address"
    required: bool
    description: str
    default: Optional[Any] = None
    validation_pattern: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "default": self.default,
            "validation_pattern": self.validation_pattern,
        }


@dataclass
class ConversationTemplate:
    """
    Reusable conversation workflow with predefined agent sequences.

    Templates enable users to run complex multi-agent workflows
    with a single chat command.
    """

    id: UUID
    name: str
    description: str
    category: str  # "portfolio_review", "compliance_check", "risk_analysis", etc.
    agent_sequence: List[AgentStep]
    required_inputs: Dict[str, InputSpec]
    estimated_duration_seconds: int
    created_by: UUID
    is_public: bool = False
    usage_count: int = 0
    avg_success_rate: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        category: str,
        agent_sequence: List[AgentStep],
        required_inputs: Dict[str, InputSpec],
        estimated_duration_seconds: int,
        created_by: UUID,
        is_public: bool = False,
    ) -> "ConversationTemplate":
        """
        Create new conversation template.

        Args:
            name: Template name
            description: Template description
            category: Category for organization
            agent_sequence: Sequence of agent steps
            required_inputs: Required input specifications
            estimated_duration_seconds: Estimated execution time
            created_by: User who created template
            is_public: Whether template is publicly accessible

        Returns:
            ConversationTemplate instance
        """
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            category=category,
            agent_sequence=agent_sequence,
            required_inputs=required_inputs,
            estimated_duration_seconds=estimated_duration_seconds,
            created_by=created_by,
            is_public=is_public,
        )

    def increment_usage(self, success: bool) -> None:
        """
        Increment usage counter and update success rate.

        Args:
            success: Whether execution was successful
        """
        total_success = self.avg_success_rate * self.usage_count
        self.usage_count += 1

        if success:
            total_success += 1

        self.avg_success_rate = total_success / self.usage_count
        self.updated_at = datetime.now(UTC)

    def get_total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.agent_sequence)

    def get_parallel_steps(self) -> List[int]:
        """Get indices of steps that can run in parallel."""
        return [
            i for i, step in enumerate(self.agent_sequence) if step.parallel_execution
        ]

    def validate_inputs(self, inputs: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate provided inputs against requirements.

        Args:
            inputs: User-provided inputs

        Returns:
            Tuple of (is_valid, error_message)
        """
        for key, spec in self.required_inputs.items():
            if spec.required and key not in inputs:
                return False, f"Missing required input: {key}"

            if key in inputs:
                value = inputs[key]
                # Type validation
                if spec.type == "number" and not isinstance(value, (int, float)):
                    return False, f"Input '{key}' must be a number"
                elif spec.type == "boolean" and not isinstance(value, bool):
                    return False, f"Input '{key}' must be a boolean"
                elif spec.type == "string" and not isinstance(value, str):
                    return False, f"Input '{key}' must be a string"

        return True, None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "agent_sequence": [step.to_dict() for step in self.agent_sequence],
            "required_inputs": {
                key: spec.to_dict() for key, spec in self.required_inputs.items()
            },
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "created_by": str(self.created_by),
            "is_public": self.is_public,
            "usage_count": self.usage_count,
            "avg_success_rate": self.avg_success_rate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
