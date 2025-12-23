"""
Wallet Query Model.

Read-optimized model for wallet listing with owner information.
"""

from datetime import datetime
from typing import TypedDict

from app.domain.enums.chain_type import ChainType
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.wallet_status import WalletStatus


class WalletOwnerInfo(TypedDict):
    """Owner information embedded in wallet query result."""

    user_id: int
    email: str
    first_name: str
    last_name: str


class WalletQueryModel(TypedDict):
    """
    Query model for wallet listing.

    Includes wallet details and owner information for admin views.
    """

    id: int
    address: str
    privy_wallet_id: str | None
    provider: WalletProvider
    default_chain: ChainType
    status: WalletStatus
    created_at: datetime
    updated_at: datetime
    # Owner info
    owner: WalletOwnerInfo
    # Privy configuration
    policy_ids: list[str]
    owner_type: str | None
    owner_id: str | None
    exported_at: datetime | None
    imported_at: datetime | None
    last_privy_sync_at: datetime | None
