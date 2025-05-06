"""Base Agent implementation for NeuroSpark Core.

This module provides the base Agent class that all agents in the system should inherit from.
It handles message passing, state management, and lifecycle events.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, cast

from pydantic import BaseModel, Field
from pydantic_ai import Agent as PydanticAgent, RunContext

from src.common.config import Settings
from src.message_bus.redis_streams import RedisStreamClient

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AgentState(str, Enum):
    """Enum representing the possible states of an agent."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class MessageType(str, Enum):
    """Enum representing the types of messages that can be exchanged between agents."""

    COMMAND = "command"
    EVENT = "event"
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class Message(BaseModel):
    """Base class for messages exchanged between agents."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    sender: str
    recipient: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None


@dataclass
class AgentDependencies:
    """Dependencies required by an agent."""

    settings: Settings
    message_bus: RedisStreamClient


class Agent(ABC):
    """Base Agent class for NeuroSpark Core.
    
    All agents in the system should inherit from this class. It provides common
    functionality for message passing, state management, and lifecycle events.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        dependencies: AgentDependencies,
        capabilities: Optional[List[str]] = None,
    ):
        """Initialize the agent.
        
        Args:
            agent_id: Unique identifier for the agent.
            name: Human-readable name for the agent.
            dependencies: Dependencies required by the agent.
            capabilities: List of capabilities provided by the agent.
        """
        self.id = agent_id
        self.name = name
        self.dependencies = dependencies
        self.capabilities = set(capabilities or [])
        self.state = AgentState.INITIALIZING
        self.message_queue: asyncio.Queue[Message] = asyncio.Queue()
        self.subscribed_topics: Set[str] = set()
        self._tasks: List[asyncio.Task] = []
        self._llm_agent: Optional[PydanticAgent] = None
        self._stopping = False
        
        # Register with the message bus
        self._register_with_message_bus()
    
    def _register_with_message_bus(self) -> None:
        """Register the agent with the message bus."""
        # Subscribe to agent-specific topic
        self.subscribe(f"agent.{self.id}")
        # Subscribe to broadcast topic
        self.subscribe("agent.broadcast")
    
    def subscribe(self, topic: str) -> None:
        """Subscribe to a topic on the message bus.
        
        Args:
            topic: The topic to subscribe to.
        """
        self.subscribed_topics.add(topic)
    
    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic on the message bus.
        
        Args:
            topic: The topic to unsubscribe from.
        """
        self.subscribed_topics.discard(topic)
    
    async def start(self) -> None:
        """Start the agent.
        
        This method initializes the agent and starts the message processing loop.
        """
        logger.info(f"Starting agent {self.name} ({self.id})")
        
        # Initialize the agent
        await self.initialize()
        
        # Start message processing loop
        self._tasks.append(asyncio.create_task(self._process_messages()))
        
        # Start message subscription loop
        self._tasks.append(asyncio.create_task(self._subscribe_to_topics()))
        
        # Set state to idle
        self.state = AgentState.IDLE
        
        # Publish agent started event
        await self.publish_event("agent.started", {
            "agent_id": self.id,
            "name": self.name,
            "capabilities": list(self.capabilities),
        })
    
    async def stop(self) -> None:
        """Stop the agent.
        
        This method stops the agent and cleans up any resources.
        """
        logger.info(f"Stopping agent {self.name} ({self.id})")
        
        # Set stopping flag
        self._stopping = True
        self.state = AgentState.STOPPING
        
        # Publish agent stopping event
        await self.publish_event("agent.stopping", {
            "agent_id": self.id,
            "name": self.name,
        })
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Clean up
        await self.cleanup()
        
        # Set state to stopped
        self.state = AgentState.STOPPED
        
        # Publish agent stopped event
        await self.publish_event("agent.stopped", {
            "agent_id": self.id,
            "name": self.name,
        })
    
    async def _process_messages(self) -> None:
        """Process messages from the message queue."""
        while not self._stopping:
            try:
                # Get message from queue
                message = await self.message_queue.get()
                
                # Set state to busy
                self.state = AgentState.BUSY
                
                # Process message
                await self.process_message(message)
                
                # Set state back to idle
                self.state = AgentState.IDLE
                
                # Mark message as processed
                self.message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                self.state = AgentState.ERROR
    
    async def _subscribe_to_topics(self) -> None:
        """Subscribe to topics on the message bus."""
        while not self._stopping:
            try:
                # Get messages from subscribed topics
                for topic in self.subscribed_topics:
                    messages = await self.dependencies.message_bus.read_messages(topic)
                    for msg_data in messages:
                        # Convert message data to Message object
                        message = Message.model_validate(msg_data)
                        # Add message to queue
                        await self.message_queue.put(message)
                
                # Sleep briefly to avoid tight loop
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error subscribing to topics: {e}")
                await asyncio.sleep(1)  # Sleep longer on error
    
    async def send_message(self, message: Message) -> None:
        """Send a message to another agent.
        
        Args:
            message: The message to send.
        """
        if message.recipient:
            topic = f"agent.{message.recipient}"
        else:
            topic = "agent.broadcast"
        
        await self.dependencies.message_bus.publish_message(
            topic, message.model_dump()
        )
    
    async def publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event to the message bus.
        
        Args:
            event_type: The type of event.
            payload: The event payload.
        """
        message = Message(
            type=MessageType.EVENT,
            sender=self.id,
            payload={"event_type": event_type, **payload},
        )
        
        await self.dependencies.message_bus.publish_message(
            f"event.{event_type}", message.model_dump()
        )
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent.
        
        This method should be implemented by subclasses to perform any
        initialization logic.
        """
        pass
    
    @abstractmethod
    async def process_message(self, message: Message) -> None:
        """Process a message.
        
        This method should be implemented by subclasses to handle incoming messages.
        
        Args:
            message: The message to process.
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources.
        
        This method should be implemented by subclasses to clean up any resources
        when the agent is stopping.
        """
        pass
