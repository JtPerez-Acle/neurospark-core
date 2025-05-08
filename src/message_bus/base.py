"""Base message bus interface for NeuroSpark Core.

This module provides the base MessageBus interface that all message bus
implementations should implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union


class MessageBus(ABC):
    """Base interface for message bus implementations.
    
    All message bus implementations should inherit from this class and implement
    the required methods.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the message bus."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the message bus."""
        pass
    
    @abstractmethod
    async def publish_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Publish a message to a topic.
        
        Args:
            topic: The topic to publish to.
            message: The message to publish.
        """
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, callback: callable) -> None:
        """Subscribe to a topic.
        
        Args:
            topic: The topic to subscribe to.
            callback: The callback to call when a message is received.
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic.
        
        Args:
            topic: The topic to unsubscribe from.
        """
        pass
