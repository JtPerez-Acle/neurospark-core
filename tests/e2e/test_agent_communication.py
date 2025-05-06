"""End-to-end tests for agent communication through the message bus."""

import asyncio
import os
import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import Agent, AgentDependencies, Message, MessageType
from src.agents.manager import AgentManager
from src.common.config import Settings
from tests.mocks.redis_mock import MockRedisStreamClient


class EchoAgent(Agent):
    """Simple agent that echoes messages back to the sender."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        dependencies: AgentDependencies,
        capabilities: Optional[List[str]] = None,
    ):
        """Initialize the echo agent."""
        super().__init__(agent_id, name, dependencies, capabilities)
        self.received_messages: List[Message] = []

    async def initialize(self) -> None:
        """Initialize the agent."""
        pass

    async def process_message(self, message: Message) -> None:
        """Process a message by echoing it back to the sender."""
        self.received_messages.append(message)

        # Only echo if the message is not from this agent
        if message.sender != self.id:
            # Create echo message with string type
            echo_message = {
                "id": str(uuid.uuid4()),
                "type": "response",  # Use string instead of enum
                "sender": self.id,
                "recipient": message.sender,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "content": f"Echo: {message.payload.get('content', '')}",
                    "original_message_id": message.id,
                },
                "correlation_id": message.id,
            }

            # Send echo message directly to the message bus
            await self.dependencies.message_bus.publish_message(
                f"agent.{message.sender}", echo_message
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


class CounterAgent(Agent):
    """Agent that counts messages and can increment a counter."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        dependencies: AgentDependencies,
        capabilities: Optional[List[str]] = None,
    ):
        """Initialize the counter agent."""
        super().__init__(agent_id, name, dependencies, capabilities)
        self.counter = 0
        self.received_messages: List[Message] = []

    async def initialize(self) -> None:
        """Initialize the agent."""
        pass

    async def process_message(self, message: Message) -> None:
        """Process a message by updating the counter."""
        self.received_messages.append(message)

        # Check if the message is a command to increment the counter
        if message.type == MessageType.COMMAND or message.type == "command":
            command = message.payload.get("command")

            if command == "increment":
                # Increment the counter
                self.counter += 1

                # Send response with string type
                response = {
                    "id": str(uuid.uuid4()),
                    "type": "response",  # Use string instead of enum
                    "sender": self.id,
                    "recipient": message.sender,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": {
                        "content": f"Counter incremented to {self.counter}",
                        "counter": self.counter,
                    },
                    "correlation_id": message.id,
                }

                # Send response directly to the message bus
                await self.dependencies.message_bus.publish_message(
                    f"agent.{message.sender}", response
                )

            elif command == "get_count":
                # Send response with current count and string type
                response = {
                    "id": str(uuid.uuid4()),
                    "type": "response",  # Use string instead of enum
                    "sender": self.id,
                    "recipient": message.sender,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": {
                        "content": f"Current count is {self.counter}",
                        "counter": self.counter,
                    },
                    "correlation_id": message.id,
                }

                # Send response directly to the message bus
                await self.dependencies.message_bus.publish_message(
                    f"agent.{message.sender}", response
                )

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


@pytest_asyncio.fixture
async def redis_url():
    """Get the Redis URL for testing."""
    # Use a mock URL
    return "redis://mock:6379/0"


@pytest_asyncio.fixture
async def redis_client(redis_url):
    """Create a mock Redis client for testing."""
    # Create mock client
    client = MockRedisStreamClient(url=redis_url)

    # Connect to Redis
    await client.connect()

    yield client

    # Disconnect from Redis
    await client.disconnect()


class TestAgentManager(AgentManager):
    """Agent manager for testing."""

    async def _load_configured_agents(self) -> None:
        """Override to avoid loading agents from a configuration file."""
        # Do nothing
        pass


@pytest_asyncio.fixture
async def agent_manager(redis_client, redis_url):
    """Create an agent manager for testing."""
    # Create settings
    settings = Settings(redis_url=redis_url)

    # Create manager
    manager = TestAgentManager(settings, redis_client)

    # Start manager
    await manager.start()

    yield manager

    # Stop manager
    await manager.stop()


