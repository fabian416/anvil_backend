"""
HPKE Encryption/Decryption Utilities
For decrypting wallet private keys exported from Privy.

Uses HPKE with the following configuration (as per Privy docs):
- KEM: DHKEM_P256_HKDF_SHA256
- KDF: HKDF_SHA256
- AEAD: CHACHA20_POLY1305
- Mode: BASE
"""

import base64
import logging
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


@dataclass
class HPKEKeyPair:
    """HPKE key pair for encryption/decryption."""

    private_key: ec.EllipticCurvePrivateKey
    public_key_bytes: bytes

    @property
    def public_key_b64(self) -> str:
        """Base64-encoded public key (raw uncompressed format)."""
        return base64.b64encode(self.public_key_bytes).decode()


class HPKEDecryptor:
    """
    HPKE decryption for Privy wallet exports.
    
    Privy uses HPKE (Hybrid Public Key Encryption) with:
    - KEM: DHKEM_P256_HKDF_SHA256
    - KDF: HKDF_SHA256
    - AEAD: CHACHA20_POLY1305
    """

    __slots__ = ("_key_pair",)

    def __init__(self, key_pair: HPKEKeyPair | None = None) -> None:
        """
        Initialize decryptor.
        
        Args:
            key_pair: Optional existing key pair. If not provided,
                     a new one will be generated when needed.
        """
        self._key_pair = key_pair

    @staticmethod
    def generate_key_pair() -> HPKEKeyPair:
        """
        Generate a new P-256 key pair for HPKE.
        
        Returns:
            HPKEKeyPair with private and public keys.
        """
        # Generate P-256 key pair
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        # Get public key in uncompressed point format (raw bytes)
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )

        return HPKEKeyPair(
            private_key=private_key,
            public_key_bytes=public_key_bytes,
        )

    def get_or_create_key_pair(self) -> HPKEKeyPair:
        """Get existing key pair or generate a new one."""
        if self._key_pair is None:
            self._key_pair = self.generate_key_pair()
        return self._key_pair

    def decrypt(
        self,
        ciphertext_b64: str,
        encapsulated_key_b64: str,
    ) -> str:
        """
        Decrypt a message encrypted with HPKE.
        
        Args:
            ciphertext_b64: Base64-encoded ciphertext from Privy.
            encapsulated_key_b64: Base64-encoded encapsulated key from Privy.
            
        Returns:
            Decrypted private key as a string.
            
        Raises:
            ValueError: If decryption fails.
        """
        try:
            from pyhpke import AEADId, CipherSuite, KDFId, KEMId
        except ImportError as e:
            raise ImportError(
                "pyhpke library is required for wallet export. "
                "Install it with: pip install pyhpke"
            ) from e

        if self._key_pair is None:
            raise ValueError("No key pair available for decryption")

        # Initialize the cipher suite as per Privy docs
        suite = CipherSuite.new(
            KEMId.DHKEM_P256_HKDF_SHA256,
            KDFId.HKDF_SHA256,
            AEADId.CHACHA20_POLY1305,
        )

        # Decode base64 values
        ciphertext = base64.b64decode(ciphertext_b64)
        encapsulated_key = base64.b64decode(encapsulated_key_b64)

        # Extract the raw private key bytes (32 bytes for P-256)
        private_number = self._key_pair.private_key.private_numbers().private_value
        private_bytes = private_number.to_bytes(32, byteorder="big")

        # Deserialize keys for HPKE
        private_kem_key = suite.kem.deserialize_private_key(private_bytes)

        # Create recipient context and decrypt
        # The encapsulated key is the sender's ephemeral public key
        recipient_context = suite.create_recipient_context(
            encapsulated_key,
            private_kem_key,
        )

        # Decrypt and return as UTF-8 string
        decrypted = recipient_context.open(ciphertext)
        return decrypted.decode("utf-8")
