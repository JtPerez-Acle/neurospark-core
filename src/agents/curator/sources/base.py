"""Base document source implementation for the Curator Agent.

This module provides the base DocumentSource class that all document sources
should inherit from.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SourceConfig(BaseModel):
    """Configuration for a document source."""

    type: str = Field(..., description="Type of document source")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters for the source")
    credentials: Optional[Dict[str, str]] = Field(None, description="Credentials for the source")


class DocumentSource(ABC):
    """Base class for document sources.
    
    All document sources should inherit from this class and implement the discover method.
    """

    def __init__(self, config: SourceConfig):
        """Initialize the document source.
        
        Args:
            config: Configuration for the document source.
        """
        self.config = config
    
    @abstractmethod
    async def discover(self) -> List[Dict[str, Any]]:
        """Discover documents from the source.
        
        Returns:
            List of discovered documents. Each document should have the following fields:
            - title: The title of the document
            - source_url: The URL of the document
            - source_type: The type of source (e.g., "openalex", "newsapi", "serpapi")
            - content: The content of the document
            - metadata: Additional metadata for the document
        """
        pass
    
    def _parse_date_range(self, date_range: str) -> Dict[str, datetime]:
        """Parse a date range string into start and end dates.
        
        Args:
            date_range: Date range string (e.g., "last_day", "last_week", "last_month", "last_year")
            
        Returns:
            Dictionary with start_date and end_date.
        """
        now = datetime.utcnow()
        
        if date_range == "last_day":
            start_date = now - timedelta(days=1)
        elif date_range == "last_week":
            start_date = now - timedelta(weeks=1)
        elif date_range == "last_month":
            start_date = now - timedelta(days=30)
        elif date_range == "last_year":
            start_date = now - timedelta(days=365)
        else:
            # Default to last week
            start_date = now - timedelta(weeks=1)
        
        return {
            "start_date": start_date,
            "end_date": now
        }
    
    def _extract_topics(self) -> List[str]:
        """Extract topics from the source configuration.
        
        Returns:
            List of topics.
        """
        return self.config.filters.get("topics", [])
