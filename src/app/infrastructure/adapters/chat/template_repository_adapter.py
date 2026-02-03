"""
Template repository adapter implementation.

SQLAlchemy implementation of TemplateRepository port for PostgreSQL.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_

from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, Float, Text, DateTime

from app.domain.chat.ports.template_repository import TemplateRepository
from app.domain.entities.chat.conversation_template import (
    ConversationTemplate,
    AgentStep,
    InputSpec,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.infrastructure.adapters.types import MainAsyncSession


class TemplateRepositoryAdapter(TemplateRepository):
    """
    SQLAlchemy adapter for conversation templates.

    Implements persistence for conversation templates using PostgreSQL.
    Stores complex structures (agent sequences, inputs) as JSONB.
    """

    def __init__(self, session: MainAsyncSession) -> None:
        """
        Initialize repository adapter.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_by_id(self, template_id: UUID) -> Optional[ConversationTemplate]:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            ConversationTemplate or None if not found
        """
        stmt = select(ConversationTemplateModel).where(
            ConversationTemplateModel.template_id == template_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_domain(model)

    async def get_by_name(self, name: str) -> Optional[ConversationTemplate]:
        """
        Get template by name.

        Args:
            name: Template name

        Returns:
            ConversationTemplate or None if not found
        """
        stmt = select(ConversationTemplateModel).where(
            ConversationTemplateModel.name == name
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_domain(model)

    async def get_available_for_user(
        self,
        user_id: UUID,
        category: Optional[str] = None,
    ) -> List[ConversationTemplate]:
        """
        Get templates available for user (public + user's private).

        Args:
            user_id: User identifier
            category: Optional category filter

        Returns:
            List of available templates
        """
        # Templates are available if they're public or created by the user
        conditions = [
            ConversationTemplateModel.is_active == True,
            or_(
                ConversationTemplateModel.is_system == True,
                ConversationTemplateModel.created_by_user_id == user_id,
            ),
        ]

        if category:
            conditions.append(ConversationTemplateModel.category == category)

        stmt = select(ConversationTemplateModel).where(and_(*conditions))
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_by_creator(self, user_id: UUID) -> List[ConversationTemplate]:
        """
        Get templates created by user.

        Args:
            user_id: User identifier

        Returns:
            List of user's templates
        """
        stmt = select(ConversationTemplateModel).where(
            ConversationTemplateModel.created_by_user_id == user_id
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def save(self, template: ConversationTemplate) -> ConversationTemplate:
        """
        Save or update template.

        Args:
            template: Template to save

        Returns:
            Saved template
        """
        try:
            # Check if template exists
            stmt = select(ConversationTemplateModel).where(
                ConversationTemplateModel.template_id == template.id
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                self._update_model(existing, template)
            else:
                # Create new
                model = self._to_model(template)
                self._session.add(model)

            await self._session.commit()
            await self._session.refresh(existing if existing else model)

            return template

        except Exception as e:
            await self._session.rollback()
            raise

    async def delete(self, template_id: UUID) -> bool:
        """
        Delete template.

        Args:
            template_id: Template identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(ConversationTemplateModel).where(
                ConversationTemplateModel.template_id == template_id
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                await self._session.delete(model)
                await self._session.commit()
                return True

            return False

        except Exception:
            await self._session.rollback()
            return False

    async def get_popular_templates(
        self, limit: int = 10
    ) -> List[ConversationTemplate]:
        """
        Get most popular templates by usage count.

        Args:
            limit: Maximum number of templates to return

        Returns:
            List of popular templates
        """
        stmt = (
            select(ConversationTemplateModel)
            .where(
                and_(
                    ConversationTemplateModel.is_active == True,
                    ConversationTemplateModel.is_system
                    == True,  # Only public templates
                )
            )
            .order_by(ConversationTemplateModel.usage_count.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    # =========================================================================
    # CONVERSION METHODS
    # =========================================================================

    def _to_domain(self, model: "ConversationTemplateModel") -> ConversationTemplate:
        """
        Convert database model to domain entity.

        Args:
            model: Database model

        Returns:
            ConversationTemplate domain entity
        """
        # Parse agent sequence from JSONB
        agent_sequence = []
        if model.steps and "agent_sequence" in model.steps:
            for step_dict in model.steps["agent_sequence"]:
                agent_sequence.append(
                    AgentStep(
                        agent_name=step_dict["agent_name"],
                        prompt_template=step_dict["prompt_template"],
                        depends_on=step_dict.get("depends_on", []),
                        parallel_execution=step_dict.get("parallel_execution", False),
                        timeout_seconds=step_dict.get("timeout_seconds", 30),
                        outputs=step_dict.get("outputs", []),
                    )
                )

        # Parse required inputs from JSONB
        required_inputs = {}
        if model.steps and "required_inputs" in model.steps:
            for key, spec_dict in model.steps["required_inputs"].items():
                required_inputs[key] = InputSpec(
                    type=spec_dict["type"],
                    required=spec_dict["required"],
                    description=spec_dict["description"],
                    default=spec_dict.get("default"),
                    validation_pattern=spec_dict.get("validation_pattern"),
                )

        # Convert estimated duration from minutes to seconds
        estimated_duration_seconds = (
            model.estimated_duration_minutes * 60
            if model.estimated_duration_minutes
            else 0
        )

        return ConversationTemplate(
            id=model.template_id,
            name=model.name,
            description=model.description,
            category=model.category,
            agent_sequence=agent_sequence,
            required_inputs=required_inputs,
            estimated_duration_seconds=estimated_duration_seconds,
            created_by=model.created_by_user_id,
            is_public=model.is_system,
            usage_count=model.usage_count,
            avg_success_rate=model.avg_completion_rate,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, template: ConversationTemplate) -> "ConversationTemplateModel":
        """
        Convert domain entity to database model.

        Args:
            template: Domain entity

        Returns:
            Database model
        """
        # Serialize agent sequence and required inputs
        steps_data = {
            "agent_sequence": [step.to_dict() for step in template.agent_sequence],
            "required_inputs": {
                key: spec.to_dict() for key, spec in template.required_inputs.items()
            },
        }

        # Convert estimated duration from seconds to minutes
        estimated_duration_minutes = template.estimated_duration_seconds // 60

        return ConversationTemplateModel(
            template_id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            is_system=template.is_public,
            is_active=True,
            created_by_user_id=template.created_by,
            steps=steps_data,
            tags=[],  # Can be enhanced later
            estimated_duration_minutes=estimated_duration_minutes,
            difficulty_level=None,  # Can be calculated based on steps
            usage_count=template.usage_count,
            avg_completion_rate=template.avg_success_rate,
            avg_user_rating=None,  # Not tracked in entity yet
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    def _update_model(
        self,
        model: "ConversationTemplateModel",
        template: ConversationTemplate,
    ) -> None:
        """
        Update database model from domain entity.

        Args:
            model: Database model to update
            template: Domain entity
        """
        # Serialize agent sequence and required inputs
        steps_data = {
            "agent_sequence": [step.to_dict() for step in template.agent_sequence],
            "required_inputs": {
                key: spec.to_dict() for key, spec in template.required_inputs.items()
            },
        }

        estimated_duration_minutes = template.estimated_duration_seconds // 60

        model.name = template.name
        model.description = template.description
        model.category = template.category
        model.is_system = template.is_public
        model.steps = steps_data
        model.estimated_duration_minutes = estimated_duration_minutes
        model.usage_count = template.usage_count
        model.avg_completion_rate = template.avg_success_rate
        model.updated_at = template.updated_at


# =============================================================================
# DATABASE MODEL
# =============================================================================


@mapping_registry.mapped
class ConversationTemplateModel:
    """
    SQLAlchemy model for conversation templates.

    Maps to 'conversation_templates' table in PostgreSQL.
    """

    __tablename__ = "conversation_templates"

    template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )

    # Steps stored as JSONB (contains agent_sequence and required_inputs)
    steps: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Metadata
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    difficulty_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Usage stats
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_completion_rate: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    avg_user_rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
