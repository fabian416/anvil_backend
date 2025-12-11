"""
Transfer Status Enum.

Represents the status of a cross-chain transfer.
"""

from enum import Enum


class TransferStatus(Enum):
    """
    Cross-chain transfer status.

    Tracks the lifecycle of an Axelar bridge transfer.
    """

    PENDING = "pending"  # Initiated
    CONFIRMED = "confirmed"  # Source chain confirmed
    EXECUTING = "executing"  # Relaying to destination
    EXECUTED = "executed"  # Successfully completed
    FAILED = "failed"  # Transfer failed
