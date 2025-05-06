"""Tests for the agent framework."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType
from src.agents.factory import AgentFactory
from src.agents.llm_agent import LLMAgent, LLMAgentConfig
from src.agents.manager import AgentManager
from src.agents.service_discovery import AgentRegistry
from src.common.config import Settings


class TestAgent(Agent):
    """Test agent implementation."""

    async def initialize(self) -> None:
        """Initialize the agent."""
        self.initialize_called = True

    async def process_message(self, message: Message) -> None:
        """Process a message."""
        self.last_message = message

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.cleanup_called = True


@pytest.fixture
def settings():
    """Create test settings."""
    settings = Settings(
        redis_url="redis://localhost:6379/0",
    )
    # Add config_dir attribute
    settings.__dict__["config_dir"] = "/tmp"
    return settings


@pytest.fixture
def message_bus():
    """Create a mock message bus."""
    message_bus = AsyncMock()
    message_bus.publish_message = AsyncMock()
    message_bus.read_messages = AsyncMock(return_value=[])
    return message_bus


@pytest.fixture
def agent_dependencies(settings, message_bus):
    """Create agent dependencies."""
    return AgentDependencies(settings, message_bus)


@pytest.mark.asyncio
async def test_agent_lifecycle(agent_dependencies):
    """Test agent lifecycle."""
    # Create agent
    agent = TestAgent("test-agent", "Test Agent", agent_dependencies)

    # Start agent
    await agent.start()

    # Check state
    assert agent.state == AgentState.IDLE
    assert hasattr(agent, "initialize_called")

    # Send message
    message = Message(
        type=MessageType.NOTIFICATION,
        sender="sender",
        recipient="test-agent",
        payload={"content": "Hello"},
    )
    await agent.message_queue.put(message)

    # Wait for message to be processed
    await asyncio.sleep(0.1)

    # Check message was processed
    assert hasattr(agent, "last_message")
    assert agent.last_message == message

    # Stop agent
    await agent.stop()

    # Check state
    assert agent.state == AgentState.STOPPED
    assert hasattr(agent, "cleanup_called")


@pytest.mark.asyncio
async def test_agent_factory(settings, message_bus):
    """Test agent factory."""
    # Create factory
    factory = AgentFactory(settings, message_bus)

    # Create LLM agent
    agent = factory.create_llm_agent(
        name="Test LLM Agent",
        model_name="gpt-4",
        system_prompt="You are a helpful assistant.",
    )

    # Check agent
    assert isinstance(agent, LLMAgent)
    assert agent.name == "Test LLM Agent"
    assert agent.config.model_name == "gpt-4"
    assert agent.config.system_prompt == "You are a helpful assistant."


@pytest.mark.asyncio
async def test_agent_registry(settings, message_bus):
    """Test agent registry."""
    # Create registry
    registry = AgentRegistry(settings, message_bus)

    # Start registry
    await registry.start()

    # Handle agent started event
    await registry._handle_agent_started({
        "payload": {
            "agent_id": "test-agent",
            "name": "Test Agent",
            "capabilities": ["test"],
        }
    })

    # Check agent is registered
    agent = registry.get_agent("test-agent")
    assert agent is not None
    assert agent["name"] == "Test Agent"

    # Check capability is registered
    agents = registry.get_agents_by_capability("test")
    assert len(agents) == 1
    assert agents[0]["id"] == "test-agent"

    # Handle agent stopped event
    await registry._handle_agent_stopped({
        "payload": {
            "agent_id": "test-agent",
        }
    })

    # Check agent is marked as inactive
    agent = registry.get_agent("test-agent")
    assert agent is not None
    assert agent["status"] == "inactive"

    # Check capability is unregistered
    agents = registry.get_agents_by_capability("test")
    assert len(agents) == 0

    # Stop registry
    await registry.stop()


@pytest.mark.asyncio
async def test_agent_manager(settings, message_bus):
    """Test agent manager."""
    # Mock the _load_configured_agents method to avoid file system access
    with patch.object(AgentManager, '_load_configured_agents', return_value=None), \
         patch('pydantic_ai.Agent', MagicMock()), \
         patch.object(LLMAgent, 'initialize', AsyncMock()):
        # Create manager
        manager = AgentManager(settings, message_bus)

        # Start manager
        await manager.start()

        # Create agent
        agent = await manager.create_llm_agent(
            name="Test LLM Agent",
            model_name="gpt-4",
            system_prompt="You are a helpful assistant.",
        )

        # Check agent is registered
        assert agent.id in manager.agents

        # Get agent
        retrieved_agent = manager.get_agent(agent.id)
        assert retrieved_agent is not None
        assert retrieved_agent.name == "Test LLM Agent"

        # Unregister agent
        await manager.unregister_agent(agent.id)

        # Check agent is unregistered
        assert agent.id not in manager.agents

        # Stop manager
        await manager.stop()
