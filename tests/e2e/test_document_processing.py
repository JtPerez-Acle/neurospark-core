"""End-to-end tests for document processing workflow."""

import pytest
import uuid
from unittest.mock import patch

from tests.test_utils import generate_random_document


@pytest.mark.e2e
@pytest.mark.skip(reason="API endpoints not implemented yet")
@patch("src.vector_store.qdrant.QdrantVectorStore")
@patch("src.search.elastic.ElasticSearch")
@patch("src.storage.minio.MinioStorage")
def test_document_processing_workflow(
    mock_minio, mock_elastic, mock_qdrant, db_session, api_client
):
    """Test the end-to-end document processing workflow."""
    # Create a test document
    document = generate_random_document()
    document_id = str(uuid.uuid4())
    document["id"] = document_id

    # Mock the storage service
    mock_minio_instance = mock_minio.return_value
    mock_minio_instance.upload_object.return_value = None

    # Mock the search service
    mock_elastic_instance = mock_elastic.return_value
    mock_elastic_instance.index_document.return_value = None

    # Mock the vector store service
    mock_qdrant_instance = mock_qdrant.return_value
    mock_qdrant_instance.upsert_points.return_value = None

    # Upload the document
    response = api_client.post("/documents", json=document)
    assert response.status_code == 200
    assert response.json()["id"] == document_id

    # Verify the document was stored in MinIO
    mock_minio_instance.upload_object.assert_called_once()

    # Verify the document was indexed in ElasticSearch
    mock_elastic_instance.index_document.assert_called_once()

    # Verify the document embedding was stored in Qdrant
    mock_qdrant_instance.upsert_points.assert_called_once()

    # Retrieve the document
    response = api_client.get(f"/documents/{document_id}")
    assert response.status_code == 200
    assert response.json()["id"] == document_id
    assert response.json()["title"] == document["title"]

    # Search for the document
    response = api_client.get(f"/documents/search?query={document['title']}")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0

    # Delete the document
    response = api_client.delete(f"/documents/{document_id}")
    assert response.status_code == 204

    # Verify the document was deleted
    response = api_client.get(f"/documents/{document_id}")
    assert response.status_code == 404
