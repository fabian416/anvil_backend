"""
Privy HTTP Client
Handles communication with Privy API for wallet operations.
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.setup.config.privy import PrivySettings

logger = logging.getLogger(__name__)


@dataclass
class WalletExportResponse:
    """Response from Privy wallet export endpoint."""

    encryption_type: str
    ciphertext: str
    encapsulated_key: str


class PrivyClientError(Exception):
    """Base exception for Privy client errors."""

    pass


class PrivyAuthenticationError(PrivyClientError):
    """Authentication failed with Privy API."""

    pass


class PrivyWalletNotFoundError(PrivyClientError):
    """Wallet not found in Privy."""

    pass


class PrivyClient:
    """
    HTTP client for Privy API.
    
    Handles wallet export operations using HPKE encryption.
    """

    __slots__ = ("_settings", "_http_client")

    def __init__(self, settings: PrivySettings) -> None:
        self._settings = settings
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._settings.api_base_url,
                timeout=30.0,
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client is not None and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for Privy API requests."""
        return {
            "Authorization": f"Basic {self._settings.basic_auth_credentials}",
            "Content-Type": "application/json",
            "privy-app-id": self._settings.app_id,
        }

    async def export_wallet(
        self,
        wallet_id: str,
        recipient_public_key_b64: str,
    ) -> WalletExportResponse:
        """
        Export a wallet's private key via Privy API.
        
        The private key is returned encrypted with HPKE and must be
        decrypted using the corresponding private key.
        
        Args:
            wallet_id: The Privy wallet ID to export.
            recipient_public_key_b64: Base64-encoded HPKE public key for encryption.
            
        Returns:
            WalletExportResponse with encrypted private key data.
            
        Raises:
            PrivyAuthenticationError: If authentication fails.
            PrivyWalletNotFoundError: If wallet is not found.
            PrivyClientError: For other API errors.
        """
        client = await self._get_client()

        logger.info(f"Exporting wallet {wallet_id} via Privy API")

        try:
            response = await client.post(
                f"/v1/wallets/{wallet_id}/export",
                headers=self._get_headers(),
                json={
                    "encryption_type": "HPKE",
                    "recipient_public_key": recipient_public_key_b64,
                },
            )

            if response.status_code == 401:
                raise PrivyAuthenticationError("Invalid Privy credentials")

            if response.status_code == 404:
                raise PrivyWalletNotFoundError(f"Wallet {wallet_id} not found")

            if response.status_code >= 400:
                error_detail = response.text
                logger.error(f"Privy API error: {response.status_code} - {error_detail}")
                raise PrivyClientError(
                    f"Privy API error: {response.status_code} - {error_detail}"
                )

            data: dict[str, Any] = response.json()

            return WalletExportResponse(
                encryption_type=data["encryption_type"],
                ciphertext=data["ciphertext"],
                encapsulated_key=data["encapsulated_key"],
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Privy API: {e}")
            raise PrivyClientError(f"Failed to call Privy API: {e}") from e

    async def get_wallet(self, wallet_id: str) -> dict[str, Any]:
        """
        Get wallet details from Privy.
        
        Args:
            wallet_id: The Privy wallet ID.
            
        Returns:
            Wallet data from Privy API.
        """
        client = await self._get_client()

        response = await client.get(
            f"/v1/wallets/{wallet_id}",
            headers=self._get_headers(),
        )

        if response.status_code == 404:
            raise PrivyWalletNotFoundError(f"Wallet {wallet_id} not found")

        if response.status_code >= 400:
            raise PrivyClientError(f"Privy API error: {response.status_code}")

        return response.json()

