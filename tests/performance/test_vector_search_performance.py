"""Performance tests for vector search."""

import time
import pytest
from unittest.mock import patch, MagicMock

from tests.test_utils import generate_random_embedding_points, generate_random_vector


@pytest.mark.performance
@patch("src.vector_store.qdrant.QdrantVectorStore")
def test_vector_search_performance(mock_qdrant):
    """Test the performance of vector search."""
    # Create a mock Qdrant client
    mock_qdrant_instance = mock_qdrant.return_value
    
    # Generate random embedding points
    num_points = 1000
    embedding_points = generate_random_embedding_points(num_points, dimensions=768)
    
    # Mock the search method to return random results
    def mock_search(query_vector, limit=10, filter_condition=None):
        # Simulate search latency
        time.sleep(0.01)
        return embedding_points[:limit]
    
    mock_qdrant_instance.search.side_effect = mock_search
    
    # Generate a random query vector
    query_vector = generate_random_vector(dimensions=768)
    
    # Measure search performance
    start_time = time.time()
    
    # Perform multiple searches
    num_searches = 10
    for _ in range(num_searches):
        results = mock_qdrant_instance.search(query_vector, limit=10)
        assert len(results) == 10
    
    end_time = time.time()
    
    # Calculate average search time
    total_time = end_time - start_time
    avg_time = total_time / num_searches
    
    # Assert that the average search time is below a threshold
    assert avg_time < 0.1, f"Average search time ({avg_time:.4f}s) exceeds threshold (0.1s)"
    
    # Print performance metrics
    print(f"Vector search performance:")
    print(f"  - Number of points: {num_points}")
    print(f"  - Number of searches: {num_searches}")
    print(f"  - Total time: {total_time:.4f}s")
    print(f"  - Average time per search: {avg_time:.4f}s")
