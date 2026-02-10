"""QR code generator for wallet addresses.

Generates QR codes using EIP-681 format for wallet addresses.
Format: ethereum:{chain_id}:{address}
Example: ethereum:8453:0x7a23B8c9D4e5F6a7b8c9d4e5f6a78f4d
"""

from io import BytesIO

import qrcode
from PIL import Image
from qrcode.constants import ERROR_CORRECT_H


class QRCodeGenerator:
    """Generate QR codes for wallet addresses using EIP-681 format.

    Attributes:
        _box_size: Size of each QR code module in pixels
        _border: Number of modules for the border
        _fill_color: QR code color (Anvil brand color by default)
        _back_color: Background color
    """

    def __init__(
        self,
        box_size: int = 12,
        border: int = 4,
        fill_color: str = "#00d4aa",  # Anvil brand color
        back_color: str = "white",
    ):
        """Initialize QR code generator.

        Args:
            box_size: Size of each QR code module in pixels
            border: Number of modules for the border
            fill_color: QR code color (default: Anvil brand teal)
            back_color: Background color (default: white)
        """
        self._box_size = box_size
        self._border = border
        self._fill_color = fill_color
        self._back_color = back_color

    def generate(
        self,
        address: str,
        chain_id: int = 8453,
        size: int = 300,
    ) -> bytes:
        """Generate QR code PNG bytes for wallet address.

        Uses EIP-681 URI format: ethereum:{chain_id}:{address}

        Args:
            address: EVM wallet address (0x...)
            chain_id: Blockchain chain ID (default: 8453 for Base)
            size: Output image size in pixels

        Returns:
            PNG image as bytes
        """
        # Build EIP-681 URI
        qr_data = self.get_qr_data(address, chain_id)

        # Create QR code with high error correction
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_H,
            box_size=self._box_size,
            border=self._border,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Generate image with custom colors
        img = qr.make_image(
            fill_color=self._fill_color,
            back_color=self._back_color,
        )

        # Convert to PIL Image for resizing
        if hasattr(img, "get_image"):
            pil_img = img.get_image()
        else:
            pil_img = img

        # Resize to requested size using high-quality resampling
        pil_img = pil_img.resize((size, size), Image.LANCZOS)

        # Convert to bytes
        buffer = BytesIO()
        pil_img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()

    def get_qr_data(self, address: str, chain_id: int = 8453) -> str:
        """Get QR data string without generating image.

        Useful for client-side QR generation fallback.

        Args:
            address: EVM wallet address (0x...)
            chain_id: Blockchain chain ID

        Returns:
            EIP-681 URI string
        """
        return f"ethereum:{chain_id}:{address}"

    def get_storage_path(self, address: str) -> str:
        """Generate storage path for QR image.

        Uses address prefix for directory sharding to avoid
        too many files in a single directory.

        Path format: qr/{prefix}/{address.lower()}.png

        Args:
            address: EVM wallet address (0x...)

        Returns:
            Storage path for the QR image
        """
        # Use first 2 chars after 0x for directory sharding
        prefix = address[2:4].lower()
        filename = f"{address.lower()}.png"
        return f"qr/{prefix}/{filename}"
