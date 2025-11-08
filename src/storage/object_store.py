"""
Object storage for manifest files and content.

Supports S3-compatible storage (MinIO, AWS S3) with hot/warm/cold tiers.
"""

import io
import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Optional

from minio import Minio
from minio.error import S3Error


class StorageTier(str, Enum):
    """Storage tiers."""

    HOT = "hot"  # Active, frequently accessed
    WARM = "warm"  # Archived, occasionally accessed
    COLD = "cold"  # Long-term retention, rarely accessed


class ObjectStorage:
    """Object storage manager for S3-compatible storage."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = True,
        region: Optional[str] = None,
    ):
        """
        Initialize object storage.

        Args:
            endpoint: S3 endpoint (e.g., 's3.amazonaws.com' or 'minio:9000')
            access_key: Access key ID
            secret_key: Secret access key
            secure: Use HTTPS
            region: AWS region (optional)
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )

        # Bucket names for different tiers
        self.buckets = {
            StorageTier.HOT: "openmediatrust-hot",
            StorageTier.WARM: "openmediatrust-warm",
            StorageTier.COLD: "openmediatrust-cold",
        }

    def initialize_buckets(self) -> None:
        """Create storage buckets if they don't exist."""
        for tier, bucket_name in self.buckets.items():
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    print(f"Created bucket: {bucket_name}")

                    # Set lifecycle policy for tiering
                    if tier == StorageTier.HOT:
                        # Transition to warm after 90 days
                        self._set_lifecycle_policy(bucket_name, transition_days=90)

            except S3Error as e:
                print(f"Error creating bucket {bucket_name}: {e}")

    def _set_lifecycle_policy(
        self, bucket_name: str, transition_days: int
    ) -> None:
        """Set lifecycle policy for automatic tiering."""
        # This is a placeholder - actual implementation depends on S3 provider
        # For MinIO/AWS S3, use bucket lifecycle configuration
        pass

    def upload_manifest(
        self,
        manifest_id: str,
        manifest_data: dict,
        tier: StorageTier = StorageTier.HOT,
    ) -> str:
        """
        Upload manifest JSON to object storage.

        Args:
            manifest_id: Manifest identifier
            manifest_data: Manifest data dictionary
            tier: Storage tier

        Returns:
            Object path in storage
        """
        bucket_name = self.buckets[tier]
        object_name = f"manifests/{manifest_id}.json"

        # Convert to JSON bytes
        json_data = json.dumps(manifest_data, indent=2, default=str)
        json_bytes = json_data.encode("utf-8")

        # Upload
        try:
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(json_bytes),
                length=len(json_bytes),
                content_type="application/json",
            )
            return f"{tier.value}/{object_name}"
        except S3Error as e:
            raise Exception(f"Failed to upload manifest: {e}")

    def download_manifest(self, manifest_id: str, tier: StorageTier = StorageTier.HOT) -> Optional[dict]:
        """
        Download manifest from object storage.

        Args:
            manifest_id: Manifest identifier
            tier: Storage tier

        Returns:
            Manifest data dictionary or None
        """
        bucket_name = self.buckets[tier]
        object_name = f"manifests/{manifest_id}.json"

        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            return json.loads(data.decode("utf-8"))
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            raise Exception(f"Failed to download manifest: {e}")
        finally:
            if response:
                response.close()
                response.release_conn()

    def upload_content(
        self,
        file_path: str,
        object_name: str,
        tier: StorageTier = StorageTier.HOT,
    ) -> str:
        """
        Upload content file to object storage.

        Args:
            file_path: Path to file
            object_name: Object name in storage
            tier: Storage tier

        Returns:
            Object path in storage
        """
        bucket_name = self.buckets[tier]
        full_object_name = f"content/{object_name}"

        try:
            self.client.fput_object(bucket_name, full_object_name, file_path)
            return f"{tier.value}/{full_object_name}"
        except S3Error as e:
            raise Exception(f"Failed to upload content: {e}")

    def download_content(
        self, object_name: str, output_path: str, tier: StorageTier = StorageTier.HOT
    ) -> None:
        """
        Download content file from object storage.

        Args:
            object_name: Object name in storage
            output_path: Path to save file
            tier: Storage tier
        """
        bucket_name = self.buckets[tier]
        full_object_name = f"content/{object_name}"

        try:
            self.client.fget_object(bucket_name, full_object_name, output_path)
        except S3Error as e:
            raise Exception(f"Failed to download content: {e}")

    def move_to_tier(
        self,
        manifest_id: str,
        from_tier: StorageTier,
        to_tier: StorageTier,
    ) -> str:
        """
        Move manifest to different storage tier.

        Args:
            manifest_id: Manifest identifier
            from_tier: Current tier
            to_tier: Target tier

        Returns:
            New object path
        """
        object_name = f"manifests/{manifest_id}.json"

        # Download from source
        manifest_data = self.download_manifest(manifest_id, from_tier)
        if not manifest_data:
            raise Exception(f"Manifest not found in {from_tier}")

        # Upload to target
        new_path = self.upload_manifest(manifest_id, manifest_data, to_tier)

        # Delete from source
        try:
            self.client.remove_object(self.buckets[from_tier], object_name)
        except S3Error as e:
            print(f"Warning: Failed to delete from source tier: {e}")

        return new_path

    def delete_manifest(
        self, manifest_id: str, tier: StorageTier = StorageTier.HOT
    ) -> None:
        """
        Delete manifest from storage.

        Args:
            manifest_id: Manifest identifier
            tier: Storage tier
        """
        bucket_name = self.buckets[tier]
        object_name = f"manifests/{manifest_id}.json"

        try:
            self.client.remove_object(bucket_name, object_name)
        except S3Error as e:
            raise Exception(f"Failed to delete manifest: {e}")

    def get_presigned_url(
        self,
        manifest_id: str,
        tier: StorageTier = StorageTier.HOT,
        expires: timedelta = timedelta(hours=1),
    ) -> str:
        """
        Get presigned URL for temporary access.

        Args:
            manifest_id: Manifest identifier
            tier: Storage tier
            expires: URL expiration time

        Returns:
            Presigned URL
        """
        bucket_name = self.buckets[tier]
        object_name = f"manifests/{manifest_id}.json"

        try:
            url = self.client.presigned_get_object(
                bucket_name, object_name, expires=expires
            )
            return url
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    def list_manifests(
        self, tier: StorageTier = StorageTier.HOT, prefix: str = "manifests/"
    ) -> list:
        """
        List manifests in a tier.

        Args:
            tier: Storage tier
            prefix: Object prefix

        Returns:
            List of object names
        """
        bucket_name = self.buckets[tier]

        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            raise Exception(f"Failed to list manifests: {e}")
