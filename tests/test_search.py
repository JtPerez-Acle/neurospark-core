"""Tests for search module."""

import pytest
from unittest.mock import patch, MagicMock, call
import json

from src.search.elastic import (
    ElasticSearch,
    SearchResult,
    SearchResults,
)


@pytest.fixture
def mock_elasticsearch_client():
    """Create a mock Elasticsearch client."""
    with patch("src.search.elastic.Elasticsearch") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def elastic_search(mock_elasticsearch_client):
    """Create an ElasticSearch instance with a mock client."""
    return ElasticSearch(
        host="localhost",
        port=9200,
        index_name="test_index",
    )


def test_init_with_host_port():
    """Test initializing ElasticSearch with host and port."""
    with patch("src.search.elastic.Elasticsearch") as mock_client_class:
        search = ElasticSearch(
            host="localhost",
            port=9200,
            index_name="test_index",
        )
        
        mock_client_class.assert_called_once_with(
            hosts=[{"host": "localhost", "port": 9200}]
        )
        assert search.index_name == "test_index"


def test_init_with_url():
    """Test initializing ElasticSearch with URL."""
    with patch("src.search.elastic.Elasticsearch") as mock_client_class:
        search = ElasticSearch(
            url="http://localhost:9200",
            index_name="test_index",
        )
        
        mock_client_class.assert_called_once_with(hosts=["http://localhost:9200"])
        assert search.index_name == "test_index"


def test_create_index(elastic_search, mock_elasticsearch_client):
    """Test creating an index."""
    # Setup
    mock_elasticsearch_client.indices.exists.return_value = False
    
    # Execute
    elastic_search.create_index(
        mappings={"properties": {"text": {"type": "text"}}},
        settings={"number_of_shards": 1},
        recreate_if_exists=False,
    )
    
    # Assert
    mock_elasticsearch_client.indices.exists.assert_called_once_with(index="test_index")
    mock_elasticsearch_client.indices.create.assert_called_once_with(
        index="test_index",
        body={
            "mappings": {"properties": {"text": {"type": "text"}}},
            "settings": {"number_of_shards": 1},
        },
    )


def test_create_index_already_exists(elastic_search, mock_elasticsearch_client):
    """Test creating an index that already exists."""
    # Setup
    mock_elasticsearch_client.indices.exists.return_value = True
    
    # Execute
    elastic_search.create_index(
        mappings={"properties": {"text": {"type": "text"}}},
        settings={"number_of_shards": 1},
        recreate_if_exists=False,
    )
    
    # Assert
    mock_elasticsearch_client.indices.exists.assert_called_once_with(index="test_index")
    mock_elasticsearch_client.indices.create.assert_not_called()


def test_create_index_recreate(elastic_search, mock_elasticsearch_client):
    """Test recreating an index that already exists."""
    # Setup
    mock_elasticsearch_client.indices.exists.return_value = True
    
    # Execute
    elastic_search.create_index(
        mappings={"properties": {"text": {"type": "text"}}},
        settings={"number_of_shards": 1},
        recreate_if_exists=True,
    )
    
    # Assert
    mock_elasticsearch_client.indices.exists.assert_called_once_with(index="test_index")
    mock_elasticsearch_client.indices.delete.assert_called_once_with(index="test_index")
    mock_elasticsearch_client.indices.create.assert_called_once_with(
        index="test_index",
        body={
            "mappings": {"properties": {"text": {"type": "text"}}},
            "settings": {"number_of_shards": 1},
        },
    )


def test_index_document(elastic_search, mock_elasticsearch_client):
    """Test indexing a document."""
    # Setup
    document = {
        "id": "doc1",
        "text": "This is a test document.",
        "metadata": {"source": "test"},
    }
    
    # Execute
    elastic_search.index_document(document)
    
    # Assert
    mock_elasticsearch_client.index.assert_called_once_with(
        index="test_index",
        id="doc1",
        body={
            "text": "This is a test document.",
            "metadata": {"source": "test"},
        },
    )


def test_index_documents(elastic_search, mock_elasticsearch_client):
    """Test indexing multiple documents."""
    # Setup
    documents = [
        {
            "id": "doc1",
            "text": "This is the first test document.",
            "metadata": {"source": "test1"},
        },
        {
            "id": "doc2",
            "text": "This is the second test document.",
            "metadata": {"source": "test2"},
        },
    ]
    
    # Execute
    elastic_search.index_documents(documents)
    
    # Assert
    assert mock_elasticsearch_client.bulk.call_count == 1
    bulk_actions = mock_elasticsearch_client.bulk.call_args[1]["body"]
    
    # Check that the bulk actions are correct
    assert len(bulk_actions) == 4  # 2 documents * 2 actions (index action + document)
    assert bulk_actions[0] == {"index": {"_index": "test_index", "_id": "doc1"}}
    assert bulk_actions[1] == {
        "text": "This is the first test document.",
        "metadata": {"source": "test1"},
    }
    assert bulk_actions[2] == {"index": {"_index": "test_index", "_id": "doc2"}}
    assert bulk_actions[3] == {
        "text": "This is the second test document.",
        "metadata": {"source": "test2"},
    }


