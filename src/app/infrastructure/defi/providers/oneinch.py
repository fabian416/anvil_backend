"""
1inch DEX aggregator API client.
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class OneInchClient:
    """
    Client for 1inch DEX aggregator API.

    Provides token swap quotes and execution via 1inch.
    """

    BASE_URL = "https://api.1inch.dev"

    def __init__(self, api_key: str, chain_id: int = 1):
        """
        Initialize 1inch client.

        Args:
            api_key: 1inch API key
            chain_id: Blockchain network ID (1=Ethereum, 137=Polygon, etc.)
        """
        self.api_key = api_key
        self.chain_id = chain_id
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "accept": "application/json",
            },
            timeout=30.0,
        )

    async def get_quote(
        self,
        src: str,
        dst: str,
        amount: str,
        slippage: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Get swap quote from 1inch.

        Args:
            src: Source token address
            dst: Destination token address
            amount: Amount in source token's smallest unit (wei)
            slippage: Slippage tolerance percentage (0.5-50)

        Returns:
            Quote data including estimated output amount

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            response = await self._client.get(
                f"/swap/v5.2/{self.chain_id}/quote",
                params={
                    "src": src,
                    "dst": dst,
                    "amount": amount,
                    "includeTokensInfo": "true",
                    "includeProtocols": "true",
                },
            )
            response.raise_for_status()

            data = response.json()
            logger.info(
                f"1inch quote: {amount} {src[:8]}... -> {data.get('toAmount')} {dst[:8]}..."
            )

            return data

        except httpx.HTTPError as e:
            logger.error(f"1inch API error: {e}")
            raise

    async def get_swap(
        self,
        src: str,
        dst: str,
        amount: str,
        from_address: str,
        slippage: float = 1.0,
        disable_estimate: bool = True,
    ) -> Dict[str, Any]:
        """
        Get swap transaction data.

        Args:
            src: Source token address
            dst: Destination token address
            amount: Amount in source token's smallest unit
            from_address: User's wallet address
            slippage: Slippage tolerance percentage
            disable_estimate: Disable gas estimation

        Returns:
            Transaction data ready for signing
        """
        try:
            response = await self._client.get(
                f"/swap/v5.2/{self.chain_id}/swap",
                params={
                    "src": src,
                    "dst": dst,
                    "amount": amount,
                    "from": from_address,
                    "slippage": slippage,
                    "disableEstimate": str(disable_estimate).lower(),
                },
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"1inch swap prepared for {from_address}")

            return data

        except httpx.HTTPError as e:
            logger.error(f"1inch swap error: {e}")
            raise

    async def get_tokens(self) -> Dict[str, Any]:
        """
        Get list of supported tokens.

        Returns:
            Dictionary of token address -> token info
        """
        try:
            response = await self._client.get(f"/swap/v5.2/{self.chain_id}/tokens")
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"1inch tokens error: {e}")
            raise

    async def get_spender_address(self) -> str:
        """
        Get 1inch contract address for token approval.

        Returns:
            Spender contract address
        """
        try:
            response = await self._client.get(
                f"/swap/v5.2/{self.chain_id}/approve/spender"
            )
            response.raise_for_status()

            data = response.json()
            return data.get("address", "")

        except httpx.HTTPError as e:
            logger.error(f"1inch spender error: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


class OneInchError(Exception):
    """1inch API error."""

    pass
