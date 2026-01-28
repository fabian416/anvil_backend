"""
Lending background tasks for Celery.

These tasks handle periodic monitoring, health checks, and alert generation
for lending positions across Aave and Morpho protocols.
"""

import logging
from datetime import datetime, UTC
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.domain.entities.lending.lending_health_check import LendingHealthCheck
from app.domain.entities.lending.lending_alert import LendingAlert

logger = logging.getLogger(__name__)


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
