"""Enhanced Agent base class with bidirectional communication capabilities.

This module provides an enhanced Agent base class with bidirectional communication
capabilities, including feedback, assistance requests, and needs expression.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union, cast

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType as BaseMessageType
from src.agents.enhanced_message import (
    AssistanceRequestMessage,
    AssistanceResponseMessage,
    EnhancedMessage,
    FeedbackMessage,
    MessageFactory,
    MessageIntent,
    MessageType,
    NeedExpressionMessage,
    NeedFulfillmentMessage,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)

# Type alias for message handlers
MessageHandler = Callable[[Union[Message, EnhancedMessage]], None]


class EnhancedAgent(Agent):
    """Enhanced Agent base class with bidirectional communication capabilities.
    
    This class extends the base Agent class with additional methods for
    bidirectional communication, including feedback, assistance requests,
    and needs expression.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        dependencies: AgentDependencies,
        capabilities: Optional[List[str]] = None,
    ):
        """Initialize the enhanced agent.
        
        Args:
            agent_id: Unique identifier for the agent.
            name: Human-readable name for the agent.
            dependencies: Dependencies required by the agent.
            capabilities: List of capabilities provided by the agent.
        """
        super().__init__(agent_id, name, dependencies, capabilities)
        
        # Initialize tracking dictionaries for requests and needs
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        self._expressed_needs: Dict[str, Dict[str, Any]] = {}
        self._received_feedback: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize custom message handlers
        self._message_handlers: Dict[str, MessageHandler] = {}
        
        # Register default handlers for enhanced message types
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default handlers for enhanced message types."""
        self._message_handlers = {
            MessageType.FEEDBACK: self._handle_feedback,
            MessageType.ASSISTANCE_REQUEST: self._handle_assistance_request,
            MessageType.ASSISTANCE_RESPONSE: self._handle_assistance_response,
            MessageType.NEED_EXPRESSION: self._handle_need_expression,
            MessageType.NEED_FULFILLMENT: self._handle_need_fulfillment,
        }
    
    def register_message_handler(self, message_type: str, handler: MessageHandler) -> None:
        """Register a custom message handler.
        
        Args:
            message_type: The type of message to handle.
            handler: The handler function to call for this message type.
        """
        self._message_handlers[message_type] = handler
    
    async def process_message(self, message: Union[Message, EnhancedMessage]) -> None:
        """Process a message.
        
        This method handles incoming messages for the agent, routing them to the
        appropriate handler based on the message type.
        
        Args:
            message: The message to process.
        """
        logger.debug(f"Processing message: {message.type} from {message.sender}")
        
        try:
            # Check if we have a custom handler for this message type
            if message.type in self._message_handlers:
                await self._message_handlers[message.type](message)
            else:
                # Default handling for standard message types
                if message.type == BaseMessageType.COMMAND:
                    await self._handle_command(message)
                elif message.type == BaseMessageType.EVENT:
                    await self._handle_event(message)
                elif message.type == BaseMessageType.REQUEST:
                    await self._handle_request(message)
                elif message.type == BaseMessageType.RESPONSE:
                    await self._handle_response(message)
                elif message.type == BaseMessageType.NOTIFICATION:
                    await self._handle_notification(message)
                else:
                    logger.warning(f"Unknown message type: {message.type}")
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            
            # Send error response if there's a reply_to
            if hasattr(message, 'reply_to') and message.reply_to:
                error_response = MessageFactory.create_direct_message(
                    sender=self.id,
                    recipient=message.sender,
                    payload={"error": str(e)},
                    correlation_id=message.id,
                )
                await self.send_enhanced_message(error_response)
    
    async def send_enhanced_message(self, message: EnhancedMessage) -> None:
        """Send an enhanced message to another agent.
        
        Args:
            message: The enhanced message to send.
        """
        if message.recipient:
            topic = f"agent.{message.recipient}"
        else:
            topic = "agent.broadcast"
        
        await self.dependencies.message_bus.publish_message(
            topic, message.model_dump()
        )
    
    async def send_feedback(
        self,
        recipient_id: str,
        about_message_id: str,
        feedback_data: Dict[str, Any],
    ) -> str:
        """Send feedback to another agent.
        
        Args:
            recipient_id: The ID of the recipient agent.
            about_message_id: The ID of the message the feedback is about.
            feedback_data: The feedback data.
            
        Returns:
            The ID of the feedback message.
        """
        feedback_message = MessageFactory.create_feedback_message(
            sender=self.id,
            recipient=recipient_id,
            about_message_id=about_message_id,
            feedback_data=feedback_data,
        )
        
        await self.send_enhanced_message(feedback_message)
        return feedback_message.id
    
    async def request_assistance(
        self,
        recipient_id: str,
        request_type: str,
        context: Dict[str, Any],
        timeout_seconds: int = 60,
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    ) -> str:
        """Request assistance from another agent.
        
        Args:
            recipient_id: The ID of the recipient agent.
            request_type: The type of assistance requested.
            context: The context for the assistance request.
            timeout_seconds: The timeout in seconds for the request.
            urgency: The urgency level of the request.
            
        Returns:
            The ID of the assistance request message.
        """
        # Calculate response_by time
        response_by = datetime.utcnow() + timedelta(seconds=timeout_seconds)
        
        # Create assistance request message
        request_message = MessageFactory.create_assistance_request(
            sender=self.id,
            recipient=recipient_id,
            request_type=request_type,
            context=context,
            urgency=urgency,
            response_by=response_by,
        )
        
        # Track the request
        self._pending_requests[request_message.id] = {
            "recipient": recipient_id,
            "request_type": request_type,
            "context": context,
            "created_at": datetime.utcnow(),
            "expires_at": response_by,
            "status": "pending",
        }
        
        # Send the message
        await self.send_enhanced_message(request_message)
        
        # Schedule cleanup of expired request
        asyncio.create_task(self._cleanup_expired_request(request_message.id, timeout_seconds))
        
        return request_message.id
    
    async def express_need(
        self,
        need_type: str,
        description: str,
        required_capabilities: List[str],
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    ) -> str:
        """Express a need to agents with specific capabilities.
        
        Args:
            need_type: The type of need.
            description: A description of the need.
            required_capabilities: The capabilities required to fulfill the need.
            urgency: The urgency level of the need.
            
        Returns:
            The ID of the need expression message.
        """
        # Create need expression message
        need_message = MessageFactory.create_need_expression(
            sender=self.id,
            need_type=need_type,
            description=description,
            required_capabilities=required_capabilities,
            urgency=urgency,
        )
        
        # Track the need
        self._expressed_needs[need_message.id] = {
            "need_type": need_type,
            "description": description,
            "required_capabilities": required_capabilities,
            "created_at": datetime.utcnow(),
            "status": "pending",
            "fulfillments": [],
        }
        
        # Send the message
        await self.send_enhanced_message(need_message)
        
        return need_message.id
    
    async def _cleanup_expired_request(self, request_id: str, timeout_seconds: int) -> None:
        """Clean up an expired request.
        
        Args:
            request_id: The ID of the request to clean up.
            timeout_seconds: The timeout in seconds for the request.
        """
        await asyncio.sleep(timeout_seconds)
        
        if request_id in self._pending_requests:
            request = self._pending_requests[request_id]
            if request["status"] == "pending":
                request["status"] = "expired"
                logger.warning(f"Request {request_id} expired without response")
    
    async def _handle_command(self, message: Message) -> None:
        """Handle a command message.
        
        Args:
            message: The command message to handle.
        """
        logger.warning(f"Command message not handled: {message.payload}")
    
    async def _handle_event(self, message: Message) -> None:
        """Handle an event message.
        
        Args:
            message: The event message to handle.
        """
        logger.debug(f"Received event: {message.payload}")
    
    async def _handle_request(self, message: Message) -> None:
        """Handle a request message.
        
        Args:
            message: The request message to handle.
        """
        logger.warning(f"Request message not handled: {message.payload}")
    
    async def _handle_response(self, message: Message) -> None:
        """Handle a response message.
        
        Args:
            message: The response message to handle.
        """
        logger.debug(f"Received response: {message.payload}")
    
    async def _handle_notification(self, message: Message) -> None:
        """Handle a notification message.
        
        Args:
            message: The notification message to handle.
        """
        logger.debug(f"Received notification: {message.payload}")
    
    async def _handle_feedback(self, message: FeedbackMessage) -> None:
        """Handle a feedback message.
        
        Args:
            message: The feedback message to handle.
        """
        logger.debug(f"Received feedback from {message.sender}")
        
        # Extract feedback data
        about_message_id = message.payload.get("about_message_id")
        feedback_data = message.payload.get("feedback_data", {})
        
        # Store feedback
        if about_message_id:
            if about_message_id not in self._received_feedback:
                self._received_feedback[about_message_id] = []
            
            self._received_feedback[about_message_id].append({
                "sender": message.sender,
                "feedback_data": feedback_data,
                "received_at": datetime.utcnow(),
            })
    
    async def _handle_assistance_request(self, message: AssistanceRequestMessage) -> None:
        """Handle an assistance request message.
        
        Args:
            message: The assistance request message to handle.
        """
        logger.debug(f"Received assistance request from {message.sender}")
        
        # Default implementation just logs the request
        # Subclasses should override this method to provide actual assistance
        logger.warning(f"Assistance request not handled: {message.payload}")
    
    async def _handle_assistance_response(self, message: AssistanceResponseMessage) -> None:
        """Handle an assistance response message.
        
        Args:
            message: The assistance response message to handle.
        """
        logger.debug(f"Received assistance response from {message.sender}")
        
        # Check if this is a response to a pending request
        if message.correlation_id and message.correlation_id in self._pending_requests:
            request = self._pending_requests[message.correlation_id]
            request["status"] = "fulfilled"
            request["response"] = message.payload
            request["response_time"] = datetime.utcnow()
    
    async def _handle_need_expression(self, message: NeedExpressionMessage) -> None:
        """Handle a need expression message.
        
        Args:
            message: The need expression message to handle.
        """
        logger.debug(f"Received need expression from {message.sender}")
        
        # Check if we have the required capabilities
        required_capabilities = message.payload.get("required_capabilities", [])
        if not required_capabilities or any(cap in self.capabilities for cap in required_capabilities):
            # We have at least one of the required capabilities
            # Default implementation just logs the need
            # Subclasses should override this method to fulfill needs
            logger.warning(f"Need expression not handled: {message.payload}")
    
    async def _handle_need_fulfillment(self, message: NeedFulfillmentMessage) -> None:
        """Handle a need fulfillment message.
        
        Args:
            message: The need fulfillment message to handle.
        """
        logger.debug(f"Received need fulfillment from {message.sender}")
        
        # Check if this is a fulfillment for an expressed need
        need_id = message.payload.get("need_id")
        if need_id and need_id in self._expressed_needs:
            need = self._expressed_needs[need_id]
            need["status"] = "fulfilled"
            need["fulfillments"].append({
                "sender": message.sender,
                "fulfillment_data": message.payload.get("fulfillment_data", {}),
                "received_at": datetime.utcnow(),
            })
