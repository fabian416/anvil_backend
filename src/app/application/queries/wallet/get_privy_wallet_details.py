"""
Get Privy Wallet Details Query

Retrieves detailed wallet information for admin management, combining
local database data with live Privy API data.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.services.authorization.authorize import authorize
from app.application.common.services.authorization.permissions import (
    CanManageRole,
    RoleManagementContext,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.wallet import AdditionalSigner
from app.domain.enums.user_role import UserRole
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.infrastructure.privy.client import (
    PrivyClient,
    PrivyClientError,
    PrivyWalletNotFoundError,
)

logger = logging.getLogger(__name__)


class WalletNotFoundError(Exception):
    """Wallet not found in database or Privy."""

    pass


class WalletQueryError(Exception):
    """Error querying wallet details."""

    pass


@dataclass(frozen=True, slots=True)
class GetPrivyWalletDetailsRequest:
    """Request to get wallet details."""

    privy_wallet_id: str


@dataclass
class AdditionalSignerDTO:
    """Additional signer information."""

    signer_id: str
    override_policy_ids: list[str] | None = None


@dataclass
class AdminWalletDetailsDTO:
    """
    Admin-facing wallet details DTO.

    Combines local database data with live Privy API data.
    """

    # Identification
    local_wallet_id: int | None
    privy_wallet_id: str
    address: str
    chain_type: str

    # User association
    user_id: int | None
    owner_type: str | None
    owner_id: str | None

    # Privy configuration (editable via admin)
    policy_ids: list[str] = field(default_factory=list)
    additional_signers: list[AdditionalSignerDTO] = field(default_factory=list)

    # Status
    provider: str = "privy"
    status: str = "active"
    is_recoverable: bool = True

    # Timestamps
    created_at: datetime | None = None
    exported_at: datetime | None = None
    imported_at: datetime | None = None
    last_privy_sync_at: datetime | None = None

    # Raw data for debugging
    privy_raw_data: dict[str, Any] = field(default_factory=dict)


class GetPrivyWalletDetails:
    """
    Query service to get detailed wallet information for admin.

    This query:
    1. Validates admin permissions
    2. Fetches local wallet data from database
    3. Fetches live wallet data from Privy API
    4. Merges data and updates local cache
    5. Returns combined admin-facing DTO
    """

    __slots__ = (
        "_current_user_service",
        "_privy_client",
        "_wallet_repository",
    )

    def __init__(
        self,
        current_user_service: CurrentUserService,
        wallet_repository: WalletRepository,
        privy_client: PrivyClient,
    ) -> None:
        self._current_user_service = current_user_service
        self._wallet_repository = wallet_repository
        self._privy_client = privy_client

    async def execute(
        self,
        request: GetPrivyWalletDetailsRequest,
    ) -> AdminWalletDetailsDTO:
        """
        Get detailed wallet information for admin management.

        Args:
            request: Request containing the Privy wallet ID.

        Returns:
            AdminWalletDetailsDTO with combined local and Privy data.

        Raises:
            AuthorizationError: If user is not an admin.
            WalletNotFoundError: If wallet doesn't exist.
            WalletQueryError: If there's an error fetching wallet data.
        """
        logger.info(f"GetPrivyWalletDetails: started for {request.privy_wallet_id}")

        # Step 1: Validate admin permissions
        current_user = await self._current_user_service.get_current_user()
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=UserRole.USER,
            ),
        )

        try:
            # Step 2: Fetch local wallet data
            local_wallet = await self._wallet_repository.get_by_privy_wallet_id(
                request.privy_wallet_id
            )

            # Step 3: Fetch live Privy wallet data
            try:
                privy_wallet = await self._privy_client.get_wallet(
                    request.privy_wallet_id
                )
            except PrivyWalletNotFoundError as e:
                if local_wallet is None:
                    msg = f"Wallet {request.privy_wallet_id} not found"
                    raise WalletNotFoundError(msg) from e
                # Wallet exists locally but not in Privy - return local data only
                logger.warning(
                    f"Wallet {request.privy_wallet_id} exists locally but not in Privy"
                )
                privy_wallet = None

            # Step 4: Build the DTO
            metadata = privy_wallet.metadata if privy_wallet else {}

            # Parse additional signers from Privy metadata
            additional_signers: list[AdditionalSignerDTO] = []
            privy_signers = metadata.get("additional_signers", [])
            if isinstance(privy_signers, list):
                for signer_data in privy_signers:
                    if isinstance(signer_data, dict):
                        additional_signers.append(
                            AdditionalSignerDTO(
                                signer_id=signer_data.get("signer_id", ""),
                                override_policy_ids=signer_data.get(
                                    "override_policy_ids"
                                ),
                            )
                        )

            dto = AdminWalletDetailsDTO(
                # Identification
                local_wallet_id=local_wallet.id_.value if local_wallet else None,
                privy_wallet_id=request.privy_wallet_id,
                address=privy_wallet.address
                if privy_wallet
                else (local_wallet.address if local_wallet else ""),
                chain_type=privy_wallet.chain_type.value
                if privy_wallet
                else (local_wallet.default_chain.value if local_wallet else "ethereum"),
                # User association
                user_id=local_wallet.user_id.value if local_wallet else None,
                owner_type=metadata.get("owner_type")
                or (local_wallet.owner_type if local_wallet else None),
                owner_id=metadata.get("owner_id")
                or (local_wallet.owner_id if local_wallet else None),
                # Privy configuration
                policy_ids=metadata.get("policy_ids", [])
                or (local_wallet.policy_ids if local_wallet else []),
                additional_signers=additional_signers,
                # Status
                provider=local_wallet.provider.value if local_wallet else "privy",
                status=local_wallet.status.name.lower() if local_wallet else "active",
                is_recoverable=privy_wallet.is_recoverable if privy_wallet else True,
                # Timestamps
                created_at=privy_wallet.created_at
                if privy_wallet
                else (local_wallet.created_at.value if local_wallet else None),
                exported_at=metadata.get("exported_at")
                or (local_wallet.exported_at if local_wallet else None),
                imported_at=metadata.get("imported_at")
                or (local_wallet.imported_at if local_wallet else None),
                last_privy_sync_at=datetime.now(UTC),
                # Raw data
                privy_raw_data=metadata.get("raw", {}),
            )

            # Step 5: Update local cache if we have both local and Privy data
            if local_wallet and privy_wallet:
                # Update local wallet with Privy data
                local_wallet.policy_ids = metadata.get("policy_ids", [])
                local_wallet.owner_type = metadata.get("owner_type")
                local_wallet.owner_id = metadata.get("owner_id")
                local_wallet.additional_signers = [
                    AdditionalSigner(
                        signer_id=s.get("signer_id", ""),
                        override_policy_ids=s.get("override_policy_ids"),
                    )
                    for s in metadata.get("additional_signers", [])
                    if isinstance(s, dict)
                ]
                local_wallet.exported_at = metadata.get("exported_at")
                local_wallet.imported_at = metadata.get("imported_at")
                local_wallet.last_privy_sync_at = datetime.now(UTC)

                await self._wallet_repository.update(local_wallet)

            logger.info(
                f"GetPrivyWalletDetails: completed for {request.privy_wallet_id}"
            )
            return dto

        except PrivyClientError as e:
            logger.error(f"Privy API error: {e}")
            raise WalletQueryError(f"Failed to fetch wallet from Privy: {e}") from e
        except Exception as e:
            if isinstance(
                e, (AuthorizationError, WalletNotFoundError, WalletQueryError)
            ):
                raise
            logger.error(f"Unexpected error in GetPrivyWalletDetails: {e}")
            raise WalletQueryError(f"Failed to get wallet details: {e}") from e
