"""ElasticLite search implementation."""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result model."""
    
    id: str
    score: float
    text: str
    metadata: Dict[str, Any]


@dataclass
class SearchResults:
    """Search results model."""
    
    total: int
    hits: List[SearchResult]


class ElasticSearch:
    """ElasticLite search implementation."""
    
    def __init__(
        self,
        index_name: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize the ElasticLite search.
        
        Args:
            index_name: The name of the index.
            host: The host of the ElasticLite server.
            port: The port of the ElasticLite server.
            url: The URL of the ElasticLite server.
            username: The username for authentication.
            password: The password for authentication.
        """
        self.index_name = index_name
        
        if url:
            self.client = Elasticsearch(hosts=[url])
        else:
            self.client = Elasticsearch(
                hosts=[{"host": host, "port": port}],
            )
    
    def create_index(
        self,
        mappings: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
        recreate_if_exists: bool = False,
    ) -> None:
        """Create an index.
        
        Args:
            mappings: The mappings for the index.
            settings: The settings for the index.
            recreate_if_exists: Whether to recreate the index if it already exists.
        """
        if self.client.indices.exists(index=self.index_name):
            if recreate_if_exists:
                logger.info(f"Index {self.index_name} already exists, recreating")
                self.client.indices.delete(index=self.index_name)
            else:
                logger.info(f"Index {self.index_name} already exists, skipping creation")
                return
        
        logger.info(f"Creating index {self.index_name}")
        self.client.indices.create(
            index=self.index_name,
            body={
                "mappings": mappings,
                "settings": settings or {},
            },
        )
    
    def index_document(self, document: Dict[str, Any]) -> None:
        """Index a document.
        
        Args:
            document: The document to index.
        """
        logger.info(f"Indexing document {document.get('id')} into index {self.index_name}")
        
        # Extract the ID from the document
        doc_id = document.pop("id")
        
        # Index the document
        self.client.index(
            index=self.index_name,
            id=doc_id,
            body=document,
        )
    
    def index_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100) -> None:
        """Index multiple documents.
        
        Args:
            documents: The documents to index.
            batch_size: The batch size for indexing documents.
        """
        logger.info(f"Indexing {len(documents)} documents into index {self.index_name}")
        
        # Prepare bulk actions
        bulk_actions = []
        for document in documents:
            # Extract the ID from the document
            doc_id = document.pop("id")
            
            # Add the index action
            bulk_actions.append({"index": {"_index": self.index_name, "_id": doc_id}})
            
            # Add the document
            bulk_actions.append(document)
        
        # Execute bulk indexing
        if bulk_actions:
            self.client.bulk(body=bulk_actions)
    
    def search(
        self,
        query: str,
        fields: List[str],
        limit: int = 10,
        filter_condition: Optional[Dict[str, Any]] = None,
    ) -> SearchResults:
        """Search for documents.
        
        Args:
            query: The search query.
            fields: The fields to search in.
            limit: The maximum number of results to return.
            filter_condition: The filter condition to apply.
            
        Returns:
            The search results.
        """
        logger.info(f"Searching in index {self.index_name}")
        
        # Prepare the search query
        search_query = {
            "multi_match": {
                "query": query,
                "fields": fields,
                "type": "best_fields",
            }
        }
        
        # Add filter if provided
        if filter_condition:
            search_body = {
                "query": {
                    "bool": {
                        "must": search_query,
                        "filter": {"term": filter_condition},
                    }
                },
                "size": limit,
            }
        else:
            search_body = {
                "query": search_query,
                "size": limit,
            }
        
        # Execute the search
        response = self.client.search(
            index=self.index_name,
            body=search_body,
        )
        
        # Process the search results
        total = response["hits"]["total"]["value"]
        hits = []
        
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            text = source.get("text", "")
            metadata = source.get("metadata", {})
            
            hits.append(
                SearchResult(
                    id=hit["_id"],
                    score=hit["_score"],
                    text=text,
                    metadata=metadata,
                )
            )
        
        return SearchResults(total=total, hits=hits)
    
    def delete_document(self, doc_id: str) -> None:
        """Delete a document.
        
        Args:
            doc_id: The ID of the document to delete.
        """
        logger.info(f"Deleting document {doc_id} from index {self.index_name}")
        self.client.delete(
            index=self.index_name,
            id=doc_id,
        )
    
    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete multiple documents.
        
        Args:
            doc_ids: The IDs of the documents to delete.
        """
        logger.info(f"Deleting {len(doc_ids)} documents from index {self.index_name}")
        
        # Prepare bulk actions
        bulk_actions = []
        for doc_id in doc_ids:
            # Add the delete action
            bulk_actions.append({"delete": {"_index": self.index_name, "_id": doc_id}})
        
        # Execute bulk deletion
        if bulk_actions:
            self.client.bulk(body=bulk_actions)
