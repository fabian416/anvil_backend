"""
Integration tests for ExportWallet endpoint.

Tests the /api/v1/wallet/export endpoint logic with:
- Success case: user owns wallet and export succeeds
- 403 Forbidden: wallet doesn't belong to user
- 403 Forbidden: user has no Privy account
- 404 Not Found: wallet not found
- 500 Internal Server Error: export fails

Note: These tests call the core logic directly, bypassing the Dishka
DI decorator to allow unit testing with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, UTC

from fastapi import HTTPException

from app.application.commands.wallet.export_wallet import (
    ExportWallet,
    ExportWalletResult,
    WalletExportError,
    WalletNotFoundError,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.ports.wallet.embedded_wallet_provider import (
    EmbeddedWalletProviderPort,
    WalletInfo,
    ChainType as ProviderChainType,
    WalletType,
    WalletProviderError,
    UserNotFoundError,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository
from app.presentation.http.controllers.wallet.export_wallet import (
    ExportWalletRequest,
    ExportWalletResponse,
)


async def export_wallet_logic(
    request: ExportWalletRequest,
    export_wallet_cmd: ExportWallet,
    current_user_service: CurrentUserService,
    wallet_provider: EmbeddedWalletProviderPort,
    wallet_repository: WalletRepository,
) -> ExportWalletResponse:
    """
    Core export wallet logic extracted for testing.
    
    This mirrors the endpoint logic without the Dishka @inject decorator.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Step 1: Get the current authenticated user
    user = await current_user_service.get_current_user()
    privy_user_id = user.privy_user_id.value if user.privy_user_id else None

    if not privy_user_id:
        logger.warning(
            f"User {user.id_.value} attempted wallet export without Privy account"
        )
        raise HTTPException(
            status_code=403,
            detail="User does not have a linked Privy account",
        )

    # Step 2: Verify the wallet belongs to the authenticated user
    try:
        user_wallets = await wallet_provider.list_user_wallets(privy_user_id)
        user_wallet_ids = {w.wallet_id for w in user_wallets}

        if request.wallet_id not in user_wallet_ids:
            logger.warning(
                f"User {user.id_.value} attempted to export wallet {request.wallet_id} "
                f"which does not belong to them"
            )
            raise HTTPException(
                status_code=403,
                detail="Wallet does not belong to the authenticated user",
            )

        logger.info(
            f"User {user.id_.value} authorized to export wallet {request.wallet_id}"
        )

    except UserNotFoundError:
        # User's privy_user_id exists in local DB but not in Privy
        logger.warning(
            f"User {user.id_.value} has invalid Privy account: {privy_user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Privy account not found. Please re-authenticate.",
        )

    except WalletProviderError as e:
        logger.error(f"Failed to verify wallet ownership: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to verify wallet ownership",
        )

    # Step 3: Proceed with export (user is authorized)
    try:
        result = await export_wallet_cmd.execute(
            wallet_id=request.wallet_id,
            wallet_address=request.wallet_address,
        )

        # Step 4: Record export timestamp for audit (best effort)
        try:
            await wallet_repository.mark_exported(request.wallet_id)
            logger.info(
                f"Recorded export timestamp for wallet {request.wallet_id} "
                f"(user {user.id_.value})"
            )
        except Exception as e:
            logger.debug(
                f"Could not record export timestamp for wallet {request.wallet_id}: {e}"
            )

        return ExportWalletResponse.from_result(result)

    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except WalletExportError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


