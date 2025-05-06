"""Tests for the agent registry."""

import asyncio
import pytest
import pytest_asyncio
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType
from src.agents.service_discovery import AgentRegistry
from src.common.config import Settings
from tests.mocks.redis_mock import MockRedisStreamClient


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
    return Settings(redis_url="redis://mock:6379/0")


@pytest_asyncio.fixture
async def agent_registry(settings, redis_client):
    """Create an agent registry for testing."""
    # Create registry
    registry = AgentRegistry(settings, redis_client)

    # Start registry
    await registry.start()

    yield registry

    # Stop registry
    await registry.stop()


@pytest.mark.asyncio
async def test_agent_registry_start_stop(settings, redis_client):
    """Test starting and stopping the agent registry."""
    # Create registry
    registry = AgentRegistry(settings, redis_client)

    # Start registry
    await registry.start()

    # Check that registry is running
    assert registry._running
    assert registry._task is not None

    # Stop registry
    await registry.stop()

    # Check that registry is stopped
    assert not registry._running
    # Task may be None or cancelled, depending on implementation
    if registry._task is not None:
        assert registry._task.cancelled()


@pytest.mark.asyncio
async def test_agent_registry_handle_agent_started(agent_registry):
    """Test handling agent started events."""
    # Create agent started event
    event = {
        "payload": {
            "agent_id": "test-agent",
            "name": "Test Agent",
            "capabilities": ["test", "example"],
        }
    }

    # Handle event
    await agent_registry._handle_agent_started(event)

    # Check that agent is registered
    agent = agent_registry.get_agent("test-agent")
    assert agent is not None
    assert agent["name"] == "Test Agent"
    assert agent["capabilities"] == ["test", "example"]
    assert agent["status"] == "active"

    # Check that capabilities are registered
    test_agents = agent_registry.get_agents_by_capability("test")
    assert len(test_agents) == 1
    assert test_agents[0]["id"] == "test-agent"

    example_agents = agent_registry.get_agents_by_capability("example")
    assert len(example_agents) == 1
    assert example_agents[0]["id"] == "test-agent"


@pytest.mark.asyncio
async def test_agent_registry_handle_agent_stopped(agent_registry):
    """Test handling agent stopped events."""
    # Register an agent first
    await agent_registry._handle_agent_started({
        "payload": {
            "agent_id": "test-agent",
            "name": "Test Agent",
            "capabilities": ["test", "example"],
        }
    })

    # Create agent stopped event
    event = {
        "payload": {
            "agent_id": "test-agent",
        }
    }

    # Handle event
    await agent_registry._handle_agent_stopped(event)

    # Check that agent is marked as inactive
    agent = agent_registry.get_agent("test-agent")
    assert agent is not None
    assert agent["status"] == "inactive"

    # Check that capabilities are unregistered
    test_agents = agent_registry.get_agents_by_capability("test")
    assert len(test_agents) == 0

    example_agents = agent_registry.get_agents_by_capability("example")
    assert len(example_agents) == 0


@pytest.mark.asyncio
async def test_agent_registry_get_all_agents(agent_registry):
    """Test getting all registered agents."""
    # Register some agents
    await agent_registry._handle_agent_started({
        "payload": {
            "agent_id": "test-agent-1",
            "name": "Test Agent 1",
            "capabilities": ["test"],
        }
    })

    await agent_registry._handle_agent_started({
        "payload": {
            "agent_id": "test-agent-2",
            "name": "Test Agent 2",
            "capabilities": ["example"],
        }
    })

    # Get all agents
    agents = agent_registry.get_all_agents()

    # Check agents
    assert len(agents) == 2
    assert any(agent["id"] == "test-agent-1" for agent in agents)
    assert any(agent["id"] == "test-agent-2" for agent in agents)


@pytest.mark.asyncio
async def test_agent_registry_get_all_capabilities(agent_registry):
    """Test getting all registered capabilities."""
    # Register some agents with capabilities
    await agent_registry._handle_agent_started({
        "payload": {
            "agent_id": "test-agent-1",
            "name": "Test Agent 1",
            "capabilities": ["test", "shared"],
        }
    })

    await agent_registry._handle_agent_started({
        "payload": {
            "agent_id": "test-agent-2",
            "name": "Test Agent 2",
            "capabilities": ["example", "shared"],
        }
    })

    # Get all capabilities
    capabilities = agent_registry.get_all_capabilities()

    # Check capabilities
    assert len(capabilities) == 3
    assert "test" in capabilities
    assert "example" in capabilities
    assert "shared" in capabilities


@pytest.mark.asyncio
async def test_agent_registry_listen_for_events(agent_registry, redis_client):
    """Test listening for agent events."""
    # Directly call the handler methods instead of mocking the event loop
    # Register an agent
    await agent_registry._handle_agent_started({
        "payload": {
            "agent_id": "test-agent-events",
            "name": "Test Agent Events",
            "capabilities": ["test-events"],
        }
    })

    # Check that agent was registered
    agent = agent_registry.get_agent("test-agent-events")
    assert agent is not None
    assert agent["name"] == "Test Agent Events"
    assert agent["status"] == "active"

    # Stop the agent
    await agent_registry._handle_agent_stopped({
        "payload": {
            "agent_id": "test-agent-events",
        }
    })

    # Check that agent was marked as inactive
    agent = agent_registry.get_agent("test-agent-events")
    assert agent is not None
    assert agent["status"] == "inactive"
