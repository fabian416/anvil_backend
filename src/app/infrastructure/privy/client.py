"""
Privy HTTP Client.

Handles communication with Privy API for wallet and user operations.
Implements EmbeddedWalletProviderPort for easy provider switching.

API Documentation: https://docs.privy.io/api-reference/introduction

To switch to another provider (e.g., Dynamic, Turnkey):
1. Create a new client in infrastructure/wallet_providers/<provider>/
2. Implement EmbeddedWalletProviderPort
3. Update the dependency injection in setup/providers.py
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
import jwt

from app.domain.ports.wallet.embedded_wallet_provider import (
    AuthenticationError,
    ChainType,
    EmbeddedWalletProviderPort,
    RateLimitError,
    TokenVerificationResult,
    UserInfo,
    UserNotFoundError,
    WalletInfo,
    WalletListResult,
    WalletNotFoundError,
    WalletProviderError,
    WalletType,
)
from app.setup.config.privy import PrivySettings

logger = logging.getLogger(__name__)

PROVIDER_NAME = "privy"


# ============================================================
# Legacy DTOs (kept for backward compatibility)
# ============================================================


@dataclass
class WalletExportResponse:
    """Response from Privy wallet export endpoint."""

    encryption_type: str
    ciphertext: str
    encapsulated_key: str


# ============================================================
# Legacy Exceptions (kept for backward compatibility)
# ============================================================


class PrivyClientError(WalletProviderError):
    """Base exception for Privy client errors."""

    def __init__(self, message: str):
        super().__init__(message, provider=PROVIDER_NAME)


class PrivyAuthenticationError(PrivyClientError, AuthenticationError):
    """Authentication failed with Privy API."""

    pass


class PrivyWalletNotFoundError(PrivyClientError, WalletNotFoundError):
    """Wallet not found in Privy."""

    pass


class PrivyUserNotFoundError(PrivyClientError, UserNotFoundError):
    """User not found in Privy."""

    pass


class PrivyPolicyNotFoundError(PrivyClientError):
    """Policy not found in Privy."""

    pass


class PrivyMethodNotAllowedError(PrivyClientError):
    """HTTP method not allowed for the requested Privy resource."""

    pass


class PrivyRateLimitError(PrivyClientError, RateLimitError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        # Call RateLimitError.__init__ which sets retry_after
        RateLimitError.__init__(
            self, message, provider=PROVIDER_NAME, retry_after=retry_after
        )


# ============================================================
# Privy Client
# ============================================================


class PrivyClient(EmbeddedWalletProviderPort):
    """
    HTTP client for Privy API.

    Implements EmbeddedWalletProviderPort to allow switching providers.

    Features:
    - Token verification (JWT validation)
    - User management (get by ID, email, wallet)
    - Wallet operations (get, list, create)
    - Wallet export with HPKE encryption

    Usage:
        settings = PrivySettings(APP_ID="xxx", APP_SECRET="yyy")
        client = PrivyClient(settings)

        # Verify a token from the frontend
        result = await client.verify_token(access_token)
        if result.is_valid:
            print(f"User: {result.user_id}")

        # Get user's wallets
        wallets = await client.list_user_wallets(user_id)

        # Always close when done
        await client.close()
    """

    __slots__ = ("_http_client", "_settings")

    def __init__(self, settings: PrivySettings) -> None:
        self._settings = settings
        self._http_client: httpx.AsyncClient | None = None

    # --------------------------------------------------------
    # Properties
    # --------------------------------------------------------

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return PROVIDER_NAME

    # --------------------------------------------------------
    # HTTP Client Management
    # --------------------------------------------------------

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

    async def _handle_response(
        self, response: httpx.Response, context: str = ""
    ) -> dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: HTTP response from Privy API.
            context: Context for error messages (e.g., "get_user").

        Returns:
            Parsed JSON response.

        Raises:
            PrivyAuthenticationError: For 401 errors.
            PrivyRateLimitError: For 429 errors.
            PrivyClientError: For other errors.
        """
        if response.status_code == 401:
            raise PrivyAuthenticationError("Invalid Privy credentials")

        if response.status_code == 404:
            raise PrivyClientError(f"Resource not found: {context}")

        if response.status_code == 405:
            raise PrivyMethodNotAllowedError(
                f"Method not allowed: {context} ({response.request.method} {response.request.url})"
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise PrivyRateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 400:
            error_detail = response.text
            logger.error(
                f"Privy API error ({context}): {response.status_code} - {error_detail}"
            )
            raise PrivyClientError(
                f"API error: {response.status_code} - {error_detail}"
            )

        return response.json()

    # --------------------------------------------------------
    # Token Verification
    # --------------------------------------------------------

    async def verify_token(self, access_token: str) -> TokenVerificationResult:
        """
        Verify a Privy access token from the frontend.

        Privy tokens are JWTs that can be verified by:
        1. Decoding the JWT to get claims
        2. Validating the signature against Privy's public keys
        3. Checking expiration and issuer

        For production, you should verify the signature using Privy's
        JWKS endpoint. This implementation does basic validation.

        Args:
            access_token: The JWT token from Privy frontend SDK.

        Returns:
            TokenVerificationResult with validation status.
        """
        try:
            # Decode without verification first to extract claims
            # In production, you should verify the signature using JWKS
            unverified = jwt.decode(
                access_token,
                options={"verify_signature": False},
                algorithms=["ES256"],
            )

            # Extract claims
            user_id = unverified.get("sub")
            app_id = unverified.get("aud")
            issued_at = unverified.get("iat")
            expires_at = unverified.get("exp")

            # Basic validation
            if not user_id:
                return TokenVerificationResult(
                    is_valid=False,
                    error_message="Missing subject claim",
                )

            # Check if the token is for our app
            if app_id and app_id != self._settings.app_id:
                return TokenVerificationResult(
                    is_valid=False,
                    error_message=f"Token not issued for this app: {app_id}",
                )

            # Check expiration
            now = int(time.time())
            if expires_at and expires_at < now:
                return TokenVerificationResult(
                    is_valid=False,
                    error_message="Token has expired",
                )

            return TokenVerificationResult(
                is_valid=True,
                user_id=user_id,
                app_id=app_id,
                issued_at=datetime.fromtimestamp(issued_at) if issued_at else None,
                expires_at=datetime.fromtimestamp(expires_at) if expires_at else None,
            )

        except jwt.DecodeError as e:
            logger.warning(f"Failed to decode Privy token: {e}")
            return TokenVerificationResult(
                is_valid=False,
                error_message=f"Invalid token format: {e}",
            )
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            return TokenVerificationResult(
                is_valid=False,
                error_message=str(e),
            )

    # --------------------------------------------------------
    # User Operations
    # --------------------------------------------------------

    async def get_user(self, user_id: str) -> UserInfo:
        """
        Get user information by Privy user ID.

        API: GET /v1/users/{user_id}

        Args:
            user_id: Privy user ID (e.g., did:privy:xxx).

        Returns:
            UserInfo with user profile and linked wallets.

        Raises:
            PrivyUserNotFoundError: If user doesn't exist.
        """
        client = await self._get_client()

        response = await client.get(
            f"/v1/users/{user_id}",
            headers=self._get_headers(),
        )

        if response.status_code == 404:
            raise PrivyUserNotFoundError(f"User not found: {user_id}")

        data = await self._handle_response(response, f"get_user({user_id})")
        return self._parse_user_response(data)

    async def get_user_by_email(self, email: str) -> UserInfo | None:
        """
        Get user by email address.

        API: GET /v1/users?email={email}

        Args:
            email: User's email address.

        Returns:
            UserInfo if found, None otherwise.
        """
        client = await self._get_client()

        response = await client.get(
            "/v1/users",
            params={"email": email},
            headers=self._get_headers(),
        )

        if response.status_code == 404:
            return None

        data = await self._handle_response(response, f"get_user_by_email({email})")

        # API returns a list of users
        users = data.get("data", [])
        if not users:
            return None

        return self._parse_user_response(users[0])

    async def get_user_by_wallet_address(self, address: str) -> UserInfo | None:
        """
        Get user by wallet address.

        API: GET /v1/users?wallet_address={address}

        Args:
            address: Blockchain wallet address.

        Returns:
            UserInfo if found, None otherwise.
        """
        client = await self._get_client()

        response = await client.get(
            "/v1/users",
            params={"wallet_address": address.lower()},
            headers=self._get_headers(),
        )

        if response.status_code == 404:
            return None

        data = await self._handle_response(response, f"get_user_by_wallet({address})")

        users = data.get("data", [])
        if not users:
            return None

        return self._parse_user_response(users[0])

    def _parse_user_response(self, data: dict[str, Any]) -> UserInfo:
        """Parse Privy user API response into UserInfo."""
        # Extract linked accounts (social logins)
        linked_accounts = []
        for account in data.get("linked_accounts", []):
            account_type = account.get("type")
            if account_type and account_type != "wallet":
                linked_accounts.append(account_type)

        # Extract wallets from linked accounts
        wallets = []
        for account in data.get("linked_accounts", []):
            if account.get("type") == "wallet":
                wallet = self._parse_wallet_from_linked_account(account, data.get("id"))
                if wallet:
                    wallets.append(wallet)

        # Parse creation date
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        return UserInfo(
            user_id=data.get("id", ""),
            email=data.get("email", {}).get("address")
            if isinstance(data.get("email"), dict)
            else data.get("email"),
            phone=data.get("phone", {}).get("number")
            if isinstance(data.get("phone"), dict)
            else data.get("phone"),
            created_at=created_at,
            linked_wallets=wallets,
            linked_accounts=linked_accounts,
            metadata={"raw": data},
        )

    def _parse_wallet_from_linked_account(
        self, account: dict, owner_id: str | None = None
    ) -> WalletInfo | None:
        """Parse wallet info from a linked account."""
        if account.get("type") != "wallet":
            return None

        chain_type = self._map_chain_type(account.get("chain_type", "ethereum"))
        wallet_client = account.get("wallet_client_type", "")

        # Determine wallet type
        if wallet_client == "privy":
            wallet_type = WalletType.EMBEDDED
        else:
            wallet_type = WalletType.EXTERNAL

        return WalletInfo(
            wallet_id=account.get("id", account.get("address", "")),
            address=account.get("address", ""),
            chain_type=chain_type,
            wallet_type=wallet_type,
            owner_id=owner_id,
            metadata={
                "wallet_client": wallet_client,
                "connector_type": account.get("connector_type"),
                "verified_at": account.get("verified_at"),
            },
        )

    # --------------------------------------------------------
    # Wallet Operations
    # --------------------------------------------------------

    async def get_wallet(self, wallet_id: str) -> WalletInfo:
        """
        Get wallet details from Privy.

        API: GET /v1/wallets/{wallet_id}

        Args:
            wallet_id: The Privy wallet ID.

        Returns:
            WalletInfo with wallet details.

        Raises:
            PrivyWalletNotFoundError: If wallet doesn't exist.
        """
        client = await self._get_client()

        response = await client.get(
            f"/v1/wallets/{wallet_id}",
            headers=self._get_headers(),
        )

        if response.status_code == 404:
            raise PrivyWalletNotFoundError(f"Wallet not found: {wallet_id}")

        data = await self._handle_response(response, f"get_wallet({wallet_id})")
        return self._parse_wallet_response(data)

    async def update_wallet(
        self,
        wallet_id: str,
        *,
        policy_ids: list[str] | None = None,
        owner: dict[str, Any] | None = None,
        owner_id: str | None = None,
        additional_signers: list[dict[str, Any]] | None = None,
    ) -> WalletInfo:
        """
        Update wallet configuration in Privy.

        API: PATCH /v1/wallets/{wallet_id}

        This endpoint allows admins to update wallet configuration including:
        - policy_ids: Array of policy IDs to attach to the wallet
        - owner: Object specifying new owner (user_id or public_key)
        - owner_id: String ID of new owner (alternative to owner object)
        - additional_signers: Array of additional signer configurations

        Args:
            wallet_id: The Privy wallet ID.
            policy_ids: Optional list of policy IDs.
            owner: Optional owner object (e.g., {"user_id": "did:privy:xxx"}).
            owner_id: Optional owner ID string.
            additional_signers: Optional list of additional signer objects.

        Returns:
            WalletInfo with updated wallet details.

        Raises:
            PrivyWalletNotFoundError: If wallet doesn't exist.
            PrivyAuthenticationError: If authentication fails.
            PrivyClientError: For other API errors.
        """
        client = await self._get_client()

        # Build request payload with only provided fields
        payload: dict[str, Any] = {}

        if policy_ids is not None:
            payload["policy_ids"] = policy_ids

        if owner is not None:
            payload["owner"] = owner
        elif owner_id is not None:
            payload["owner_id"] = owner_id

        if additional_signers is not None:
            payload["additional_signers"] = additional_signers

        logger.info(
            f"Updating wallet {wallet_id} via Privy API with payload: {payload}"
        )

        response = await client.patch(
            f"/v1/wallets/{wallet_id}",
            headers=self._get_headers(),
            json=payload,
        )

        if response.status_code == 404:
            raise PrivyWalletNotFoundError(f"Wallet not found: {wallet_id}")

        data = await self._handle_response(response, f"update_wallet({wallet_id})")
        return self._parse_wallet_response(data)

    async def get_wallet_by_address(
        self, address: str, chain_type: ChainType = ChainType.ETHEREUM
    ) -> WalletInfo | None:
        """
        Get wallet by blockchain address.

        This iterates through wallets to find by address.

        Args:
            address: Blockchain wallet address.
            chain_type: The blockchain type to search in.

        Returns:
            WalletInfo if found, None otherwise.
        """
        # Privy doesn't have a direct "get by address" endpoint
        # We can try to find the user by wallet address and then get their wallets
        user = await self.get_user_by_wallet_address(address)
        if not user:
            return None

        for wallet in user.linked_wallets:
            if (
                wallet.address.lower() == address.lower()
                and wallet.chain_type == chain_type
            ):
                return wallet

        return None

    async def list_wallets(
        self,
        cursor: str | None = None,
        limit: int = 100,
        chain_type: ChainType | None = None,
    ) -> WalletListResult:
        """
        List all wallets for the application (paginated).

        API: GET /v1/wallets

        Args:
            cursor: Pagination cursor from previous request.
            limit: Maximum wallets per page (default: 100).
            chain_type: Filter by blockchain type.

        Returns:
            WalletListResult with paginated wallets.
        """
        client = await self._get_client()

        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if chain_type:
            params["chain_type"] = chain_type.value

        response = await client.get(
            "/v1/wallets",
            params=params,
            headers=self._get_headers(),
        )

        data = await self._handle_response(response, "list_wallets")

        wallets = [self._parse_wallet_response(w) for w in data.get("data", [])]

        return WalletListResult(
            wallets=wallets,
            next_cursor=data.get("next_cursor"),
            total_count=data.get("total_count"),
        )

    async def list_user_wallets(self, user_id: str) -> list[WalletInfo]:
        """
        List all wallets for a specific user.

        Args:
            user_id: The Privy user ID.

        Returns:
            List of WalletInfo for the user.
        """
        user = await self.get_user(user_id)
        return user.linked_wallets

    # --------------------------------------------------------
    # Policy Operations
    # --------------------------------------------------------

    async def create_policy(
        self,
        *,
        version: str,
        name: str,
        chain_type: str,
        rules: list[dict[str, Any]],
        owner: dict[str, Any] | None = None,
        owner_id: str | None = None,
        authorization_signature: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a policy in Privy.

        API: POST /v1/policies

        Note:
        - If the policy has an owner/owner_id, Privy may require the
          `privy-authorization-signature` header.
        """
        client = await self._get_client()

        payload: dict[str, Any] = {
            "version": version,
            "name": name,
            "chain_type": chain_type,
            "rules": rules,
        }
        if owner is not None:
            payload["owner"] = owner
        elif owner_id is not None:
            payload["owner_id"] = owner_id

        headers = self._get_headers()
        if authorization_signature:
            headers["privy-authorization-signature"] = authorization_signature

        response = await client.post(
            "/v1/policies",
            headers=headers,
            json=payload,
        )
        return await self._handle_response(response, "create_policy")

    async def list_policies(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
        chain_type: str | None = None,
    ) -> Any:
        """
        List policies for the application.

        API: GET /v1/policies

        Notes:
        - Response shape may vary; this method returns the parsed JSON.
        - Pagination parameters are passed through when provided.
        """
        client = await self._get_client()

        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
        if chain_type:
            params["chain_type"] = chain_type

        response = await client.get(
            "/v1/policies",
            params=params or None,
            headers=self._get_headers(),
        )
        return await self._handle_response(response, "list_policies")

    async def get_policy(self, policy_id: str) -> dict[str, Any]:
        """Get a policy by ID from Privy. API: GET /v1/policies/{policy_id}"""
        client = await self._get_client()

        response = await client.get(
            f"/v1/policies/{policy_id}",
            headers=self._get_headers(),
        )
        if response.status_code == 404:
            raise PrivyPolicyNotFoundError(f"Policy not found: {policy_id}")
        return await self._handle_response(response, f"get_policy({policy_id})")

    async def update_policy(
        self,
        policy_id: str,
        *,
        name: str | None = None,
        rules: list[dict[str, Any]] | None = None,
        authorization_signature: str | None = None,
    ) -> dict[str, Any]:
        """Update a policy. API: PATCH /v1/policies/{policy_id}"""
        client = await self._get_client()

        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if rules is not None:
            payload["rules"] = rules

        headers = self._get_headers()
        if authorization_signature:
            headers["privy-authorization-signature"] = authorization_signature

        response = await client.patch(
            f"/v1/policies/{policy_id}",
            headers=headers,
            json=payload,
        )
        if response.status_code == 404:
            raise PrivyPolicyNotFoundError(f"Policy not found: {policy_id}")
        return await self._handle_response(response, f"update_policy({policy_id})")

    async def create_policy_rule(
        self,
        policy_id: str,
        *,
        rule: dict[str, Any],
        authorization_signature: str | None = None,
    ) -> dict[str, Any]:
        """Create a rule for a policy. API: POST /v1/policies/{policy_id}/rules"""
        client = await self._get_client()

        headers = self._get_headers()
        if authorization_signature:
            headers["privy-authorization-signature"] = authorization_signature

        response = await client.post(
            f"/v1/policies/{policy_id}/rules",
            headers=headers,
            json=rule,
        )
        if response.status_code == 404:
            raise PrivyPolicyNotFoundError(f"Policy not found: {policy_id}")
        return await self._handle_response(response, f"create_policy_rule({policy_id})")

    async def update_policy_rule(
        self,
        policy_id: str,
        rule_id: str,
        *,
        rule: dict[str, Any],
        authorization_signature: str | None = None,
    ) -> dict[str, Any]:
        """Update a policy rule. API: PATCH /v1/policies/{policy_id}/rules/{rule_id}"""
        client = await self._get_client()

        headers = self._get_headers()
        if authorization_signature:
            headers["privy-authorization-signature"] = authorization_signature

        response = await client.patch(
            f"/v1/policies/{policy_id}/rules/{rule_id}",
            headers=headers,
            json=rule,
        )
        if response.status_code == 404:
            raise PrivyPolicyNotFoundError(
                f"Policy or rule not found: policy_id={policy_id}, rule_id={rule_id}"
            )
        return await self._handle_response(
            response, f"update_policy_rule({policy_id},{rule_id})"
        )

    async def delete_policy_rule(
        self,
        policy_id: str,
        rule_id: str,
        *,
        authorization_signature: str | None = None,
    ) -> dict[str, Any]:
        """Delete a policy rule. API: DELETE /v1/policies/{policy_id}/rules/{rule_id}"""
        client = await self._get_client()

        headers = self._get_headers()
        if authorization_signature:
            headers["privy-authorization-signature"] = authorization_signature

        response = await client.delete(
            f"/v1/policies/{policy_id}/rules/{rule_id}",
            headers=headers,
            json={"policy_id": policy_id},
        )
        if response.status_code == 404:
            raise PrivyPolicyNotFoundError(
                f"Policy or rule not found: policy_id={policy_id}, rule_id={rule_id}"
            )
        # Some Privy endpoints may return 204 No Content for deletes.
        if response.status_code == 204:
            return {"success": True}
        return await self._handle_response(
            response, f"delete_policy_rule({policy_id},{rule_id})"
        )

    def _parse_wallet_response(self, data: dict[str, Any]) -> WalletInfo:
        """Parse Privy wallet API response into WalletInfo."""
        chain_type = self._map_chain_type(data.get("chain_type", "ethereum"))

        # Determine wallet type based on ownership
        wallet_type = WalletType.EMBEDDED
        if data.get("owner_type") == "authorization_key":
            wallet_type = WalletType.SERVER_CONTROLLED

        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        # Parse exported_at timestamp
        exported_at = None
        if data.get("exported_at"):
            try:
                exported_at = datetime.fromisoformat(
                    data["exported_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        # Parse imported_at timestamp
        imported_at = None
        if data.get("imported_at"):
            try:
                imported_at = datetime.fromisoformat(
                    data["imported_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

        return WalletInfo(
            wallet_id=data.get("id", ""),
            address=data.get("address", ""),
            chain_type=chain_type,
            wallet_type=wallet_type,
            created_at=created_at,
            owner_id=data.get("owner_id"),
            is_recoverable=data.get("is_recoverable", True),
            metadata={
                "raw": data,
                # Extract Privy configuration fields explicitly
                "policy_ids": data.get("policy_ids", []),
                "owner_type": data.get("owner_type"),
                "owner_id": data.get("owner_id"),
                "additional_signers": data.get("additional_signers", []),
                "exported_at": exported_at,
                "imported_at": imported_at,
            },
        )

    def _map_chain_type(self, chain: str) -> ChainType:
        """Map Privy chain type string to ChainType enum."""
        chain_lower = chain.lower()
        if chain_lower == "ethereum":
            return ChainType.ETHEREUM
        if chain_lower == "solana":
            return ChainType.SOLANA
        # Privy returns "bitcoin-segwit" or "bitcoin-taproot" for Bitcoin wallets
        if chain_lower in ("bitcoin", "bitcoin-segwit", "bitcoin-taproot"):
            return ChainType.BITCOIN
        if chain_lower == "polygon":
            return ChainType.POLYGON
        if chain_lower == "arbitrum":
            return ChainType.ARBITRUM
        if chain_lower == "optimism":
            return ChainType.OPTIMISM
        if chain_lower == "base":
            return ChainType.BASE
        return ChainType.OTHER

    # --------------------------------------------------------
    # Wallet Creation
    # --------------------------------------------------------

    def _map_chain_type_for_privy_api(self, chain_type: ChainType) -> str:
        """
        Map internal ChainType to Privy API chain_type string.

        Privy uses different chain type identifiers than our internal enum.
        For example, Bitcoin is 'bitcoin-segwit' in Privy API.
        """
        privy_chain_map = {
            ChainType.ETHEREUM: "ethereum",
            ChainType.SOLANA: "solana",
            ChainType.BITCOIN: "bitcoin-segwit",  # Privy uses 'bitcoin-segwit'
            ChainType.POLYGON: "ethereum",  # Polygon uses same wallet as Ethereum
            ChainType.ARBITRUM: "ethereum",
            ChainType.OPTIMISM: "ethereum",
            ChainType.BASE: "ethereum",
        }
        return privy_chain_map.get(chain_type, "ethereum")

    async def create_wallet_for_user(
        self,
        user_id: str,
        chain_type: ChainType = ChainType.ETHEREUM,
    ) -> WalletInfo:
        """
        Create a new embedded wallet for a user.

        API: POST /v1/wallets

        Args:
            user_id: The Privy user ID (e.g., 'did:privy:xxx').
            chain_type: Blockchain type for the new wallet.

        Returns:
            WalletInfo for the newly created wallet.
        """
        client = await self._get_client()

        # Map chain type to Privy API format
        privy_chain_type = self._map_chain_type_for_privy_api(chain_type)

        # Privy API expects owner.user_id directly, not owner.type and owner.id
        payload = {
            "owner": {"user_id": user_id},
            "chain_type": privy_chain_type,
        }

        logger.info(
            f"Creating wallet via Privy API: chain={privy_chain_type}, user={user_id}"
        )

        response = await client.post(
            "/v1/wallets",
            headers=self._get_headers(),
            json=payload,
        )

        data = await self._handle_response(
            response, f"create_wallet_for_user({user_id})"
        )
        return self._parse_wallet_response(data)

    # --------------------------------------------------------
    # Wallet Export (Legacy method kept for compatibility)
    # --------------------------------------------------------

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
                logger.error(
                    f"Privy API error: {response.status_code} - {error_detail}"
                )
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

    # --------------------------------------------------------
    # Health Check
    # --------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        """
        Check Privy API health.

        Returns:
            Dict with status, latency_ms, and message.
        """
        start = time.time()

        try:
            client = await self._get_client()

            # Simple request to check connectivity
            response = await client.get(
                "/v1/apps/current",
                headers=self._get_headers(),
            )

            latency_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency_ms, 2),
                    "message": "Privy API is responding",
                }
            if response.status_code == 401:
                return {
                    "status": "degraded",
                    "latency_ms": round(latency_ms, 2),
                    "message": "Authentication failed - check credentials",
                }
            return {
                "status": "degraded",
                "latency_ms": round(latency_ms, 2),
                "message": f"Unexpected status: {response.status_code}",
            }

        except httpx.TimeoutException:
            return {
                "status": "down",
                "latency_ms": round((time.time() - start) * 1000, 2),
                "message": "Request timed out",
            }
        except Exception as e:
            return {
                "status": "down",
                "latency_ms": round((time.time() - start) * 1000, 2),
                "message": str(e),
            }
