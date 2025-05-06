"""Vector Store module for NeuroSpark Core.

This module contains the vector database interface for Qdrant.
"""

from src.vector_store.qdrant import QdrantVectorStore, Distance
from src.vector_store.utils import (
    cosine_similarity,
    euclidean_distance,
    dot_product,
    normalize_vector,
    average_vectors,
    calculate_relevance_score,
)
