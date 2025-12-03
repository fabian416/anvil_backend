"""
Export Wallet Command
Exports a user's embedded wallet private key via Privy API.
"""

import logging
from dataclasses import dataclass

from app.infrastructure.privy.client import (
    PrivyClient,
    PrivyClientError,
    PrivyWalletNotFoundError,
)
from app.infrastructure.privy.hpke import HPKEDecryptor

logger = logging.getLogger(__name__)


class WalletExportError(Exception):
    """Error during wallet export."""

    pass


class WalletNotFoundError(WalletExportError):
    """Wallet not found."""

    pass


@dataclass
class ExportWalletResult:
    """Result of wallet export operation."""

    wallet_id: str
    address: str
    private_key: str
    chain_type: str


class ExportWallet:
    """
    Use case for exporting a wallet's private key.
    
    This command:
    1. Generates an HPKE key pair for secure key transfer
    2. Calls Privy API to export the wallet (encrypted)
    3. Decrypts the private key using HPKE
    4. Returns the decrypted private key
    
    Security Note:
    - The private key is only decrypted server-side
    - It should be transmitted securely to the frontend
    - Consider implementing additional authorization checks
    """

    __slots__ = ("_privy_client",)

    def __init__(self, privy_client: PrivyClient) -> None:
        self._privy_client = privy_client

    async def execute(
        self,
        wallet_id: str,
        wallet_address: str | None = None,
    ) -> ExportWalletResult:
        """
        Export a wallet's private key.
        
        Args:
            wallet_id: The Privy wallet ID to export.
            wallet_address: Optional wallet address for verification.
            
        Returns:
            ExportWalletResult with the decrypted private key.
            
        Raises:
            WalletNotFoundError: If wallet doesn't exist.
            WalletExportError: If export fails.
        """
        logger.info(f"Starting wallet export for wallet_id={wallet_id}")

        try:
            # Step 1: Generate HPKE key pair for secure transfer
            decryptor = HPKEDecryptor()
            key_pair = decryptor.get_or_create_key_pair()

            logger.debug("Generated HPKE key pair for wallet export")

            # Step 2: Get wallet info from Privy (optional, for verification)
            wallet_info = await self._privy_client.get_wallet(wallet_id)
            actual_address = wallet_info.get("address", "")
            chain_type = wallet_info.get("chain_type", "ethereum")

            # Verify address if provided
            if wallet_address and actual_address.lower() != wallet_address.lower():
                raise WalletExportError(
                    f"Address mismatch: expected {wallet_address}, got {actual_address}"
                )

            # Step 3: Call Privy API to export (encrypted)
            export_response = await self._privy_client.export_wallet(
                wallet_id=wallet_id,
                recipient_public_key_b64=key_pair.public_key_b64,
            )

            logger.debug("Received encrypted wallet export from Privy")

            # Step 4: Decrypt the private key
            private_key = decryptor.decrypt(
                ciphertext_b64=export_response.ciphertext,
                encapsulated_key_b64=export_response.encapsulated_key,
            )

            logger.info(f"Successfully exported wallet {wallet_id}")

            return ExportWalletResult(
                wallet_id=wallet_id,
                address=actual_address,
                private_key=private_key,
                chain_type=chain_type,
            )

        except PrivyWalletNotFoundError as e:
            logger.warning(f"Wallet not found: {wallet_id}")
            raise WalletNotFoundError(f"Wallet {wallet_id} not found") from e

        except PrivyClientError as e:
            logger.error(f"Privy API error during export: {e}")
            raise WalletExportError(f"Failed to export wallet: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error during wallet export: {e}")
            raise WalletExportError(f"Wallet export failed: {e}") from e

