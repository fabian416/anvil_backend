"""
Chat domain ports.

Contains interfaces for chat-related operations following hexagonal architecture.
"""

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)

__all__ = [
    "IntentDetectionPort",
    "IntentDetectionRequest",
    "IntentDetectionResult",
]
