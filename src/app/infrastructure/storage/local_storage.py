"""Local filesystem storage adapter.

Stores files locally and serves via static file endpoint.
Used as fallback when CDN is not configured.
"""

import logging
from pathlib import Path

import aiofiles

from app.domain.ports.storage.file_storage import FileStoragePort

logger = logging.getLogger(__name__)


class LocalStorageAdapter(FileStoragePort):
    """Local filesystem storage adapter.

    Stores files in: {base_path}/{path}
    Serves via: {base_url}/{path}
    """

    def __init__(
        self,
        base_path: Path | str,
        base_url: str = "/static",
    ):
        """Initialize local storage adapter.

        Args:
            base_path: Base directory for file storage
            base_url: Base URL for serving files (default: /static)
        """
        self._base_path = Path(base_path)
        self._base_url = base_url.rstrip("/")

        # Ensure base directory exists
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "image/png",
    ) -> str:
        """Save file locally and return URL.

        Args:
            data: File content as bytes
            path: Relative path within storage (e.g., "qr/7a/0x7a23...png")
            content_type: MIME type (unused for local storage)

        Returns:
            Local URL to access the file
        """
        full_path = self._base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)

        logger.debug(f"Saved file to local storage: {path}")
        return f"{self._base_url}/{path}"

    async def delete(self, path: str) -> bool:
        """Delete local file.

        Args:
            path: Relative path within storage

        Returns:
            True if file was deleted, False if not found
        """
        full_path = self._base_path / path
        if full_path.exists():
            full_path.unlink()
            logger.debug(f"Deleted file from local storage: {path}")
            return True
        return False

    async def exists(self, path: str) -> bool:
        """Check if file exists locally.

        Args:
            path: Relative path within storage

        Returns:
            True if file exists
        """
        return (self._base_path / path).exists()