@pytest.mark.asyncio
async def test_agent_echo(agent_manager, redis_client, redis_url):
    """Test that agents can send and receive messages."""
    # Create echo agent
    echo_agent = EchoAgent(
        agent_id="echo-agent",
        name="Echo Agent",
        dependencies=AgentDependencies(
            settings=Settings(redis_url=redis_url),
            message_bus=redis_client,
        ),
        capabilities=["echo"],
    )

    # Register agent
    await agent_manager.register_agent(echo_agent)

    # Create a test message
    message = {
        "id": str(uuid.uuid4()),
        "type": "notification",
        "sender": "test-sender",
        "recipient": "echo-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {"content": "Hello, Echo Agent!"},
    }

    # Send message
    await redis_client.publish_message(f"agent.{message['recipient']}", message)

    # Wait for message to be processed
    await asyncio.sleep(0.5)

    # Check that the agent received the message
    assert len(echo_agent.received_messages) == 1
    assert echo_agent.received_messages[0].payload.get("content") == "Hello, Echo Agent!"

    # Check that the echo message was sent
    # We need to read from the sender's topic
    messages = await redis_client.read_messages(f"agent.test-sender")

    # There should be one message
    assert len(messages) == 1

    # Check the message content
    echo_message = messages[0]
    assert echo_message["type"] == "response"
    assert echo_message["sender"] == "echo-agent"
    assert echo_message["recipient"] == "test-sender"
    assert echo_message["payload"]["content"] == "Echo: Hello, Echo Agent!"


@pytest.mark.asyncio
async def test_agent_counter(agent_manager, redis_client, redis_url):
    """Test that agents can maintain state and respond to commands."""
    # Create counter agent
    counter_agent = CounterAgent(
        agent_id="counter-agent",
        name="Counter Agent",
        dependencies=AgentDependencies(
            settings=Settings(redis_url=redis_url),
            message_bus=redis_client,
        ),
        capabilities=["counter"],
    )

    # Register agent
    await agent_manager.register_agent(counter_agent)

    # Create a command to increment the counter
    increment_command = {
        "id": str(uuid.uuid4()),
        "type": "command",
        "sender": "test-sender",
        "recipient": "counter-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {"command": "increment"},
    }

    # Send command
    await redis_client.publish_message(
        f"agent.{increment_command['recipient']}", increment_command
    )

    # Wait for command to be processed
    await asyncio.sleep(0.5)

    # Check that the counter was incremented
    assert counter_agent.counter == 1

    # Send another increment command
    await redis_client.publish_message(
        f"agent.{increment_command['recipient']}", increment_command
    )

    # Wait for command to be processed
    await asyncio.sleep(0.5)

    # Check that the counter was incremented again
    assert counter_agent.counter == 2

    # Create a command to get the current count
    get_count_command = {
        "id": str(uuid.uuid4()),
        "type": "command",
        "sender": "test-sender",
        "recipient": "counter-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {"command": "get_count"},
    }

    # Send command
    await redis_client.publish_message(
        f"agent.{get_count_command['recipient']}", get_count_command
    )

    # Wait for command to be processed
    await asyncio.sleep(0.5)

    # Read the response
    messages = await redis_client.read_messages(f"agent.test-sender")

    # There should be three messages (two increment responses and one get_count response)
    assert len(messages) == 3

    # Check the last message
    count_response = messages[2]
    assert count_response["type"] == "response"
    assert count_response["sender"] == "counter-agent"
    assert count_response["recipient"] == "test-sender"
    assert count_response["payload"]["counter"] == 2


@pytest.mark.asyncio
async def test_agent_broadcast(agent_manager, redis_client, redis_url):
    """Test that agents can receive broadcast messages."""
    # Create an agent
    echo_agent = EchoAgent(
        agent_id="echo-agent-broadcast",
        name="Echo Agent Broadcast",
        dependencies=AgentDependencies(
            settings=Settings(redis_url=redis_url),
            message_bus=redis_client,
        ),
        capabilities=["echo"],
    )

    # Register agent
    await agent_manager.register_agent(echo_agent)

    # Create a broadcast message
    broadcast_message = {
        "id": str(uuid.uuid4()),
        "type": "notification",
        "sender": "test-sender",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {"content": "Broadcast message"},
    }

    # Send broadcast message
    await redis_client.publish_message("agent.broadcast", broadcast_message)

    # Wait for message to be processed (longer wait for broadcast)
    await asyncio.sleep(1.0)

    # Check that the agent received the broadcast message
    assert len(echo_agent.received_messages) == 1
    assert echo_agent.received_messages[0].payload.get("content") == "Broadcast message"
