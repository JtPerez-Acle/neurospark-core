"""Tests for teaching-specific communication patterns.

This module contains tests for teaching-specific communication patterns between agents.
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
from src.agents.teaching.patterns import (
    TeachingIntent,
    TeachingPatterns,
    TeachingMessageMixin,
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


class TestTutorAgent(EnhancedAgent, TeachingMessageMixin):
    """Test Tutor Agent for testing teaching patterns."""

    def __init__(self, agent_id: str, name: str, dependencies: AgentDependencies):
        """Initialize the test tutor agent."""
        super().__init__(
            agent_id=agent_id,
            name=name,
            dependencies=dependencies,
            capabilities=["teaching", "conversation"],
        )
        self.teaching_patterns = TeachingPatterns(self)

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.initialize_teaching_handlers()

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass


class TestProfessorAgent(EnhancedAgent, TeachingMessageMixin):
    """Test Professor Agent for testing teaching patterns."""

    def __init__(self, agent_id: str, name: str, dependencies: AgentDependencies):
        """Initialize the test professor agent."""
        super().__init__(
            agent_id=agent_id,
            name=name,
            dependencies=dependencies,
            capabilities=["content-creation", "knowledge-base"],
        )
        self.teaching_patterns = TeachingPatterns(self)
        self.content_requests = []

    async def initialize(self) -> None:
        """Initialize the agent."""
        await self.initialize_teaching_handlers()

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def _handle_knowledge_gap(self, message: EnhancedMessage) -> None:
        """Handle a knowledge gap message."""
        # Override the default handler from TeachingMessageMixin
        # Store the request for verification in tests
        self.content_requests.append(message.payload)

        # Create content based on the knowledge gap
        topic = message.payload.get("topic")
        content = f"Content for {topic}"

        # Send content back to the requester
        response = MessageFactory.create_direct_message(
            sender=self.id,
            recipient=message.sender,
            payload={
                "content": content,
                "metadata": {
                    "topic": topic,
                    "created_at": datetime.utcnow().isoformat(),
                },
            },
            intent=TeachingIntent.CONTENT_DELIVERY,
            correlation_id=message.id,
        )

        await self.send_enhanced_message(response)


@pytest.mark.asyncio
async def test_knowledge_gap_identification(mock_dependencies):
    """Test knowledge gap identification pattern."""
    # Setup
    tutor = TestTutorAgent("tutor-agent", "Test Tutor", mock_dependencies)
    professor = TestProfessorAgent("professor-agent", "Test Professor", mock_dependencies)

    # Initialize agents
    await tutor.initialize()
    await professor.initialize()

    # Execute knowledge gap identification
    gap_id = await tutor.teaching_patterns.identify_knowledge_gap(
        user_id="user123",
        topic="machine learning",
        context={"user_waiting": True, "difficulty": "intermediate"},
    )

    # Get the message from the message bus
    message_bus = mock_dependencies.message_bus
    messages = message_bus.get_published_messages(f"agent.professor-agent")

    # Verify message was sent
    assert len(messages) == 1
    message = messages[0]
    assert message["intent"] == TeachingIntent.KNOWLEDGE_GAP
    assert message["sender"] == "tutor-agent"
    assert message["recipient"] == "professor-agent"
    assert message["payload"]["topic"] == "machine learning"
    assert message["payload"]["user_id"] == "user123"
    assert message["payload"]["context"]["user_waiting"] is True

    # Simulate professor receiving and processing the message
    # First call the handler directly to ensure the content_requests list is updated
    enhanced_message = EnhancedMessage.model_validate(message)
    await professor._handle_knowledge_gap(enhanced_message)

    # Verify professor processed the message
    assert len(professor.content_requests) == 1
    assert professor.content_requests[0]["topic"] == "machine learning"

    # Verify professor sent a response
    response_messages = message_bus.get_published_messages(f"agent.tutor-agent")
    assert len(response_messages) == 1
    response = response_messages[0]
    assert response["intent"] == TeachingIntent.CONTENT_DELIVERY
    assert response["sender"] == "professor-agent"
    assert response["recipient"] == "tutor-agent"
    assert "Content for machine learning" in response["payload"]["content"]
    assert response["correlation_id"] == message["id"]


@pytest.mark.asyncio
async def test_student_progress_reporting(mock_dependencies):
    """Test student progress reporting pattern."""
    # Setup
    tutor = TestTutorAgent("tutor-agent", "Test Tutor", mock_dependencies)
    professor = TestProfessorAgent("professor-agent", "Test Professor", mock_dependencies)

    # Initialize agents
    await tutor.initialize()
    await professor.initialize()

    # Execute student progress reporting
    progress_id = await tutor.teaching_patterns.report_student_progress(
        user_id="user123",
        topic="machine learning",
        mastery_level=0.7,
        learning_style="visual",
        pain_points=["neural networks", "backpropagation"],
    )

    # Get the message from the message bus
    message_bus = mock_dependencies.message_bus
    messages = message_bus.get_published_messages(f"agent.professor-agent")

    # Verify message was sent
    assert len(messages) == 1
    message = messages[0]
    assert message["intent"] == TeachingIntent.STUDENT_PROGRESS
    assert message["sender"] == "tutor-agent"
    assert message["recipient"] == "professor-agent"
    assert message["payload"]["topic"] == "machine learning"
    assert message["payload"]["user_id"] == "user123"
    assert message["payload"]["mastery_level"] == 0.7
    assert message["payload"]["learning_style"] == "visual"
    assert "neural networks" in message["payload"]["pain_points"]


@pytest.mark.asyncio
async def test_clarification_request(mock_dependencies):
    """Test clarification request pattern."""
    # Setup
    tutor = TestTutorAgent("tutor-agent", "Test Tutor", mock_dependencies)
    professor = TestProfessorAgent("professor-agent", "Test Professor", mock_dependencies)

    # Initialize agents
    await tutor.initialize()
    await professor.initialize()

    # Execute clarification request
    clarification_id = await tutor.teaching_patterns.request_clarification(
        user_id="user123",
        topic="machine learning",
        question="What is backpropagation?",
    )

    # Get the message from the message bus
    message_bus = mock_dependencies.message_bus
    messages = message_bus.get_published_messages(f"agent.professor-agent")

    # Verify message was sent
    assert len(messages) == 1
    message = messages[0]
    assert message["intent"] == TeachingIntent.CLARIFICATION_REQUEST
    assert message["sender"] == "tutor-agent"
    assert message["recipient"] == "professor-agent"
    assert message["payload"]["topic"] == "machine learning"
    assert message["payload"]["user_id"] == "user123"
    assert message["payload"]["question"] == "What is backpropagation?"
