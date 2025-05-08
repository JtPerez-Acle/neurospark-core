"""SerpAPI document source implementation for the Curator Agent.

This module provides the SerpAPISource class for discovering web search results
from the SerpAPI.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import trafilatura

from src.agents.curator.sources.base import DocumentSource, SourceConfig

logger = logging.getLogger(__name__)


class SerpAPISource(DocumentSource):
    """SerpAPI document source for discovering web search results."""

    def __init__(self, config: SourceConfig):
        """Initialize the SerpAPI document source.

        Args:
            config: Configuration for the document source.
        """
        super().__init__(config)
        self.api_key = config.credentials.get("api_key") if config.credentials else None
        self.base_url = "https://serpapi.com/search"

    async def discover(self) -> List[Dict[str, Any]]:
        """Discover documents from SerpAPI.

        Returns:
            List of discovered documents.
        """
        logger.info("Discovering documents from SerpAPI")

        # Check if API key is available
        if not self.api_key:
            logger.warning("SerpAPI API key not provided")
            return []

        # Extract topics and date range
        topics = self._extract_topics()
        date_range = self._parse_date_range(self.config.filters.get("date_range", "last_week"))

        # Format date range for SerpAPI
        time_period = "d"  # Default to last day
        if date_range["start_date"] < datetime.utcnow() - timedelta(days=7):
            time_period = "w"  # Last week
        if date_range["start_date"] < datetime.utcnow() - timedelta(days=30):
            time_period = "m"  # Last month
        if date_range["start_date"] < datetime.utcnow() - timedelta(days=365):
            time_period = "y"  # Last year

        documents = []

        # Process each topic
        for topic in topics:
            try:
                # Build query parameters
                params = {
                    "q": topic,
                    "engine": "google",
                    "google_domain": "google.com",
                    "gl": "us",
                    "hl": "en",
                    "tbm": "nws" if "news" in topic.lower() else "",
                    "tbs": f"qdr:{time_period}" if time_period else "",
                    "num": 10,
                    "api_key": self.api_key,
                }

                # Make API request
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    data = response.json() if callable(response.json) else await response.json()

                # Process organic results
                for result in data.get("organic_results", []):
                    try:
                        # Extract document data
                        title = result.get("title")
                        url = result.get("link")
                        snippet = result.get("snippet")

                        # Skip if missing required fields
                        if not title or not url:
                            continue

                        # Fetch full content
                        content = await self._fetch_content(url)
                        if not content:
                            content = snippet or "No content available."

                        # Create document
                        document = {
                            "title": title,
                            "source_url": url,
                            "source_type": "serpapi",
                            "content": content,
                            "metadata": {
                                "topic": topic,
                                "snippet": snippet,
                                "position": result.get("position"),
                                "discovered_date": datetime.utcnow().isoformat(),
                            }
                        }

                        documents.append(document)
                    except Exception as e:
                        logger.exception(f"Error processing SerpAPI result: {e}")
            except Exception as e:
                logger.exception(f"Error querying SerpAPI for topic '{topic}': {e}")

        logger.info(f"Discovered {len(documents)} documents from SerpAPI")
        return documents

    async def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch and extract content from a URL.

        Args:
            url: URL to fetch content from.

        Returns:
            Extracted content or None if extraction failed.
        """
        try:
            # Fetch URL content
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()
                html = response.text if isinstance(response.text, str) else await response.text

            # Extract content using trafilatura
            content = trafilatura.extract(html)

            return content
        except Exception as e:
            logger.warning(f"Error fetching content from {url}: {e}")
            return None
