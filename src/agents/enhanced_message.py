"""Enhanced message types and schemas for bidirectional agent communication.

This module provides enhanced message types and schemas for bidirectional
communication between agents, including feedback, assistance requests, and
needs expression.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Enum representing the types of messages that can be exchanged between agents."""

    # Standard message types
    COMMAND = "command"
    EVENT = "event"
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"

    # Enhanced message types for bidirectional communication
    FEEDBACK = "feedback"
    ASSISTANCE_REQUEST = "assistance_request"
    ASSISTANCE_RESPONSE = "assistance_response"
    NEED_EXPRESSION = "need_expression"
    NEED_FULFILLMENT = "need_fulfillment"
    TEACHING = "teaching"
    LEARNING = "learning"


class MessageIntent(str, Enum):
    """Enum representing the intent of a message."""

    # General intents
    INFORM = "inform"
    REQUEST = "request"
    RESPOND = "respond"
    NOTIFY = "notify"

    # Feedback intents
    PROVIDE_FEEDBACK = "provide_feedback"
    REQUEST_FEEDBACK = "request_feedback"

    # Assistance intents
    REQUEST_ASSISTANCE = "request_assistance"
    OFFER_ASSISTANCE = "offer_assistance"

    # Need intents
    EXPRESS_NEED = "express_need"
    FULFILL_NEED = "fulfill_need"

    # Teaching intents
    TEACH = "teach"
    LEARN = "learn"
    CLARIFY = "clarify"
    ASSESS = "assess"

    # Specialized teaching intents
    KNOWLEDGE_GAP = "knowledge_gap"
    CONTENT_REQUEST = "content_request"
    CONTENT_DELIVERY = "content_delivery"
    CONTENT_REVIEW = "content_review"
    CONTENT_FEEDBACK = "content_feedback"
    CLARIFICATION_REQUEST = "clarification_request"
    CLARIFICATION_RESPONSE = "clarification_response"
    STUDENT_PROGRESS = "student_progress"
    CURRICULUM_UPDATE = "curriculum_update"
    LEARNING_ASSESSMENT = "learning_assessment"
    LEARNING_FEEDBACK = "learning_feedback"


class UrgencyLevel(str, Enum):
    """Enum representing the urgency level of a message."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EnhancedMessage(BaseModel):
    """Enhanced message class for bidirectional agent communication."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    sender: str
    recipient: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None

    # Enhanced fields
    intent: Optional[MessageIntent] = None
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    requires_response: bool = False
    response_by: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackMessage(EnhancedMessage):
    """Feedback message for providing feedback about previous messages or content."""

    type: MessageType = MessageType.FEEDBACK
    intent: MessageIntent = MessageIntent.PROVIDE_FEEDBACK

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "sender": "reviewer-agent",
                "recipient": "professor-agent",
                "payload": {
                    "about_message_id": "550e8400-e29b-41d4-a716-446655440001",
                    "feedback_data": {
                        "quality": 8,
                        "relevance": 9,
                        "suggestions": ["Improve clarity", "Add more examples"],
                    }
                },
                "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }


class AssistanceRequestMessage(EnhancedMessage):
    """Assistance request message for requesting help from other agents."""

    type: MessageType = MessageType.ASSISTANCE_REQUEST
    intent: MessageIntent = MessageIntent.REQUEST_ASSISTANCE
    requires_response: bool = True

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "sender": "tutor-agent",
                "recipient": "professor-agent",
                "payload": {
                    "request_type": "content-creation",
                    "context": {
                        "topic": "machine learning",
                        "difficulty": "intermediate",
                        "format": "lesson",
                    }
                },
                "urgency": "high",
                "requires_response": True,
                "response_by": "2023-01-01T12:00:00Z",
            }
        }


