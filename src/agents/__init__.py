"""Agent framework for NeuroSpark Core.

This package provides a framework for creating and managing agents in the system.
"""

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType
from src.agents.factory import AgentFactory
from src.agents.llm_agent import LLMAgent, LLMAgentConfig
from src.agents.manager import AgentManager
from src.agents.service_discovery import AgentRegistry

__all__ = [
    "Agent",
    "AgentDependencies",
    "AgentFactory",
    "AgentManager",
    "AgentRegistry",
    "AgentState",
    "LLMAgent",
    "LLMAgentConfig",
    "Message",
    "MessageType",
]
