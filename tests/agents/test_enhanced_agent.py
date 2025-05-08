"""Tests for the enhanced Agent base class with bidirectional communication capabilities.

This module contains tests for the enhanced Agent base class, focusing on
bidirectional communication capabilities such as feedback, assistance requests,
and needs expression.
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType as BaseMessageType
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
from src.message_bus.base import MessageBus


class MockMessageBus(MessageBus):
    """Mock implementation of MessageBus for testing."""

    def __init__(self):
        self.published_messages = []
        self.subscribed_topics = set()
        self.message_callbacks = {}

    async def connect(self) -> None:
        """Connect to the message bus."""
        pass

    async def disconnect(self) -> None:
        """Disconnect from the message bus."""
        pass

    async def publish_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Publish a message to a topic."""
        self.published_messages.append((topic, message))

    async def subscribe(self, topic: str, callback: callable) -> None:
        """Subscribe to a topic."""
        self.subscribed_topics.add(topic)
        self.message_callbacks[topic] = callback

    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        if topic in self.subscribed_topics:
            self.subscribed_topics.remove(topic)
            if topic in self.message_callbacks:
                del self.message_callbacks[topic]

    def get_published_messages(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all published messages, optionally filtered by topic."""
        if topic:
            return [msg for t, msg in self.published_messages if t == topic]
        return [msg for _, msg in self.published_messages]

    async def simulate_message(self, topic: str, message: Dict[str, Any]) -> None:
        """Simulate receiving a message on a topic."""
        if topic in self.message_callbacks:
            await self.message_callbacks[topic](message)


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for testing."""
    return AgentDependencies(
        message_bus=MockMessageBus(),
        settings=MagicMock(),
    )


class TestAgent(EnhancedAgent):
    """Test agent implementation for testing."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        dependencies: AgentDependencies,
        capabilities: Optional[List[str]] = None,
    ):
        """Initialize the test agent."""
        super().__init__(agent_id, name, dependencies, capabilities)
        self._register_default_handlers()

    async def initialize(self) -> None:
        """Initialize the agent."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def _handle_command(self, message: Message) -> None:
        """Handle a command message."""
        pass


@pytest.fixture
def test_agent(mock_dependencies):
    """Create a test agent for testing."""
    agent = TestAgent(
        agent_id="test-agent",
        name="Test Agent",
        dependencies=mock_dependencies,
        capabilities=["test"],
    )
    return agent


@pytest.mark.asyncio
async def test_send_feedback(test_agent):
    """Test sending feedback to another agent."""
    # Setup
    recipient_id = "recipient-agent"
    message_id = str(uuid.uuid4())
    feedback_data = {
        "quality": 8,
        "relevance": 9,
        "suggestions": ["Improve clarity", "Add more examples"],
    }

    # Execute
    await test_agent.send_feedback(
        recipient_id=recipient_id,
        about_message_id=message_id,
        feedback_data=feedback_data
    )

    # Verify
    message_bus = test_agent.dependencies.message_bus
    messages = message_bus.get_published_messages(f"agent.{recipient_id}")

    assert len(messages) == 1
    message = messages[0]
    assert message["type"] == EnhancedMessageType.FEEDBACK
    assert message["sender"] == test_agent.id
    assert message["recipient"] == recipient_id
    assert message["payload"]["about_message_id"] == message_id
    assert message["payload"]["feedback_data"] == feedback_data


@pytest.mark.asyncio
async def test_request_assistance(test_agent):
    """Test requesting assistance from another agent."""
    # Setup
    recipient_id = "helper-agent"
    request_type = "data-analysis"
    context = {"data_source": "customer-survey", "format": "csv"}

    # Execute
    request_id = await test_agent.request_assistance(
        recipient_id=recipient_id,
        request_type=request_type,
        context=context,
        timeout_seconds=60
    )

    # Verify
    message_bus = test_agent.dependencies.message_bus
    messages = message_bus.get_published_messages(f"agent.{recipient_id}")

    assert len(messages) == 1
    message = messages[0]
    assert message["type"] == EnhancedMessageType.ASSISTANCE_REQUEST
    assert message["sender"] == test_agent.id
    assert message["recipient"] == recipient_id
    assert message["payload"]["request_type"] == request_type
    assert message["payload"]["context"] == context
    assert message["id"] == request_id

    # Verify request tracking
    assert request_id in test_agent._pending_requests
    pending_request = test_agent._pending_requests[request_id]
    assert pending_request["recipient"] == recipient_id
    assert pending_request["request_type"] == request_type
    assert pending_request["expires_at"] > datetime.utcnow()


@pytest.mark.asyncio
async def test_express_need(test_agent):
    """Test expressing a need to agents with specific capabilities."""
    # Setup
    need_type = "data-source"
    need_description = "Need access to customer survey data"
    required_capabilities = ["data-access", "storage"]

    # Execute
    need_id = await test_agent.express_need(
        need_type=need_type,
        description=need_description,
        required_capabilities=required_capabilities,
        urgency="high"
    )

    # Verify
    message_bus = test_agent.dependencies.message_bus
    messages = message_bus.get_published_messages("agent.broadcast")

    assert len(messages) == 1
    message = messages[0]
    assert message["type"] == EnhancedMessageType.NEED_EXPRESSION
    assert message["sender"] == test_agent.id
    assert message["payload"]["need_type"] == need_type
    assert message["payload"]["description"] == need_description
    assert message["payload"]["required_capabilities"] == required_capabilities
    assert message["urgency"] == "high"
    assert message["id"] == need_id

    # Verify need tracking
    assert need_id in test_agent._expressed_needs
    expressed_need = test_agent._expressed_needs[need_id]
    assert expressed_need["need_type"] == need_type
    assert expressed_need["required_capabilities"] == required_capabilities


@pytest.mark.asyncio
async def test_handle_feedback(test_agent):
    """Test handling feedback from another agent."""
    # Setup
    sender_id = "sender-agent"
    about_message_id = str(uuid.uuid4())
    feedback_data = {
        "quality": 7,
        "relevance": 8,
        "suggestions": ["Be more concise"],
    }

    feedback_message = FeedbackMessage(
        id=str(uuid.uuid4()),
        sender=sender_id,
        recipient=test_agent.id,
        payload={
            "about_message_id": about_message_id,
            "feedback_data": feedback_data,
        },
    )

    # Create a mock handler
    mock_handler = AsyncMock()

    # Replace the handler
    original_handler = test_agent._message_handlers[EnhancedMessageType.FEEDBACK]
    test_agent._message_handlers[EnhancedMessageType.FEEDBACK] = mock_handler

    # Execute
    await test_agent.process_message(feedback_message)

    # Verify the mock was called
    mock_handler.assert_called_once_with(feedback_message)

    # Restore the original handler
    test_agent._message_handlers[EnhancedMessageType.FEEDBACK] = original_handler


@pytest.mark.asyncio
async def test_handle_assistance_request(test_agent):
    """Test handling an assistance request from another agent."""
    # Setup
    sender_id = "requester-agent"
    request_type = "data-analysis"
    context = {"data_source": "customer-survey", "format": "csv"}

    request_message = AssistanceRequestMessage(
        id=str(uuid.uuid4()),
        sender=sender_id,
        recipient=test_agent.id,
        payload={
            "request_type": request_type,
            "context": context,
        },
    )

    # Create a mock handler
    mock_handler = AsyncMock()

    # Replace the handler
    original_handler = test_agent._message_handlers[EnhancedMessageType.ASSISTANCE_REQUEST]
    test_agent._message_handlers[EnhancedMessageType.ASSISTANCE_REQUEST] = mock_handler

    # Execute
    await test_agent.process_message(request_message)

    # Verify the mock was called
    mock_handler.assert_called_once_with(request_message)

    # Restore the original handler
    test_agent._message_handlers[EnhancedMessageType.ASSISTANCE_REQUEST] = original_handler


@pytest.mark.asyncio
async def test_handle_need_expression(test_agent):
    """Test handling a need expression from another agent."""
    # Setup
    sender_id = "needy-agent"
    need_type = "data-source"
    description = "Need access to customer survey data"
    required_capabilities = ["data-access", "storage"]

    need_message = NeedExpressionMessage(
        id=str(uuid.uuid4()),
        sender=sender_id,
        recipient=None,  # Broadcast
        payload={
            "need_type": need_type,
            "description": description,
            "required_capabilities": required_capabilities,
            "urgency": "high",
        },
    )

    # Create a mock handler
    mock_handler = AsyncMock()

    # Replace the handler
    original_handler = test_agent._message_handlers[EnhancedMessageType.NEED_EXPRESSION]
    test_agent._message_handlers[EnhancedMessageType.NEED_EXPRESSION] = mock_handler

    # Execute
    await test_agent.process_message(need_message)

    # Verify the mock was called
    mock_handler.assert_called_once_with(need_message)

    # Restore the original handler
    test_agent._message_handlers[EnhancedMessageType.NEED_EXPRESSION] = original_handler


@pytest.mark.asyncio
async def test_register_custom_handler(test_agent):
    """Test registering a custom message handler."""
    # Setup
    custom_handler = AsyncMock()
    custom_message_type = EnhancedMessageType.NOTIFICATION  # Use a valid message type

    # Execute
    test_agent.register_message_handler(custom_message_type, custom_handler)

    # Create a custom message with the custom type
    custom_message = EnhancedMessage(
        id=str(uuid.uuid4()),
        type=custom_message_type,
        sender="sender-agent",
        recipient=test_agent.id,
        payload={"custom": "data"},
    )

    # Process the message
    await test_agent.process_message(custom_message)

    # Verify
    custom_handler.assert_called_once_with(custom_message)
