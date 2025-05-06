"""Mock Redis implementation for testing."""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MockRedisStreamClient:
    """Mock Redis Stream client for testing."""

    def __init__(self, url: Optional[str] = None):
        """Initialize the mock Redis Stream client.

        Args:
            url: The URL of the Redis server (ignored in mock).
        """
        self.redis_url = url or "redis://mock:6379/0"
        self.streams: Dict[str, List[Dict[str, Any]]] = {}
        self.last_ids: Dict[str, str] = {}
        self.consumer_id = f"consumer-{str(uuid.uuid4())[:8]}"
        self.connected = False

    async def connect(self) -> None:
        """Connect to Redis (mock)."""
        self.connected = True
        logger.info(f"Connected to Redis at {self.redis_url}")

    async def disconnect(self) -> None:
        """Disconnect from Redis (mock)."""
        self.connected = False
        logger.info("Disconnected from Redis")

    async def ensure_connected(self) -> None:
        """Ensure connection to Redis (mock)."""
        if not self.connected:
            await self.connect()

    async def publish_message(self, topic: str, message: Dict[str, Any]) -> str:
        """Publish a message to a topic.

        Args:
            topic: The topic to publish to.
            message: The message to publish.

        Returns:
            The ID of the published message.
        """
        await self.ensure_connected()

        # Convert message to string values
        string_message = {}
        for key, value in message.items():
            if isinstance(value, (dict, list)):
                string_message[key] = json.dumps(value)
            else:
                string_message[key] = str(value)

        # Create stream if it doesn't exist
        if topic not in self.streams:
            self.streams[topic] = []

        # Generate message ID
        timestamp = int(time.time() * 1000)
        sequence = len(self.streams[topic])
        message_id = f"{timestamp}-{sequence}"

        # Add message to stream
        self.streams[topic].append({
            "id": message_id,
            "data": string_message,
        })

        # Handle broadcast messages
        if topic == "agent.broadcast":
            # Find all agent topics
            agent_topics = [t for t in self.streams.keys() if t.startswith("agent.") and t != "agent.broadcast"]

            # Publish to all agent topics
            for agent_topic in agent_topics:
                if agent_topic not in self.streams:
                    self.streams[agent_topic] = []

                # Generate message ID for this topic
                agent_timestamp = int(time.time() * 1000)
                agent_sequence = len(self.streams[agent_topic])
                agent_message_id = f"{agent_timestamp}-{agent_sequence}"

                # Add message to stream
                self.streams[agent_topic].append({
                    "id": agent_message_id,
                    "data": string_message,
                })

                logger.debug(f"Published broadcast message to {agent_topic} with ID {agent_message_id}")

        logger.debug(f"Published message to {topic} with ID {message_id}")

        return message_id

    async def read_messages(
        self, topic: str, count: int = 10, block: int = 100
    ) -> List[Dict[str, Any]]:
        """Read messages from a topic.

        Args:
            topic: The topic to read from.
            count: The maximum number of messages to read.
            block: The number of milliseconds to block waiting for messages.

        Returns:
            A list of messages.
        """
        await self.ensure_connected()

        # Create stream if it doesn't exist
        if topic not in self.streams:
            self.streams[topic] = []

        # Get last ID for this topic
        last_id = self.last_ids.get(topic, "0-0")

        # Find messages after last ID
        messages = []
        for message in self.streams[topic]:
            if message["id"] > last_id:
                # Update last ID
                self.last_ids[topic] = message["id"]

                # Parse message data
                parsed_data = {}
                for key, value in message["data"].items():
                    try:
                        # Try to parse as JSON
                        parsed_data[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, use as is
                        parsed_data[key] = value

                # Ensure the message has the required fields for Message.model_validate
                if "type" in parsed_data and isinstance(parsed_data["type"], str):
                    # If type is a string like "notification", keep it as is
                    pass
                elif "type" not in parsed_data:
                    # If type is missing, add a default
                    parsed_data["type"] = "notification"

                # Ensure id is present
                if "id" not in parsed_data:
                    parsed_data["id"] = str(uuid.uuid4())

                # Ensure timestamp is present
                if "timestamp" not in parsed_data:
                    parsed_data["timestamp"] = datetime.now().isoformat()

                # Ensure sender is present
                if "sender" not in parsed_data:
                    parsed_data["sender"] = "system"

                messages.append(parsed_data)

                # Stop if we've reached the count
                if len(messages) >= count:
                    break

        return messages

    async def create_consumer_group(
        self, topic: str, group_name: str, start_id: str = "0"
    ) -> None:
        """Create a consumer group for a topic (mock).

        Args:
            topic: The topic to create the group for.
            group_name: The name of the consumer group.
            start_id: The ID to start consuming from.
        """
        await self.ensure_connected()

        # Create stream if it doesn't exist
        if topic not in self.streams:
            self.streams[topic] = []

        logger.info(f"Created consumer group {group_name} for topic {topic}")

    async def read_group(
        self,
        topic: str,
        group_name: str,
        consumer_name: Optional[str] = None,
        count: int = 10,
        block: int = 100,
        no_ack: bool = False,
    ) -> List[Dict[str, Any]]:
        """Read messages from a consumer group (mock).

        Args:
            topic: The topic to read from.
            group_name: The name of the consumer group.
            consumer_name: The name of the consumer.
            count: The maximum number of messages to read.
            block: The number of milliseconds to block waiting for messages.
            no_ack: Whether to automatically acknowledge messages.

        Returns:
            A list of messages.
        """
        # This is a simplified implementation that just calls read_messages
        messages = await self.read_messages(topic, count, block)

        # Add message ID
        for message in messages:
            message["_id"] = str(uuid.uuid4())

        return messages

    async def acknowledge_message(
        self, topic: str, group_name: str, message_id: str
    ) -> None:
        """Acknowledge a message (mock).

        Args:
            topic: The topic the message was read from.
            group_name: The name of the consumer group.
            message_id: The ID of the message to acknowledge.
        """
        await self.ensure_connected()

        logger.debug(f"Acknowledged message {message_id} from {topic} for {group_name}")

    async def delete_message(self, topic: str, message_id: str) -> None:
        """Delete a message from a topic (mock).

        Args:
            topic: The topic to delete from.
            message_id: The ID of the message to delete.
        """
        await self.ensure_connected()

        # Create stream if it doesn't exist
        if topic not in self.streams:
            self.streams[topic] = []

        # Find and remove message
        self.streams[topic] = [
            message for message in self.streams[topic] if message["id"] != message_id
        ]

        logger.debug(f"Deleted message {message_id} from {topic}")
