"""Redis Streams message bus implementation."""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import redis.asyncio as aioredis
from redis import Redis
from redis.exceptions import ResponseError

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Message model."""

    id: str
    data: Dict[str, Any]


@dataclass
class StreamConfig:
    """Stream configuration model."""

    stream_name: str
    group_name: str
    consumer_name: str


class RedisMessageBus:
    """Redis Streams message bus implementation."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        url: Optional[str] = None,
    ):
        """Initialize the Redis Streams message bus.

        Args:
            host: The host of the Redis server.
            port: The port of the Redis server.
            password: The password for authentication.
            url: The URL of the Redis server.
        """
        if url:
            self.client = Redis(url=url, decode_responses=True)
        else:
            self.client = Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=True,
            )

    def create_stream(self, stream_name: str) -> None:
        """Create a stream if it doesn't exist.

        Args:
            stream_name: The name of the stream.
        """
        try:
            # Check if the stream exists
            self.client.xinfo_stream(stream_name, full=True)
            logger.info(f"Stream {stream_name} already exists")
        except Exception as e:
            # Stream doesn't exist, create it with an initial message
            logger.info(f"Creating stream {stream_name}")
            self.client.xadd(stream_name, {"init": "true"}, id="0-0")

    def create_consumer_group(self, stream_name: str, group_name: str) -> None:
        """Create a consumer group for a stream.

        Args:
            stream_name: The name of the stream.
            group_name: The name of the consumer group.
        """
        try:
            # Create the consumer group
            self.client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
            logger.info(f"Consumer group {group_name} created for stream {stream_name}")
        except Exception as e:
            # Group might already exist
            logger.info(f"Consumer group {group_name} already exists for stream {stream_name}")

    def publish_message(self, stream_name: str, message: Dict[str, Any]) -> str:
        """Publish a message to a stream.

        Args:
            stream_name: The name of the stream.
            message: The message to publish.

        Returns:
            The ID of the published message.
        """
        logger.info(f"Publishing message to stream {stream_name}")
        message_id = self.client.xadd(stream_name, message)
        return message_id

    def consume_messages(
        self,
        stream_config: StreamConfig,
        count: int = 1,
        block: Optional[int] = None,
    ) -> List[Message]:
        """Consume messages from a stream.

        Args:
            stream_config: The stream configuration.
            count: The maximum number of messages to consume.
            block: The number of milliseconds to block waiting for messages.

        Returns:
            A list of messages.
        """
        logger.info(
            f"Consuming messages from stream {stream_config.stream_name} "
            f"for group {stream_config.group_name} "
            f"as consumer {stream_config.consumer_name}"
        )

        # Read messages from the stream
        response = self.client.xreadgroup(
            groupname=stream_config.group_name,
            consumername=stream_config.consumer_name,
            streams={stream_config.stream_name: ">"},
            count=count,
            block=block,
        )

        # Process the response
        messages = []
        if response:
            for stream_data in response:
                stream_name, stream_messages = stream_data
                for message_id, message_data in stream_messages:
                    messages.append(Message(id=message_id, data=message_data))

        return messages

    def acknowledge_message(
        self, stream_name: str, group_name: str, message_id: str
    ) -> None:
        """Acknowledge a message.

        Args:
            stream_name: The name of the stream.
            group_name: The name of the consumer group.
            message_id: The ID of the message to acknowledge.
        """
        logger.info(
            f"Acknowledging message {message_id} "
            f"from stream {stream_name} "
            f"for group {group_name}"
        )
        self.client.xack(stream_name, group_name, message_id)

    def acknowledge_messages(
        self, stream_name: str, group_name: str, message_ids: List[str]
    ) -> None:
        """Acknowledge multiple messages.

        Args:
            stream_name: The name of the stream.
            group_name: The name of the consumer group.
            message_ids: The IDs of the messages to acknowledge.
        """
        logger.info(
            f"Acknowledging {len(message_ids)} messages "
            f"from stream {stream_name} "
            f"for group {group_name}"
        )
        self.client.xack(stream_name, group_name, *message_ids)

    def get_pending_messages(
        self, stream_name: str, group_name: str
    ) -> Dict[str, Any]:
        """Get information about pending messages.

        Args:
            stream_name: The name of the stream.
            group_name: The name of the consumer group.

        Returns:
            Information about pending messages.
        """
        logger.info(
            f"Getting pending messages from stream {stream_name} "
            f"for group {group_name}"
        )
        return self.client.xpending(stream_name, group_name)

    def get_stream_info(self, stream_name: str) -> Dict[str, Any]:
        """Get information about a stream.

        Args:
            stream_name: The name of the stream.

        Returns:
            Information about the stream.
        """
        logger.info(f"Getting information about stream {stream_name}")
        return self.client.xinfo_stream(stream_name, full=True)


