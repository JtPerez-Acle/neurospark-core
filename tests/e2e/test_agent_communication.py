"""End-to-end tests for agent communication through the message bus."""

import asyncio
import os
import pytest
import pytest_asyncio
import uuid
from typing import Dict, List, Optional, Any

from src.agents.base import Agent, AgentDependencies, Message, MessageType
from src.agents.manager import AgentManager
from src.common.config import Settings
from src.message_bus.redis_streams import RedisStreamClient


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
            # Create echo message
            echo_message = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                payload={
                    "content": f"Echo: {message.payload.get('content', '')}",
                    "original_message_id": message.id,
                },
                correlation_id=message.id,
            )

            # Send echo message
            await self.send_message(echo_message)

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
        if message.type == MessageType.COMMAND:
            command = message.payload.get("command")

            if command == "increment":
                # Increment the counter
                self.counter += 1

                # Send response
                response = Message(
                    type=MessageType.RESPONSE,
                    sender=self.id,
                    recipient=message.sender,
                    payload={
                        "content": f"Counter incremented to {self.counter}",
                        "counter": self.counter,
                    },
                    correlation_id=message.id,
                )

                await self.send_message(response)

            elif command == "get_count":
                # Send response with current count
                response = Message(
                    type=MessageType.RESPONSE,
                    sender=self.id,
                    recipient=message.sender,
                    payload={
                        "content": f"Current count is {self.counter}",
                        "counter": self.counter,
                    },
                    correlation_id=message.id,
                )

                await self.send_message(response)

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


@pytest_asyncio.fixture
async def redis_url():
    """Get the Redis URL for testing."""
    # Use environment variable for Redis URL if available
    return os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/0")


@pytest_asyncio.fixture
async def redis_client(redis_url):
    """Create a Redis client for testing."""
    # Create client
    client = RedisStreamClient(url=redis_url)

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
    message = Message(
        type=MessageType.NOTIFICATION,
        sender="test-sender",
        recipient="echo-agent",
        payload={"content": "Hello, Echo Agent!"},
    )

    # Send message
    await redis_client.publish_message(f"agent.{message.recipient}", message.model_dump())

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
    increment_command = Message(
        type=MessageType.COMMAND,
        sender="test-sender",
        recipient="counter-agent",
        payload={"command": "increment"},
    )

    # Send command
    await redis_client.publish_message(
        f"agent.{increment_command.recipient}", increment_command.model_dump()
    )

    # Wait for command to be processed
    await asyncio.sleep(0.5)

    # Check that the counter was incremented
    assert counter_agent.counter == 1

    # Send another increment command
    await redis_client.publish_message(
        f"agent.{increment_command.recipient}", increment_command.model_dump()
    )

    # Wait for command to be processed
    await asyncio.sleep(0.5)

    # Check that the counter was incremented again
    assert counter_agent.counter == 2

    # Create a command to get the current count
    get_count_command = Message(
        type=MessageType.COMMAND,
        sender="test-sender",
        recipient="counter-agent",
        payload={"command": "get_count"},
    )

    # Send command
    await redis_client.publish_message(
        f"agent.{get_count_command.recipient}", get_count_command.model_dump()
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
    # Create two agents
    echo_agent1 = EchoAgent(
        agent_id="echo-agent-1",
        name="Echo Agent 1",
        dependencies=AgentDependencies(
            settings=Settings(redis_url=redis_url),
            message_bus=redis_client,
        ),
        capabilities=["echo"],
    )

    echo_agent2 = EchoAgent(
        agent_id="echo-agent-2",
        name="Echo Agent 2",
        dependencies=AgentDependencies(
            settings=Settings(redis_url=redis_url),
            message_bus=redis_client,
        ),
        capabilities=["echo"],
    )

    # Register agents
    await agent_manager.register_agent(echo_agent1)
    await agent_manager.register_agent(echo_agent2)

    # Create a broadcast message
    broadcast_message = Message(
        type=MessageType.NOTIFICATION,
        sender="test-sender",
        payload={"content": "Broadcast message"},
    )

    # Send broadcast message
    await redis_client.publish_message("agent.broadcast", broadcast_message.model_dump())

    # Wait for message to be processed
    await asyncio.sleep(0.5)

    # Check that both agents received the message
    assert len(echo_agent1.received_messages) == 1
    assert echo_agent1.received_messages[0].payload.get("content") == "Broadcast message"

    assert len(echo_agent2.received_messages) == 1
    assert echo_agent2.received_messages[0].payload.get("content") == "Broadcast message"
