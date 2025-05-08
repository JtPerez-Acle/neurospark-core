"""Curator Agent module.

The Curator Agent is responsible for discovering documents from trusted sources
like OpenAlex, NewsAPI, and SerpAPI.
"""

from src.agents.curator.agent import CuratorAgent, CuratorAgentConfig
from src.agents.curator.sources import (
    DocumentSource,
    SourceConfig,
    create_source,
    OpenAlexSource,
    NewsAPISource,
    SerpAPISource,
)

__all__ = [
    "CuratorAgent",
    "CuratorAgentConfig",
    "DocumentSource",
    "SourceConfig",
    "create_source",
    "OpenAlexSource",
    "NewsAPISource",
    "SerpAPISource",
]
