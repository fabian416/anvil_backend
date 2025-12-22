"""
Template execution repository adapter implementation.

SQLAlchemy implementation of TemplateExecutionRepository port for PostgreSQL.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select

from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime

from app.domain.chat.ports.template_execution_repository import TemplateExecutionRepository
from app.domain.entities.chat.template_execution import (
    TemplateExecution,
    StepResult,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.infrastructure.adapters.types import MainAsyncSession


class TemplateExecutionRepositoryAdapter(TemplateExecutionRepository):
    """
    SQLAlchemy adapter for template executions.

    Implements persistence for template execution tracking using PostgreSQL.
    Stores step results as JSONB for flexible data storage.
    """

    def __init__(self, session: MainAsyncSession) -> None:
        """
        Initialize repository adapter.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def save(self, execution: TemplateExecution) -> TemplateExecution:
        """
        Save or update execution record.

        Args:
            execution: Execution entity to save

        Returns:
            Saved execution entity
        """
        try:
            stmt = select(TemplateExecutionModel).where(
                TemplateExecutionModel.execution_id == execution.id
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                self._update_model(existing, execution)
            else:
                model = self._to_model(execution)
                self._session.add(model)

            await self._session.commit()
            return execution

        except Exception:
            await self._session.rollback()
            raise

    async def get_by_id(self, execution_id: UUID) -> Optional[TemplateExecution]:
        """
        Get execution by ID.

        Args:
            execution_id: Execution identifier

        Returns:
            TemplateExecution or None if not found
        """
        stmt = select(TemplateExecutionModel).where(
            TemplateExecutionModel.execution_id == execution_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_domain(model)

    async def get_by_template(self, template_id: UUID) -> List[TemplateExecution]:
        """
        Get all executions for a template.

        Args:
            template_id: Template identifier

        Returns:
            List of executions for the template
        """
        stmt = (
            select(TemplateExecutionModel)
            .where(TemplateExecutionModel.template_id == template_id)
            .order_by(TemplateExecutionModel.started_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_by_conversation(
        self, conversation_id: UUID
    ) -> List[TemplateExecution]:
        """
        Get all executions for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of executions for the conversation
        """
        stmt = (
            select(TemplateExecutionModel)
            .where(TemplateExecutionModel.conversation_id == conversation_id)
            .order_by(TemplateExecutionModel.started_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_by_user(
        self, user_id: UUID, limit: int = 50
    ) -> List[TemplateExecution]:
        """
        Get executions for user.

        Args:
            user_id: User identifier
            limit: Maximum number of executions to return

        Returns:
            List of user's executions (most recent first)
        """
        stmt = (
            select(TemplateExecutionModel)
            .where(TemplateExecutionModel.user_id == user_id)
            .order_by(TemplateExecutionModel.started_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_in_progress(self, limit: int = 100) -> List[TemplateExecution]:
        """
        Get in-progress executions.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of in-progress executions
        """
        stmt = (
            select(TemplateExecutionModel)
            .where(TemplateExecutionModel.status == "in_progress")
            .order_by(TemplateExecutionModel.started_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_paused(self, user_id: UUID) -> List[TemplateExecution]:
        """
        Get paused executions for user.

        Args:
            user_id: User identifier

        Returns:
            List of paused executions
        """
        stmt = (
            select(TemplateExecutionModel)
            .where(
                TemplateExecutionModel.user_id == user_id,
                TemplateExecutionModel.status == "paused",
            )
            .order_by(TemplateExecutionModel.paused_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def delete(self, execution_id: UUID) -> bool:
        """
        Delete execution record.

        Args:
            execution_id: Execution identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(TemplateExecutionModel).where(
                TemplateExecutionModel.execution_id == execution_id
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

    # =========================================================================
    # CONVERSION METHODS
    # =========================================================================

    def _to_domain(self, model: "TemplateExecutionModel") -> TemplateExecution:
        """
        Convert database model to domain entity.

        Args:
            model: Database model

        Returns:
            TemplateExecution domain entity
        """
        # Parse step results from JSONB
        step_results: List[StepResult] = []
        if model.step_results:
            for result_dict in model.step_results:
                step_results.append(
                    StepResult(
                        step_index=result_dict["step_index"],
                        agent_name=result_dict["agent_name"],
                        response=result_dict["response"],
                        execution_time_seconds=result_dict["execution_time_seconds"],
                        success=result_dict["success"],
                        error_message=result_dict.get("error_message"),
                        metadata=result_dict.get("metadata", {}),
                    )
                )

        return TemplateExecution(
            id=model.execution_id,
            template_id=model.template_id,
            conversation_id=model.conversation_id,
            user_id=model.user_id,
            status=model.status,
            current_step_index=model.current_step_index,
            step_results=step_results,
            execution_time_seconds=model.execution_time_seconds,
            completion_rate=model.completion_rate,
            started_at=model.started_at,
            completed_at=model.completed_at,
            paused_at=model.paused_at,
        )

    def _to_model(self, execution: TemplateExecution) -> "TemplateExecutionModel":
        """
        Convert domain entity to database model.

        Args:
            execution: Domain entity

        Returns:
            Database model
        """
        # Serialize step results to JSONB
        step_results_data = [result.to_dict() for result in execution.step_results]

        return TemplateExecutionModel(
            execution_id=execution.id,
            template_id=execution.template_id,
            conversation_id=execution.conversation_id,
            user_id=execution.user_id,
            status=execution.status,
            current_step_index=execution.current_step_index,
            step_results=step_results_data,
            execution_time_seconds=execution.execution_time_seconds,
            completion_rate=execution.completion_rate,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            paused_at=execution.paused_at,
        )

    def _update_model(
        self,
        model: "TemplateExecutionModel",
        execution: TemplateExecution,
    ) -> None:
        """
        Update database model from domain entity.

        Args:
            model: Database model to update
            execution: Domain entity
        """
        # Serialize step results
        step_results_data = [result.to_dict() for result in execution.step_results]

        model.status = execution.status
        model.current_step_index = execution.current_step_index
        model.step_results = step_results_data
        model.execution_time_seconds = execution.execution_time_seconds
        model.completion_rate = execution.completion_rate
        model.completed_at = execution.completed_at
        model.paused_at = execution.paused_at


# =============================================================================
# DATABASE MODEL
# =============================================================================


@mapping_registry.mapped
class TemplateExecutionModel:
    """
    SQLAlchemy model for template executions.

    Maps to 'template_executions' table in PostgreSQL.
    """

    __tablename__ = "template_executions"

    execution_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    current_step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Step results stored as JSONB
    step_results: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Metrics
    execution_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
