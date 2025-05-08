"""Tests for message bus module."""

import pytest
from unittest.mock import patch, MagicMock, call
import json
import time

from src.message_bus.redis_streams import (
    RedisMessageBus,
    Message,
    StreamConfig,
)

# We'll use the actual RedisMessageBus class for testing


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    with patch("src.message_bus.redis_streams.Redis") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def redis_message_bus(mock_redis_client):
    """Create a RedisMessageBus instance with a mock client."""
    return RedisMessageBus(
        host="localhost",
        port=6379,
        password="redis_password",
    )


def test_init_with_host_port():
    """Test initializing RedisMessageBus with host and port."""
    with patch("src.message_bus.redis_streams.Redis") as mock_client_class:
        message_bus = RedisMessageBus(
            host="localhost",
            port=6379,
            password="redis_password",
        )

        mock_client_class.assert_called_once_with(
            host="localhost",
            port=6379,
            password="redis_password",
            decode_responses=True,
        )


def test_init_with_url():
    """Test initializing RedisMessageBus with URL."""
    with patch("src.message_bus.redis_streams.Redis") as mock_client_class:
        message_bus = RedisMessageBus(
            url="redis://:redis_password@localhost:6379",
        )

        mock_client_class.assert_called_once_with(
            url="redis://:redis_password@localhost:6379",
            decode_responses=True,
        )


def test_create_stream(redis_message_bus, mock_redis_client):
    """Test creating a stream."""
    # Setup
    stream_name = "test-stream"

    # Execute
    redis_message_bus.create_stream(stream_name)

    # Assert
    mock_redis_client.xinfo_stream.assert_called_once_with(stream_name, full=True)


def test_create_stream_with_error(redis_message_bus, mock_redis_client):
    """Test creating a stream with an error."""
    # Setup
    stream_name = "test-stream"
    mock_redis_client.xinfo_stream.side_effect = Exception("Stream does not exist")

    # Execute
    redis_message_bus.create_stream(stream_name)

    # Assert
    mock_redis_client.xinfo_stream.assert_called_once_with(stream_name, full=True)
    mock_redis_client.xadd.assert_called_once_with(
        stream_name, {"init": "true"}, id="0-0"
    )


def test_create_consumer_group(redis_message_bus, mock_redis_client):
    """Test creating a consumer group."""
    # Setup
    stream_name = "test-stream"
    group_name = "test-group"

    # Execute
    redis_message_bus.create_consumer_group(stream_name, group_name)

    # Assert
    mock_redis_client.xgroup_create.assert_called_once_with(
        stream_name, group_name, id="0", mkstream=True
    )


def test_create_consumer_group_with_error(redis_message_bus, mock_redis_client):
    """Test creating a consumer group with an error."""
    # Setup
    stream_name = "test-stream"
    group_name = "test-group"
    mock_redis_client.xgroup_create.side_effect = Exception("Group already exists")

    # Execute
    redis_message_bus.create_consumer_group(stream_name, group_name)

    # Assert
    mock_redis_client.xgroup_create.assert_called_once_with(
        stream_name, group_name, id="0", mkstream=True
    )


def test_publish_message(redis_message_bus, mock_redis_client):
    """Test publishing a message."""
    # Setup
    stream_name = "test-stream"
    message = {"key": "value"}
    mock_redis_client.xadd.return_value = "1234567890-0"

    # Execute
    message_id = redis_message_bus.publish_message(stream_name, message)

    # Assert
    mock_redis_client.xadd.assert_called_once_with(stream_name, message)
    assert message_id == "1234567890-0"


def test_consume_messages(redis_message_bus, mock_redis_client):
    """Test consuming messages."""
    # Setup
    stream_config = StreamConfig(
        stream_name="test-stream",
        group_name="test-group",
        consumer_name="test-consumer",
    )

    mock_response = [
        [
            "test-stream",
            [
                ["1234567890-0", {"key": "value1"}],
                ["1234567891-0", {"key": "value2"}],
            ],
        ]
    ]
    mock_redis_client.xreadgroup.return_value = mock_response

    # Execute
    messages = redis_message_bus.consume_messages(stream_config, count=2)

    # Assert
    mock_redis_client.xreadgroup.assert_called_once_with(
        groupname="test-group",
        consumername="test-consumer",
        streams={"test-stream": ">"},
        count=2,
        block=None,
    )

    assert len(messages) == 2
    assert messages[0].id == "1234567890-0"
    assert messages[0].data == {"key": "value1"}
    assert messages[1].id == "1234567891-0"
    assert messages[1].data == {"key": "value2"}


