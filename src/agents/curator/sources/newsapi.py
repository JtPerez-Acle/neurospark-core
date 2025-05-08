"""NewsAPI document source implementation for the Curator Agent.

This module provides the NewsAPISource class for discovering news articles
from the NewsAPI.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.agents.curator.sources.base import DocumentSource, SourceConfig

logger = logging.getLogger(__name__)


class NewsAPISource(DocumentSource):
    """NewsAPI document source for discovering news articles."""

    def __init__(self, config: SourceConfig):
        """Initialize the NewsAPI document source.

        Args:
            config: Configuration for the document source.
        """
        super().__init__(config)
        self.api_key = config.credentials.get("api_key") if config.credentials else None
        self.base_url = "https://newsapi.org/v2/everything"

    async def discover(self) -> List[Dict[str, Any]]:
        """Discover documents from NewsAPI.

        Returns:
            List of discovered documents.
        """
        logger.info("Discovering documents from NewsAPI")

        # Check if API key is available
        if not self.api_key:
            logger.warning("NewsAPI API key not provided")
            return []

        # Extract topics and date range
        topics = self._extract_topics()
        date_range = self._parse_date_range(self.config.filters.get("date_range", "last_week"))

        # Format date range for NewsAPI
        from_date = date_range["start_date"].strftime("%Y-%m-%d")
        to_date = date_range["end_date"].strftime("%Y-%m-%d")

        # Build query parameters
        params = {
            "q": " OR ".join(topics),
            "from": from_date,
            "to": to_date,
            "sortBy": "relevancy",
            "pageSize": 25,
            "apiKey": self.api_key,
        }

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json() if callable(response.json) else await response.json()

        # Check if request was successful
        if data.get("status") != "ok":
            logger.error(f"NewsAPI request failed: {data.get('message')}")
            return []

        # Process results
        documents = []
        for article in data.get("articles", []):
            try:
                # Extract document data
                title = article.get("title")
                url = article.get("url")
                content = article.get("content") or article.get("description") or "No content available."
                published_at = article.get("publishedAt")
                author = article.get("author")
                source_name = article.get("source", {}).get("name")

                # Skip if missing required fields
                if not title or not url:
                    continue

                # Create document
                document = {
                    "title": title,
                    "source_url": url,
                    "source_type": "newsapi",
                    "content": content,
                    "metadata": {
                        "author": author,
                        "source_name": source_name,
                        "published_date": published_at,
                        "topics": topics,
                        "image_url": article.get("urlToImage"),
                    }
                }

                documents.append(document)
            except Exception as e:
                logger.exception(f"Error processing NewsAPI article: {e}")

        logger.info(f"Discovered {len(documents)} documents from NewsAPI")
        return documents
