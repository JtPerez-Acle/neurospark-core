"""Utility functions for vector operations."""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate the cosine similarity between two vectors.
    
    Args:
        vec1: The first vector.
        vec2: The second vector.
        
    Returns:
        The cosine similarity between the two vectors.
        
    Raises:
        ValueError: If the vectors have different dimensions.
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vectors have different dimensions: {len(vec1)} and {len(vec2)}")
    
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm_vec1 = np.linalg.norm(vec1_np)
    norm_vec2 = np.linalg.norm(vec2_np)
    
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    
    return float(dot_product / (norm_vec1 * norm_vec2))


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate the Euclidean distance between two vectors.
    
    Args:
        vec1: The first vector.
        vec2: The second vector.
        
    Returns:
        The Euclidean distance between the two vectors.
        
    Raises:
        ValueError: If the vectors have different dimensions.
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vectors have different dimensions: {len(vec1)} and {len(vec2)}")
    
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    return float(np.linalg.norm(vec1_np - vec2_np))


def dot_product(vec1: List[float], vec2: List[float]) -> float:
    """Calculate the dot product between two vectors.
    
    Args:
        vec1: The first vector.
        vec2: The second vector.
        
    Returns:
        The dot product between the two vectors.
        
    Raises:
        ValueError: If the vectors have different dimensions.
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vectors have different dimensions: {len(vec1)} and {len(vec2)}")
    
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    return float(np.dot(vec1_np, vec2_np))


def normalize_vector(vec: List[float]) -> List[float]:
    """Normalize a vector to unit length.
    
    Args:
        vec: The vector to normalize.
        
    Returns:
        The normalized vector.
    """
    vec_np = np.array(vec)
    norm = np.linalg.norm(vec_np)
    
    if norm == 0:
        return vec
    
    return (vec_np / norm).tolist()


def average_vectors(vectors: List[List[float]]) -> List[float]:
    """Calculate the average of multiple vectors.
    
    Args:
        vectors: The vectors to average.
        
    Returns:
        The average vector.
        
    Raises:
        ValueError: If the vectors have different dimensions.
    """
    if not vectors:
        raise ValueError("Cannot average empty list of vectors")
    
    # Check if all vectors have the same dimension
    dim = len(vectors[0])
    for i, vec in enumerate(vectors):
        if len(vec) != dim:
            raise ValueError(f"Vector at index {i} has dimension {len(vec)}, expected {dim}")
    
    # Convert to numpy array and calculate average
    vectors_np = np.array(vectors)
    avg_vec = np.mean(vectors_np, axis=0)
    
    return avg_vec.tolist()


def calculate_relevance_score(
    embedding_sim: float,
    citations: int = 0,
    recency_norm: float = 0.0,
    domain_trust: float = 0.0,
) -> float:
    """Calculate the relevance score based on the formula in the PROMPT.
    
    Score = 0.4 * embedding_sim + 0.3 * log10(citations+1) / 5 + 0.2 * recency_norm + 0.1 * domain_trust
    
    Args:
        embedding_sim: The embedding similarity (0.0 to 1.0).
        citations: The number of citations.
        recency_norm: The recency normalized (0.0 to 1.0).
        domain_trust: The domain trust score (0.0 to 1.0).
        
    Returns:
        The relevance score (0.0 to 1.0).
    """
    import math
    
    # Ensure inputs are within valid ranges
    embedding_sim = max(0.0, min(1.0, embedding_sim))
    citations = max(0, citations)
    recency_norm = max(0.0, min(1.0, recency_norm))
    domain_trust = max(0.0, min(1.0, domain_trust))
    
    # Calculate the score
    score = (
        0.4 * embedding_sim
        + 0.3 * math.log10(citations + 1) / 5
        + 0.2 * recency_norm
        + 0.1 * domain_trust
    )
    
    return score
