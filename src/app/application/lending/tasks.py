"""
Lending background tasks for Celery.

These tasks handle periodic monitoring, health checks, and alert generation
for lending positions across Aave and Morpho protocols.
"""

import logging
from datetime import datetime, UTC
from decimal import Decimal
from typing import Protocol, Any
from uuid import UUID

from app.domain.entities.lending.lending_health_check import LendingHealthCheck
from app.domain.entities.lending.lending_alert import LendingAlert

logger = logging.getLogger(__name__)


class Web3Provider(Protocol):
    """Port for Web3 blockchain interactions."""

    async def get_transaction_receipt(
        self, tx_hash: str, chain: str
    ) -> dict[str, Any] | None:
        """Get transaction receipt."""
        ...

    async def wait_for_transaction(
        self, tx_hash: str, chain: str, timeout: int = 120
    ) -> dict[str, Any]:
        """Wait for transaction confirmation."""
        ...


class LendingRepository(Protocol):
    """Port for lending repository operations."""

    async def save_health_check(self, check: LendingHealthCheck) -> None:
        """Save health check snapshot."""
        ...

    async def create_alert(self, alert: LendingAlert) -> None:
        """Create new alert."""
        ...

    async def get_user_preferences(self, user_id: UUID):
        """Get user lending preferences."""
        ...


class PositionProvider(Protocol):
    """Port for fetching positions from protocols."""

    async def get_position(
        self,
        wallet_address: str,
        protocol: str,
        chain: str,
    ):
        """Get user's lending position from protocol."""
        ...


class MonitorHealthFactorsTask:
    """
    Task to monitor all active lending positions and check health factors.

    Runs periodically to:
    1. Fetch all active positions from protocols
    2. Calculate current health factors
    3. Save health check snapshots
    4. Generate alerts for critical positions
    """

    def __init__(
        self,
        position_provider: PositionProvider,
        repository: LendingRepository,
    ):
        self._position_provider = position_provider
        self._repository = repository

    async def run(self) -> dict:
        """
        Monitor all positions and generate health checks.

        Returns:
            Dictionary with stats: {
                "positions_checked": int,
                "alerts_created": int,
                "critical_positions": int,
            }
        """
        logger.info("Starting health factor monitoring task")

        stats = {
            "positions_checked": 0,
            "alerts_created": 0,
            "critical_positions": 0,
        }

        try:
            # Get all active positions (users with lending positions)
            # This would typically query user_lending_preferences for active users
            # For now, we'll need to implement a method to get active users
            # TODO: Add method to repository to get users with active positions

            # For each user with active positions:
            # 1. Fetch current position from protocol
            # 2. Calculate health factor
            # 3. Save health check snapshot
            # 4. Create alerts if needed

            logger.info(f"Health monitoring complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error in health factor monitoring: {e}", exc_info=True)
            raise


