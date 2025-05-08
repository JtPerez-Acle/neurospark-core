"""Tests for the Curator Agent document sources."""

import asyncio
import json
import os
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Mock modules
import sys
from unittest.mock import MagicMock

# Mock pydantic_ai module
class MockPydanticAgent:
    def __init__(self, *args, **kwargs):
        pass

class MockRunContext:
    def __init__(self, *args, **kwargs):
        pass

mock_pydantic_ai = MagicMock()
mock_pydantic_ai.Agent = MockPydanticAgent
mock_pydantic_ai.RunContext = MockRunContext
sys.modules['pydantic_ai'] = mock_pydantic_ai

# Mock Settings class
class MockSettings:
    def __init__(self, **kwargs):
        self.redis_url = kwargs.get('redis_url', 'redis://localhost:6379/0')
        self.config_dir = '/tmp'
        self.agent_settings = MagicMock()
        self.agent_settings.curator_poll_interval = 3600
        self.external_api_settings = MagicMock()
        self.external_api_settings.openalex_api_key = None
        self.external_api_settings.newsapi_api_key = None
        self.external_api_settings.serpapi_api_key = None

# Patch the Settings import
sys.modules['src.common.config'] = MagicMock()
sys.modules['src.common.config'].Settings = MockSettings

# Mock Redis
mock_redis = MagicMock()
mock_redis.asyncio = MagicMock()
sys.modules['redis'] = mock_redis

# Mock RedisStreamClient
class MockRedisStreamClient:
    """Mock Redis client for testing."""

    def __init__(self, url: str):
        """Initialize the mock Redis client.

        Args:
            url: Redis URL.
        """
        self.url = url
        self.messages = {}
        self.subscriptions = set()
        self.connected = False
        self.message_queue = asyncio.Queue()

    async def connect(self) -> None:
        """Connect to Redis."""
        self.connected = True

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self.connected = False

    async def publish_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Publish a message to a topic.

        Args:
            topic: Topic to publish to.
            message: Message to publish.
        """
        if not self.connected:
            raise RuntimeError("Not connected to Redis")

        if topic not in self.messages:
            self.messages[topic] = []

        self.messages[topic].append(message)

        # Add message to queue if subscribed
        if topic in self.subscriptions:
            await self.message_queue.put({
                "topic": topic,
                "message": message,
            })

    async def subscribe(self, topic: str) -> None:
        """Subscribe to a topic.

        Args:
            topic: Topic to subscribe to.
        """
        if not self.connected:
            raise RuntimeError("Not connected to Redis")

        self.subscriptions.add(topic)

    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from.
        """
        if not self.connected:
            raise RuntimeError("Not connected to Redis")

        if topic in self.subscriptions:
            self.subscriptions.remove(topic)

    async def get_message(self) -> Optional[Dict[str, Any]]:
        """Get a message from subscribed topics.

        Returns:
            Message or None if no message is available.
        """
        if not self.connected:
            raise RuntimeError("Not connected to Redis")

        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

    def get_messages(self, topic: str) -> List[Dict[str, Any]]:
        """Get all messages for a topic.

        Args:
            topic: Topic to get messages for.

        Returns:
            List of messages.
        """
        return self.messages.get(topic, [])

