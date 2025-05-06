"""Agent factory for NeuroSpark Core.

This module provides a factory for creating agents of different types.
"""

import logging
import uuid
from typing import Dict, List, Optional, Type, Union

from src.agents.base import Agent, AgentDependencies
from src.agents.llm_agent import LLMAgent, LLMAgentConfig
from src.common.config import Settings
from src.message_bus.redis_streams import RedisStreamClient

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating agents.
    
    This class provides methods for creating agents of different types.
    """

    def __init__(self, settings: Settings, message_bus: RedisStreamClient):
        """Initialize the agent factory.
        
        Args:
            settings: Application settings.
            message_bus: Message bus client.
        """
        self.settings = settings
        self.message_bus = message_bus
        self.dependencies = AgentDependencies(settings, message_bus)
    
    def create_llm_agent(
        self,
        name: str,
        model_name: str,
        system_prompt: str,
        agent_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List] = None,
    ) -> LLMAgent:
        """Create an LLM agent.
        
        Args:
            name: Human-readable name for the agent.
            model_name: Name of the LLM model to use.
            system_prompt: System prompt for the LLM.
            agent_id: Unique identifier for the agent (optional).
            capabilities: List of capabilities provided by the agent (optional).
            temperature: Temperature parameter for the LLM (default: 0.7).
            max_tokens: Maximum number of tokens for the LLM (optional).
            tools: List of tools for the LLM agent (optional).
            
        Returns:
            An LLM agent.
        """
        # Generate agent ID if not provided
        if not agent_id:
            agent_id = f"llm-{str(uuid.uuid4())[:8]}"
        
        # Create agent config
        config = LLMAgentConfig(
            model_name=model_name,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools or [],
        )
        
        # Create agent
        agent = LLMAgent(
            agent_id=agent_id,
            name=name,
            dependencies=self.dependencies,
            config=config,
            capabilities=capabilities,
        )
        
        logger.info(f"Created LLM agent {name} ({agent_id}) with model {model_name}")
        return agent
    
    def create_agent_from_config(self, config: Dict) -> Agent:
        """Create an agent from a configuration dictionary.
        
        Args:
            config: Agent configuration dictionary.
            
        Returns:
            An agent instance.
            
        Raises:
            ValueError: If the agent type is unknown.
        """
        agent_type = config.get("type")
        agent_id = config.get("id")
        name = config.get("name")
        capabilities = config.get("capabilities")
        
        if not agent_type or not name:
            raise ValueError("Agent configuration must include 'type' and 'name'")
        
        if agent_type == "llm":
            model_name = config.get("model_name")
            system_prompt = config.get("system_prompt")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens")
            
            if not model_name or not system_prompt:
                raise ValueError("LLM agent configuration must include 'model_name' and 'system_prompt'")
            
            return self.create_llm_agent(
                name=name,
                model_name=model_name,
                system_prompt=system_prompt,
                agent_id=agent_id,
                capabilities=capabilities,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    def create_agents_from_config(self, config: List[Dict]) -> List[Agent]:
        """Create multiple agents from a configuration list.
        
        Args:
            config: List of agent configuration dictionaries.
            
        Returns:
            A list of agent instances.
        """
        agents = []
        for agent_config in config:
            try:
                agent = self.create_agent_from_config(agent_config)
                agents.append(agent)
            except Exception as e:
                logger.exception(f"Error creating agent from config: {e}")
        
        return agents
