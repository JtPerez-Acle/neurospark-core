"""Factory for creating document sources.

This module provides a factory function for creating document sources based on
their type.
"""

import logging
from typing import Dict, Type

from src.agents.curator.sources.base import DocumentSource, SourceConfig
from src.agents.curator.sources.openalex import OpenAlexSource
from src.agents.curator.sources.newsapi import NewsAPISource
from src.agents.curator.sources.serpapi import SerpAPISource

logger = logging.getLogger(__name__)

# Registry of document source types
SOURCE_REGISTRY: Dict[str, Type[DocumentSource]] = {
    "openalex": OpenAlexSource,
    "newsapi": NewsAPISource,
    "serpapi": SerpAPISource,
}


def create_source(config: SourceConfig) -> DocumentSource:
    """Create a document source based on its type.
    
    Args:
        config: Configuration for the document source.
        
    Returns:
        A document source instance.
        
    Raises:
        ValueError: If the source type is not supported.
    """
    source_type = config.type
    
    if source_type not in SOURCE_REGISTRY:
        raise ValueError(f"Unsupported document source type: {source_type}")
    
    source_class = SOURCE_REGISTRY[source_type]
    return source_class(config)
