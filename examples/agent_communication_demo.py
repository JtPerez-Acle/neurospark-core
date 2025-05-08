#!/usr/bin/env python3
"""
Agent Communication Demo

This script demonstrates the enhanced agent communication system with
bidirectional communication capabilities.

It sets up two agents:
1. A tutor agent that can identify knowledge gaps and request clarifications
2. A professor agent that can provide content and respond to clarification requests

The agents communicate using the enhanced message system with specialized intents.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.enhanced_agent import EnhancedAgent
from src.agents.enhanced_message import EnhancedMessage, MessageFactory, MessageIntent
from src.agents.teaching.patterns import TeachingIntent, TeachingMessageMixin, TeachingPatterns
from src.common.config import Settings
from src.message_bus.base import MessageBus


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MockMessageBus(MessageBus):
    """Mock message bus for demonstration purposes."""

    def __init__(self):
        """Initialize the mock message bus."""
        self.messages = {}
        self.subscribers = {}

    async def connect(self) -> None:
        """Connect to the message bus."""
        logger.info("Connected to mock message bus")

    async def disconnect(self) -> None:
        """Disconnect from the message bus."""
        logger.info("Disconnected from mock message bus")

    async def publish_message(self, topic: str, message: Dict) -> None:
        """Publish a message to a topic."""
        logger.info(f"Publishing message to {topic}: {message}")
        if topic not in self.messages:
            self.messages[topic] = []
        self.messages[topic].append(message)

        # Deliver to subscribers
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                await callback(message)

    async def subscribe(self, topic: str, callback) -> None:
        """Subscribe to a topic."""
        logger.info(f"Subscribing to {topic}")
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)

    async def unsubscribe(self, topic: str, callback=None) -> None:
        """Unsubscribe from a topic.

        Args:
            topic: The topic to unsubscribe from.
            callback: Optional callback to remove. If None, removes all callbacks.
        """
        logger.info(f"Unsubscribing from {topic}")
        if callback is None:
            # Remove all callbacks for this topic
            if topic in self.subscribers:
                self.subscribers.pop(topic)
        else:
            # Remove specific callback
            if topic in self.subscribers and callback in self.subscribers[topic]:
                self.subscribers[topic].remove(callback)


class AgentDependencies:
    """Dependencies for agents."""

    def __init__(self, settings: Settings, message_bus: MessageBus):
        """Initialize agent dependencies."""
        self.settings = settings
        self.message_bus = message_bus


class TutorAgent(EnhancedAgent, TeachingMessageMixin):
    """Tutor agent that can identify knowledge gaps and request clarifications."""

    def __init__(self, agent_id: str, name: str, dependencies: AgentDependencies):
        """Initialize the tutor agent."""
        super().__init__(
            agent_id=agent_id,
            name=name,
            dependencies=dependencies,
            capabilities=["tutoring", "student-support"],
        )
        self.teaching_patterns = TeachingPatterns(self)
        self.received_content = []

    async def initialize(self) -> None:
        """Initialize the agent."""
        logger.info(f"Initializing {self.name}")
        await self.initialize_teaching_handlers()

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info(f"Cleaning up {self.name}")

    async def _handle_content_delivery(self, message: EnhancedMessage) -> None:
        """Handle a content delivery message."""
        logger.info(f"Received content: {message.payload['content']}")
        self.received_content.append(message.payload)

        # Send feedback about the content
        feedback = MessageFactory.create_feedback_message(
            sender=self.id,
            recipient=message.sender,
            about_message_id=message.id,
            feedback_data={
                "quality": "excellent",
                "relevance": "high",
                "suggestions": ["Add more examples", "Include visual aids"],
            },
        )

        await self.send_enhanced_message(feedback)


class ProfessorAgent(EnhancedAgent, TeachingMessageMixin):
    """Professor agent that can provide content and respond to clarification requests."""

    def __init__(self, agent_id: str, name: str, dependencies: AgentDependencies):
        """Initialize the professor agent."""
        super().__init__(
            agent_id=agent_id,
            name=name,
            dependencies=dependencies,
            capabilities=["content-creation", "knowledge-base"],
        )
        self.content_requests = []
        self.feedback_received = []

    async def initialize(self) -> None:
        """Initialize the agent."""
        logger.info(f"Initializing {self.name}")
        await self.initialize_teaching_handlers()

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info(f"Cleaning up {self.name}")

    async def _handle_knowledge_gap(self, message: EnhancedMessage) -> None:
        """Handle a knowledge gap message."""
        logger.info(f"Received knowledge gap: {message.payload}")
        self.content_requests.append(message.payload)

        # Create content based on the knowledge gap
        topic = message.payload.get("topic")
        content = f"Detailed explanation of {topic}: This is a comprehensive overview of the topic..."

        # Send content back to the requester
        response = MessageFactory.create_direct_message(
            sender=self.id,
            recipient=message.sender,
            payload={
                "content": content,
                "metadata": {
                    "topic": topic,
                    "created_at": datetime.utcnow().isoformat(),
                    "difficulty": message.payload.get("context", {}).get("difficulty", "beginner"),
                },
            },
            intent=TeachingIntent.CONTENT_DELIVERY,
            correlation_id=message.id,
        )

        await self.send_enhanced_message(response)

    async def _handle_clarification_request(self, message: EnhancedMessage) -> None:
        """Handle a clarification request message."""
        logger.info(f"Received clarification request: {message.payload}")

        # Create clarification response
        topic = message.payload.get("topic")
        question = message.payload.get("question")
        answer = f"Clarification for '{question}' regarding {topic}: Here's a detailed explanation..."

        # Send clarification back to the requester
        response = MessageFactory.create_direct_message(
            sender=self.id,
            recipient=message.sender,
            payload={
                "answer": answer,
                "topic": topic,
                "question": question,
            },
            intent=TeachingIntent.CLARIFICATION_RESPONSE,
            correlation_id=message.id,
        )

        await self.send_enhanced_message(response)

    async def _handle_feedback(self, message: EnhancedMessage) -> None:
        """Handle a feedback message."""
        logger.info(f"Received feedback: {message.payload}")
        self.feedback_received.append(message.payload)


async def run_demo():
    """Run the agent communication demo."""
    # Create dependencies
    settings = Settings()
    message_bus = MockMessageBus()
    dependencies = AgentDependencies(settings, message_bus)

    # Create agents
    tutor = TutorAgent("tutor-agent", "Tutor Agent", dependencies)
    professor = ProfessorAgent("professor-agent", "Professor Agent", dependencies)

    # Initialize agents
    await tutor.initialize()
    await professor.initialize()

    # Demonstrate knowledge gap identification
    logger.info("\n=== Knowledge Gap Identification ===")
    await tutor.teaching_patterns.identify_knowledge_gap(
        user_id="student123",
        topic="machine learning",
        context={"user_waiting": True, "difficulty": "intermediate"},
    )

    # Wait for message processing
    await asyncio.sleep(1)

    # Demonstrate clarification request
    logger.info("\n=== Clarification Request ===")
    await tutor.teaching_patterns.request_clarification(
        user_id="student123",
        topic="machine learning",
        question="What is backpropagation?",
    )

    # Wait for message processing
    await asyncio.sleep(1)

    # Print results
    logger.info("\n=== Results ===")
    logger.info(f"Professor content requests: {len(professor.content_requests)}")
    logger.info(f"Tutor received content: {len(tutor.received_content)}")
    logger.info(f"Professor feedback received: {len(professor.feedback_received)}")

    # Clean up
    await tutor.cleanup()
    await professor.cleanup()


if __name__ == "__main__":
    asyncio.run(run_demo())
