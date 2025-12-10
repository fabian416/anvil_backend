"""
Update Privy Wallet Command

Admin command to update wallet configuration in Privy and sync to local database.
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
from app.application.queries.wallet.get_privy_wallet_details import (
    AdditionalSignerDTO,
    AdminWalletDetailsDTO,
)
from app.domain.entities.wallet import AdditionalSigner
from app.domain.enums.user_role import UserRole
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.infrastructure.privy.client import (
    PrivyClient,
    PrivyClientError,
    PrivyWalletNotFoundError,
)

logger = logging.getLogger(__name__)


class WalletUpdateError(Exception):
    """Error updating wallet configuration."""

    pass


class WalletNotFoundError(Exception):
    """Wallet not found in database or Privy."""

    pass


@dataclass
class UpdatePrivyWalletRequest:
    """
    Request to update wallet configuration.

    All fields are optional - only provided fields will be updated.
    """

    privy_wallet_id: str

    # Editable fields
    policy_ids: list[str] | None = None
    owner: dict[str, Any] | None = None  # e.g., {"user_id": "did:privy:xxx"}
    owner_id: str | None = None  # Alternative to owner object
    additional_signers: list[dict[str, Any]] | None = None


@dataclass
class UpdatePrivyWalletResult:
    """Result of wallet update operation."""

    success: bool
    wallet_details: AdminWalletDetailsDTO
    changes_applied: dict[str, Any] = field(default_factory=dict)


class UpdatePrivyWallet:
    """
    Command service to update wallet configuration in Privy.

    This command:
    1. Validates admin permissions
    2. Calls Privy API to update wallet configuration
    3. Syncs updated configuration to local database
    4. Returns updated wallet details

    Security Note:
    - Only admins can execute this command
    - Changes are audited (logged)
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
        request: UpdatePrivyWalletRequest,
    ) -> UpdatePrivyWalletResult:
        """
        Update wallet configuration in Privy.

        Args:
            request: Request containing the wallet ID and fields to update.

        Returns:
            UpdatePrivyWalletResult with updated wallet details.

        Raises:
            AuthorizationError: If user is not an admin.
            WalletNotFoundError: If wallet doesn't exist.
            WalletUpdateError: If there's an error updating the wallet.
        """
        logger.info(f"UpdatePrivyWallet: started for {request.privy_wallet_id}")

        # Step 1: Validate admin permissions
        current_user = await self._current_user_service.get_current_user()
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=UserRole.USER,
            ),
        )

        # Track changes for audit logging
        changes_applied: dict[str, Any] = {}

        try:
            # Step 2: Call Privy API to update wallet
            updated_privy_wallet = await self._privy_client.update_wallet(
                wallet_id=request.privy_wallet_id,
                policy_ids=request.policy_ids,
                owner=request.owner,
                owner_id=request.owner_id,
                additional_signers=request.additional_signers,
            )

            # Track what was changed
            if request.policy_ids is not None:
                changes_applied["policy_ids"] = request.policy_ids
            if request.owner is not None:
                changes_applied["owner"] = request.owner
            if request.owner_id is not None:
                changes_applied["owner_id"] = request.owner_id
            if request.additional_signers is not None:
                changes_applied["additional_signers"] = request.additional_signers

            # Step 3: Sync updated configuration to local database
            local_wallet = await self._wallet_repository.get_by_privy_wallet_id(
                request.privy_wallet_id
            )

            metadata = updated_privy_wallet.metadata

            if local_wallet:
                # Update local wallet with new Privy data
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
                    f"Updated local wallet record for {request.privy_wallet_id}"
                )

            # Step 4: Build response DTO
            additional_signers_dto: list[AdditionalSignerDTO] = []
            privy_signers = metadata.get("additional_signers", [])
            if isinstance(privy_signers, list):
                for signer_data in privy_signers:
                    if isinstance(signer_data, dict):
                        additional_signers_dto.append(
                            AdditionalSignerDTO(
                                signer_id=signer_data.get("signer_id", ""),
                                override_policy_ids=signer_data.get(
                                    "override_policy_ids"
                                ),
                            )
                        )

            wallet_details = AdminWalletDetailsDTO(
                local_wallet_id=local_wallet.id_.value if local_wallet else None,
                privy_wallet_id=request.privy_wallet_id,
                address=updated_privy_wallet.address,
                chain_type=updated_privy_wallet.chain_type.value,
                user_id=local_wallet.user_id.value if local_wallet else None,
                owner_type=metadata.get("owner_type"),
                owner_id=metadata.get("owner_id"),
                policy_ids=metadata.get("policy_ids", []),
                additional_signers=additional_signers_dto,
                provider=local_wallet.provider.value if local_wallet else "privy",
                status=local_wallet.status.name.lower() if local_wallet else "active",
                is_recoverable=updated_privy_wallet.is_recoverable,
                created_at=updated_privy_wallet.created_at,
                exported_at=metadata.get("exported_at"),
                imported_at=metadata.get("imported_at"),
                last_privy_sync_at=datetime.now(UTC),
                privy_raw_data=metadata.get("raw", {}),
            )

            # Log audit information
            logger.info(
                f"UpdatePrivyWallet: completed for {request.privy_wallet_id} "
                f"by admin user_id={current_user.id_.value}. "
                f"Changes: {changes_applied}"
            )

            return UpdatePrivyWalletResult(
                success=True,
                wallet_details=wallet_details,
                changes_applied=changes_applied,
            )

        except PrivyWalletNotFoundError as e:
            logger.warning(f"Wallet not found: {request.privy_wallet_id}")
            raise WalletNotFoundError(
                f"Wallet {request.privy_wallet_id} not found in Privy"
            ) from e

        except PrivyClientError as e:
            logger.error(f"Privy API error during update: {e}")
            raise WalletUpdateError(f"Failed to update wallet in Privy: {e}") from e

        except Exception as e:
            if isinstance(
                e, (AuthorizationError, WalletNotFoundError, WalletUpdateError)
            ):
                raise
            logger.error(f"Unexpected error in UpdatePrivyWallet: {e}")
            raise WalletUpdateError(f"Failed to update wallet: {e}") from e