# Mock RedisMessageBus
class MockRedisMessageBus:
    """Mock Redis message bus for testing."""

    def __init__(self, url: str):
        """Initialize the mock Redis message bus.

        Args:
            url: Redis URL.
        """
        self.url = url
        self.messages = {}
        self.subscriptions = set()
        self.connected = False
        self.message_queue = asyncio.Queue()

    async def connect(self) -> None:
        """Connect to Redis."""
        self.connected = True

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self.connected = False

    async def publish(self, topic: str, message: Dict[str, Any]) -> None:
        """Publish a message to a topic.

        Args:
            topic: Topic to publish to.
            message: Message to publish.
        """
        if not self.connected:
            raise RuntimeError("Not connected to Redis")

        if topic not in self.messages:
            self.messages[topic] = []

        self.messages[topic].append(message)

        # Add message to queue if subscribed
        if topic in self.subscriptions:
            await self.message_queue.put({
                "topic": topic,
                "message": message,
            })

    async def subscribe(self, topic: str) -> None:
        """Subscribe to a topic.

        Args:
            topic: Topic to subscribe to.
        """
        if not self.connected:
            raise RuntimeError("Not connected to Redis")

        self.subscriptions.add(topic)

    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from.
        """
        if not self.connected:
            raise RuntimeError("Not connected to Redis")

        if topic in self.subscriptions:
            self.subscriptions.remove(topic)

    async def get_message(self) -> Optional[Dict[str, Any]]:
        """Get a message from subscribed topics.

        Returns:
            Message or None if no message is available.
        """
        if not self.connected:
            raise RuntimeError("Not connected to Redis")

        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

# Mock Message class
class MockMessage:
    """Mock message for testing."""

    def __init__(self, topic: str, payload: Dict[str, Any]):
        """Initialize the mock message.

        Args:
            topic: Message topic.
            payload: Message payload.
        """
        self.topic = topic
        self.payload = payload

# Mock StreamConfig class
class MockStreamConfig:
    """Mock stream configuration for testing."""

    def __init__(self, stream_name: str, consumer_group: str, consumer_name: str):
        """Initialize the mock stream configuration.

        Args:
            stream_name: Stream name.
            consumer_group: Consumer group name.
            consumer_name: Consumer name.
        """
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name

# Patch the redis_streams module
sys.modules['src.message_bus.redis_streams'] = MagicMock()
sys.modules['src.message_bus.redis_streams'].RedisStreamClient = MockRedisStreamClient
sys.modules['src.message_bus.redis_streams'].RedisMessageBus = MockRedisMessageBus
sys.modules['src.message_bus.redis_streams'].Message = MockMessage
sys.modules['src.message_bus.redis_streams'].StreamConfig = MockStreamConfig

from src.agents.curator.sources.base import DocumentSource, SourceConfig
from src.agents.curator.sources.openalex import OpenAlexSource
from src.agents.curator.sources.newsapi import NewsAPISource
from src.agents.curator.sources.serpapi import SerpAPISource


@pytest.fixture
def openalex_config():
    """Create an OpenAlex source configuration."""
    return SourceConfig(
        type="openalex",
        filters={
            "topics": ["machine learning", "artificial intelligence"],
            "date_range": "last_month"
        }
    )


@pytest.fixture
def newsapi_config():
    """Create a NewsAPI source configuration."""
    return SourceConfig(
        type="newsapi",
        filters={
            "topics": ["technology", "science"],
            "date_range": "last_week"
        }
    )


@pytest.fixture
def serpapi_config():
    """Create a SerpAPI source configuration."""
    return SourceConfig(
        type="serpapi",
        filters={
            "topics": ["machine learning tutorial", "AI news"],
            "date_range": "last_day"
        }
    )


@pytest.mark.asyncio
async def test_openalex_source_initialization(openalex_config):
    """Test OpenAlex source initialization."""
    source = OpenAlexSource(openalex_config)

    # Check source properties
    assert source.config.type == "openalex"
    assert "machine learning" in source.config.filters["topics"]
    assert source.config.filters["date_range"] == "last_month"


@pytest.mark.asyncio
async def test_newsapi_source_initialization(newsapi_config):
    """Test NewsAPI source initialization."""
    source = NewsAPISource(newsapi_config)

    # Check source properties
    assert source.config.type == "newsapi"
    assert "technology" in source.config.filters["topics"]
    assert source.config.filters["date_range"] == "last_week"


@pytest.mark.asyncio
async def test_serpapi_source_initialization(serpapi_config):
    """Test SerpAPI source initialization."""
    source = SerpAPISource(serpapi_config)

    # Check source properties
    assert source.config.type == "serpapi"
    assert "machine learning tutorial" in source.config.filters["topics"]
    assert source.config.filters["date_range"] == "last_day"


@pytest.mark.asyncio
async def test_openalex_source_discover(openalex_config):
    """Test OpenAlex source document discovery."""
    # Mock the OpenAlex API response
    api_response = {
        "results": [
            {
                "id": "W1",
                "title": "Machine Learning Paper",
                "doi": "10.1234/5678",
                "publication_date": "2023-01-01",
                "abstract": "This is a paper about machine learning.",
                "authorships": [
                    {
                        "author": {
                            "display_name": "John Doe"
                        }
                    }
                ],
                "primary_location": {
                    "landing_page_url": "https://example.com/paper1"
                }
            },
            {
                "id": "W2",
                "title": "Artificial Intelligence Paper",
                "doi": "10.5678/1234",
                "publication_date": "2023-01-02",
                "abstract": "This is a paper about artificial intelligence.",
                "authorships": [
                    {
                        "author": {
                            "display_name": "Jane Smith"
                        }
                    }
                ],
                "primary_location": {
                    "landing_page_url": "https://example.com/paper2"
                }
            }
        ]
    }

    # Create a mock response
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=api_response)
    mock_response.raise_for_status = MagicMock()

    # Create a mock client
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    # Add API key to the config
    openalex_config.credentials = {"api_key": "test_api_key"}

    # Patch the httpx.AsyncClient
    with patch("httpx.AsyncClient", return_value=mock_client):
        # Patch the _parse_date_range method to return a fixed date range
        with patch.object(OpenAlexSource, '_parse_date_range', return_value={
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 1, 31)
        }):
            source = OpenAlexSource(openalex_config)
            documents = await source.discover()

    # Check that documents were discovered
    assert len(documents) == 2
    assert documents[0]["title"] == "Machine Learning Paper"
    assert documents[0]["source_type"] == "openalex"
    assert documents[0]["source_url"] == "https://example.com/paper1"
    assert documents[0]["content"] == "This is a paper about machine learning."
    assert documents[0]["metadata"]["author"] == "John Doe"
    assert documents[0]["metadata"]["doi"] == "10.1234/5678"
    assert documents[0]["metadata"]["published_date"] == "2023-01-01"


@pytest.mark.asyncio
async def test_newsapi_source_discover(newsapi_config):
    """Test NewsAPI source document discovery."""
    # Mock the NewsAPI response
    api_response = {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "source": {
                    "id": "source1",
                    "name": "Tech News"
                },
                "author": "John Doe",
                "title": "Technology Article",
                "description": "This is an article about technology.",
                "url": "https://example.com/article1",
                "urlToImage": "https://example.com/image1.jpg",
                "publishedAt": "2023-01-01T12:00:00Z",
                "content": "This is the content of the technology article."
            },
            {
                "source": {
                    "id": "source2",
                    "name": "Science News"
                },
                "author": "Jane Smith",
                "title": "Science Article",
                "description": "This is an article about science.",
                "url": "https://example.com/article2",
                "urlToImage": "https://example.com/image2.jpg",
                "publishedAt": "2023-01-02T12:00:00Z",
                "content": "This is the content of the science article."
            }
        ]
    }

    # Create a mock response
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=api_response)
    mock_response.raise_for_status = MagicMock()

    # Create a mock client
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    # Add API key to the config
    newsapi_config.credentials = {"api_key": "test_api_key"}

    # Patch the httpx.AsyncClient
    with patch("httpx.AsyncClient", return_value=mock_client):
        # Patch the _parse_date_range method to return a fixed date range
        with patch.object(NewsAPISource, '_parse_date_range', return_value={
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 1, 31)
        }):
            source = NewsAPISource(newsapi_config)
            documents = await source.discover()

    # Check that documents were discovered
    assert len(documents) == 2
    assert documents[0]["title"] == "Technology Article"
    assert documents[0]["source_type"] == "newsapi"
    assert documents[0]["source_url"] == "https://example.com/article1"
    assert documents[0]["content"] == "This is the content of the technology article."
    assert documents[0]["metadata"]["author"] == "John Doe"
    assert documents[0]["metadata"]["source_name"] == "Tech News"
    assert documents[0]["metadata"]["published_date"] == "2023-01-01T12:00:00Z"


@pytest.mark.asyncio
async def test_serpapi_source_discover(serpapi_config):
    """Test SerpAPI source document discovery."""
    # Mock the SerpAPI response
    api_response = {
        "organic_results": [
            {
                "position": 1,
                "title": "Machine Learning Tutorial",
                "link": "https://example.com/tutorial1",
                "snippet": "This is a tutorial about machine learning."
            },
            {
                "position": 2,
                "title": "AI News Article",
                "link": "https://example.com/news1",
                "snippet": "This is a news article about AI."
            }
        ]
    }

    # Create a mock response for the API
    mock_api_response = MagicMock()
    mock_api_response.json = MagicMock(return_value=api_response)
    mock_api_response.raise_for_status = MagicMock()

    # Create a mock response for the content fetch
    mock_content_response = MagicMock()
    mock_content_response.text = "<html><body><p>This is the full content of the page.</p></body></html>"
    mock_content_response.raise_for_status = MagicMock()

    # Create a mock client
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    # Set up the get method to return different responses based on the URL
    async def mock_get(*args, **kwargs):
        if kwargs.get("params", {}).get("engine", "") == "google":
            return mock_api_response
        return mock_content_response

    mock_client.get = AsyncMock(side_effect=mock_get)

    # Add API key to the config
    serpapi_config.credentials = {"api_key": "test_api_key"}

    # Patch the httpx.AsyncClient and trafilatura.extract
    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("trafilatura.extract", return_value="This is the extracted content."), \
         patch.object(SerpAPISource, '_parse_date_range', return_value={
             "start_date": datetime(2023, 1, 1),
             "end_date": datetime(2023, 1, 31)
         }), \
         patch.object(SerpAPISource, '_fetch_content', return_value="This is the extracted content."):
        source = SerpAPISource(serpapi_config)
        documents = await source.discover()

    # Check that documents were discovered
    assert len(documents) > 0
    assert documents[0]["title"] == "Machine Learning Tutorial"
    assert documents[0]["source_type"] == "serpapi"
    assert documents[0]["source_url"] == "https://example.com/tutorial1"
    assert documents[0]["content"] == "This is the extracted content."
    assert documents[0]["metadata"]["topic"] == "machine learning tutorial"
    assert documents[0]["metadata"]["snippet"] == "This is a tutorial about machine learning."
    assert documents[0]["metadata"]["position"] == 1
