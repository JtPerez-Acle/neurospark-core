"""Tests for the Curator Agent."""

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

# Mock Document model
class MockDocument:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Patch the database models
sys.modules['src.database.models'] = MagicMock()
sys.modules['src.database.models'].Document = MockDocument

# Mock database connection
mock_session = MagicMock()
mock_get_session_sync = MagicMock()
mock_get_session_sync.return_value = iter([mock_session])
sys.modules['src.database.connection'] = MagicMock()
sys.modules['src.database.connection'].get_session_sync = mock_get_session_sync

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

sys.modules['src.message_bus.redis_streams'] = MagicMock()
sys.modules['src.message_bus.redis_streams'].RedisStreamClient = MockRedisStreamClient

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType
from src.agents.curator.agent import CuratorAgent, CuratorAgentConfig
from src.agents.curator.sources.base import DocumentSource, SourceConfig


class MockDocumentSource(DocumentSource):
    """Mock document source for testing."""

    def __init__(self, config: SourceConfig):
        """Initialize the mock document source."""
        super().__init__(config)
        self.discover_called = False
        self.mock_documents = []

    async def discover(self) -> List[Dict[str, Any]]:
        """Discover documents from the source."""
        self.discover_called = True
        return self.mock_documents

    def set_mock_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Set mock documents to return."""
        self.mock_documents = documents


@pytest_asyncio.fixture
async def redis_client():
    """Create a mock Redis client for testing."""
    # Create mock client
    client = MockRedisStreamClient(url="redis://mock:6379/0")

    # Connect to Redis
    await client.connect()

    yield client

    # Disconnect from Redis
    await client.disconnect()


@pytest_asyncio.fixture
async def settings():
    """Create test settings."""
    return MockSettings(redis_url="redis://mock:6379/0")


@pytest_asyncio.fixture
async def dependencies(settings, redis_client):
    """Create agent dependencies for testing."""
    return AgentDependencies(settings=settings, message_bus=redis_client)


@pytest_asyncio.fixture
async def mock_source():
    """Create a mock document source."""
    config = SourceConfig(
        type="mock",
        filters={
            "topics": ["test"],
            "date_range": "last_week"
        }
    )
    source = MockDocumentSource(config)
    return source


@pytest_asyncio.fixture
async def curator_config():
    """Create a curator agent configuration."""
    return CuratorAgentConfig(
        refresh_interval=60,
        max_documents_per_source=10,
        sources=[
            SourceConfig(
                type="mock",
                filters={
                    "topics": ["test"],
                    "date_range": "last_week"
                }
            )
        ]
    )


@pytest_asyncio.fixture
async def curator_agent(dependencies, curator_config, mock_source):
    """Create a curator agent for testing."""
    with patch("src.agents.curator.agent.create_source", return_value=mock_source):
        agent = CuratorAgent(
            agent_id="test-curator",
            name="Test Curator",
            dependencies=dependencies,
            config=curator_config
        )

        # Patch the initialize method
        async def mock_initialize():
            agent.sources = [mock_source]
            agent._db_session = mock_session
            agent.state = AgentState.IDLE

        agent.initialize = mock_initialize

        yield agent

        # Stop the agent
        await agent.stop()


@pytest.mark.asyncio
async def test_curator_agent_initialization(curator_agent):
    """Test curator agent initialization."""
    # Check agent properties
    assert curator_agent.id == "test-curator"
    assert curator_agent.name == "Test Curator"
    assert "discover-documents" in curator_agent.capabilities

    # Initialize the agent
    await curator_agent.initialize()

    # Check that sources were created
    assert len(curator_agent.sources) == 1
    assert isinstance(curator_agent.sources[0], MockDocumentSource)
    assert curator_agent.state == AgentState.IDLE


@pytest.mark.asyncio
async def test_curator_agent_discover_documents(curator_agent, mock_source):
    """Test curator agent document discovery."""
    # Set up mock documents
    mock_documents = [
        {
            "title": "Test Document 1",
            "source_url": "https://example.com/test1",
            "source_type": "mock",
            "content": "This is test document 1.",
            "metadata": {
                "author": "Test Author 1",
                "published_date": datetime.utcnow().isoformat(),
                "topics": ["test", "document"]
            }
        },
        {
            "title": "Test Document 2",
            "source_url": "https://example.com/test2",
            "source_type": "mock",
            "content": "This is test document 2.",
            "metadata": {
                "author": "Test Author 2",
                "published_date": datetime.utcnow().isoformat(),
                "topics": ["test", "document"]
            }
        }
    ]
    mock_source.set_mock_documents(mock_documents)

    # Initialize the agent
    await curator_agent.initialize()

    # Reset mock session
    mock_session.reset_mock()

    # Discover documents
    discovered_docs = await curator_agent.discover_documents()

    # Check that documents were discovered
    assert len(discovered_docs) == 2
    assert discovered_docs[0]["title"] == "Test Document 1"
    assert discovered_docs[1]["title"] == "Test Document 2"

    # Check that documents were saved to the database
    assert mock_session.add.call_count == 2
    assert mock_session.commit.call_count == 1


@pytest.mark.asyncio
async def test_curator_agent_process_message(curator_agent, mock_source):
    """Test curator agent message processing."""
    # Set up mock documents
    mock_documents = [
        {
            "title": "Test Document 1",
            "source_url": "https://example.com/test1",
            "source_type": "mock",
            "content": "This is test document 1.",
            "metadata": {
                "author": "Test Author 1",
                "published_date": datetime.utcnow().isoformat(),
                "topics": ["test", "document"]
            }
        }
    ]
    mock_source.set_mock_documents(mock_documents)

    # Initialize the agent
    await curator_agent.initialize()

    # Mock discover_documents method
    curator_agent.discover_documents = AsyncMock(return_value=mock_documents)
    curator_agent.send_message = AsyncMock()

    # Create a discover message
    message = Message(
        type=MessageType.COMMAND,
        sender="test-sender",
        recipient="test-curator",
        payload={
            "command": "discover",
            "topics": ["test"]
        }
    )

    # Process the message
    await curator_agent.process_message(message)

    # Check that discover_documents was called
    curator_agent.discover_documents.assert_called_once()

    # Check that a response was sent
    curator_agent.send_message.assert_called_once()
    response_args = curator_agent.send_message.call_args[0][0]
    assert response_args.type == MessageType.RESPONSE
    assert response_args.sender == "test-curator"
    assert response_args.recipient == "test-sender"
    assert "documents" in response_args.payload
    assert len(response_args.payload["documents"]) == 1