def test_consume_messages_with_block(redis_message_bus, mock_redis_client):
    """Test consuming messages with block."""
    # Setup
    stream_config = StreamConfig(
        stream_name="test-stream",
        group_name="test-group",
        consumer_name="test-consumer",
    )

    mock_response = [
        [
            "test-stream",
            [
                ["1234567890-0", {"key": "value"}],
            ],
        ]
    ]
    mock_redis_client.xreadgroup.return_value = mock_response

    # Execute
    messages = redis_message_bus.consume_messages(
        stream_config, count=1, block=1000
    )

    # Assert
    mock_redis_client.xreadgroup.assert_called_once_with(
        groupname="test-group",
        consumername="test-consumer",
        streams={"test-stream": ">"},
        count=1,
        block=1000,
    )

    assert len(messages) == 1
    assert messages[0].id == "1234567890-0"
    assert messages[0].data == {"key": "value"}


def test_consume_messages_empty(redis_message_bus, mock_redis_client):
    """Test consuming messages with empty response."""
    # Setup
    stream_config = StreamConfig(
        stream_name="test-stream",
        group_name="test-group",
        consumer_name="test-consumer",
    )

    mock_redis_client.xreadgroup.return_value = []

    # Execute
    messages = redis_message_bus.consume_messages(stream_config, count=1)

    # Assert
    mock_redis_client.xreadgroup.assert_called_once_with(
        groupname="test-group",
        consumername="test-consumer",
        streams={"test-stream": ">"},
        count=1,
        block=None,
    )

    assert len(messages) == 0


def test_acknowledge_message(redis_message_bus, mock_redis_client):
    """Test acknowledging a message."""
    # Setup
    stream_name = "test-stream"
    group_name = "test-group"
    message_id = "1234567890-0"

    # Execute
    redis_message_bus.acknowledge_message(stream_name, group_name, message_id)

    # Assert
    mock_redis_client.xack.assert_called_once_with(
        stream_name, group_name, message_id
    )


def test_acknowledge_messages(redis_message_bus, mock_redis_client):
    """Test acknowledging multiple messages."""
    # Setup
    stream_name = "test-stream"
    group_name = "test-group"
    message_ids = ["1234567890-0", "1234567891-0"]

    # Execute
    redis_message_bus.acknowledge_messages(stream_name, group_name, message_ids)

    # Assert
    mock_redis_client.xack.assert_called_once_with(
        stream_name, group_name, *message_ids
    )


def test_get_pending_messages(redis_message_bus, mock_redis_client):
    """Test getting pending messages."""
    # Setup
    stream_name = "test-stream"
    group_name = "test-group"

    mock_response = {
        "pending": 2,
        "min": "1234567890-0",
        "max": "1234567891-0",
        "consumers": {
            "test-consumer": 2,
        },
    }
    mock_redis_client.xpending.return_value = mock_response

    # Execute
    pending_info = redis_message_bus.get_pending_messages(stream_name, group_name)

    # Assert
    mock_redis_client.xpending.assert_called_once_with(
        stream_name, group_name
    )

    assert pending_info == mock_response


def test_get_stream_info(redis_message_bus, mock_redis_client):
    """Test getting stream info."""
    # Setup
    stream_name = "test-stream"

    mock_response = {
        "length": 10,
        "radix-tree-keys": 1,
        "radix-tree-nodes": 2,
        "groups": 1,
        "last-generated-id": "1234567899-0",
        "first-entry": ["1234567890-0", {"key": "value1"}],
        "last-entry": ["1234567899-0", {"key": "value10"}],
    }
    mock_redis_client.xinfo_stream.return_value = mock_response

    # Execute
    stream_info = redis_message_bus.get_stream_info(stream_name)

    # Assert
    mock_redis_client.xinfo_stream.assert_called_once_with(
        stream_name, full=True
    )

    assert stream_info == mock_response
