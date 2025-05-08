"""Tests for the needs expression protocol.

This module contains tests for the needs expression protocol, including
needs expression, fulfillment, and tracking.
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import AgentDependencies, AgentState
from src.agents.enhanced_agent import EnhancedAgent
from src.agents.enhanced_message import (
    EnhancedMessage,
    MessageFactory,
    MessageIntent,
    MessageType,
    UrgencyLevel,
)
from src.agents.needs.protocol import (
    NeedType,
    NeedsProtocol,
    NeedsExpressionMixin,
    NeedsFulfillmentMixin,
)


class MockMessageBus:
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


class TestNeedyAgent(EnhancedAgent, NeedsExpressionMixin):
    """Test agent that expresses needs."""

    def __init__(self, agent_id: str, name: str, dependencies: AgentDependencies):
        """Initialize the test needy agent."""
        EnhancedAgent.__init__(
            self,
            agent_id=agent_id,
            name=name,
            dependencies=dependencies,
            capabilities=["test"],
        )
        NeedsExpressionMixin.__init__(self, self)

    async def initialize(self) -> None:
        """Initialize the agent."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


class TestProviderAgent(EnhancedAgent, NeedsFulfillmentMixin):
    """Test agent that fulfills needs."""

    def __init__(self, agent_id: str, name: str, dependencies: AgentDependencies):
        """Initialize the test provider agent."""
        EnhancedAgent.__init__(
            self,
            agent_id=agent_id,
            name=name,
            dependencies=dependencies,
            capabilities=["data-access", "storage"],
        )
        NeedsFulfillmentMixin.__init__(self, self)

    async def initialize(self) -> None:
        """Initialize the agent."""
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


@pytest.mark.asyncio
async def test_express_need(mock_dependencies):
    """Test expressing a need."""
    # Setup
    needy_agent = TestNeedyAgent("needy-agent", "Test Needy Agent", mock_dependencies)

    # Execute
    need_id = await needy_agent.needs_protocol.express_need(
        need_type=NeedType.DATA_SOURCE,
        description="Need access to customer survey data",
        required_capabilities=["data-access", "storage"],
        context={"format": "csv", "timeframe": "last_month"},
        urgency=UrgencyLevel.HIGH,
    )

    # Verify
    message_bus = mock_dependencies.message_bus
    messages = message_bus.get_published_messages("agent.broadcast")

    assert len(messages) == 1
    message = messages[0]
    assert message["type"] == MessageType.NEED_EXPRESSION
    assert message["sender"] == "needy-agent"
    assert message["recipient"] is None  # Broadcast
    assert message["payload"]["need_type"] == NeedType.DATA_SOURCE
    assert message["payload"]["description"] == "Need access to customer survey data"
    assert message["payload"]["required_capabilities"] == ["data-access", "storage"]
    assert message["payload"]["context"] == {"format": "csv", "timeframe": "last_month"}
    assert message["urgency"] == UrgencyLevel.HIGH
    assert "expires_at" in message["payload"]

    # Verify need tracking
    expressed_need = needy_agent.get_expressed_need(need_id)
    assert expressed_need is not None
    assert expressed_need["need_type"] == NeedType.DATA_SOURCE
    assert expressed_need["description"] == "Need access to customer survey data"
    assert expressed_need["required_capabilities"] == ["data-access", "storage"]
    assert expressed_need["context"] == {"format": "csv", "timeframe": "last_month"}
    assert expressed_need["status"] == "pending"


@pytest.mark.asyncio
async def test_fulfill_need(mock_dependencies):
    """Test fulfilling a need."""
    # Setup
    needy_agent = TestNeedyAgent("needy-agent", "Test Needy Agent", mock_dependencies)
    provider_agent = TestProviderAgent("provider-agent", "Test Provider Agent", mock_dependencies)

    # Express a need
    need_id = await needy_agent.needs_protocol.express_need(
        need_type=NeedType.DATA_SOURCE,
        description="Need access to customer survey data",
        required_capabilities=["data-access", "storage"],
    )

    # Fulfill the need
    fulfillment_id = await provider_agent.fulfill_need(
        need_id=need_id,
        sender_id="needy-agent",
        fulfillment_data={
            "data_source": "https://example.com/data/customer-survey.csv",
            "access_token": "abc123",
            "expiration": "2023-12-31T23:59:59Z",
        },
    )

    # Verify
    message_bus = mock_dependencies.message_bus
    messages = message_bus.get_published_messages("agent.needy-agent")

    assert len(messages) == 1
    message = messages[0]
    assert message["type"] == MessageType.NEED_FULFILLMENT
    assert message["sender"] == "provider-agent"
    assert message["recipient"] == "needy-agent"
    assert message["payload"]["need_id"] == need_id
    assert "data_source" in message["payload"]["fulfillment_data"]
    assert "access_token" in message["payload"]["fulfillment_data"]
    assert message["correlation_id"] == need_id

    # Verify fulfillment tracking
    fulfilled_needs = provider_agent.get_fulfilled_needs(need_id)
    assert len(fulfilled_needs) == 1
    assert fulfilled_needs[0]["recipient"] == "needy-agent"
    assert "data_source" in fulfilled_needs[0]["fulfillment_data"]
    assert "access_token" in fulfilled_needs[0]["fulfillment_data"]


@pytest.mark.asyncio
async def test_get_expressed_needs(mock_dependencies):
    """Test getting expressed needs."""
    # Setup
    needy_agent = TestNeedyAgent("needy-agent", "Test Needy Agent", mock_dependencies)

    # Express multiple needs
    need_id1 = await needy_agent.needs_protocol.express_need(
        need_type=NeedType.DATA_SOURCE,
        description="Need access to customer survey data",
        required_capabilities=["data-access"],
    )

    need_id2 = await needy_agent.needs_protocol.express_need(
        need_type=NeedType.API_ACCESS,
        description="Need access to external API",
        required_capabilities=["api-access"],
    )

    # Get all expressed needs
    all_needs = needy_agent.get_expressed_needs()
    assert len(all_needs) == 2

    # Get needs by type
    data_needs = needy_agent.get_expressed_needs(need_type=NeedType.DATA_SOURCE)
    assert len(data_needs) == 1
    assert data_needs[0]["need_type"] == NeedType.DATA_SOURCE

    api_needs = needy_agent.get_expressed_needs(need_type=NeedType.API_ACCESS)
    assert len(api_needs) == 1
    assert api_needs[0]["need_type"] == NeedType.API_ACCESS

    # Get needs by status
    pending_needs = needy_agent.get_expressed_needs(status="pending")
    assert len(pending_needs) == 2

    # Mark one need as fulfilled
    needy_agent.needs_protocol._expressed_needs[need_id1]["status"] = "fulfilled"

    # Get needs by status again
    pending_needs = needy_agent.get_expressed_needs(status="pending")
    assert len(pending_needs) == 1
    assert pending_needs[0]["id"] == need_id2

    fulfilled_needs = needy_agent.get_expressed_needs(status="fulfilled")
    assert len(fulfilled_needs) == 1
    assert fulfilled_needs[0]["id"] == need_id1