def test_search(elastic_search, mock_elasticsearch_client):
    """Test searching for documents."""
    # Setup
    mock_response = {
        "took": 5,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": {"value": 2, "relation": "eq"},
            "max_score": 1.0,
            "hits": [
                {
                    "_index": "test_index",
                    "_id": "doc1",
                    "_score": 1.0,
                    "_source": {
                        "text": "This is the first test document.",
                        "metadata": {"source": "test1"},
                    },
                },
                {
                    "_index": "test_index",
                    "_id": "doc2",
                    "_score": 0.8,
                    "_source": {
                        "text": "This is the second test document.",
                        "metadata": {"source": "test2"},
                    },
                },
            ],
        },
    }
    mock_elasticsearch_client.search.return_value = mock_response
    
    # Execute
    results = elastic_search.search(
        query="test document",
        fields=["text"],
        limit=10,
    )
    
    # Assert
    mock_elasticsearch_client.search.assert_called_once_with(
        index="test_index",
        body={
            "query": {
                "multi_match": {
                    "query": "test document",
                    "fields": ["text"],
                    "type": "best_fields",
                }
            },
            "size": 10,
        },
    )
    
    assert isinstance(results, SearchResults)
    assert results.total == 2
    assert len(results.hits) == 2
    
    assert results.hits[0].id == "doc1"
    assert results.hits[0].score == 1.0
    assert results.hits[0].text == "This is the first test document."
    assert results.hits[0].metadata == {"source": "test1"}
    
    assert results.hits[1].id == "doc2"
    assert results.hits[1].score == 0.8
    assert results.hits[1].text == "This is the second test document."
    assert results.hits[1].metadata == {"source": "test2"}


def test_search_with_filter(elastic_search, mock_elasticsearch_client):
    """Test searching with a filter."""
    # Setup
    mock_response = {
        "took": 5,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": {"value": 1, "relation": "eq"},
            "max_score": 1.0,
            "hits": [
                {
                    "_index": "test_index",
                    "_id": "doc1",
                    "_score": 1.0,
                    "_source": {
                        "text": "This is the first test document.",
                        "metadata": {"source": "test1"},
                    },
                },
            ],
        },
    }
    mock_elasticsearch_client.search.return_value = mock_response
    
    # Execute
    results = elastic_search.search(
        query="test document",
        fields=["text"],
        limit=10,
        filter_condition={"metadata.source": "test1"},
    )
    
    # Assert
    mock_elasticsearch_client.search.assert_called_once_with(
        index="test_index",
        body={
            "query": {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": "test document",
                            "fields": ["text"],
                            "type": "best_fields",
                        }
                    },
                    "filter": {"term": {"metadata.source": "test1"}},
                }
            },
            "size": 10,
        },
    )
    
    assert isinstance(results, SearchResults)
    assert results.total == 1
    assert len(results.hits) == 1
    
    assert results.hits[0].id == "doc1"
    assert results.hits[0].score == 1.0
    assert results.hits[0].text == "This is the first test document."
    assert results.hits[0].metadata == {"source": "test1"}


def test_delete_document(elastic_search, mock_elasticsearch_client):
    """Test deleting a document."""
    # Execute
    elastic_search.delete_document("doc1")
    
    # Assert
    mock_elasticsearch_client.delete.assert_called_once_with(
        index="test_index",
        id="doc1",
    )


def test_delete_documents(elastic_search, mock_elasticsearch_client):
    """Test deleting multiple documents."""
    # Execute
    elastic_search.delete_documents(["doc1", "doc2"])
    
    # Assert
    assert mock_elasticsearch_client.bulk.call_count == 1
    bulk_actions = mock_elasticsearch_client.bulk.call_args[1]["body"]
    
    # Check that the bulk actions are correct
    assert len(bulk_actions) == 2  # 2 documents * 1 action (delete action)
    assert bulk_actions[0] == {"delete": {"_index": "test_index", "_id": "doc1"}}
    assert bulk_actions[1] == {"delete": {"_index": "test_index", "_id": "doc2"}}
