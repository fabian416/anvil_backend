"""
Distillation telemetry repository port.

Defines interface for persisting telemetry data.
"""

from typing import Protocol, List, Dict, Any
from datetime import date

from app.domain.services.distillation.telemetry_collector import (
    DistillationTelemetryRecord,
)


class DistillationTelemetryRepository(Protocol):
    """
    Port for distillation telemetry repository.

    Defines interface for storing and querying distillation telemetry.
    """

    async def save(self, record: DistillationTelemetryRecord) -> None:
        """
        Save a single telemetry record.

        Args:
            record: Telemetry record to save
        """
        ...

    async def save_batch(self, records: List[DistillationTelemetryRecord]) -> None:
        """
        Save multiple telemetry records in a batch.

        Args:
            records: List of telemetry records
        """
        ...

    async def get_daily_metrics(
        self,
        start_date: date,
        end_date: date,
        provider: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Get daily aggregated metrics.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            provider: Optional provider filter

        Returns:
            List of daily metrics dictionaries
        """
        ...

    async def refresh_materialized_view(self) -> None:
        """Refresh the materialized view for daily metrics."""
        ...
