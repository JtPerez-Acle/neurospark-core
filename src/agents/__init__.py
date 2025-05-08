"""Agent framework for NeuroSpark Core.

This package provides a framework for creating and managing agents in the system,
including enhanced bidirectional communication capabilities.
"""

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType
from src.agents.enhanced_agent import EnhancedAgent
from src.agents.enhanced_message import (
    EnhancedMessage,
    FeedbackMessage,
    AssistanceRequestMessage,
    AssistanceResponseMessage,
    NeedExpressionMessage,
    NeedFulfillmentMessage,
    MessageFactory,
    MessageIntent,
    MessageType as EnhancedMessageType,
    UrgencyLevel,
)
from src.agents.factory import AgentFactory
from src.agents.feedback import FeedbackManager, FeedbackAnalyzer, FeedbackAwareAgent
from src.agents.llm_agent import LLMAgent, LLMAgentConfig
from src.agents.manager import AgentManager
from src.agents.needs import NeedsProtocol, NeedsExpressionMixin, NeedsFulfillmentMixin
from src.agents.service_discovery import AgentRegistry
from src.agents.teaching import TeachingIntent, TeachingPatterns, TeachingMessageMixin

__all__ = [
    # Base agent framework
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

    # Enhanced bidirectional communication
    "EnhancedAgent",
    "EnhancedMessage",
    "FeedbackMessage",
    "AssistanceRequestMessage",
    "AssistanceResponseMessage",
    "NeedExpressionMessage",
    "NeedFulfillmentMessage",
    "MessageFactory",
    "MessageIntent",
    "EnhancedMessageType",
    "UrgencyLevel",

    # Feedback system
    "FeedbackManager",
    "FeedbackAnalyzer",
    "FeedbackAwareAgent",

    # Needs expression protocol
    "NeedsProtocol",
    "NeedsExpressionMixin",
    "NeedsFulfillmentMixin",

    # Teaching patterns
    "TeachingIntent",
    "TeachingPatterns",
    "TeachingMessageMixin",
]
