#!/usr/bin/env python3
"""
End-to-End Agent Communication Demo

This script demonstrates the enhanced agent communication system with
bidirectional communication capabilities using the actual Redis message bus.

It sets up two agents:
1. A tutor agent that can identify knowledge gaps and request clarifications
2. A professor agent that can provide content and respond to clarification requests

The agents communicate using the enhanced message system with specialized intents.
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.enhanced_agent import EnhancedAgent
from src.agents.enhanced_message import EnhancedMessage, MessageFactory, MessageIntent
from src.agents.teaching.patterns import TeachingIntent, TeachingMessageMixin, TeachingPatterns
from src.common.config import Settings
from src.message_bus.redis_streams import RedisStreamClient


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AgentDependencies:
    """Dependencies for agents."""

    def __init__(self, settings: Settings, message_bus: RedisStreamClient):
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
        await self.dependencies.message_bus.connect()
        await self.initialize_teaching_handlers()

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info(f"Cleaning up {self.name}")
        await self.dependencies.message_bus.disconnect()

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
        await self.dependencies.message_bus.connect()
        await self.initialize_teaching_handlers()

    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info(f"Cleaning up {self.name}")
        await self.dependencies.message_bus.disconnect()

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


def start_redis_container() -> Tuple[subprocess.Popen, str]:
    """Start a Redis container for the demo.
    
    Returns:
        A tuple containing the container process and container ID.
    """
    logger.info("Starting Redis container...")
    
    # Check if container already exists
    check_cmd = ["docker", "ps", "-q", "-f", "name=neurospark-redis-demo"]
    container_id = subprocess.check_output(check_cmd).decode().strip()
    
    if container_id:
        logger.info(f"Redis container already running with ID: {container_id}")
        return None, container_id
    
    # Start Redis container
    cmd = [
        "docker", "run", "--name", "neurospark-redis-demo",
        "-p", "6379:6379", "-d",
        "redis:7-alpine", "redis-server", "--requirepass", "redis_password"
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        logger.error(f"Failed to start Redis container: {stderr.decode()}")
        raise RuntimeError("Failed to start Redis container")
    
    container_id = stdout.decode().strip()
    logger.info(f"Redis container started with ID: {container_id}")
    
    # Wait for Redis to be ready
    time.sleep(2)
    
    return process, container_id


def stop_redis_container(container_id: str) -> None:
    """Stop and remove the Redis container.
    
    Args:
        container_id: The ID of the container to stop.
    """
    logger.info(f"Stopping Redis container {container_id}...")
    
    # Stop container
    stop_cmd = ["docker", "stop", container_id]
    subprocess.run(stop_cmd, check=True)
    
    # Remove container
    rm_cmd = ["docker", "rm", container_id]
    subprocess.run(rm_cmd, check=True)
    
    logger.info("Redis container stopped and removed")


async def run_demo():
    """Run the agent communication demo."""
    # Start Redis container
    redis_process, container_id = start_redis_container()
    
    try:
        # Create dependencies with real Redis connection
        settings = Settings()
        message_bus = RedisStreamClient(
            host="localhost",
            port=6379,
            password="redis_password"
        )
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
        await asyncio.sleep(2)
        
        # Demonstrate clarification request
        logger.info("\n=== Clarification Request ===")
        await tutor.teaching_patterns.request_clarification(
            user_id="student123",
            topic="machine learning",
            question="What is backpropagation?",
        )
        
        # Wait for message processing
        await asyncio.sleep(2)
        
        # Print results
        logger.info("\n=== Results ===")
        logger.info(f"Professor content requests: {len(professor.content_requests)}")
        logger.info(f"Tutor received content: {len(tutor.received_content)}")
        logger.info(f"Professor feedback received: {len(professor.feedback_received)}")
        
        # Clean up agents
        await tutor.cleanup()
        await professor.cleanup()
    
    finally:
        # Stop Redis container
        if container_id:
            stop_redis_container(container_id)


def handle_sigint(sig, frame):
    """Handle SIGINT signal."""
    logger.info("Received SIGINT, shutting down...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, handle_sigint)
    
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.exception(f"Error running demo: {e}")
