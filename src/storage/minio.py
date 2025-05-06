"""MinIO storage implementation."""

import io
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


@dataclass
class StorageObject:
    """Storage object model."""
    
    object_name: str
    size: int
    etag: str
    last_modified: str
    metadata: Optional[Dict[str, str]] = None


class MinioStorage:
    """MinIO storage implementation."""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False,
    ):
        """Initialize the MinIO storage.
        
        Args:
            endpoint: The endpoint of the MinIO server.
            access_key: The access key for authentication.
            secret_key: The secret key for authentication.
            bucket_name: The name of the bucket.
            secure: Whether to use HTTPS.
        """
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
    
    def create_bucket(self) -> None:
        """Create a bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                logger.info(f"Creating bucket {self.bucket_name}")
                self.client.make_bucket(self.bucket_name)
            else:
                logger.info(f"Bucket {self.bucket_name} already exists")
        except S3Error as e:
            logger.error(f"Error creating bucket {self.bucket_name}: {e}")
            raise
    
    def upload_object(
        self,
        data: bytes,
        object_name: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Upload an object to the bucket.
        
        Args:
            data: The data to upload.
            object_name: The name of the object.
            content_type: The content type of the object.
            metadata: Optional metadata for the object.
        """
        try:
            logger.info(f"Uploading object {object_name} to bucket {self.bucket_name}")
            
            # Convert bytes to BytesIO
            data_stream = io.BytesIO(data)
            
            # Upload the object
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type,
                metadata=metadata,
            )
            
            logger.info(f"Object {object_name} uploaded successfully")
        except S3Error as e:
            logger.error(f"Error uploading object {object_name}: {e}")
            raise
    
    def download_object(self, object_name: str) -> bytes:
        """Download an object from the bucket.
        
        Args:
            object_name: The name of the object.
            
        Returns:
            The object data.
        """
        try:
            logger.info(f"Downloading object {object_name} from bucket {self.bucket_name}")
            
            # Download the object
            response = self.client.get_object(self.bucket_name, object_name)
            
            # Read the data
            data = response.data
            
            logger.info(f"Object {object_name} downloaded successfully")
            return data
        except S3Error as e:
            logger.error(f"Error downloading object {object_name}: {e}")
            raise
    
    def get_object_info(self, object_name: str) -> StorageObject:
        """Get information about an object.
        
        Args:
            object_name: The name of the object.
            
        Returns:
            The object information.
        """
        try:
            logger.info(f"Getting info for object {object_name} from bucket {self.bucket_name}")
            
            # Get the object stats
            stat = self.client.stat_object(self.bucket_name, object_name)
            
            # Create a StorageObject
            storage_object = StorageObject(
                object_name=object_name,
                size=stat.size,
                etag=stat.etag,
                last_modified=stat.last_modified,
                metadata=stat.metadata,
            )
            
            return storage_object
        except S3Error as e:
            logger.error(f"Error getting info for object {object_name}: {e}")
            raise
    
    def list_objects(
        self, prefix: Optional[str] = None, recursive: bool = True
    ) -> List[StorageObject]:
        """List objects in the bucket.
        
        Args:
            prefix: Optional prefix to filter objects.
            recursive: Whether to list objects recursively.
            
        Returns:
            A list of objects.
        """
        try:
            logger.info(f"Listing objects in bucket {self.bucket_name}")
            
            # List objects
            objects = self.client.list_objects(
                self.bucket_name, prefix=prefix, recursive=recursive
            )
            
            # Convert to StorageObject list
            storage_objects = []
            for obj in objects:
                storage_object = StorageObject(
                    object_name=obj.object_name,
                    size=obj.size,
                    etag=obj.etag,
                    last_modified=obj.last_modified,
                    metadata=None,  # Metadata not available in list_objects
                )
                storage_objects.append(storage_object)
            
            return storage_objects
        except S3Error as e:
            logger.error(f"Error listing objects in bucket {self.bucket_name}: {e}")
            raise
    
    def delete_object(self, object_name: str) -> None:
        """Delete an object from the bucket.
        
        Args:
            object_name: The name of the object.
        """
        try:
            logger.info(f"Deleting object {object_name} from bucket {self.bucket_name}")
            
            # Delete the object
            self.client.remove_object(self.bucket_name, object_name)
            
            logger.info(f"Object {object_name} deleted successfully")
        except S3Error as e:
            logger.error(f"Error deleting object {object_name}: {e}")
            raise
    
    def delete_objects(self, object_names: List[str]) -> None:
        """Delete multiple objects from the bucket.
        
        Args:
            object_names: The names of the objects.
        """
        try:
            logger.info(f"Deleting {len(object_names)} objects from bucket {self.bucket_name}")
            
            # Delete the objects
            self.client.remove_objects(self.bucket_name, object_names)
            
            logger.info(f"{len(object_names)} objects deleted successfully")
        except S3Error as e:
            logger.error(f"Error deleting objects: {e}")
            raise
