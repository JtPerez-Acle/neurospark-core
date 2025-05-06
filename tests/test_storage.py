"""Tests for storage module."""

import io
import pytest
from unittest.mock import patch, MagicMock, call
import json

from src.storage.minio import (
    MinioStorage,
    StorageObject,
)


@pytest.fixture
def mock_minio_client():
    """Create a mock MinIO client."""
    with patch("src.storage.minio.Minio") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def minio_storage(mock_minio_client):
    """Create a MinioStorage instance with a mock client."""
    return MinioStorage(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        bucket_name="test-bucket",
    )


def test_init_with_endpoint():
    """Test initializing MinioStorage with endpoint."""
    with patch("src.storage.minio.Minio") as mock_client_class:
        storage = MinioStorage(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
        )

        mock_client_class.assert_called_once_with(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False,
        )
        assert storage.bucket_name == "test-bucket"


def test_init_with_secure():
    """Test initializing MinioStorage with secure=True."""
    with patch("src.storage.minio.Minio") as mock_client_class:
        storage = MinioStorage(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            secure=True,
        )

        mock_client_class.assert_called_once_with(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=True,
        )
        assert storage.bucket_name == "test-bucket"


def test_create_bucket_new(minio_storage, mock_minio_client):
    """Test creating a new bucket."""
    # Setup
    mock_minio_client.bucket_exists.return_value = False

    # Execute
    minio_storage.create_bucket()

    # Assert
    mock_minio_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_minio_client.make_bucket.assert_called_once_with("test-bucket")


def test_create_bucket_exists(minio_storage, mock_minio_client):
    """Test creating a bucket that already exists."""
    # Setup
    mock_minio_client.bucket_exists.return_value = True

    # Execute
    minio_storage.create_bucket()

    # Assert
    mock_minio_client.bucket_exists.assert_called_once_with("test-bucket")
    mock_minio_client.make_bucket.assert_not_called()


def test_upload_object(minio_storage, mock_minio_client):
    """Test uploading an object."""
    # Setup
    data = b"test data"
    object_name = "test-object.txt"
    content_type = "text/plain"

    # Execute
    minio_storage.upload_object(
        data=data,
        object_name=object_name,
        content_type=content_type,
    )

    # Assert
    mock_minio_client.put_object.assert_called_once()
    call_args = mock_minio_client.put_object.call_args[0]
    call_kwargs = mock_minio_client.put_object.call_args[1]
    assert call_args[0] == "test-bucket"
    assert call_args[1] == "test-object.txt"
    assert isinstance(call_args[2], io.BytesIO)
    assert call_kwargs["length"] == len(data)
    assert call_kwargs["content_type"] == "text/plain"


def test_upload_object_with_metadata(minio_storage, mock_minio_client):
    """Test uploading an object with metadata."""
    # Setup
    data = b"test data"
    object_name = "test-object.txt"
    content_type = "text/plain"
    metadata = {"source": "test", "author": "user"}

    # Execute
    minio_storage.upload_object(
        data=data,
        object_name=object_name,
        content_type=content_type,
        metadata=metadata,
    )

    # Assert
    mock_minio_client.put_object.assert_called_once()
    call_args = mock_minio_client.put_object.call_args[0]
    call_kwargs = mock_minio_client.put_object.call_args[1]
    assert call_args[0] == "test-bucket"
    assert call_args[1] == "test-object.txt"
    assert isinstance(call_args[2], io.BytesIO)
    assert call_kwargs["length"] == len(data)
    assert call_kwargs["content_type"] == "text/plain"
    assert call_kwargs["metadata"] == {"source": "test", "author": "user"}


def test_download_object(minio_storage, mock_minio_client):
    """Test downloading an object."""
    # Setup
    mock_response = MagicMock()
    mock_response.data = b"test data"
    mock_minio_client.get_object.return_value = mock_response

    # Execute
    data = minio_storage.download_object("test-object.txt")

    # Assert
    mock_minio_client.get_object.assert_called_once_with(
        "test-bucket", "test-object.txt"
    )
    assert data == b"test data"