class RedisStreamClient:
    """Asynchronous Redis Streams client for agent communication."""

    def __init__(
        self,
        url: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
    ):
        """Initialize the Redis Streams client.

        Args:
            url: The URL of the Redis server.
            host: The host of the Redis server.
            port: The port of the Redis server.
            password: The password for authentication.
        """
        if url:
            self.redis_url = url
        else:
            self.redis_url = f"redis://{host or 'localhost'}:{port or 6379}"
            if password:
                self.redis_url = f"redis://:{password}@{host or 'localhost'}:{port or 6379}"

        self.client = None
        self.consumer_id = f"consumer-{str(uuid.uuid4())[:8]}"
        self.last_ids = {}

    async def connect(self) -> None:
        """Connect to Redis."""
        if self.client is None:
            self.client = await aioredis.from_url(
                self.redis_url, decode_responses=True
            )
            logger.info(f"Connected to Redis at {self.redis_url}")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")

    async def ensure_connected(self) -> None:
        """Ensure connection to Redis."""
        if self.client is None:
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

        # Publish message
        message_id = await self.client.xadd(topic, string_message)
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

        # Get last ID for this topic
        last_id = self.last_ids.get(topic, "0-0")

        # Read messages
        response = await self.client.xread(
            {topic: last_id}, count=count, block=block
        )

        messages = []
        if response:
            for stream_name, stream_messages in response:
                for message_id, message_data in stream_messages:
                    # Update last ID
                    self.last_ids[topic] = message_id

                    # Parse message data
                    parsed_data = {}
                    for key, value in message_data.items():
                        try:
                            # Try to parse as JSON
                            parsed_data[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, use as is
                            parsed_data[key] = value

                    messages.append(parsed_data)

        return messages

    async def create_consumer_group(
        self, topic: str, group_name: str, start_id: str = "0"
    ) -> None:
        """Create a consumer group for a topic.

        Args:
            topic: The topic to create the group for.
            group_name: The name of the consumer group.
            start_id: The ID to start consuming from.
        """
        await self.ensure_connected()

        try:
            await self.client.xgroup_create(
                topic, group_name, id=start_id, mkstream=True
            )
            logger.info(f"Created consumer group {group_name} for topic {topic}")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group {group_name} already exists for topic {topic}")
            else:
                raise

    async def read_group(
        self,
        topic: str,
        group_name: str,
        consumer_name: Optional[str] = None,
        count: int = 10,
        block: int = 100,
        no_ack: bool = False,
    ) -> List[Dict[str, Any]]:
        """Read messages from a consumer group.

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
        await self.ensure_connected()

        # Use provided consumer name or default
        consumer = consumer_name or self.consumer_id

        # Read messages
        response = await self.client.xreadgroup(
            group_name,
            consumer,
            {topic: ">"},
            count=count,
            block=block,
            noack=no_ack,
        )

        messages = []
        if response:
            for stream_name, stream_messages in response:
                for message_id, message_data in stream_messages:
                    # Parse message data
                    parsed_data = {}
                    for key, value in message_data.items():
                        try:
                            # Try to parse as JSON
                            parsed_data[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, use as is
                            parsed_data[key] = value

                    # Add message ID
                    parsed_data["_id"] = message_id

                    messages.append(parsed_data)

        return messages

    async def acknowledge_message(
        self, topic: str, group_name: str, message_id: str
    ) -> None:
        """Acknowledge a message.

        Args:
            topic: The topic the message was read from.
            group_name: The name of the consumer group.
            message_id: The ID of the message to acknowledge.
        """
        await self.ensure_connected()

        await self.client.xack(topic, group_name, message_id)
        logger.debug(f"Acknowledged message {message_id} from {topic} for {group_name}")

    async def delete_message(self, topic: str, message_id: str) -> None:
        """Delete a message from a topic.

        Args:
            topic: The topic to delete from.
            message_id: The ID of the message to delete.
        """
        await self.ensure_connected()

        await self.client.xdel(topic, message_id)
        logger.debug(f"Deleted message {message_id} from {topic}")
