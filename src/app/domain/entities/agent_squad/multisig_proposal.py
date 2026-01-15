"""
Multi-Sig Proposal entity - Treasury management proposals.
"""

from dataclasses import dataclass
from typing import Any
from decimal import Decimal
from datetime import datetime, UTC
import uuid

from app.domain.entities.base import Entity
from app.domain.value_objects.wallet_address import WalletAddress
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class MultiSigProposalId:
    """Multi-Sig Proposal identifier."""
    value: uuid.UUID
    
    def __init__(self, value: uuid.UUID | str):
        if isinstance(value, str):
            value = uuid.UUID(value)
        object.__setattr__(self, 'value', value)
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MultiSigProposalId):
            return False
        return self.value == other.value
    
    def __str__(self) -> str:
        return str(self.value)


class ProposalStatus:
    """Proposal status enum."""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class PolicyCheckResult:
    """Policy check result enum."""
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class Approval:
    """Single approval from a signer."""
    signer: str  # Signer address
    timestamp: datetime
    ip_address: str
    comment: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "signer": self.signer,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "comment": self.comment,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Approval":
        return cls(
            signer=data["signer"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ip_address=data["ip_address"],
            comment=data.get("comment"),
        )


@dataclass(eq=False, kw_only=True)
class MultiSigProposal(Entity[MultiSigProposalId]):
    """
    Multi-sig proposal: treasury management workflow.
    
    Enterprise feature for multi-signature wallet coordination:
    - Gnosis Safe integration
    - Approval workflows (2-of-3, 3-of-5, etc.)
    - Policy enforcement (budget, limits, whitelist)
    - Auto-execution when threshold met
    - Immutable audit trail
    """
    safe_address: WalletAddress  # Gnosis Safe address
    transaction_hash: str | None  # Null until executed
    nonce: int  # Gnosis Safe nonce
    amount_usd: Decimal  # Transaction amount in USD
    destination_address: WalletAddress
    purpose: str  # Transaction purpose/description
    budget_code: str | None  # Budget code (e.g., ENG-2025-Q4-001)
    policy_check_result: str  # "passed" or "failed"
    approval_policy: str  # "2-of-3", "3-of-5", etc.
    approvals: list[Approval]  # List of approvals
    status: str  # "pending", "approved", "executed", "cancelled"
    executed_at: datetime | None
    created_at: CreatedAt
    updated_at: UpdatedAt
    
    @classmethod
    def create(
        cls,
        safe_address: WalletAddress,
        nonce: int,
        amount_usd: Decimal,
        destination_address: WalletAddress,
        purpose: str,
        approval_policy: str,
        policy_check_result: str = PolicyCheckResult.PASSED,
        budget_code: str | None = None,
    ) -> "MultiSigProposal":
        """Create new multi-sig proposal."""
        now = CreatedAt.now()
        return cls(
            id_=MultiSigProposalId(uuid.uuid4()),
            safe_address=safe_address,
            transaction_hash=None,
            nonce=nonce,
            amount_usd=amount_usd,
            destination_address=destination_address,
            purpose=purpose,
            budget_code=budget_code,
            policy_check_result=policy_check_result,
            approval_policy=approval_policy,
            approvals=[],
            status=ProposalStatus.PENDING,
            executed_at=None,
            created_at=now,
            updated_at=UpdatedAt(now.value),
        )
    
    def add_approval(
        self,
        signer: str,
        ip_address: str,
        comment: str | None = None,
    ) -> None:
        """Add approval from a signer."""
        approval = Approval(
            signer=signer,
            timestamp=datetime.now(UTC),
            ip_address=ip_address,
            comment=comment,
        )
        self.approvals.append(approval)
        self.updated_at = UpdatedAt.now()
        
        # Check if threshold met
        if self.is_threshold_met():
            self.status = ProposalStatus.APPROVED
    
    def mark_executed(self, transaction_hash: str) -> None:
        """Mark proposal as executed."""
        self.transaction_hash = transaction_hash
        self.status = ProposalStatus.EXECUTED
        self.executed_at = datetime.now(UTC)
        self.updated_at = UpdatedAt.now()
    
    def cancel(self) -> None:
        """Cancel proposal."""
        self.status = ProposalStatus.CANCELLED
        self.updated_at = UpdatedAt.now()
    
    @property
    def approval_count(self) -> int:
        """Get number of approvals."""
        return len(self.approvals)
    
    @property
    def required_approvals(self) -> int:
        """Get required number of approvals from policy (e.g., 3 from "3-of-5")."""
        # Parse approval_policy (e.g., "3-of-5" -> 3)
        parts = self.approval_policy.split("-of-")
        if len(parts) == 2:
            return int(parts[0])
        return 1
    
    @property
    def total_signers(self) -> int:
        """Get total number of signers from policy (e.g., 5 from "3-of-5")."""
        # Parse approval_policy (e.g., "3-of-5" -> 5)
        parts = self.approval_policy.split("-of-")
        if len(parts) == 2:
            return int(parts[1])
        return 1
    
    def is_threshold_met(self) -> bool:
        """Check if approval threshold is met."""
        return self.approval_count >= self.required_approvals
    
    @property
    def is_pending(self) -> bool:
        """Check if proposal is pending."""
        return self.status == ProposalStatus.PENDING
    
    @property
    def is_approved(self) -> bool:
        """Check if proposal is approved (threshold met)."""
        return self.status == ProposalStatus.APPROVED
    
    @property
    def is_executed(self) -> bool:
        """Check if proposal is executed."""
        return self.status == ProposalStatus.EXECUTED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if proposal is cancelled."""
        return self.status == ProposalStatus.CANCELLED
    
    @property
    def policy_passed(self) -> bool:
        """Check if policy check passed."""
        return self.policy_check_result == PolicyCheckResult.PASSED
    
    def has_signer_approved(self, signer: str) -> bool:
        """Check if specific signer has approved."""
        return any(approval.signer == signer for approval in self.approvals)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id_),
            "safe_address": str(self.safe_address.value),
            "transaction_hash": self.transaction_hash,
            "nonce": self.nonce,
            "amount_usd": float(self.amount_usd),
            "destination_address": str(self.destination_address.value),
            "purpose": self.purpose,
            "budget_code": self.budget_code,
            "policy_check_result": self.policy_check_result,
            "approval_policy": self.approval_policy,
            "approvals": [approval.to_dict() for approval in self.approvals],
            "status": self.status,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.value.isoformat(),
            "updated_at": self.updated_at.value.isoformat(),
        }
