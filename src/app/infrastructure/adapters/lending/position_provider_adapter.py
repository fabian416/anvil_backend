"""
Position provider adapter for fetching lending positions from protocols.

Uses MCP clients to fetch positions from Aave and Morpho protocols.
"""

import logging
from decimal import Decimal
from typing import Protocol

from app.domain.entities.lending.aave_position import AavePosition
from app.infrastructure.mcp.mcp_client import MCPClient

logger = logging.getLogger(__name__)


class PositionProviderAdapter:
    """
    Adapter for fetching positions from lending protocols via MCP.

    Implements PositionProvider protocol for Aave and Morpho.
    """

    def __init__(
        self,
        mcp_client: MCPClient,
        aave_base_url: str = "http://localhost:8085",
        morpho_base_url: str = "http://localhost:8088",
    ):
        self._mcp_client = mcp_client
        self._aave_base_url = aave_base_url
        self._morpho_base_url = morpho_base_url

    async def get_position(
        self,
        wallet_address: str,
        protocol: str,
        chain: str = "ethereum",
    ) -> AavePosition:
        """
        Get user's lending position from protocol.

        Args:
            wallet_address: User's wallet address
            protocol: Protocol name ("aave" or "morpho")
            chain: Blockchain network

        Returns:
            AavePosition entity with current position data

        Raises:
            ValueError: If protocol is not supported
            Exception: If MCP call fails
        """
        logger.info(
            f"Fetching position for wallet={wallet_address[:10]}..., "
            f"protocol={protocol}, chain={chain}"
        )

        if protocol.lower() == "aave":
            return await self._get_aave_position(wallet_address, chain)
        elif protocol.lower() == "morpho":
            return await self._get_morpho_position(wallet_address, chain)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

    async def _get_aave_position(
        self,
        wallet_address: str,
        chain: str,
    ) -> AavePosition:
        """Get Aave position via MCP."""
        chain_id = self._chain_to_id(chain)

        try:
            # Call Aave MCP get_user_positions tool
            response = await self._mcp_client.call_tool(
                server_url=self._aave_base_url,
                tool_name="get_user_positions",
                arguments={
                    "chain_id": chain_id,
                    "user_address": wallet_address,
                },
            )

            # Transform MCP response to AavePosition entity
            return self._transform_aave_response(response, chain)

        except Exception as e:
            logger.error(f"Failed to fetch Aave position: {e}", exc_info=True)
            raise

    async def _get_morpho_position(
        self,
        wallet_address: str,
        chain: str,
    ) -> AavePosition:
        """Get Morpho position via MCP."""
        chain_id = self._chain_to_id(chain)

        try:
            # Call Morpho MCP morpho_get_user_positions tool
            response = await self._mcp_client.call_tool(
                server_url=self._morpho_base_url,
                tool_name="morpho_get_user_positions",
                arguments={
                    "chain_id": chain_id,
                    "user_address": wallet_address,
                },
            )

            # Transform Morpho response to AavePosition entity
            # Note: Morpho only has supply positions (no borrow)
            return self._transform_morpho_response(response, chain)

        except Exception as e:
            logger.error(f"Failed to fetch Morpho position: {e}", exc_info=True)
            raise

    def _transform_aave_response(
        self,
        response: dict,
        chain: str,
    ) -> AavePosition:
        """Transform Aave MCP response to AavePosition entity."""
        from app.domain.entities.lending.aave_position import (
            AaveSupplyPosition,
            AaveBorrowPosition,
        )

        # Extract position data from response
        supplies_data = response.get("supplies", [])
        borrows_data = response.get("borrows", [])

        # Transform supplies
        supplies = []
        for supply in supplies_data:
            supplies.append(
                AaveSupplyPosition(
                    asset_address=supply.get("asset_address", supply.get("asset", "")),
                    symbol=supply.get("symbol", ""),
                    balance=Decimal(str(supply.get("balance", 0))),
                    balance_usd=Decimal(str(supply.get("balance_usd", 0))),
                    apy=Decimal(str(supply.get("apy", 0))),
                    is_collateral=supply.get("is_collateral", False),
                )
            )

        # Transform borrows
        borrows = []
        for borrow in borrows_data:
            borrows.append(
                AaveBorrowPosition(
                    asset_address=borrow.get("asset_address", borrow.get("asset", "")),
                    symbol=borrow.get("symbol", ""),
                    balance=Decimal(str(borrow.get("debt", borrow.get("balance", 0)))),
                    balance_usd=Decimal(
                        str(borrow.get("debt_usd", borrow.get("balance_usd", 0)))
                    ),
                    apy=Decimal(str(borrow.get("apy", 0))),
                    borrow_type=borrow.get(
                        "rate_mode", borrow.get("borrow_type", "variable")
                    ),
                )
            )

        # Calculate totals
        total_collateral_usd = sum(s.balance_usd for s in supplies)
        total_debt_usd = sum(b.debt_usd for b in borrows)

        # Get health factor
        health_factor = Decimal(str(response.get("health_factor", "0")))

        # Get max LTV (for liquidation threshold calculation)
        max_ltv = Decimal(str(response.get("max_ltv", "0.8")))

        from datetime import datetime, UTC

        return AavePosition(
            user_address=response.get("user_address", ""),
            chain=chain,
            supplies=supplies,
            borrows=borrows,
            total_collateral_usd=total_collateral_usd,
            total_debt_usd=total_debt_usd,
            available_borrow_usd=Decimal(str(response.get("available_borrow_usd", 0))),
            net_worth_usd=total_collateral_usd - total_debt_usd,
            health_factor=health_factor,
            current_ltv=(
                total_debt_usd / total_collateral_usd
                if total_collateral_usd > 0
                else Decimal("0")
            ),
            max_ltv=max_ltv,
            updated_at=datetime.now(UTC),
        )

    def _transform_morpho_response(
        self,
        response: dict,
        chain: str,
    ) -> AavePosition:
        """Transform Morpho MCP response to AavePosition entity."""
        from app.domain.entities.lending.aave_position import AaveSupplyPosition

        # Morpho only has supply positions (no borrow)
        positions_data = response.get("positions", [])

        from datetime import datetime, UTC

        supplies = []
        for pos in positions_data:
            supplies.append(
                AaveSupplyPosition(
                    asset_address=pos.get("asset_address", pos.get("asset", "")),
                    symbol=pos.get("symbol", ""),
                    balance=Decimal(str(pos.get("balance", 0))),
                    balance_usd=Decimal(str(pos.get("balance_usd", 0))),
                    apy=Decimal(str(pos.get("apy", 0))),
                    is_collateral=True,  # Morpho positions are always collateral
                )
            )

        total_collateral_usd = sum(s.balance_usd for s in supplies)

        return AavePosition(
            user_address=response.get("user_address", ""),
            chain=chain,
            supplies=supplies,
            borrows=[],  # Morpho doesn't support borrowing
            total_collateral_usd=total_collateral_usd,
            total_debt_usd=Decimal("0"),
            available_borrow_usd=Decimal("0"),
            net_worth_usd=total_collateral_usd,
            health_factor=Decimal("inf"),  # No debt = infinite HF
            current_ltv=Decimal("0"),
            max_ltv=Decimal("0"),  # Not applicable for Morpho
            updated_at=datetime.now(UTC),
        )

    def _chain_to_id(self, chain: str) -> int:
        """Convert chain name to chain ID."""
        chain_map = {
            "ethereum": 1,
            "polygon": 137,
            "arbitrum": 42161,
            "optimism": 10,
            "base": 8453,
            "avalanche": 43114,
        }
        return chain_map.get(chain.lower(), 1)
