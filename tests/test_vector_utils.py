"""Tests for vector utility functions."""

import pytest
import numpy as np
import math
from typing import List

from src.vector_store.utils import (
    cosine_similarity,
    euclidean_distance,
    dot_product,
    normalize_vector,
    average_vectors,
    calculate_relevance_score,
)


def test_cosine_similarity():
    """Test cosine similarity calculation."""
    # Test with orthogonal vectors (should be 0)
    vec1 = [1, 0, 0]
    vec2 = [0, 1, 0]
    assert cosine_similarity(vec1, vec2) == 0.0
    
    # Test with parallel vectors (should be 1)
    vec1 = [1, 2, 3]
    vec2 = [2, 4, 6]
    assert cosine_similarity(vec1, vec2) == 1.0
    
    # Test with opposite vectors (should be -1)
    vec1 = [1, 2, 3]
    vec2 = [-1, -2, -3]
    assert cosine_similarity(vec1, vec2) == -1.0
    
    # Test with arbitrary vectors
    vec1 = [1, 2, 3]
    vec2 = [4, 5, 6]
    expected = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    assert cosine_similarity(vec1, vec2) == pytest.approx(expected)
    
    # Test with zero vector
    vec1 = [0, 0, 0]
    vec2 = [1, 2, 3]
    assert cosine_similarity(vec1, vec2) == 0.0
    
    # Test with different dimensions
    vec1 = [1, 2, 3]
    vec2 = [1, 2]
    with pytest.raises(ValueError):
        cosine_similarity(vec1, vec2)


def test_euclidean_distance():
    """Test Euclidean distance calculation."""
    # Test with same vectors (should be 0)
    vec1 = [1, 2, 3]
    vec2 = [1, 2, 3]
    assert euclidean_distance(vec1, vec2) == 0.0
    
    # Test with unit vectors
    vec1 = [1, 0, 0]
    vec2 = [0, 1, 0]
    assert euclidean_distance(vec1, vec2) == pytest.approx(math.sqrt(2))
    
    # Test with arbitrary vectors
    vec1 = [1, 2, 3]
    vec2 = [4, 5, 6]
    expected = np.linalg.norm(np.array(vec1) - np.array(vec2))
    assert euclidean_distance(vec1, vec2) == pytest.approx(expected)
    
    # Test with different dimensions
    vec1 = [1, 2, 3]
    vec2 = [1, 2]
    with pytest.raises(ValueError):
        euclidean_distance(vec1, vec2)


def test_dot_product():
    """Test dot product calculation."""
    # Test with orthogonal vectors (should be 0)
    vec1 = [1, 0, 0]
    vec2 = [0, 1, 0]
    assert dot_product(vec1, vec2) == 0.0
    
    # Test with arbitrary vectors
    vec1 = [1, 2, 3]
    vec2 = [4, 5, 6]
    expected = 1*4 + 2*5 + 3*6
    assert dot_product(vec1, vec2) == expected
    
    # Test with different dimensions
    vec1 = [1, 2, 3]
    vec2 = [1, 2]
    with pytest.raises(ValueError):
        dot_product(vec1, vec2)


def test_normalize_vector():
    """Test vector normalization."""
    # Test with unit vector (should remain unchanged)
    vec = [1, 0, 0]
    assert normalize_vector(vec) == vec
    
    # Test with arbitrary vector
    vec = [3, 4, 0]
    expected = [3/5, 4/5, 0]
    assert normalize_vector(vec) == pytest.approx(expected)
    
    # Test with zero vector (should remain unchanged)
    vec = [0, 0, 0]
    assert normalize_vector(vec) == vec


def test_average_vectors():
    """Test vector averaging."""
    # Test with single vector
    vectors = [[1, 2, 3]]
    assert average_vectors(vectors) == [1, 2, 3]
    
    # Test with multiple vectors
    vectors = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    expected = [4, 5, 6]
    assert average_vectors(vectors) == expected
    
    # Test with empty list
    with pytest.raises(ValueError):
        average_vectors([])
    
    # Test with vectors of different dimensions
    vectors = [[1, 2, 3], [4, 5]]
    with pytest.raises(ValueError):
        average_vectors(vectors)


def test_calculate_relevance_score():
    """Test relevance score calculation."""
    # Test with all zeros
    assert calculate_relevance_score(0.0, 0, 0.0, 0.0) == 0.0
    
    # Test with all ones
    expected = 0.4 + 0.3 * math.log10(2) / 5 + 0.2 + 0.1
    assert calculate_relevance_score(1.0, 1, 1.0, 1.0) == pytest.approx(expected)
    
    # Test with embedding_sim only
    assert calculate_relevance_score(0.5, 0, 0.0, 0.0) == pytest.approx(0.2)
    
    # Test with citations only
    expected = 0.3 * math.log10(11) / 5
    assert calculate_relevance_score(0.0, 10, 0.0, 0.0) == pytest.approx(expected)
    
    # Test with recency_norm only
    assert calculate_relevance_score(0.0, 0, 0.5, 0.0) == pytest.approx(0.1)
    
    # Test with domain_trust only
    assert calculate_relevance_score(0.0, 0, 0.0, 0.5) == pytest.approx(0.05)
    
    # Test with values out of range (should be clamped)
    assert calculate_relevance_score(1.5, -5, 1.5, -0.5) == calculate_relevance_score(1.0, 0, 1.0, 0.0)
