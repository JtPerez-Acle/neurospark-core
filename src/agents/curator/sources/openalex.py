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

        # Extract topics
        topics = self._extract_topics()

        # Build query parameters with a fixed historical date
        # Using a single date instead of a range as per API requirements
        params = {
            "filter": "from_publication_date:2022-01-01",
            "search": " OR ".join(topics),
            "sort": "cited_by_count:desc",
            "per_page": 10,
        }

        # Add polite identification
        if self.api_key:
            params["api_key"] = self.api_key
        else:
            # Use email parameter for polite usage
            params["email"] = "user@example.com"

        try:
            # Make API request
            logger.info(f"Making request to OpenAlex with params: {params}")
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)

                # Check for errors
                if response.status_code != 200:
                    logger.error(f"OpenAlex API error: {response.status_code} - {response.text}")
                    return []

                # Parse response
                data = response.json()

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

        except Exception as e:
            logger.exception(f"Error fetching documents from OpenAlex: {e}")
            return []
