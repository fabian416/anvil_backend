"""File storage port for QR codes and other assets."""

from typing import Protocol


class FileStoragePort(Protocol):
    """Port for file storage operations.

    Abstracts storage backend (local filesystem or CDN like Recallium/DigitalOcean Spaces).
    """

    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "image/png",
    ) -> str:
        """Upload file and return public URL.

        Args:
            data: File content as bytes
            path: Storage path (e.g., "qr/7a/0x7a23...8f4d.png")
            content_type: MIME type (default: image/png)

        Returns:
            Public URL to access the file
        """
        ...

    async def delete(self, path: str) -> bool:
        """Delete file by path.

        Args:
            path: Storage path to delete

        Returns:
            True if file was deleted, False if not found
        """
        ...

    async def exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: Storage path to check

        Returns:
            True if file exists
        """
        ...
