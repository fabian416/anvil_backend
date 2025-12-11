"""
Handler for creating Bitcoin wallets via Privy Server API.

Bitcoin wallets in Privy must be created server-side, unlike EVM wallets
which are created automatically. This handler:
1. Gets the authenticated user's Privy ID
2. Calls Privy API to create a Bitcoin SegWit wallet
3. Saves the wallet to the local database
4. Returns the wallet address to the frontend
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.wallet import Wallet, WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.enums.wallet_status import WalletStatus
from app.domain.ports.wallet.embedded_wallet_provider import (
    ChainType as PrivyChainType,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.user_id import UserId
from app.infrastructure.privy.client import PrivyClient

logger = logging.getLogger(__name__)


@dataclass
class CreateBitcoinWalletResult:
    """Result of Bitcoin wallet creation."""

    wallet_id: int
    address: str
    chain: str
    privy_wallet_id: str
    created_at: str


class CreateBitcoinWalletHandler:
    """
    Handler to create a Bitcoin wallet for the current user via Privy.

    Bitcoin wallets must be created server-side using Privy's REST API.
    This handler:
    1. Authenticates the user
    2. Checks if user already has a Bitcoin wallet
    3. Calls Privy API to create a Bitcoin SegWit wallet
    4. Saves the wallet to the database
    5. Returns the wallet info
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        privy_client: PrivyClient,
        wallet_repository: WalletRepository,
    ):
        self._current_user_service = current_user_service
        self._privy_client = privy_client
        self._wallet_repository = wallet_repository

    async def execute(self) -> CreateBitcoinWalletResult:
        """
        Create a Bitcoin wallet for the current user.

        Returns:
            CreateBitcoinWalletResult with the new wallet info.

        Raises:
            ValueError: If user already has a Bitcoin wallet or missing Privy ID.
            PrivyClientError: If Privy API call fails.
        """
        # Get current authenticated user
        user = await self._current_user_service.get_current_user()
        user_id = UserId(user.id_.value)

        logger.info(f"Creating Bitcoin wallet for user {user.id_.value}")

        # Check if user has a Privy ID
        if not user.privy_user_id:
            logger.error(f"User {user.id_.value} has no Privy ID")
            raise ValueError(
                "User does not have a Privy account. "
                "Please link your account first."
            )

        privy_user_id = user.privy_user_id.value

        # Check if user already has a Bitcoin wallet
        existing_wallets = await self._wallet_repository.get_by_user_id(user_id)
        for wallet in existing_wallets:
            if wallet.default_chain in (ChainType.BITCOIN, ChainType.BITCOIN_TESTNET):
                logger.info(
                    f"User {user.id_.value} already has a Bitcoin wallet: "
                    f"{wallet.address}"
                )
                return CreateBitcoinWalletResult(
                    wallet_id=wallet.id_.value,
                    address=wallet.address,
                    chain=wallet.default_chain.value,
                    privy_wallet_id=wallet.privy_wallet_id or "",
                    created_at=wallet.created_at.value.isoformat(),
                )

        # Call Privy API to create Bitcoin wallet
        logger.info(f"Calling Privy API to create Bitcoin wallet for {privy_user_id}")

        try:
            wallet_info = await self._privy_client.create_wallet_for_user(
                user_id=privy_user_id,
                chain_type=PrivyChainType.BITCOIN,
            )
        except Exception as e:
            logger.error(f"Failed to create Bitcoin wallet via Privy: {e}")
            raise ValueError(f"Failed to create Bitcoin wallet: {e}") from e

        logger.info(
            f"Privy created Bitcoin wallet: {wallet_info.address} "
            f"(id: {wallet_info.wallet_id})"
        )

        # Save wallet to database
        now = datetime.now(UTC)
        wallet = Wallet(
            id_=WalletId(0),  # Will be assigned by DB
            user_id=user_id,
            privy_wallet_id=wallet_info.wallet_id,
            address=wallet_info.address.lower(),
            provider=WalletProvider.PRIVY,
            default_chain=ChainType.BITCOIN,  # Use mainnet type, address determines network
            status=WalletStatus.ACTIVE,
            created_at=CreatedAt(now),
            updated_at=UpdatedAt(now),
            policy_ids=[],
            owner_type="user",
            owner_id=privy_user_id,
            additional_signers=[],
            exported_at=None,
            imported_at=None,
            last_privy_sync_at=now,
        )

        saved_wallet = await self._wallet_repository.save(wallet)

        logger.info(
            f"Bitcoin wallet saved to database: id={saved_wallet.id_.value}, "
            f"address={saved_wallet.address}"
        )

        return CreateBitcoinWalletResult(
            wallet_id=saved_wallet.id_.value,
            address=saved_wallet.address,
            chain=saved_wallet.default_chain.value,
            privy_wallet_id=wallet_info.wallet_id,
            created_at=saved_wallet.created_at.value.isoformat(),
        )


class GetBitcoinWalletHandler:
    """
    Handler to get the current user's Bitcoin wallet.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_repository: WalletRepository,
    ):
        self._current_user_service = current_user_service
        self._wallet_repository = wallet_repository

    async def execute(self) -> CreateBitcoinWalletResult | None:
        """
        Get the current user's Bitcoin wallet if it exists.

        Returns:
            CreateBitcoinWalletResult if wallet exists, None otherwise.
        """
        user = await self._current_user_service.get_current_user()
        user_id = UserId(user.id_.value)

        wallets = await self._wallet_repository.get_by_user_id(user_id)

        for wallet in wallets:
            if wallet.default_chain in (ChainType.BITCOIN, ChainType.BITCOIN_TESTNET):
                return CreateBitcoinWalletResult(
                    wallet_id=wallet.id_.value,
                    address=wallet.address,
                    chain=wallet.default_chain.value,
                    privy_wallet_id=wallet.privy_wallet_id or "",
                    created_at=wallet.created_at.value.isoformat(),
                )

        return None
