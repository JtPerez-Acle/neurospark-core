"""Tests for agent configuration loading."""

import asyncio
import json
import os
import pytest
import pytest_asyncio
import tempfile
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType
from src.agents.factory import AgentFactory
from src.agents.llm_agent import LLMAgent, LLMAgentConfig
from src.agents.manager import AgentManager
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
async def temp_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest_asyncio.fixture
async def settings(temp_config_dir):
    """Create test settings with a temporary config directory."""
    settings = Settings(redis_url="redis://mock:6379/0")
    # Set config_dir to the temporary directory
    settings.__dict__["config_dir"] = temp_config_dir
    return settings


@pytest_asyncio.fixture
async def agent_factory(settings, redis_client):
    """Create an agent factory for testing."""
    return AgentFactory(settings, redis_client)


@pytest_asyncio.fixture
async def agent_manager(settings, redis_client):
    """Create an agent manager for testing."""
    # Create manager
    manager = AgentManager(settings, redis_client)
    
    yield manager
    
    # Stop manager
    await manager.stop()


@pytest.mark.asyncio
async def test_create_agent_from_config(agent_factory):
    """Test creating an agent from a configuration dictionary."""
    # Create a configuration dictionary
    config = {
        "type": "llm",
        "id": "test-llm-agent",
        "name": "Test LLM Agent",
        "model_name": "gpt-4",
        "system_prompt": "You are a helpful assistant.",
        "temperature": 0.5,
        "max_tokens": 1000,
        "capabilities": ["test", "assistant"],
    }
    
    # Create agent from config
    agent = agent_factory.create_agent_from_config(config)
    
    # Check agent properties
    assert agent.id == "test-llm-agent"
    assert agent.name == "Test LLM Agent"
    assert agent.capabilities == {"test", "assistant"}
    assert isinstance(agent, LLMAgent)
    assert agent.config.model_name == "gpt-4"
    assert agent.config.system_prompt == "You are a helpful assistant."
    assert agent.config.temperature == 0.5
    assert agent.config.max_tokens == 1000


@pytest.mark.asyncio
async def test_create_agents_from_config(agent_factory):
    """Test creating multiple agents from a configuration list."""
    # Create a configuration list
    config = [
        {
            "type": "llm",
            "id": "test-llm-agent-1",
            "name": "Test LLM Agent 1",
            "model_name": "gpt-4",
            "system_prompt": "You are a helpful assistant.",
            "capabilities": ["test", "assistant"],
        },
        {
            "type": "llm",
            "id": "test-llm-agent-2",
            "name": "Test LLM Agent 2",
            "model_name": "gpt-3.5-turbo",
            "system_prompt": "You are a creative assistant.",
            "capabilities": ["creative", "assistant"],
        },
    ]
    
    # Create agents from config
    with patch.object(LLMAgent, 'initialize', AsyncMock()):
        agents = agent_factory.create_agents_from_config(config)
    
    # Check agents
    assert len(agents) == 2
    
    # Check first agent
    assert agents[0].id == "test-llm-agent-1"
    assert agents[0].name == "Test LLM Agent 1"
    assert agents[0].capabilities == {"test", "assistant"}
    assert isinstance(agents[0], LLMAgent)
    assert agents[0].config.model_name == "gpt-4"
    assert agents[0].config.system_prompt == "You are a helpful assistant."
    
    # Check second agent
    assert agents[1].id == "test-llm-agent-2"
    assert agents[1].name == "Test LLM Agent 2"
    assert agents[1].capabilities == {"creative", "assistant"}
    assert isinstance(agents[1], LLMAgent)
    assert agents[1].config.model_name == "gpt-3.5-turbo"
    assert agents[1].config.system_prompt == "You are a creative assistant."


@pytest.mark.asyncio
async def test_load_agents_from_config_file(agent_manager, temp_config_dir):
    """Test loading agents from a configuration file."""
    # Create a configuration file
    config = [
        {
            "type": "llm",
            "id": "test-llm-agent-1",
            "name": "Test LLM Agent 1",
            "model_name": "gpt-4",
            "system_prompt": "You are a helpful assistant.",
            "capabilities": ["test", "assistant"],
        },
        {
            "type": "llm",
            "id": "test-llm-agent-2",
            "name": "Test LLM Agent 2",
            "model_name": "gpt-3.5-turbo",
            "system_prompt": "You are a creative assistant.",
            "capabilities": ["creative", "assistant"],
        },
    ]
    
    # Write configuration to file
    config_path = os.path.join(temp_config_dir, "agents.json")
    with open(config_path, "w") as f:
        json.dump(config, f)
    
    # Mock the initialize method to avoid actual initialization
    with patch.object(LLMAgent, 'initialize', AsyncMock()), \
         patch.object(LLMAgent, 'start', AsyncMock()):
        # Start the agent manager
        await agent_manager.start()
        
        # Wait for agents to be loaded
        await asyncio.sleep(0.5)
    
    # Check that agents were loaded
    assert len(agent_manager.agents) == 2
    assert "test-llm-agent-1" in agent_manager.agents
    assert "test-llm-agent-2" in agent_manager.agents
    
    # Check first agent
    agent1 = agent_manager.agents["test-llm-agent-1"]
    assert agent1.name == "Test LLM Agent 1"
    assert agent1.capabilities == {"test", "assistant"}
    assert isinstance(agent1, LLMAgent)
    
    # Check second agent
    agent2 = agent_manager.agents["test-llm-agent-2"]
    assert agent2.name == "Test LLM Agent 2"
    assert agent2.capabilities == {"creative", "assistant"}
    assert isinstance(agent2, LLMAgent)
