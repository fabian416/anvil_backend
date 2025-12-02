from enum import Enum


class ModelStatus(str, Enum):
    """Model status for AI telemetry."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
