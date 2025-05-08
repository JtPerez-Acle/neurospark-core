"""Needs expression protocol for agents.

This module provides a protocol for agents to express their needs and for other
agents to fulfill those needs.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from src.agents.enhanced_agent import EnhancedAgent
from src.agents.enhanced_message import (
    EnhancedMessage,
    MessageFactory,
    MessageIntent,
    MessageType,
    NeedExpressionMessage,
    NeedFulfillmentMessage,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


class NeedType(str, Enum):
    """Enum representing types of needs that agents can express."""
    
    # Resource needs
    COMPUTE_RESOURCES = "compute_resources"
    STORAGE_RESOURCES = "storage_resources"
    MEMORY_RESOURCES = "memory_resources"
    
    # Data needs
    DATA_SOURCE = "data_source"
    DATA_ACCESS = "data_access"
    DATA_PROCESSING = "data_processing"
    
    # Knowledge needs
    KNOWLEDGE_BASE = "knowledge_base"
    DOMAIN_EXPERTISE = "domain_expertise"
    TRAINING_DATA = "training_data"
    
    # Service needs
    API_ACCESS = "api_access"
    EXTERNAL_SERVICE = "external_service"
    AUTHENTICATION = "authentication"
    
    # Coordination needs
    TASK_DELEGATION = "task_delegation"
    WORKFLOW_COORDINATION = "workflow_coordination"
    PRIORITY_ADJUSTMENT = "priority_adjustment"


class NeedsProtocol:
    """Protocol for needs expression and fulfillment between agents."""
    
    def __init__(self, agent: EnhancedAgent):
        """Initialize the needs protocol.
        
        Args:
            agent: The agent instance to use for communication.
        """
        self.agent = agent
        self._expressed_needs: Dict[str, Dict[str, Any]] = {}
        self._fulfilled_needs: Dict[str, Dict[str, Any]] = {}
    
    async def express_need(
        self,
        need_type: Union[str, NeedType],
        description: str,
        required_capabilities: List[str],
        context: Dict[str, Any] = None,
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
        timeout_seconds: int = 300,
    ) -> str:
        """Express a need to agents with specific capabilities.
        
        Args:
            need_type: The type of need.
            description: A description of the need.
            required_capabilities: The capabilities required to fulfill the need.
            context: Additional context for the need.
            urgency: The urgency level of the need.
            timeout_seconds: The timeout in seconds for the need.
            
        Returns:
            The ID of the need expression message.
        """
        # Create need expression message
        need_message = MessageFactory.create_need_expression(
            sender=self.agent.id,
            need_type=need_type if isinstance(need_type, str) else need_type.value,
            description=description,
            required_capabilities=required_capabilities,
        )
        
        # Add context to payload if provided
        if context:
            need_message.payload["context"] = context
        
        # Set urgency
        need_message.urgency = urgency
        
        # Set expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
        need_message.payload["expires_at"] = expires_at.isoformat()
        
        # Track the need
        self._expressed_needs[need_message.id] = {
            "need_type": need_type if isinstance(need_type, str) else need_type.value,
            "description": description,
            "required_capabilities": required_capabilities,
            "context": context or {},
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "status": "pending",
            "fulfillments": [],
        }
        
        # Send the message
        await self.agent.send_enhanced_message(need_message)
        
        # Schedule cleanup of expired need
        asyncio.create_task(self._cleanup_expired_need(need_message.id, timeout_seconds))
        
        return need_message.id
    
    async def fulfill_need(
        self,
        need_id: str,
        sender_id: str,
        fulfillment_data: Dict[str, Any],
    ) -> str:
        """Fulfill a need expressed by another agent.
        
        Args:
            need_id: The ID of the need to fulfill.
            sender_id: The ID of the agent that expressed the need.
            fulfillment_data: The data to fulfill the need.
            
        Returns:
            The ID of the need fulfillment message.
        """
        # Create need fulfillment message
        fulfillment_message = NeedFulfillmentMessage(
            sender=self.agent.id,
            recipient=sender_id,
            payload={
                "need_id": need_id,
                "fulfillment_data": fulfillment_data,
            },
            correlation_id=need_id,
        )
        
        # Track the fulfillment
        if need_id not in self._fulfilled_needs:
            self._fulfilled_needs[need_id] = []
        
        self._fulfilled_needs[need_id].append({
            "recipient": sender_id,
            "fulfillment_data": fulfillment_data,
            "created_at": datetime.utcnow(),
        })
        
        # Send the message
        await self.agent.send_enhanced_message(fulfillment_message)
        
        return fulfillment_message.id
    
    async def _cleanup_expired_need(self, need_id: str, timeout_seconds: int) -> None:
        """Clean up an expired need.
        
        Args:
            need_id: The ID of the need to clean up.
            timeout_seconds: The timeout in seconds for the need.
        """
        await asyncio.sleep(timeout_seconds)
        
        if need_id in self._expressed_needs:
            need = self._expressed_needs[need_id]
            if need["status"] == "pending":
                need["status"] = "expired"
                logger.warning(f"Need {need_id} expired without fulfillment")
    
    def get_expressed_need(self, need_id: str) -> Optional[Dict[str, Any]]:
        """Get an expressed need by ID.
        
        Args:
            need_id: The ID of the need to get.
            
        Returns:
            The need data, or None if not found.
        """
        return self._expressed_needs.get(need_id)
    
    def get_expressed_needs(
        self,
        status: Optional[str] = None,
        need_type: Optional[Union[str, NeedType]] = None,
    ) -> List[Dict[str, Any]]:
        """Get all expressed needs, optionally filtered by status and type.
        
        Args:
            status: Optional filter for need status.
            need_type: Optional filter for need type.
            
        Returns:
            List of need data.
        """
        needs = []
        
        for need_id, need in self._expressed_needs.items():
            if status and need["status"] != status:
                continue
            
            if need_type:
                need_type_value = need_type if isinstance(need_type, str) else need_type.value
                if need["need_type"] != need_type_value:
                    continue
            
            needs.append({**need, "id": need_id})
        
        return needs
    
    def get_fulfilled_needs(self, need_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all fulfilled needs, optionally filtered by need ID.
        
        Args:
            need_id: Optional filter for need ID.
            
        Returns:
            List of fulfillment data.
        """
        if need_id:
            return self._fulfilled_needs.get(need_id, [])
        
        fulfillments = []
        for need_id, need_fulfillments in self._fulfilled_needs.items():
            for fulfillment in need_fulfillments:
                fulfillments.append({**fulfillment, "need_id": need_id})
        
        return fulfillments


