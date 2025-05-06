"""LLM Agent implementation for NeuroSpark Core.

This module provides the LLMAgent class that integrates with Pydantic AI to provide
LLM-powered agent capabilities.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from pydantic import BaseModel, Field
from pydantic_ai import Agent as PydanticAgent, RunContext, Tool

from src.agents.base import Agent, AgentDependencies, Message, MessageType

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class LLMAgentConfig:
    """Configuration for an LLM Agent."""

    model_name: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    tools: List[Tool] = None


class LLMAgent(Agent):
    """LLM Agent class for NeuroSpark Core.
    
    This agent uses Pydantic AI to provide LLM-powered capabilities.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        dependencies: AgentDependencies,
        config: LLMAgentConfig,
        capabilities: Optional[List[str]] = None,
    ):
        """Initialize the LLM agent.
        
        Args:
            agent_id: Unique identifier for the agent.
            name: Human-readable name for the agent.
            dependencies: Dependencies required by the agent.
            config: Configuration for the LLM agent.
            capabilities: List of capabilities provided by the agent.
        """
        super().__init__(agent_id, name, dependencies, capabilities)
        self.config = config
        self._message_history: List[Dict[str, Any]] = []
    
    async def initialize(self) -> None:
        """Initialize the LLM agent.
        
        This method initializes the Pydantic AI agent with the configured model and tools.
        """
        # Initialize the Pydantic AI agent
        self._llm_agent = PydanticAgent(
            self.config.model_name,
            system_prompt=self.config.system_prompt,
            deps_type=AgentDependencies,
        )
        
        # Register tools if provided
        if self.config.tools:
            for tool in self.config.tools:
                self._llm_agent.register_tool(tool)
        
        # Register default tools
        self._register_default_tools()
        
        logger.info(f"Initialized LLM agent {self.name} with model {self.config.model_name}")
    
    def _register_default_tools(self) -> None:
        """Register default tools for the LLM agent."""
        # Register send_message tool
        @self._llm_agent.tool
        async def send_message(
            ctx: RunContext[AgentDependencies], 
            recipient: str, 
            content: str,
            message_type: str = "notification"
        ) -> str:
            """Send a message to another agent.
            
            Args:
                recipient: The ID of the recipient agent.
                content: The content of the message.
                message_type: The type of message (default: notification).
                
            Returns:
                A confirmation message.
            """
            message = Message(
                type=MessageType(message_type),
                sender=self.id,
                recipient=recipient,
                payload={"content": content},
            )
            
            await self.send_message(message)
            return f"Message sent to {recipient}"
        
        # Register query_agent_registry tool
        @self._llm_agent.tool
        async def query_agent_registry(
            ctx: RunContext[AgentDependencies], 
            capability: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """Query the agent registry for agents with specific capabilities.
            
            Args:
                capability: The capability to filter by (optional).
                
            Returns:
                A list of agents matching the query.
            """
            # This is a placeholder implementation
            # In a real implementation, this would query a registry service
            return [
                {"id": "agent1", "name": "Agent 1", "capabilities": ["search", "summarize"]},
                {"id": "agent2", "name": "Agent 2", "capabilities": ["translate", "analyze"]},
            ]
    
    async def process_message(self, message: Message) -> None:
        """Process a message.
        
        This method processes incoming messages by passing them to the LLM agent.
        
        Args:
            message: The message to process.
        """
        try:
            # Add message to history
            self._message_history.append({
                "role": "user" if message.sender != self.id else "assistant",
                "content": message.payload.get("content", str(message.payload)),
            })
            
            # Limit history size
            if len(self._message_history) > 20:
                self._message_history = self._message_history[-20:]
            
            # Process message with LLM agent if it's not from this agent
            if message.sender != self.id:
                # Prepare the prompt
                prompt = f"Message from {message.sender}: {message.payload.get('content', str(message.payload))}"
                
                # Run the LLM agent
                result = await self._llm_agent.run(
                    prompt,
                    deps=self.dependencies,
                    message_history=self._message_history,
                )
                
                # Add response to history
                self._message_history.append({
                    "role": "assistant",
                    "content": result.output,
                })
                
                # Send response if there's a reply_to
                if message.reply_to:
                    response = Message(
                        type=MessageType.RESPONSE,
                        sender=self.id,
                        recipient=message.sender,
                        payload={"content": result.output},
                        correlation_id=message.id,
                    )
                    await self.send_message(response)
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            
            # Send error response if there's a reply_to
            if message.reply_to:
                error_response = Message(
                    type=MessageType.RESPONSE,
                    sender=self.id,
                    recipient=message.sender,
                    payload={"error": str(e)},
                    correlation_id=message.id,
                )
                await self.send_message(error_response)
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        # No specific cleanup needed for LLM agent
        pass
    
    async def query(self, prompt: str) -> str:
        """Query the LLM agent directly.
        
        Args:
            prompt: The prompt to send to the LLM.
            
        Returns:
            The response from the LLM.
        """
        # Add prompt to history
        self._message_history.append({
            "role": "user",
            "content": prompt,
        })
        
        # Run the LLM agent
        result = await self._llm_agent.run(
            prompt,
            deps=self.dependencies,
            message_history=self._message_history,
        )
        
        # Add response to history
        self._message_history.append({
            "role": "assistant",
            "content": result.output,
        })
        
        return result.output
