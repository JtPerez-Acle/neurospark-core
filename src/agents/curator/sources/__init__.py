"""Document sources for the Curator Agent.

This package provides document sources for discovering documents from trusted sources
like OpenAlex, NewsAPI, and SerpAPI.
"""

from src.agents.curator.sources.base import DocumentSource, SourceConfig
from src.agents.curator.sources.factory import create_source
from src.agents.curator.sources.openalex import OpenAlexSource
from src.agents.curator.sources.newsapi import NewsAPISource
from src.agents.curator.sources.serpapi import SerpAPISource

__all__ = [
    "DocumentSource",
    "SourceConfig",
    "create_source",
    "OpenAlexSource",
    "NewsAPISource",
    "SerpAPISource",
]
