"""
Privy API Client for fetching user and wallet data.

This client handles communication with the Privy API for:
- Fetching user linked accounts (wallets, social logins)
- Getting wallet IDs for balance tracking
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.setup.config.privy import PrivySettings

log = logging.getLogger(__name__)

# API timeout in seconds
PRIVY_API_TIMEOUT = 10.0


@dataclass
class PrivyWallet:
    """Wallet data from Privy API."""
    wallet_id: str  # Privy internal wallet ID (e.g., "ydsfu5mmwzcrlkykxd7ejf4j")
    address: str  # Wallet address (e.g., "0x...")
    chain_type: str  # Chain type (e.g., "ethereum", "solana")
    wallet_client: str  # Wallet client (e.g., "privy", "metamask")
    connector_type: str  # Connector type (e.g., "embedded", "injected")
    is_imported: bool  # Whether wallet was imported


@dataclass
class PrivyUserData:
    """User data from Privy API."""
    privy_user_id: str
    wallets: list[PrivyWallet]
    email: str | None = None
    name: str | None = None


class PrivyApiClient:
    """
    Client for Privy API interactions.
    
    Used to fetch wallet IDs and other user data from Privy
    that isn't available in the frontend token.
    """

    def __init__(self, settings: PrivySettings):
        self._settings = settings
        self._base_url = "https://auth.privy.io/api/v1"

    def _get_headers(self) -> dict[str, str]:
        """Get authorization headers for Privy API."""
        return {
            "Authorization": f"Basic {self._settings.basic_auth_credentials}",
            "Content-Type": "application/json",
            "privy-app-id": self._settings.app_id,
        }

    async def get_user(self, privy_user_id: str) -> PrivyUserData | None:
        """
        Fetch user data from Privy API.
        
        Args:
            privy_user_id: The Privy user ID (e.g., "did:privy:cml15tigy...")
            
        Returns:
            PrivyUserData with wallets and user info, or None on error
        """
        if not self._settings.should_call_privy:
            log.debug("Privy API calls disabled (offline mode)")
            return None

        if not self._settings.app_secret:
            log.warning("Privy app_secret not configured, skipping API call")
            return None

        url = f"{self._base_url}/users/{privy_user_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    timeout=PRIVY_API_TIMEOUT,
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_user_response(data)
                elif response.status_code == 404:
                    log.warning(f"Privy user not found: {privy_user_id}")
                    return None
                else:
                    log.error(
                        f"Privy API error fetching user {privy_user_id}: "
                        f"{response.status_code} - {response.text}"
                    )
                    return None

        except httpx.TimeoutException:
            log.warning(f"Privy API timeout fetching user {privy_user_id}")
            return None
        except httpx.RequestError as e:
            log.error(f"Privy API request error: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error fetching Privy user: {e}")
            return None

    def _parse_user_response(self, data: dict[str, Any]) -> PrivyUserData:
        """Parse Privy API user response into PrivyUserData."""
        privy_user_id = data.get("id", "")
        linked_accounts = data.get("linked_accounts", [])

        wallets: list[PrivyWallet] = []
        email: str | None = None
        name: str | None = None

        for account in linked_accounts:
            account_type = account.get("type", "")

            if account_type == "wallet":
                wallet = PrivyWallet(
                    wallet_id=account.get("id", ""),
                    address=account.get("address", ""),
                    chain_type=account.get("chain_type", "ethereum"),
                    wallet_client=account.get("wallet_client", ""),
                    connector_type=account.get("connector_type", ""),
                    is_imported=account.get("imported", False),
                )
                wallets.append(wallet)

            elif account_type in ("google_oauth", "email"):
                if not email:
                    email = account.get("email")
                if not name:
                    name = account.get("name")

        return PrivyUserData(
            privy_user_id=privy_user_id,
            wallets=wallets,
            email=email,
            name=name,
        )

    async def get_wallet_id_for_address(
        self,
        privy_user_id: str,
        wallet_address: str,
    ) -> str | None:
        """
        Get the Privy wallet ID for a specific wallet address.
        
        Args:
            privy_user_id: The Privy user ID
            wallet_address: The wallet address to find
            
        Returns:
            Privy wallet ID if found, None otherwise
        """
        user_data = await self.get_user(privy_user_id)
        if not user_data:
            return None

        # Find wallet matching the address (case-insensitive)
        normalized_address = wallet_address.lower()
        for wallet in user_data.wallets:
            if wallet.address.lower() == normalized_address:
                return wallet.wallet_id

        log.warning(
            f"Wallet address {wallet_address[:10]}... not found in Privy user {privy_user_id}"
        )
        return None
