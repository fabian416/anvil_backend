"""
Conversation export repository adapter implementation.

SQLAlchemy implementation of ExportRepository port for PostgreSQL.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, Text, DateTime

from app.domain.ports.export_repository import ExportRepository
from app.domain.entities.chat.conversation_export import ConversationExport
from app.domain.value_objects.chat.export import (
    ExportFormat,
    ComplianceStandard,
    PIIRedactionConfig,
)
from app.infrastructure.persistence_sqla.base import Base


class ExportRepositoryAdapter(ExportRepository):
    """
    SQLAlchemy adapter for conversation exports.

    Implements persistence for export requests and results using PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository adapter.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def save(self, export: ConversationExport) -> ConversationExport:
        """
        Save or update export record.

        Args:
            export: Export entity to save

        Returns:
            Saved export entity
        """
        try:
            stmt = select(ConversationExportModel).where(
                ConversationExportModel.export_id == export.id
            )
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                self._update_model(existing, export)
            else:
                model = self._to_model(export)
                self._session.add(model)

            await self._session.commit()
            return export

        except Exception:
            await self._session.rollback()
            raise

    async def get_by_id(self, export_id: UUID) -> Optional[ConversationExport]:
        """
        Get export by ID.

        Args:
            export_id: Export identifier

        Returns:
            ConversationExport or None if not found
        """
        stmt = select(ConversationExportModel).where(
            ConversationExportModel.export_id == export_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_domain(model)

    async def get_by_conversation(
        self, conversation_id: UUID
    ) -> List[ConversationExport]:
        """
        Get all exports for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of exports for the conversation
        """
        stmt = (
            select(ConversationExportModel)
            .where(ConversationExportModel.conversation_id == conversation_id)
            .order_by(ConversationExportModel.requested_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_by_user(
        self, user_id: UUID, limit: int = 50
    ) -> List[ConversationExport]:
        """
        Get exports created by user.

        Args:
            user_id: User identifier
            limit: Maximum number of exports to return

        Returns:
            List of user's exports (most recent first)
        """
        stmt = (
            select(ConversationExportModel)
            .where(ConversationExportModel.user_id == user_id)
            .order_by(ConversationExportModel.requested_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_pending_exports(self, limit: int = 100) -> List[ConversationExport]:
        """
        Get pending exports for processing.

        Args:
            limit: Maximum number of exports to return

        Returns:
            List of pending exports (oldest first)
        """
        stmt = (
            select(ConversationExportModel)
            .where(ConversationExportModel.status == "pending")
            .order_by(ConversationExportModel.requested_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_expired_exports(self, limit: int = 100) -> List[ConversationExport]:
        """
        Get completed exports that have expired.

        Args:
            limit: Maximum number of exports to return

        Returns:
            List of expired exports
        """
        stmt = (
            select(ConversationExportModel)
            .where(
                and_(
                    ConversationExportModel.status == "completed",
                    ConversationExportModel.expires_at < datetime.utcnow(),
                )
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def delete(self, export_id: UUID) -> bool:
        """
        Delete export record.

        Args:
            export_id: Export identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = select(ConversationExportModel).where(
                ConversationExportModel.export_id == export_id
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

    async def delete_expired(self) -> int:
        """
        Delete all expired export records.

        Returns:
            Number of exports deleted
        """
        try:
            stmt = select(ConversationExportModel).where(
                and_(
                    ConversationExportModel.status == "completed",
                    ConversationExportModel.expires_at < datetime.utcnow(),
                )
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            count = len(models)
            for model in models:
                await self._session.delete(model)

            await self._session.commit()
            return count

        except Exception:
            await self._session.rollback()
            return 0

    # =========================================================================
    # CONVERSION METHODS
    # =========================================================================

    def _to_domain(self, model: "ConversationExportModel") -> ConversationExport:
        """
        Convert database model to domain entity.

        Args:
            model: Database model

        Returns:
            ConversationExport domain entity
        """
        # Parse PII redaction config if present
        pii_config = None
        if model.redact_pii:
            pii_config = PIIRedactionConfig()  # Uses default config

        return ConversationExport(
            id=model.export_id,
            conversation_id=model.conversation_id,
            user_id=model.user_id,
            format=ExportFormat(model.format),
            status=model.status,
            include_metadata=model.include_metadata,
            include_timestamps=model.include_timestamps,
            include_agent_names=model.include_agent_names,
            redact_pii=model.redact_pii,
            pii_redaction_config=pii_config,
            compliance_standard=(
                ComplianceStandard(model.compliance_standard)
                if model.compliance_standard
                else None
            ),
            file_path=model.file_path,
            file_size_bytes=model.file_size_bytes,
            download_url=model.download_url,
            expires_at=model.expires_at,
            error_message=model.error_message,
            requested_at=model.requested_at,
            completed_at=model.completed_at,
        )

    def _to_model(self, export: ConversationExport) -> "ConversationExportModel":
        """
        Convert domain entity to database model.

        Args:
            export: Domain entity

        Returns:
            Database model
        """
        return ConversationExportModel(
            export_id=export.id,
            conversation_id=export.conversation_id,
            user_id=export.user_id,
            format=export.format.value,
            status=export.status,
            include_metadata=export.include_metadata,
            include_timestamps=export.include_timestamps,
            include_agent_names=export.include_agent_names,
            redact_pii=export.redact_pii,
            compliance_standard=(
                export.compliance_standard.value if export.compliance_standard else None
            ),
            file_path=export.file_path,
            file_size_bytes=export.file_size_bytes,
            download_url=export.download_url,
            expires_at=export.expires_at,
            error_message=export.error_message,
            requested_at=export.requested_at,
            completed_at=export.completed_at,
        )

    def _update_model(
        self,
        model: "ConversationExportModel",
        export: ConversationExport,
    ) -> None:
        """
        Update database model from domain entity.

        Args:
            model: Database model to update
            export: Domain entity
        """
        model.status = export.status
        model.file_path = export.file_path
        model.file_size_bytes = export.file_size_bytes
        model.download_url = export.download_url
        model.expires_at = export.expires_at
        model.error_message = export.error_message
        model.completed_at = export.completed_at


# =============================================================================
# DATABASE MODEL
# =============================================================================


class ConversationExportModel(Base):
    """
    SQLAlchemy model for conversation exports.

    Maps to 'conversation_exports' table in PostgreSQL.
    """

    __tablename__ = "conversation_exports"

    export_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    conversation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    format: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Configuration
    include_metadata: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    include_timestamps: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    include_agent_names: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    redact_pii: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    compliance_standard: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Output
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    download_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
