"""Qdrant vector store implementation."""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    CollectionInfo,
)

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Qdrant vector store implementation."""
    
    def __init__(
        self,
        collection_name: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        url: Optional[str] = None,
        in_memory: bool = False,
        api_key: Optional[str] = None,
    ):
        """Initialize the Qdrant vector store.
        
        Args:
            collection_name: The name of the collection.
            host: The host of the Qdrant server.
            port: The port of the Qdrant server.
            url: The URL of the Qdrant server.
            in_memory: Whether to use in-memory storage.
            api_key: The API key for Qdrant Cloud.
        """
        self.collection_name = collection_name
        
        if in_memory:
            self.client = QdrantClient(":memory:")
        elif url:
            self.client = QdrantClient(url=url, api_key=api_key)
        else:
            self.client = QdrantClient(host=host, port=port, api_key=api_key)
    
    def create_collection(
        self,
        dimensions: int,
        distance: Distance = Distance.COSINE,
        recreate_if_exists: bool = False,
    ) -> None:
        """Create a collection.
        
        Args:
            dimensions: The dimensions of the vectors.
            distance: The distance metric to use.
            recreate_if_exists: Whether to recreate the collection if it already exists.
        """
        if self.client.collection_exists(self.collection_name):
            if recreate_if_exists:
                logger.info(f"Collection {self.collection_name} already exists, recreating")
                self.client.delete_collection(self.collection_name)
            else:
                logger.info(f"Collection {self.collection_name} already exists, skipping creation")
                return
        
        logger.info(f"Creating collection {self.collection_name}")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=dimensions, distance=distance),
        )
    
    def upsert_points(
        self,
        points: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> None:
        """Upsert points into the collection.
        
        Args:
            points: The points to upsert.
            batch_size: The batch size for upserting points.
        """
        logger.info(f"Upserting {len(points)} points into collection {self.collection_name}")
        
        # Convert points to PointStruct objects
        point_structs = [
            PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point.get("payload", {}),
            )
            for point in points
        ]
        
        # Upsert points in batches
        for i in range(0, len(point_structs), batch_size):
            batch = point_structs[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
            )
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter_condition: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: The query vector.
            limit: The maximum number of results to return.
            filter_condition: The filter condition to apply.
            
        Returns:
            A list of search results.
        """
        logger.info(f"Searching in collection {self.collection_name}")
        
        # Create filter if filter_condition is provided
        query_filter = None
        if filter_condition:
            must_conditions = []
            for key, value in filter_condition.items():
                must_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            query_filter = Filter(must=must_conditions)
        
        # Search for similar vectors
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        
        # Convert results to dictionaries
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            }
            for result in results
        ]
    
    def delete_points(self, point_ids: List[Union[str, int]]) -> None:
        """Delete points from the collection.
        
        Args:
            point_ids: The IDs of the points to delete.
        """
        logger.info(f"Deleting {len(point_ids)} points from collection {self.collection_name}")
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids,
        )
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection.
        
        Returns:
            A dictionary containing information about the collection.
        """
        logger.info(f"Getting information about collection {self.collection_name}")
        collection_info = self.client.get_collection(self.collection_name)
        
        return {
            "dimensions": collection_info.config.params.vectors.size,
            "distance": collection_info.config.params.vectors.distance,
            "vectors_count": collection_info.vectors_count,
        }