def test_get_object_info(minio_storage, mock_minio_client):
    """Test getting object info."""
    # Setup
    mock_stat = MagicMock()
    mock_stat.size = 9
    mock_stat.etag = "test-etag"
    mock_stat.last_modified = "2023-01-01T00:00:00Z"
    mock_stat.metadata = {"source": "test", "author": "user"}
    mock_minio_client.stat_object.return_value = mock_stat

    # Execute
    info = minio_storage.get_object_info("test-object.txt")

    # Assert
    mock_minio_client.stat_object.assert_called_once_with(
        "test-bucket", "test-object.txt"
    )
    assert info.object_name == "test-object.txt"
    assert info.size == 9
    assert info.etag == "test-etag"
    assert info.last_modified == "2023-01-01T00:00:00Z"
    assert info.metadata == {"source": "test", "author": "user"}


def test_list_objects(minio_storage, mock_minio_client):
    """Test listing objects."""
    # Setup
    mock_object1 = MagicMock()
    mock_object1.object_name = "test-object1.txt"
    mock_object1.size = 9
    mock_object1.etag = "test-etag1"
    mock_object1.last_modified = "2023-01-01T00:00:00Z"

    mock_object2 = MagicMock()
    mock_object2.object_name = "test-object2.txt"
    mock_object2.size = 10
    mock_object2.etag = "test-etag2"
    mock_object2.last_modified = "2023-01-02T00:00:00Z"

    mock_minio_client.list_objects.return_value = [mock_object1, mock_object2]

    # Execute
    objects = minio_storage.list_objects()

    # Assert
    mock_minio_client.list_objects.assert_called_once_with(
        "test-bucket", prefix=None, recursive=True
    )
    assert len(objects) == 2

    assert objects[0].object_name == "test-object1.txt"
    assert objects[0].size == 9
    assert objects[0].etag == "test-etag1"
    assert objects[0].last_modified == "2023-01-01T00:00:00Z"

    assert objects[1].object_name == "test-object2.txt"
    assert objects[1].size == 10
    assert objects[1].etag == "test-etag2"
    assert objects[1].last_modified == "2023-01-02T00:00:00Z"


def test_list_objects_with_prefix(minio_storage, mock_minio_client):
    """Test listing objects with a prefix."""
    # Setup
    mock_object = MagicMock()
    mock_object.object_name = "prefix/test-object.txt"
    mock_object.size = 9
    mock_object.etag = "test-etag"
    mock_object.last_modified = "2023-01-01T00:00:00Z"

    mock_minio_client.list_objects.return_value = [mock_object]

    # Execute
    objects = minio_storage.list_objects(prefix="prefix/")

    # Assert
    mock_minio_client.list_objects.assert_called_once_with(
        "test-bucket", prefix="prefix/", recursive=True
    )
    assert len(objects) == 1
    assert objects[0].object_name == "prefix/test-object.txt"


def test_delete_object(minio_storage, mock_minio_client):
    """Test deleting an object."""
    # Execute
    minio_storage.delete_object("test-object.txt")

    # Assert
    mock_minio_client.remove_object.assert_called_once_with(
        "test-bucket", "test-object.txt"
    )


def test_delete_objects(minio_storage, mock_minio_client):
    """Test deleting multiple objects."""
    # Setup
    object_names = ["test-object1.txt", "test-object2.txt"]

    # Execute
    minio_storage.delete_objects(object_names)

    # Assert
    mock_minio_client.remove_objects.assert_called_once()
    call_args = mock_minio_client.remove_objects.call_args[0]
    assert call_args[0] == "test-bucket"

    # Check that the delete objects are correct
    delete_objects = list(call_args[1])
    assert len(delete_objects) == 2
    assert delete_objects[0] == "test-object1.txt"
    assert delete_objects[1] == "test-object2.txt"
