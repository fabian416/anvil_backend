"""
Transaction Ports.
Defines interfaces for transaction persistence operations.
"""

from app.domain.ports.transaction.transaction_repository import TransactionRepository

__all__ = ["TransactionRepository"]
