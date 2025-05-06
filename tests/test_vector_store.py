"""Tests for vector store module."""

import pytest
from unittest.mock import patch, MagicMock, call
import numpy as np

from src.vector_store.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client."""
    with patch("src.vector_store.qdrant.QdrantClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def vector_store(mock_qdrant_client):
    """Create a QdrantVectorStore instance with a mock client."""
    return QdrantVectorStore(
        host="localhost",
        port=6333,
        collection_name="test_collection",
    )


def test_init_with_host_port():
    """Test initializing QdrantVectorStore with host and port."""
    with patch("src.vector_store.qdrant.QdrantClient") as mock_client:
        store = QdrantVectorStore(
            host="localhost",
            port=6333,
            collection_name="test_collection",
        )

        mock_client.assert_called_once_with(host="localhost", port=6333, api_key=None)
        assert store.collection_name == "test_collection"


def test_init_with_url():
    """Test initializing QdrantVectorStore with URL."""
    with patch("src.vector_store.qdrant.QdrantClient") as mock_client:
        store = QdrantVectorStore(
            url="http://localhost:6333",
            collection_name="test_collection",
        )

        mock_client.assert_called_once_with(url="http://localhost:6333", api_key=None)
        assert store.collection_name == "test_collection"


def test_init_with_in_memory():
    """Test initializing QdrantVectorStore in memory."""
    with patch("src.vector_store.qdrant.QdrantClient") as mock_client:
        store = QdrantVectorStore(
            in_memory=True,
            collection_name="test_collection",
        )

        mock_client.assert_called_once_with(":memory:")
        assert store.collection_name == "test_collection"


def test_create_collection(vector_store, mock_qdrant_client):
    """Test creating a collection."""
    # Setup
    mock_qdrant_client.collection_exists.return_value = False

    # Execute
    vector_store.create_collection(
        dimensions=768,
        distance=Distance.COSINE,
        recreate_if_exists=False,
    )

    # Assert
    mock_qdrant_client.collection_exists.assert_called_once_with("test_collection")
    mock_qdrant_client.create_collection.assert_called_once_with(
        collection_name="test_collection",
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )


def test_create_collection_already_exists(vector_store, mock_qdrant_client):
    """Test creating a collection that already exists."""
    # Setup
    mock_qdrant_client.collection_exists.return_value = True

    # Execute
    vector_store.create_collection(
        dimensions=768,
        distance=Distance.COSINE,
        recreate_if_exists=False,
    )

    # Assert
    mock_qdrant_client.collection_exists.assert_called_once_with("test_collection")
    mock_qdrant_client.create_collection.assert_not_called()


def test_create_collection_recreate(vector_store, mock_qdrant_client):
    """Test recreating a collection that already exists."""
    # Setup
    mock_qdrant_client.collection_exists.return_value = True

    # Execute
    vector_store.create_collection(
        dimensions=768,
        distance=Distance.COSINE,
        recreate_if_exists=True,
    )

    # Assert
    mock_qdrant_client.collection_exists.assert_called_once_with("test_collection")
    mock_qdrant_client.delete_collection.assert_called_once_with("test_collection")
    mock_qdrant_client.create_collection.assert_called_once_with(
        collection_name="test_collection",
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )


def test_upsert_points(vector_store, mock_qdrant_client):
    """Test upserting points."""
    # Setup
    points = [
        {"id": 1, "vector": [0.1, 0.2, 0.3], "payload": {"text": "test1"}},
        {"id": 2, "vector": [0.4, 0.5, 0.6], "payload": {"text": "test2"}},
    ]

    # Execute
    vector_store.upsert_points(points)

    # Assert
    mock_qdrant_client.upsert.assert_called_once()
    call_args = mock_qdrant_client.upsert.call_args[1]
    assert call_args["collection_name"] == "test_collection"
    assert len(call_args["points"]) == 2
    assert isinstance(call_args["points"][0], PointStruct)
    assert call_args["points"][0].id == 1
    assert call_args["points"][0].vector == [0.1, 0.2, 0.3]
    assert call_args["points"][0].payload == {"text": "test1"}
    assert call_args["points"][1].id == 2
    assert call_args["points"][1].vector == [0.4, 0.5, 0.6]
    assert call_args["points"][1].payload == {"text": "test2"}


def test_search(vector_store, mock_qdrant_client):
    """Test searching for similar vectors."""
    # Setup
    mock_result = [
        MagicMock(id=1, score=0.9, payload={"text": "test1"}),
        MagicMock(id=2, score=0.8, payload={"text": "test2"}),
    ]
    mock_qdrant_client.search.return_value = mock_result

    # Execute
    results = vector_store.search(
        query_vector=[0.1, 0.2, 0.3],
        limit=2,
    )

    # Assert
    mock_qdrant_client.search.assert_called_once_with(
        collection_name="test_collection",
        query_vector=[0.1, 0.2, 0.3],
        limit=2,
        query_filter=None,
    )
    assert len(results) == 2
    assert results[0]["id"] == 1
    assert results[0]["score"] == 0.9
    assert results[0]["payload"] == {"text": "test1"}
    assert results[1]["id"] == 2
    assert results[1]["score"] == 0.8
    assert results[1]["payload"] == {"text": "test2"}


def test_search_with_filter(vector_store, mock_qdrant_client):
    """Test searching with a filter."""
    # Setup
    mock_result = [MagicMock(id=1, score=0.9, payload={"text": "test1", "category": "A"})]
    mock_qdrant_client.search.return_value = mock_result

    # Execute
    results = vector_store.search(
        query_vector=[0.1, 0.2, 0.3],
        limit=2,
        filter_condition={"category": "A"},
    )

    # Assert
    mock_qdrant_client.search.assert_called_once()
    call_args = mock_qdrant_client.search.call_args[1]
    assert call_args["collection_name"] == "test_collection"
    assert call_args["query_vector"] == [0.1, 0.2, 0.3]
    assert call_args["limit"] == 2
    assert isinstance(call_args["query_filter"], Filter)
    assert len(call_args["query_filter"].must) == 1
    assert isinstance(call_args["query_filter"].must[0], FieldCondition)
    assert call_args["query_filter"].must[0].key == "category"
    assert isinstance(call_args["query_filter"].must[0].match, MatchValue)
    assert call_args["query_filter"].must[0].match.value == "A"

    assert len(results) == 1
    assert results[0]["id"] == 1
    assert results[0]["score"] == 0.9
    assert results[0]["payload"] == {"text": "test1", "category": "A"}


def test_delete_points(vector_store, mock_qdrant_client):
    """Test deleting points."""
    # Execute
    vector_store.delete_points([1, 2, 3])

    # Assert
    mock_qdrant_client.delete.assert_called_once_with(
        collection_name="test_collection",
        points_selector=[1, 2, 3],
    )


def test_get_collection_info(vector_store, mock_qdrant_client):
    """Test getting collection info."""
    # Setup
    mock_collection_info = MagicMock()
    mock_collection_info.config = MagicMock()
    mock_collection_info.config.params = MagicMock()
    mock_collection_info.config.params.vectors = MagicMock()
    mock_collection_info.config.params.vectors.size = 768
    mock_collection_info.config.params.vectors.distance = Distance.COSINE
    mock_collection_info.vectors_count = 100

    mock_qdrant_client.get_collection.return_value = mock_collection_info

    # Execute
    info = vector_store.get_collection_info()

    # Assert
    mock_qdrant_client.get_collection.assert_called_once_with("test_collection")
    assert info["dimensions"] == 768
    assert info["distance"] == Distance.COSINE
    assert info["vectors_count"] == 100