class NeedsExpressionMixin:
    """Mixin for agents that express needs."""
    
    def __init__(self, agent: EnhancedAgent):
        """Initialize the needs expression mixin.
        
        Args:
            agent: The agent instance to use for communication.
        """
        self.needs_protocol = NeedsProtocol(agent)
    
    async def express_need(
        self,
        need_type: Union[str, NeedType],
        description: str,
        required_capabilities: List[str],
        context: Dict[str, Any] = None,
        urgency: UrgencyLevel = UrgencyLevel.NORMAL,
        timeout_seconds: int = 300,
    ) -> str:
        """Express a need to agents with specific capabilities.
        
        Args:
            need_type: The type of need.
            description: A description of the need.
            required_capabilities: The capabilities required to fulfill the need.
            context: Additional context for the need.
            urgency: The urgency level of the need.
            timeout_seconds: The timeout in seconds for the need.
            
        Returns:
            The ID of the need expression message.
        """
        return await self.needs_protocol.express_need(
            need_type=need_type,
            description=description,
            required_capabilities=required_capabilities,
            context=context,
            urgency=urgency,
            timeout_seconds=timeout_seconds,
        )
    
    def get_expressed_need(self, need_id: str) -> Optional[Dict[str, Any]]:
        """Get an expressed need by ID.
        
        Args:
            need_id: The ID of the need to get.
            
        Returns:
            The need data, or None if not found.
        """
        return self.needs_protocol.get_expressed_need(need_id)
    
    def get_expressed_needs(
        self,
        status: Optional[str] = None,
        need_type: Optional[Union[str, NeedType]] = None,
    ) -> List[Dict[str, Any]]:
        """Get all expressed needs, optionally filtered by status and type.
        
        Args:
            status: Optional filter for need status.
            need_type: Optional filter for need type.
            
        Returns:
            List of need data.
        """
        return self.needs_protocol.get_expressed_needs(status, need_type)


class NeedsFulfillmentMixin:
    """Mixin for agents that fulfill needs."""
    
    def __init__(self, agent: EnhancedAgent):
        """Initialize the needs fulfillment mixin.
        
        Args:
            agent: The agent instance to use for communication.
        """
        self.needs_protocol = NeedsProtocol(agent)
    
    async def fulfill_need(
        self,
        need_id: str,
        sender_id: str,
        fulfillment_data: Dict[str, Any],
    ) -> str:
        """Fulfill a need expressed by another agent.
        
        Args:
            need_id: The ID of the need to fulfill.
            sender_id: The ID of the agent that expressed the need.
            fulfillment_data: The data to fulfill the need.
            
        Returns:
            The ID of the need fulfillment message.
        """
        return await self.needs_protocol.fulfill_need(
            need_id=need_id,
            sender_id=sender_id,
            fulfillment_data=fulfillment_data,
        )
    
    def get_fulfilled_needs(self, need_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all fulfilled needs, optionally filtered by need ID.
        
        Args:
            need_id: Optional filter for need ID.
            
        Returns:
            List of fulfillment data.
        """
        return self.needs_protocol.get_fulfilled_needs(need_id)
