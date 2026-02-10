"""Recallium (DigitalOcean Spaces) storage adapter.

S3-compatible storage adapter for DigitalOcean Spaces CDN.
Files are stored and served via CDN for optimal performance.
"""

import logging
from functools import cached_property

import boto3
from botocore.exceptions import ClientError

from app.domain.ports.storage.file_storage import FileStoragePort

logger = logging.getLogger(__name__)


class RecalliumStorageAdapter(FileStoragePort):
    """DigitalOcean Spaces (S3-compatible) storage adapter.

    Files are stored in: {bucket}/{path}
    CDN URL: https://{bucket}.{region}.cdn.digitaloceanspaces.com/{path}
    Direct URL: https://{bucket}.{region}.digitaloceanspaces.com/{path}
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
        bucket: str,
        cdn_enabled: bool = True,
    ):
        """Initialize Recallium storage adapter.

        Args:
            access_key: DigitalOcean Spaces access key
            secret_key: DigitalOcean Spaces secret key
            region: DO region (e.g., "nyc3", "sfo3")
            bucket: Bucket name (e.g., "anvil-assets")
            cdn_enabled: Whether to use CDN URLs (default: True)
        """
        self._access_key = access_key
        self._secret_key = secret_key
        self._region = region
        self._bucket = bucket
        self._cdn_enabled = cdn_enabled

        # Build base URL for CDN or direct access
        if cdn_enabled:
            self._base_url = f"https://{bucket}.{region}.cdn.digitaloceanspaces.com"
        else:
            self._base_url = f"https://{bucket}.{region}.digitaloceanspaces.com"

    @cached_property
    def _client(self):
        """Lazy-initialize S3 client."""
        return boto3.client(
            "s3",
            region_name=self._region,
            endpoint_url=f"https://{self._region}.digitaloceanspaces.com",
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
        )

    async def upload(
        self,
        data: bytes,
        path: str,
        content_type: str = "image/png",
    ) -> str:
        """Upload to DigitalOcean Spaces and return CDN URL.

        Args:
            data: File content as bytes
            path: Storage path (e.g., "qr/7a/0x7a23...png")
            content_type: MIME type (default: image/png)

        Returns:
            CDN URL to access the file

        Raises:
            ClientError: If upload fails
        """
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=path,
                Body=data,
                ContentType=content_type,
                ACL="public-read",
                CacheControl="public, max-age=31536000",  # 1 year cache
            )
            url = f"{self._base_url}/{path}"
            logger.debug(f"Uploaded to Recallium CDN: {path}")
            return url
        except ClientError as e:
            logger.error(f"Failed to upload to Recallium: {e}")
            raise

    async def delete(self, path: str) -> bool:
        """Delete from DigitalOcean Spaces.

        Args:
            path: Storage path to delete

        Returns:
            True if deleted, False on error
        """
        try:
            self._client.delete_object(Bucket=self._bucket, Key=path)
            logger.debug(f"Deleted from Recallium CDN: {path}")
            return True
        except ClientError as e:
            logger.warning(f"Failed to delete from Recallium: {e}")
            return False

    async def exists(self, path: str) -> bool:
        """Check if file exists in bucket.

        Args:
            path: Storage path to check

        Returns:
            True if file exists
        """
        try:
            self._client.head_object(Bucket=self._bucket, Key=path)
            return True
        except ClientError:
            return False
