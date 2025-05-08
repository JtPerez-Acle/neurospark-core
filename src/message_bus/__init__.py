"""Message Bus module for NeuroSpark Core.

This module contains the message bus for inter-agent communication using Redis Streams.
"""

from src.message_bus.base import MessageBus
from src.message_bus.redis_streams import RedisMessageBus, Message, StreamConfig

__all__ = [
    "MessageBus",
    "RedisMessageBus",
    "Message",
    "StreamConfig",
]
