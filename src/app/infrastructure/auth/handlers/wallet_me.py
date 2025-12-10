"""
Handler for getting the current user's wallets.

Combines data from:
1. Local database (wallets table with imported wallets)
2. Local database (primary_wallet_address stored in users table)
3. Privy API (all linked wallets for the user)

This provides a unified view of all wallets associated with the user.
"""

import logging
from dataclasses import dataclass

from app.application.common.services.current_user import CurrentUserService
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.ports.wallet.embedded_wallet_provider import (
    EmbeddedWalletProviderPort,
    WalletProviderError,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.domain.value_objects.user_id import UserId

logger = logging.getLogger(__name__)


@dataclass
class WalletResponse:
    """Individual wallet in the response."""

    wallet_id: str
    """Unique identifier (from Privy or generated for local-only wallets)."""

    address: str
    """Blockchain address."""

    chain_type: str
    """Blockchain type (ethereum, solana, etc.)."""

    wallet_type: str
    """Type: embedded, external, or server_controlled."""

    is_primary: bool
    """Whether this is the user's primary wallet."""

    source: str
    """Data source: 'privy', 'local', or 'both'."""

    created_at: str | None = None
    """When the wallet was created."""


@dataclass
class WalletsResponse:
    """Response containing all user wallets."""

    user_id: int
    """Local user ID."""

    privy_user_id: str | None
    """Privy user ID if linked."""

    wallets: list[WalletResponse]
    """List of all wallets."""

    primary_wallet_address: str | None
    """Primary wallet address from local DB."""

    privy_connected: bool
    """Whether we successfully fetched from Privy."""

    message: str | None = None
    """Optional message (e.g., if Privy fetch failed)."""


class GetMyWalletsHandler:
    """
    Handler to get all wallets for the current authenticated user.

    Combines:
    - Local database: Imported wallets stored in wallets table
    - Local database: primary_wallet_address stored when user logs in
    - Privy API: All wallets linked to the user's Privy account

    If Privy fetch fails, we still return the local data.
    Deduplicates wallets by address across all sources.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_provider: EmbeddedWalletProviderPort,
        wallet_repository: WalletRepository,
    ):
        self._current_user_service = current_user_service
        self._wallet_provider = wallet_provider
        self._wallet_repository = wallet_repository

    async def execute(self) -> WalletsResponse:
        """
        Get all wallets for the current user.

        Returns:
            WalletsResponse with wallets from local DB (imported) and Privy.
        """
        # Get current user
        user = await self._current_user_service.get_current_user()

        wallets: list[WalletResponse] = []
        seen_addresses: set[str] = set()
        privy_connected = False
        message: str | None = None

        # Get primary wallet from local database
        primary_address = (
            user.primary_wallet_address.value if user.primary_wallet_address else None
        )
        privy_user_id = user.privy_user_id.value if user.privy_user_id else None
        user_id = UserId(user.id_.value)

        # 1. Try to fetch wallets from Privy first (they take priority)
        if privy_user_id:
            try:
                privy_wallets = await self._wallet_provider.list_user_wallets(
                    privy_user_id
                )
                privy_connected = True

                # Convert Privy wallets to response format
                for pw in privy_wallets:
                    address_lower = pw.address.lower()
                    is_primary = (
                        primary_address is not None
                        and address_lower == primary_address.lower()
                    )

                    wallets.append(
                        WalletResponse(
                            wallet_id=pw.wallet_id,
                            address=pw.address,
                            chain_type=pw.chain_type.value,
                            wallet_type=pw.wallet_type.value,
                            is_primary=is_primary,
                            source="privy",
                            created_at=pw.created_at.isoformat()
                            if pw.created_at
                            else None,
                        )
                    )
                    seen_addresses.add(address_lower)

            except WalletProviderError as e:
                logger.warning(
                    f"Failed to fetch wallets from Privy for user {user.id_.value}: {e}"
                )
                message = f"Could not fetch wallets from Privy: {e!s}"

            except Exception as e:
                logger.error(f"Unexpected error fetching wallets from Privy: {e}")
                message = "Unexpected error fetching wallets from provider"

        # 2. Fetch imported wallets from local database
        try:
            local_imported_wallets = (
                await self._wallet_repository.get_by_user_and_provider(
                    user_id=user_id,
                    provider=WalletProvider.IMPORTED,
                )
            )

            for lw in local_imported_wallets:
                address_lower = lw.address.lower()

                # Skip if already added from Privy (deduplicate)
                if address_lower in seen_addresses:
                    continue

                is_primary = (
                    primary_address is not None
                    and address_lower == primary_address.lower()
                )

                wallets.append(
                    WalletResponse(
                        wallet_id=lw.privy_wallet_id or f"imported_{lw.id_.value}",
                        address=lw.address,
                        chain_type=lw.default_chain.value,
                        wallet_type="imported",
                        is_primary=is_primary,
                        source="local",
                        created_at=lw.created_at.value.isoformat()
                        if lw.created_at
                        else None,
                    )
                )
                seen_addresses.add(address_lower)

        except Exception as e:
            logger.warning(f"Failed to fetch imported wallets from local DB: {e}")
            # Continue - we can still return Privy wallets

        # 3. If we have a primary wallet in local DB but it's not in any list,
        # add it as a local-only wallet
        if primary_address:
            primary_lower = primary_address.lower()
            if primary_lower not in seen_addresses:
                wallets.append(
                    WalletResponse(
                        wallet_id=f"local_{user.id_.value}",
                        address=primary_address,
                        chain_type="ethereum",
                        wallet_type="external",  # Not in Privy/local = external
                        is_primary=True,
                        source="local",
                        created_at=None,
                    )
                )
                seen_addresses.add(primary_lower)

        # Ensure primary wallet is first in the list
        wallets.sort(key=lambda w: (not w.is_primary, w.address))

        return WalletsResponse(
            user_id=user.id_.value,
            privy_user_id=privy_user_id,
            wallets=wallets,
            primary_wallet_address=primary_address,
            privy_connected=privy_connected,
            message=message,
        )


class SyncWalletsHandler:
    """
    Handler to sync wallets from the frontend with the backend.

    The frontend can send the list of connected wallets (from useWallets hook)
    and we persist imported wallets to the database.

    Supports:
    - Legacy format: list of wallet addresses
    - New format: list of wallet dicts with metadata (type, chain, privy_wallet_id)

    Important: Imported wallets are persisted to the local database for later retrieval.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_repository: WalletRepository,
    ):
        self._current_user_service = current_user_service
        self._wallet_repository = wallet_repository

    async def execute(
        self,
        wallet_data: list[dict[str, str | None]],
    ) -> WalletsResponse:
        """
        Sync wallets from frontend.

        For imported wallets, persists them to the local database.
        This ensures imported wallets are available via /wallet/me even after reload.

        Args:
            wallet_data: List of wallet data dicts with keys:
                - address: Wallet address (required)
                - chain_type: Blockchain type (default: ethereum)
                - wallet_type: embedded, external, imported, unknown (default: unknown)
                - privy_wallet_id: Privy wallet ID if available

        Returns:
            WalletsResponse with updated wallet info.
        """
        user = await self._current_user_service.get_current_user()
        user_id = UserId(user.id_.value)

        # Build response with synced wallets
        wallets: list[WalletResponse] = []
        primary_address = (
            user.primary_wallet_address.value if user.primary_wallet_address else None
        )
        imported_count = 0
        persisted_count = 0

        for i, wallet_info in enumerate(wallet_data):
            address = wallet_info.get("address", "")
            if not address:
                continue

            chain_type_str = wallet_info.get("chain_type", "ethereum") or "ethereum"
            wallet_type = wallet_info.get("wallet_type", "unknown") or "unknown"
            privy_wallet_id = wallet_info.get("privy_wallet_id")

            is_primary = (
                primary_address is not None
                and address.lower() == primary_address.lower()
            ) or (primary_address is None and i == 0)

            # Persist imported wallets to database
            if wallet_type == "imported":
                imported_count += 1
                try:
                    await self._wallet_repository.upsert(
                        user_id=user_id,
                        address=address,
                        provider=WalletProvider.IMPORTED,
                        privy_wallet_id=privy_wallet_id,
                        chain_type=chain_type_str,
                    )
                    persisted_count += 1
                    logger.debug(
                        f"Persisted imported wallet {address[:10]}... "
                        f"for user {user.id_.value}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to persist imported wallet {address[:10]}... "
                        f"for user {user.id_.value}: {e}"
                    )
                    # Continue - we can still return the wallet in response

            # Generate wallet_id: use privy_wallet_id if available, otherwise generate
            wallet_id = privy_wallet_id
            if not wallet_id:
                if wallet_type == "imported":
                    wallet_id = f"imported:{address.lower()}"
                else:
                    wallet_id = f"synced_{i}"

            wallets.append(
                WalletResponse(
                    wallet_id=wallet_id,
                    address=address,
                    chain_type=str(chain_type_str),
                    wallet_type=str(wallet_type),
                    is_primary=is_primary,
                    source="frontend",
                    created_at=None,
                )
            )

        # Build message
        message = "Wallets synced from frontend"
        if imported_count > 0:
            message = (
                f"Wallets synced from frontend "
                f"({imported_count} imported, {persisted_count} persisted)"
            )
            logger.info(
                f"User {user.id_.value} synced {len(wallets)} wallets "
                f"({imported_count} imported, {persisted_count} persisted to DB)"
            )

        return WalletsResponse(
            user_id=user.id_.value,
            privy_user_id=user.privy_user_id.value if user.privy_user_id else None,
            wallets=wallets,
            primary_wallet_address=primary_address,
            privy_connected=False,
            message=message,
        )
