"""
Audit log repository port.

Domain-defined interface for audit log persistence and compliance reporting.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat.audit_log import AuditLogEntry
from app.domain.enums.audit_event_type import AuditEventType


class AuditLogRepository(ABC):
    """
    Port for audit log persistence.

    Abstracts storage and retrieval of audit log entries for compliance
    and security monitoring. Supports efficient querying for compliance reports.
    """

    @abstractmethod
    async def save(self, entry: AuditLogEntry) -> AuditLogEntry:
        """
        Save audit log entry.

        Args:
            entry: Audit log entry to save

        Returns:
            Saved audit log entry
        """
        pass

    @abstractmethod
    async def save_batch(self, entries: List[AuditLogEntry]) -> List[AuditLogEntry]:
        """
        Save multiple audit log entries in batch.

        Args:
            entries: List of audit log entries to save

        Returns:
            List of saved audit log entries
        """
        pass

    @abstractmethod
    async def get_by_id(self, entry_id: UUID) -> Optional[AuditLogEntry]:
        """
        Get audit log entry by ID.

        Args:
            entry_id: Entry identifier

        Returns:
            AuditLogEntry or None if not found
        """
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of audit log entries (most recent first)
        """
        pass

    @abstractmethod
    async def get_by_event_type(
        self,
        event_type: AuditEventType,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs by event type.

        Args:
            event_type: Event type to filter by
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of audit log entries (most recent first)
        """
        pass

    @abstractmethod
    async def get_by_resource(
        self,
        resource_id: UUID,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs for a specific resource.

        Args:
            resource_id: Resource identifier
            resource_type: Optional resource type filter
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of audit log entries (most recent first)
        """
        pass

    @abstractmethod
    async def get_security_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        outcome: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """
        Get security-related audit logs.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            outcome: Filter by outcome ("success", "failure")

        Returns:
            List of security event entries (most recent first)
        """
        pass

    @abstractmethod
    async def get_data_access_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Get data access audit logs (PII, sensitive data).

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of data access entries (most recent first)
        """
        pass

    @abstractmethod
    async def get_failed_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
    ) -> List[AuditLogEntry]:
        """
        Get failed audit log entries.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            event_type: Optional event type filter

        Returns:
            List of failed entries (most recent first)
        """
        pass

    @abstractmethod
    async def get_by_ip_address(
        self,
        ip_address: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs from a specific IP address.

        Args:
            ip_address: IP address to filter by
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of audit log entries (most recent first)
        """
        pass

    @abstractmethod
    async def count_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count audit log entries for a user.

        Args:
            user_id: User identifier
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            Number of audit log entries
        """
        pass

    @abstractmethod
    async def count_by_event_type(
        self,
        event_type: AuditEventType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count audit log entries by event type.

        Args:
            event_type: Event type to filter by
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            Number of audit log entries
        """
        pass

    @abstractmethod
    async def delete_old_entries(
        self, retention_days: int, exclude_critical: bool = True
    ) -> int:
        """
        Delete audit log entries older than retention period.

        Args:
            retention_days: Number of days to retain
            exclude_critical: If True, preserve security/compliance events

        Returns:
            Number of entries deleted
        """
        pass

    @abstractmethod
    async def get_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: Optional[List[AuditEventType]] = None,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs for compliance reporting.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            event_types: Optional list of event types to include

        Returns:
            List of audit log entries for the period
        """
        pass
