"""Service discovery for NeuroSpark Core agents.

This module provides service discovery capabilities for agents to find and communicate
with each other.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set

from src.common.config import Settings
from src.message_bus.redis_streams import RedisStreamClient

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for agents in the system.
    
    This class provides a registry for agents to register themselves and discover
    other agents based on capabilities.
    """

    def __init__(self, settings: Settings, message_bus: RedisStreamClient):
        """Initialize the agent registry.
        
        Args:
            settings: Application settings.
            message_bus: Message bus client.
        """
        self.settings = settings
        self.message_bus = message_bus
        self.agents: Dict[str, Dict] = {}
        self.capabilities: Dict[str, Set[str]] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the agent registry.
        
        This method starts listening for agent registration events.
        """
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._listen_for_events())
        logger.info("Agent registry started")
    
    async def stop(self) -> None:
        """Stop the agent registry.
        
        This method stops listening for agent registration events.
        """
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Agent registry stopped")
    
    async def _listen_for_events(self) -> None:
        """Listen for agent registration events."""
        while self._running:
            try:
                # Listen for agent started events
                started_events = await self.message_bus.read_messages("event.agent.started")
                for event in started_events:
                    await self._handle_agent_started(event)
                
                # Listen for agent stopped events
                stopped_events = await self.message_bus.read_messages("event.agent.stopped")
                for event in stopped_events:
                    await self._handle_agent_stopped(event)
                
                # Sleep briefly to avoid tight loop
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error listening for events: {e}")
                await asyncio.sleep(1)  # Sleep longer on error
    
    async def _handle_agent_started(self, event: Dict) -> None:
        """Handle agent started event.
        
        Args:
            event: The agent started event.
        """
        try:
            payload = event.get("payload", {})
            agent_id = payload.get("agent_id")
            name = payload.get("name")
            capabilities = payload.get("capabilities", [])
            
            if not agent_id or not name:
                logger.warning(f"Invalid agent started event: {event}")
                return
            
            # Register agent
            self.agents[agent_id] = {
                "id": agent_id,
                "name": name,
                "capabilities": capabilities,
                "status": "active",
            }
            
            # Register capabilities
            for capability in capabilities:
                if capability not in self.capabilities:
                    self.capabilities[capability] = set()
                self.capabilities[capability].add(agent_id)
            
            logger.info(f"Registered agent {name} ({agent_id}) with capabilities {capabilities}")
        except Exception as e:
            logger.exception(f"Error handling agent started event: {e}")
    
    async def _handle_agent_stopped(self, event: Dict) -> None:
        """Handle agent stopped event.
        
        Args:
            event: The agent stopped event.
        """
        try:
            payload = event.get("payload", {})
            agent_id = payload.get("agent_id")
            
            if not agent_id:
                logger.warning(f"Invalid agent stopped event: {event}")
                return
            
            # Get agent info
            agent = self.agents.get(agent_id)
            if not agent:
                logger.warning(f"Unknown agent stopped: {agent_id}")
                return
            
            # Update agent status
            agent["status"] = "inactive"
            
            # Remove from capabilities
            for capability in agent.get("capabilities", []):
                if capability in self.capabilities:
                    self.capabilities[capability].discard(agent_id)
                    if not self.capabilities[capability]:
                        del self.capabilities[capability]
            
            logger.info(f"Unregistered agent {agent.get('name')} ({agent_id})")
        except Exception as e:
            logger.exception(f"Error handling agent stopped event: {e}")
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent information.
        
        Args:
            agent_id: The agent ID.
            
        Returns:
            The agent information, or None if not found.
        """
        return self.agents.get(agent_id)
    
    def get_agents_by_capability(self, capability: str) -> List[Dict]:
        """Get agents by capability.
        
        Args:
            capability: The capability to filter by.
            
        Returns:
            A list of agents with the specified capability.
        """
        agent_ids = self.capabilities.get(capability, set())
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    def get_all_agents(self) -> List[Dict]:
        """Get all registered agents.
        
        Returns:
            A list of all registered agents.
        """
        return list(self.agents.values())
    
    def get_all_capabilities(self) -> List[str]:
        """Get all registered capabilities.
        
        Returns:
            A list of all registered capabilities.
        """
        return list(self.capabilities.keys())