class AssistanceResponseMessage(EnhancedMessage):
    """Assistance response message for responding to assistance requests."""

    type: MessageType = MessageType.ASSISTANCE_RESPONSE
    intent: MessageIntent = MessageIntent.RESPOND

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "sender": "professor-agent",
                "recipient": "tutor-agent",
                "payload": {
                    "content": "...",
                    "metadata": {
                        "topic": "machine learning",
                        "difficulty": "intermediate",
                        "format": "lesson",
                    }
                },
                "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }


class NeedExpressionMessage(EnhancedMessage):
    """Need expression message for expressing needs to other agents."""

    type: MessageType = MessageType.NEED_EXPRESSION
    intent: MessageIntent = MessageIntent.EXPRESS_NEED

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "sender": "professor-agent",
                "recipient": None,  # Broadcast
                "payload": {
                    "need_type": "data-source",
                    "description": "Need access to machine learning datasets",
                    "required_capabilities": ["data-access", "storage"],
                },
                "urgency": "normal",
            }
        }


class NeedFulfillmentMessage(EnhancedMessage):
    """Need fulfillment message for fulfilling needs expressed by other agents."""

    type: MessageType = MessageType.NEED_FULFILLMENT
    intent: MessageIntent = MessageIntent.FULFILL_NEED

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "sender": "curator-agent",
                "recipient": "professor-agent",
                "payload": {
                    "need_id": "550e8400-e29b-41d4-a716-446655440001",
                    "fulfillment_data": {
                        "data_source": "https://example.com/datasets/ml",
                        "access_token": "...",
                    }
                },
                "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }


class MessageFactory:
    """Factory for creating different types of messages."""

    @staticmethod
    def create_direct_message(
        sender: str,
        recipient: str,
        payload: Dict[str, Any],
        intent: MessageIntent = MessageIntent.INFORM,
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
        requires_response: bool = False,
        response_by: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
    ) -> EnhancedMessage:
        """Create a direct message to a specific recipient."""
        return EnhancedMessage(
            type=MessageType.NOTIFICATION,
            sender=sender,
            recipient=recipient,
            payload=payload,
            intent=intent,
            urgency=urgency,
            requires_response=requires_response,
            response_by=response_by,
            correlation_id=correlation_id,
        )

    @staticmethod
    def create_broadcast_message(
        sender: str,
        payload: Dict[str, Any],
        intent: MessageIntent = MessageIntent.INFORM,
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    ) -> EnhancedMessage:
        """Create a broadcast message to all agents."""
        return EnhancedMessage(
            type=MessageType.NOTIFICATION,
            sender=sender,
            recipient=None,  # Broadcast
            payload=payload,
            intent=intent,
            urgency=urgency,
        )

    @staticmethod
    def create_feedback_message(
        sender: str,
        recipient: str,
        about_message_id: str,
        feedback_data: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> FeedbackMessage:
        """Create a feedback message."""
        return FeedbackMessage(
            sender=sender,
            recipient=recipient,
            payload={
                "about_message_id": about_message_id,
                "feedback_data": feedback_data,
            },
            correlation_id=correlation_id or about_message_id,
        )

    @staticmethod
    def create_assistance_request(
        sender: str,
        recipient: str,
        request_type: str,
        context: Dict[str, Any],
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
        response_by: Optional[datetime] = None,
    ) -> AssistanceRequestMessage:
        """Create an assistance request message."""
        return AssistanceRequestMessage(
            sender=sender,
            recipient=recipient,
            payload={
                "request_type": request_type,
                "context": context,
            },
            urgency=urgency,
            response_by=response_by,
        )

    @staticmethod
    def create_need_expression(
        sender: str,
        need_type: str,
        description: str,
        required_capabilities: List[str],
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    ) -> NeedExpressionMessage:
        """Create a need expression message."""
        return NeedExpressionMessage(
            sender=sender,
            recipient=None,  # Broadcast
            payload={
                "need_type": need_type,
                "description": description,
                "required_capabilities": required_capabilities,
            },
            urgency=urgency,
        )
