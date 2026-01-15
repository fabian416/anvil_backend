"""
Transaction Approval Controls

Implements OWASP LLM08 (Excessive Agency) protection by requiring
human approval for high-risk LLM-initiated actions.

OWASP Reference: OWASP LLM Top 10 - LLM08: Excessive Agency
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
import logging

logger = logging.getLogger(__name__)


class TransactionRisk(str, Enum):
    """Risk levels for LLM-initiated transactions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    """Status of transaction approval"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class TransactionApprovalRequest:
    """Represents a transaction requiring approval"""
    transaction_id: str
    user_id: str
    transaction_type: str
    risk_level: TransactionRisk
    details: Dict[str, Any]
    requested_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class TransactionApprovalService:
    """
    Service for managing transaction approvals.

    Protects against OWASP LLM08 (Excessive Agency) by ensuring
    human oversight for high-risk actions.
    """

    # High-risk transaction types that always require approval
    HIGH_RISK_TYPES = [
        "wallet_transaction",
        "fund_transfer",
        "contract_deployment",
        "token_swap",
        "liquidity_provision",
        "stake_assets",
        "governance_vote",
        "data_export",
        "system_config_change",
        "user_data_deletion"
    ]

    # Transaction patterns that indicate high risk
    RISK_INDICATORS = {
        "large_amount": TransactionRisk.HIGH,  # Large financial amounts
        "irreversible": TransactionRisk.CRITICAL,  # Can't be undone
        "external_call": TransactionRisk.MEDIUM,  # Calls external systems
        "data_modification": TransactionRisk.MEDIUM,  # Modifies user data
        "privileged_action": TransactionRisk.HIGH,  # Requires elevated permissions
    }

    def __init__(
        self,
        approval_timeout_minutes: int = 5,
        require_approval_for_high_risk: bool = True
    ):
        """
        Initialize Transaction Approval Service.

        Args:
            approval_timeout_minutes: Minutes before approval request expires
            require_approval_for_high_risk: Enforce approval for high-risk transactions
        """
        self.approval_timeout = timedelta(minutes=approval_timeout_minutes)
        self.require_approval_for_high_risk = require_approval_for_high_risk
        self.pending_approvals: Dict[str, TransactionApprovalRequest] = {}

    def assess_risk(
        self,
        transaction_type: str,
        details: Dict[str, Any]
    ) -> TransactionRisk:
        """
        Assess the risk level of a transaction.

        Args:
            transaction_type: Type of transaction
            details: Transaction details

        Returns:
            Risk level assessment
        """
        # Start with base risk from transaction type
        if transaction_type in self.HIGH_RISK_TYPES:
            risk = TransactionRisk.HIGH
        else:
            risk = TransactionRisk.LOW

        # Check for risk indicators in details
        if details.get("amount") and float(details.get("amount", 0)) > 1000:
            risk = TransactionRisk.HIGH

        if details.get("irreversible", False):
            risk = TransactionRisk.CRITICAL

        if details.get("affects_multiple_users", False):
            risk = TransactionRisk.HIGH

        if details.get("external_call", False):
            if risk == TransactionRisk.LOW:
                risk = TransactionRisk.MEDIUM

        return risk

    def requires_approval(
        self,
        transaction_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Determine if a transaction requires approval.

        Args:
            transaction_type: Type of transaction
            details: Transaction details

        Returns:
            True if approval is required
        """
        if not self.require_approval_for_high_risk:
            return False

        risk = self.assess_risk(transaction_type, details)

        # Require approval for high and critical risk transactions
        return risk in [TransactionRisk.HIGH, TransactionRisk.CRITICAL]

    def request_approval(
        self,
        transaction_id: str,
        user_id: str,
        transaction_type: str,
        details: Dict[str, Any]
    ) -> TransactionApprovalRequest:
        """
        Create an approval request for a transaction.

        Args:
            transaction_id: Unique transaction identifier
            user_id: User ID initiating the transaction
            transaction_type: Type of transaction
            details: Transaction details

        Returns:
            Approval request object
        """
        risk_level = self.assess_risk(transaction_type, details)
        now = datetime.now(UTC)

        approval_request = TransactionApprovalRequest(
            transaction_id=transaction_id,
            user_id=user_id,
            transaction_type=transaction_type,
            risk_level=risk_level,
            details=details,
            requested_at=now,
            expires_at=now + self.approval_timeout,
            status=ApprovalStatus.PENDING
        )

        self.pending_approvals[transaction_id] = approval_request

        logger.info(
            f"Transaction approval requested: {transaction_id}",
            extra={
                "transaction_id": transaction_id,
                "user_id": user_id,
                "transaction_type": transaction_type,
                "risk_level": risk_level.value,
                "expires_at": approval_request.expires_at.isoformat()
            }
        )

        return approval_request

    def approve_transaction(
        self,
        transaction_id: str,
        approver_id: str
    ) -> bool:
        """
        Approve a pending transaction.

        Args:
            transaction_id: Transaction to approve
            approver_id: User approving the transaction

        Returns:
            True if approved successfully
        """
        request = self.pending_approvals.get(transaction_id)

        if not request:
            logger.warning(f"Approval request not found: {transaction_id}")
            return False

        if request.status != ApprovalStatus.PENDING:
            logger.warning(
                f"Transaction not pending approval: {transaction_id}, status: {request.status}"
            )
            return False

        # Check if expired
        if datetime.now(UTC) > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            logger.warning(f"Approval request expired: {transaction_id}")
            return False

        # Approve
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver_id
        request.approved_at = datetime.now(UTC)

        logger.info(
            f"Transaction approved: {transaction_id}",
            extra={
                "transaction_id": transaction_id,
                "approver_id": approver_id,
                "approved_at": request.approved_at.isoformat()
            }
        )

        return True

    def reject_transaction(
        self,
        transaction_id: str,
        rejector_id: str
    ) -> bool:
        """
        Reject a pending transaction.

        Args:
            transaction_id: Transaction to reject
            rejector_id: User rejecting the transaction

        Returns:
            True if rejected successfully
        """
        request = self.pending_approvals.get(transaction_id)

        if not request:
            return False

        if request.status != ApprovalStatus.PENDING:
            return False

        request.status = ApprovalStatus.REJECTED
        request.approved_by = rejector_id
        request.approved_at = datetime.now(UTC)

        logger.info(
            f"Transaction rejected: {transaction_id}",
            extra={
                "transaction_id": transaction_id,
                "rejector_id": rejector_id
            }
        )

        return True

    def check_approval_status(
        self,
        transaction_id: str
    ) -> Optional[ApprovalStatus]:
        """
        Check the approval status of a transaction.

        Args:
            transaction_id: Transaction to check

        Returns:
            Approval status or None if not found
        """
        request = self.pending_approvals.get(transaction_id)

        if not request:
            return None

        # Check if expired
        if request.status == ApprovalStatus.PENDING and datetime.now(UTC) > request.expires_at:
            request.status = ApprovalStatus.EXPIRED

        return request.status

    def get_pending_approvals(
        self,
        user_id: Optional[str] = None
    ) -> List[TransactionApprovalRequest]:
        """
        Get pending approval requests.

        Args:
            user_id: Optional filter by user ID

        Returns:
            List of pending approval requests
        """
        pending = [
            req for req in self.pending_approvals.values()
            if req.status == ApprovalStatus.PENDING
            and datetime.now(UTC) <= req.expires_at
        ]

        if user_id:
            pending = [req for req in pending if req.user_id == user_id]

        return pending

    def cleanup_expired(self):
        """Remove expired approval requests."""
        now = datetime.now(UTC)
        expired = [
            tid for tid, req in self.pending_approvals.items()
            if req.status == ApprovalStatus.PENDING and now > req.expires_at
        ]

        for tid in expired:
            self.pending_approvals[tid].status = ApprovalStatus.EXPIRED
            logger.debug(f"Marked approval request as expired: {tid}")


# Decorator for protecting functions with approval requirements
def requires_approval(
    transaction_type: str,
    approval_service: TransactionApprovalService,
    extract_details: Callable[[Any], Dict[str, Any]]
):
    """
    Decorator to require approval for a function.

    Usage:
        @requires_approval(
            transaction_type="wallet_transaction",
            approval_service=approval_service,
            extract_details=lambda args: {"amount": args[0]}
        )
        async def transfer_funds(amount: float, recipient: str):
            ...
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract transaction details
            details = extract_details(args)

            # Check if approval required
            if not approval_service.requires_approval(transaction_type, details):
                # Execute directly
                return await func(*args, **kwargs)

            # Generate transaction ID
            import uuid
            transaction_id = str(uuid.uuid4())

            # Request approval
            approval_request = approval_service.request_approval(
                transaction_id=transaction_id,
                user_id=kwargs.get("user_id", "unknown"),
                transaction_type=transaction_type,
                details=details
            )

            # Return approval request to user
            return {
                "status": "approval_required",
                "transaction_id": transaction_id,
                "approval_request": approval_request,
                "message": f"This {transaction_type} requires approval. Please approve the transaction to proceed."
            }

        return wrapper
    return decorator
