"""Agent manager for NeuroSpark Core.

This module provides a manager for handling agent lifecycle and coordination.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Set

from src.agents.base import Agent
from src.agents.factory import AgentFactory
from src.agents.service_discovery import AgentRegistry
from src.common.config import Settings
from src.message_bus.redis_streams import RedisStreamClient

logger = logging.getLogger(__name__)


class AgentManager:
    """Manager for agents in the system.
    
    This class provides methods for starting, stopping, and managing agents.
    """

    def __init__(self, settings: Settings, message_bus: RedisStreamClient):
        """Initialize the agent manager.
        
        Args:
            settings: Application settings.
            message_bus: Message bus client.
        """
        self.settings = settings
        self.message_bus = message_bus
        self.factory = AgentFactory(settings, message_bus)
        self.registry = AgentRegistry(settings, message_bus)
        self.agents: Dict[str, Agent] = {}
        self._running = False
    
    async def start(self) -> None:
        """Start the agent manager.
        
        This method starts the agent registry and loads any configured agents.
        """
        if self._running:
            return
        
        logger.info("Starting agent manager")
        self._running = True
        
        # Start the agent registry
        await self.registry.start()
        
        # Load configured agents
        await self._load_configured_agents()
        
        logger.info("Agent manager started")
    
    async def stop(self) -> None:
        """Stop the agent manager.
        
        This method stops all managed agents and the agent registry.
        """
        if not self._running:
            return
        
        logger.info("Stopping agent manager")
        self._running = False
        
        # Stop all agents
        stop_tasks = []
        for agent_id, agent in self.agents.items():
            logger.info(f"Stopping agent {agent.name} ({agent_id})")
            stop_tasks.append(agent.stop())
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks)
        
        # Clear agents
        self.agents.clear()
        
        # Stop the agent registry
        await self.registry.stop()
        
        logger.info("Agent manager stopped")
    
    async def _load_configured_agents(self) -> None:
        """Load agents from configuration."""
        # Check if agents config file exists
        config_path = os.path.join(self.settings.config_dir, "agents.json")
        if not os.path.exists(config_path):
            logger.info(f"No agents configuration file found at {config_path}")
            return
        
        try:
            # Load agents config
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Create agents
            agents = self.factory.create_agents_from_config(config)
            
            # Start agents
            for agent in agents:
                await self.register_agent(agent)
            
            logger.info(f"Loaded {len(agents)} agents from configuration")
        except Exception as e:
            logger.exception(f"Error loading agents from configuration: {e}")
    
    async def register_agent(self, agent: Agent) -> None:
        """Register and start an agent.
        
        Args:
            agent: The agent to register and start.
        """
        if agent.id in self.agents:
            logger.warning(f"Agent {agent.name} ({agent.id}) already registered")
            return
        
        # Add to managed agents
        self.agents[agent.id] = agent
        
        # Start the agent
        await agent.start()
        
        logger.info(f"Registered and started agent {agent.name} ({agent.id})")
    
    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister and stop an agent.
        
        Args:
            agent_id: The ID of the agent to unregister and stop.
        """
        agent = self.agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return
        
        # Stop the agent
        await agent.stop()
        
        # Remove from managed agents
        del self.agents[agent_id]
        
        logger.info(f"Unregistered and stopped agent {agent.name} ({agent_id})")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to get.
            
        Returns:
            The agent, or None if not found.
        """
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        """Get all managed agents.
        
        Returns:
            A list of all managed agents.
        """
        return list(self.agents.values())
    
    async def create_llm_agent(
        self,
        name: str,
        model_name: str,
        system_prompt: str,
        agent_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
        auto_start: bool = True,
    ) -> Agent:
        """Create and optionally start an LLM agent.
        
        Args:
            name: Human-readable name for the agent.
            model_name: Name of the LLM model to use.
            system_prompt: System prompt for the LLM.
            agent_id: Unique identifier for the agent (optional).
            capabilities: List of capabilities provided by the agent (optional).
            temperature: Temperature parameter for the LLM (default: 0.7).
            max_tokens: Maximum number of tokens for the LLM (optional).
            tools: List of tools for the LLM agent (optional).
            auto_start: Whether to automatically start the agent (default: True).
            
        Returns:
            The created agent.
        """
        # Create the agent
        agent = self.factory.create_llm_agent(
            name=name,
            model_name=model_name,
            system_prompt=system_prompt,
            agent_id=agent_id,
            capabilities=capabilities,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )
        
        # Start the agent if auto_start is True
        if auto_start:
            await self.register_agent(agent)
        
        return agent