class CheckUserHealthFactorTask:
    """
    Task to check health factor for a specific user position.

    Used for:
    - On-demand health checks
    - Critical position monitoring
    - Pre-transaction validation
    """

    def __init__(
        self,
        position_provider: PositionProvider,
        repository: LendingRepository,
    ):
        self._position_provider = position_provider
        self._repository = repository

    async def run(
        self,
        user_id: UUID,
        protocol: str,
        chain: str = "ethereum",
    ) -> LendingHealthCheck:
        """
        Check health factor for a specific user position.

        Args:
            user_id: User identifier
            protocol: Protocol name ("aave" or "morpho")
            chain: Blockchain network

        Returns:
            LendingHealthCheck entity with current health metrics
        """
        logger.info(
            f"Checking health factor for user={user_id}, protocol={protocol}, chain={chain}"
        )

        try:
            # Get user's wallet address from repository
            if hasattr(self._repository, "get_user_wallet_address"):
                wallet_address = await self._repository.get_user_wallet_address(user_id)
            else:
                raise ValueError(
                    "Repository does not implement get_user_wallet_address method"
                )

            if not wallet_address:
                raise ValueError(f"No wallet address found for user {user_id}")

            # Fetch current position from protocol
            position = await self._position_provider.get_position(
                wallet_address=preferences.wallet_address,
                protocol=protocol,
                chain=chain,
            )

            # Calculate health factor
            health_factor = position.health_factor

            # Determine health factor level (matches entity enum)
            if health_factor >= Decimal("2.0"):
                health_level = "safe"
            elif health_factor >= Decimal("1.5"):
                health_level = "caution"
            elif health_factor >= Decimal("1.2"):
                health_level = "danger"
            elif health_factor >= Decimal("1.0"):
                health_level = "critical"
            else:
                health_level = "liquidatable"

            # Create health check snapshot
            # Note: LendingHealthCheck entity requires id, so we'll generate a UUID
            from uuid import uuid4

            health_check = LendingHealthCheck(
                id=uuid4(),
                user_id=user_id,
                protocol=protocol,
                chain=chain,
                health_factor=health_factor,
                health_factor_level=health_level,
                total_collateral_usd=position.total_collateral_usd,
                total_debt_usd=position.total_debt_usd,
                available_to_borrow_usd=None,  # TODO: Calculate from position
                liquidation_price=None,  # TODO: Calculate from position
                checked_at=datetime.now(UTC),
            )

            # Save health check
            await self._repository.save_health_check(health_check)

            # Create alert if health factor is critical
            if health_factor < Decimal("1.5"):
                alert = await self._create_health_alert(
                    user_id=user_id,
                    health_check=health_check,
                    position=position,
                )
                if alert:
                    await self._repository.create_alert(alert)
                    logger.warning(
                        f"Created alert for user {user_id}: HF={health_factor:.2f}"
                    )

            logger.info(
                f"Health check complete for user {user_id}: HF={health_factor:.2f}, "
                f"level={health_level}"
            )

            return health_check

        except Exception as e:
            logger.error(
                f"Error checking health factor for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def _create_health_alert(
        self,
        user_id: UUID,
        health_check: LendingHealthCheck,
        position,
    ) -> LendingAlert | None:
        """Create alert for critical health factor."""

        # Determine alert severity (note: LendingAlert uses 'critical' not 'urgent')
        if health_check.health_factor < Decimal("1.0"):
            severity = "critical"
            alert_type = "liquidation_risk"
        elif health_check.health_factor < Decimal("1.2"):
            severity = "critical"
            alert_type = "health_factor_low"
        else:
            severity = "warning"
            alert_type = "health_factor_low"

        # Create alert message
        if alert_type == "liquidation_risk":
            title = "🚨 Liquidation Risk Detected"
            message = (
                f"Your health factor is {health_check.health_factor:.2f}, "
                f"which is below the liquidation threshold. "
                f"Immediate action required to prevent liquidation."
            )
        else:
            title = "⚠️ Health Factor Warning"
            message = (
                f"Your health factor is {health_check.health_factor:.2f}. "
                f"Consider adding collateral or repaying debt to improve your position."
            )

        from uuid import uuid4

        alert = LendingAlert(
            id=uuid4(),
            user_id=user_id,
            position_id=None,  # TODO: Get from position if available
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            health_factor=health_check.health_factor,
            threshold_value=Decimal("1.5") if severity == "warning" else Decimal("1.2"),
            current_value=health_check.health_factor,
            is_read=False,
            sent_at=None,  # Will be set when alert is sent
            metadata={
                "protocol": health_check.protocol,
                "chain": health_check.chain,
                "collateral_usd": str(health_check.total_collateral_usd),
                "debt_usd": str(health_check.total_debt_usd),
            },
            created_at=datetime.now(UTC),
        )

        return alert


class RefreshPositionsTask:
    """
    Task to refresh lending positions from protocols.

    Periodically fetches latest position data from Aave and Morpho
    to keep our database in sync with on-chain state.
    """

    def __init__(
        self,
        position_provider: PositionProvider,
        repository: LendingRepository,
    ):
        self._position_provider = position_provider
        self._repository = repository

    async def run(self) -> dict:
        """
        Refresh all active positions from protocols.

        Returns:
            Dictionary with refresh stats
        """
        logger.info("Starting position refresh task")

        stats = {
            "positions_refreshed": 0,
            "errors": 0,
        }

        try:
            # Get all users with active lending preferences
            # TODO: Implement method to get active users
            # For each user:
            #   1. Fetch position from protocol
            #   2. Update position in database
            #   3. Trigger health check if needed

            logger.info(f"Position refresh complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error refreshing positions: {e}", exc_info=True)
            raise