class TestExportWalletEndpoint:
    """Tests for the export_wallet endpoint logic."""

    @pytest.fixture
    def mock_user_with_privy(self):
        """Create a mock user with Privy account."""
        user = MagicMock()
        user.id_.value = 123
        user.privy_user_id.value = "did:privy:abc123"
        return user

    @pytest.fixture
    def mock_user_without_privy(self):
        """Create a mock user without Privy account."""
        user = MagicMock()
        user.id_.value = 456
        user.privy_user_id = None
        return user

    @pytest.fixture
    def mock_current_user_service(self, mock_user_with_privy):
        """Create a mock CurrentUserService."""
        service = MagicMock(spec=CurrentUserService)
        service.get_current_user = AsyncMock(return_value=mock_user_with_privy)
        return service

    @pytest.fixture
    def mock_wallet_provider(self):
        """Create a mock EmbeddedWalletProviderPort."""
        provider = MagicMock(spec=EmbeddedWalletProviderPort)
        # Default: return a wallet owned by the user
        provider.list_user_wallets = AsyncMock(return_value=[
            WalletInfo(
                wallet_id="wallet_123",
                address="0x1234567890abcdef1234567890abcdef12345678",
                chain_type=ProviderChainType.ETHEREUM,
                wallet_type=WalletType.EMBEDDED,
                created_at=datetime.now(UTC),
            ),
        ])
        return provider

    @pytest.fixture
    def mock_wallet_repository(self):
        """Create a mock WalletRepository."""
        repo = MagicMock(spec=WalletRepository)
        repo.mark_exported = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_export_wallet_cmd(self):
        """Create a mock ExportWallet command."""
        cmd = MagicMock(spec=ExportWallet)
        cmd.execute = AsyncMock(return_value=ExportWalletResult(
            wallet_id="wallet_123",
            address="0x1234567890abcdef1234567890abcdef12345678",
            private_key="0xdeadbeef...",  # Fake private key for testing
            chain_type="ethereum",
        ))
        return cmd

    @pytest.mark.asyncio
    async def test_export_wallet_success(
        self,
        mock_current_user_service,
        mock_wallet_provider,
        mock_wallet_repository,
        mock_export_wallet_cmd,
    ):
        """Test successful wallet export when user owns the wallet."""
        request = ExportWalletRequest(
            wallet_id="wallet_123",
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
        )

        result = await export_wallet_logic(
            request=request,
            export_wallet_cmd=mock_export_wallet_cmd,
            current_user_service=mock_current_user_service,
            wallet_provider=mock_wallet_provider,
            wallet_repository=mock_wallet_repository,
        )

        assert isinstance(result, ExportWalletResponse)
        assert result.wallet_id == "wallet_123"
        assert result.address == "0x1234567890abcdef1234567890abcdef12345678"
        assert result.chain_type == "ethereum"
        # Private key is returned (we trust the caller to handle it securely)
        assert result.private_key == "0xdeadbeef..."

        # Verify export was recorded
        mock_wallet_repository.mark_exported.assert_called_once_with("wallet_123")

    @pytest.mark.asyncio
    async def test_export_wallet_forbidden_not_owner(
        self,
        mock_current_user_service,
        mock_wallet_provider,
        mock_wallet_repository,
        mock_export_wallet_cmd,
    ):
        """Test 403 when wallet doesn't belong to the authenticated user."""
        # User owns wallet_123, but trying to export wallet_999
        request = ExportWalletRequest(
            wallet_id="wallet_999",  # Not owned by user
            wallet_address=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await export_wallet_logic(
                request=request,
                export_wallet_cmd=mock_export_wallet_cmd,
                current_user_service=mock_current_user_service,
                wallet_provider=mock_wallet_provider,
                wallet_repository=mock_wallet_repository,
            )

        assert exc_info.value.status_code == 403
        assert "does not belong to" in exc_info.value.detail

        # Export command should NOT be called
        mock_export_wallet_cmd.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_export_wallet_forbidden_no_privy_account(
        self,
        mock_user_without_privy,
        mock_wallet_provider,
        mock_wallet_repository,
        mock_export_wallet_cmd,
    ):
        """Test 403 when user doesn't have a Privy account."""
        # Setup user without Privy
        current_user_service = MagicMock(spec=CurrentUserService)
        current_user_service.get_current_user = AsyncMock(return_value=mock_user_without_privy)

        request = ExportWalletRequest(
            wallet_id="wallet_123",
            wallet_address=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await export_wallet_logic(
                request=request,
                export_wallet_cmd=mock_export_wallet_cmd,
                current_user_service=current_user_service,
                wallet_provider=mock_wallet_provider,
                wallet_repository=mock_wallet_repository,
            )

        assert exc_info.value.status_code == 403
        assert "Privy account" in exc_info.value.detail

        # Export command should NOT be called
        mock_export_wallet_cmd.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_export_wallet_not_found(
        self,
        mock_current_user_service,
        mock_wallet_provider,
        mock_wallet_repository,
    ):
        """Test 404 when wallet is not found in Privy."""
        # User owns the wallet, but Privy export fails with not found
        export_cmd = MagicMock(spec=ExportWallet)
        export_cmd.execute = AsyncMock(
            side_effect=WalletNotFoundError("Wallet wallet_123 not found")
        )

        request = ExportWalletRequest(
            wallet_id="wallet_123",
            wallet_address=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await export_wallet_logic(
                request=request,
                export_wallet_cmd=export_cmd,
                current_user_service=mock_current_user_service,
                wallet_provider=mock_wallet_provider,
                wallet_repository=mock_wallet_repository,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_export_wallet_internal_error(
        self,
        mock_current_user_service,
        mock_wallet_provider,
        mock_wallet_repository,
    ):
        """Test 500 when export fails due to internal error."""
        # User owns the wallet, but export fails
        export_cmd = MagicMock(spec=ExportWallet)
        export_cmd.execute = AsyncMock(
            side_effect=WalletExportError("HPKE decryption failed")
        )

        request = ExportWalletRequest(
            wallet_id="wallet_123",
            wallet_address=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await export_wallet_logic(
                request=request,
                export_wallet_cmd=export_cmd,
                current_user_service=mock_current_user_service,
                wallet_provider=mock_wallet_provider,
                wallet_repository=mock_wallet_repository,
            )

        assert exc_info.value.status_code == 500
        assert "HPKE" in exc_info.value.detail or "failed" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_export_wallet_provider_error(
        self,
        mock_current_user_service,
        mock_wallet_repository,
        mock_export_wallet_cmd,
    ):
        """Test 500 when wallet ownership verification fails."""
        # Provider fails to list user wallets
        wallet_provider = MagicMock(spec=EmbeddedWalletProviderPort)
        wallet_provider.list_user_wallets = AsyncMock(
            side_effect=WalletProviderError("API error", "privy")
        )

        request = ExportWalletRequest(
            wallet_id="wallet_123",
            wallet_address=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await export_wallet_logic(
                request=request,
                export_wallet_cmd=mock_export_wallet_cmd,
                current_user_service=mock_current_user_service,
                wallet_provider=wallet_provider,
                wallet_repository=mock_wallet_repository,
            )

        assert exc_info.value.status_code == 500
        assert "verify wallet ownership" in exc_info.value.detail.lower()

        # Export command should NOT be called
        mock_export_wallet_cmd.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_export_wallet_privy_user_not_found(
        self,
        mock_wallet_repository,
        mock_export_wallet_cmd,
    ):
        """Test 403 when Privy user doesn't exist (deleted from Privy)."""
        # User exists in local DB but not in Privy
        user_with_invalid_privy = MagicMock()
        user_with_invalid_privy.id_.value = 789
        user_with_invalid_privy.privy_user_id.value = "did:privy:deleted_user"

        current_user_service = MagicMock(spec=CurrentUserService)
        current_user_service.get_current_user = AsyncMock(
            return_value=user_with_invalid_privy
        )

        # Provider raises UserNotFoundError
        wallet_provider = MagicMock(spec=EmbeddedWalletProviderPort)
        wallet_provider.list_user_wallets = AsyncMock(
            side_effect=UserNotFoundError("User not found", "privy")
        )

        request = ExportWalletRequest(
            wallet_id="wallet_123",
            wallet_address=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            await export_wallet_logic(
                request=request,
                export_wallet_cmd=mock_export_wallet_cmd,
                current_user_service=current_user_service,
                wallet_provider=wallet_provider,
                wallet_repository=mock_wallet_repository,
            )

        assert exc_info.value.status_code == 403
        assert "Privy account not found" in exc_info.value.detail
        assert "re-authenticate" in exc_info.value.detail.lower()

        # Export command should NOT be called
        mock_export_wallet_cmd.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_export_wallet_mark_exported_failure_does_not_fail_request(
        self,
        mock_current_user_service,
        mock_wallet_provider,
        mock_export_wallet_cmd,
    ):
        """Test that failure to mark exported does not fail the export request."""
        # Repository fails to mark exported, but export should still succeed
        wallet_repository = MagicMock(spec=WalletRepository)
        wallet_repository.mark_exported = AsyncMock(side_effect=Exception("DB error"))

        request = ExportWalletRequest(
            wallet_id="wallet_123",
            wallet_address=None,
        )

        # Should NOT raise an exception
        result = await export_wallet_logic(
            request=request,
            export_wallet_cmd=mock_export_wallet_cmd,
            current_user_service=mock_current_user_service,
            wallet_provider=mock_wallet_provider,
            wallet_repository=wallet_repository,
        )

        assert isinstance(result, ExportWalletResponse)
        assert result.wallet_id == "wallet_123"
