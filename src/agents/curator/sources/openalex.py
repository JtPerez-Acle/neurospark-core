"""OpenAlex document source implementation for the Curator Agent.

This module provides the OpenAlexSource class for discovering academic papers
from the OpenAlex API.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.agents.curator.sources.base import DocumentSource, SourceConfig

logger = logging.getLogger(__name__)


class OpenAlexSource(DocumentSource):
    """OpenAlex document source for discovering academic papers."""

    def __init__(self, config: SourceConfig):
        """Initialize the OpenAlex document source.

        Args:
            config: Configuration for the document source.
        """
        super().__init__(config)
        self.api_key = config.credentials.get("api_key") if config.credentials else None
        self.base_url = "https://api.openalex.org/works"

    async def discover(self) -> List[Dict[str, Any]]:
        """Discover documents from OpenAlex.

        Returns:
            List of discovered documents.
        """
        logger.info("Discovering documents from OpenAlex")

        # Extract topics and date range
        topics = self._extract_topics()
        date_range = self._parse_date_range(self.config.filters.get("date_range", "last_week"))

        # Format date range for OpenAlex API
        from_date = date_range["start_date"].strftime("%Y-%m-%d")
        to_date = date_range["end_date"].strftime("%Y-%m-%d")

        # Build query parameters
        params = {
            "filter": f"publication_date:{from_date}:{to_date}",
            "search": " OR ".join(topics),
            "sort": "relevance_score:desc",
            "per_page": 25,
        }

        # Add API key if available
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json() if callable(response.json) else await response.json()

        # Process results
        documents = []
        for result in data.get("results", []):
            try:
                # Extract document data
                doc_id = result.get("id")
                title = result.get("title")
                abstract = result.get("abstract") or "No abstract available."
                doi = result.get("doi")
                publication_date = result.get("publication_date")

                # Extract authors
                authors = []
                for authorship in result.get("authorships", []):
                    author = authorship.get("author", {})
                    authors.append(author.get("display_name"))

                # Extract URL
                url = result.get("primary_location", {}).get("landing_page_url")
                if not url:
                    continue

                # Create document
                document = {
                    "title": title,
                    "source_url": url,
                    "source_type": "openalex",
                    "content": abstract,
                    "metadata": {
                        "id": doc_id,
                        "doi": doi,
                        "author": ", ".join(authors),
                        "published_date": publication_date,
                        "topics": topics,
                    }
                }

                documents.append(document)
            except Exception as e:
                logger.exception(f"Error processing OpenAlex result: {e}")

        logger.info(f"Discovered {len(documents)} documents from OpenAlex")
        return documents