class ConfirmWithdrawTransactionTask:
    """
    Task to confirm withdraw transaction and update position.

    Process:
    1. Wait for transaction confirmation
    2. Update lending_transactions status
    3. Refresh user position from protocol
    4. Update lending_positions table
    5. Recalculate health factor if needed

    Used for:
    - Morpho Blue market withdrawals
    - MetaMorpho vault withdrawals
    - Aave supply withdrawals
    """

    def __init__(
        self,
        repository: LendingRepository,
        position_provider: PositionProvider,
        web3_provider: Web3Provider | None = None,
    ):
        self._repository = repository
        self._position_provider = position_provider
        self._web3_provider = web3_provider

    async def run(
        self,
        transaction_hash: str,
        user_id: UUID,
        protocol: str,
        chain: str,
        vault_address: str | None = None,
        market_id: str | None = None,
        amount: Decimal = Decimal("0"),
    ) -> dict[str, Any]:
        """
        Execute withdraw confirmation.

        Args:
            transaction_hash: On-chain transaction hash
            user_id: User identifier
            protocol: Protocol name ("morpho" or "aave")
            chain: Blockchain network
            vault_address: MetaMorpho vault address (for Morpho)
            market_id: Morpho Blue market ID (for Morpho Blue markets)
            amount: Withdrawn amount

        Returns:
            Dictionary with confirmation results
        """
        logger.info(
            f"Confirming withdraw transaction {transaction_hash} "
            f"for user={user_id}, protocol={protocol}, chain={chain}"
        )

        result = {
            "transaction_hash": transaction_hash,
            "status": "pending",
            "confirmed": False,
            "error": None,
        }

        try:
            # 1. Wait for transaction confirmation
            tx_receipt = await self._wait_for_confirmation(transaction_hash, chain)

            if not tx_receipt:
                result["status"] = "timeout"
                result["error"] = "Transaction confirmation timeout"
                await self._update_transaction_status(
                    transaction_hash=transaction_hash,
                    status="failed",
                    error_message="Transaction confirmation timeout",
                )
                return result

            if tx_receipt.get("status") != 1:
                result["status"] = "failed"
                result["error"] = "Transaction reverted on-chain"
                await self._update_transaction_status(
                    transaction_hash=transaction_hash,
                    status="failed",
                    error_message="Transaction reverted",
                    block_number=tx_receipt.get("blockNumber"),
                    gas_used=tx_receipt.get("gasUsed"),
                )
                return result

            # 2. Update transaction status to confirmed
            await self._update_transaction_status(
                transaction_hash=transaction_hash,
                status="confirmed",
                block_number=tx_receipt.get("blockNumber"),
                gas_used=tx_receipt.get("gasUsed"),
                confirmed_at=datetime.now(UTC),
            )

            # 3. Refresh position from protocol
            wallet_address = await self._get_user_wallet_address(user_id)
            if wallet_address:
                try:
                    position = await self._position_provider.get_position(
                        wallet_address=wallet_address,
                        protocol=protocol,
                        chain=chain,
                    )

                    # 4. Update position in database
                    if position:
                        await self._update_position(
                            user_id=user_id,
                            protocol=protocol,
                            chain=chain,
                            position_data={
                                "vault_address": vault_address,
                                "market_id": market_id,
                                "assets": str(position.assets if hasattr(position, 'assets') else 0),
                                "shares": str(position.shares if hasattr(position, 'shares') else 0),
                                "health_factor": str(getattr(position, 'health_factor', None)),
                            },
                        )

                    logger.info(
                        f"Position refreshed after withdraw for user {user_id}"
                    )

                except Exception as e:
                    logger.warning(
                        f"Failed to refresh position after withdraw: {e}"
                    )
                    # Don't fail the task - transaction is still confirmed

            result["status"] = "confirmed"
            result["confirmed"] = True
            result["block_number"] = tx_receipt.get("blockNumber")
            result["gas_used"] = tx_receipt.get("gasUsed")

            logger.info(
                f"Withdraw transaction confirmed: {transaction_hash}, "
                f"block={tx_receipt.get('blockNumber')}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Error confirming withdraw transaction {transaction_hash}: {e}",
                exc_info=True,
            )
            result["status"] = "error"
            result["error"] = str(e)

            await self._update_transaction_status(
                transaction_hash=transaction_hash,
                status="failed",
                error_message=str(e),
            )

            return result

    async def _wait_for_confirmation(
        self, tx_hash: str, chain: str, timeout: int = 120
    ) -> dict[str, Any] | None:
        """Wait for transaction confirmation."""
        if self._web3_provider:
            return await self._web3_provider.wait_for_transaction(
                tx_hash, chain, timeout
            )

        # Fallback: Mock confirmation for development
        logger.warning(
            f"No Web3 provider configured, mocking confirmation for {tx_hash}"
        )
        return {
            "status": 1,
            "blockNumber": 12345678,
            "gasUsed": 150000,
        }

    async def _update_transaction_status(
        self,
        transaction_hash: str,
        status: str,
        error_message: str | None = None,
        block_number: int | None = None,
        gas_used: int | None = None,
        confirmed_at: datetime | None = None,
    ) -> None:
        """Update lending transaction status in database."""
        if hasattr(self._repository, "update_transaction_status"):
            await self._repository.update_transaction_status(
                transaction_hash=transaction_hash,
                status=status,
                error_message=error_message,
                block_number=block_number,
                gas_used=gas_used,
                confirmed_at=confirmed_at,
            )
        else:
            logger.warning(
                "Repository does not implement update_transaction_status method"
            )

    async def _get_user_wallet_address(self, user_id: UUID) -> str | None:
        """Get user's wallet address from repository."""
        if hasattr(self._repository, "get_user_wallet_address"):
            return await self._repository.get_user_wallet_address(user_id)
        return None

    async def _update_position(
        self,
        user_id: UUID,
        protocol: str,
        chain: str,
        position_data: dict[str, Any],
    ) -> None:
        """Update position in database."""
        if hasattr(self._repository, "update_position"):
            await self._repository.update_position(
                user_id=user_id,
                protocol=protocol,
                chain=chain,
                position_data=position_data,
            )
        else:
            logger.warning("Repository does not implement update_position method")
