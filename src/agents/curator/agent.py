"""Curator Agent implementation for NeuroSpark Core.

This module provides the CuratorAgent class that is responsible for discovering
documents from trusted sources like OpenAlex, NewsAPI, and SerpAPI.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Type, Union

from pydantic import BaseModel, Field

from src.agents.base import Agent, AgentDependencies, AgentState, Message, MessageType
from src.agents.curator.sources.base import DocumentSource, SourceConfig
from src.agents.curator.sources.factory import create_source
from src.database.models import Document
from src.database.connection import get_session_sync

logger = logging.getLogger(__name__)


class CuratorAgentConfig(BaseModel):
    """Configuration for a Curator Agent."""

    refresh_interval: int = Field(3600, description="Refresh interval in seconds")
    max_documents_per_source: int = Field(50, description="Maximum documents per source")
    sources: List[SourceConfig] = Field(default_factory=list, description="Document sources")


class CuratorAgent(Agent):
    """Curator Agent for discovering documents from trusted sources.
    
    This agent is responsible for discovering documents from trusted sources like
    OpenAlex, NewsAPI, and SerpAPI.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        dependencies: AgentDependencies,
        config: CuratorAgentConfig,
    ):
        """Initialize the curator agent.
        
        Args:
            agent_id: Unique identifier for the agent.
            name: Human-readable name for the agent.
            dependencies: Dependencies required by the agent.
            config: Configuration for the agent.
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            dependencies=dependencies,
            capabilities=["discover-documents"],
        )
        self.config = config
        self.sources: List[DocumentSource] = []
        self._refresh_task: Optional[asyncio.Task] = None
        self._db_session = None
    
    async def initialize(self) -> None:
        """Initialize the curator agent.
        
        This method initializes the document sources and starts the refresh task.
        """
        logger.info(f"Initializing curator agent {self.name} ({self.id})")
        
        # Initialize document sources
        self.sources = []
        for source_config in self.config.sources:
            try:
                source = create_source(source_config)
                self.sources.append(source)
                logger.info(f"Initialized document source: {source_config.type}")
            except Exception as e:
                logger.exception(f"Error initializing document source {source_config.type}: {e}")
        
        # Initialize database session
        self._db_session = next(get_session_sync())
        
        # Start refresh task if interval is positive
        if self.config.refresh_interval > 0:
            self._refresh_task = asyncio.create_task(self._refresh_loop())
            logger.info(f"Started document refresh task with interval {self.config.refresh_interval}s")
    
    async def cleanup(self) -> None:
        """Clean up resources.
        
        This method stops the refresh task and closes the database session.
        """
        logger.info(f"Cleaning up curator agent {self.name} ({self.id})")
        
        # Cancel refresh task
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        
        # Close database session
        if self._db_session:
            self._db_session.close()
    
    async def process_message(self, message: Message) -> None:
        """Process a message.
        
        This method handles incoming messages for the curator agent.
        
        Args:
            message: The message to process.
        """
        logger.debug(f"Processing message: {message.type} from {message.sender}")
        
        try:
            if message.type == MessageType.COMMAND:
                await self._handle_command(message)
            elif message.type == MessageType.QUERY:
                await self._handle_query(message)
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            
            # Send error response if there's a reply_to
            if message.reply_to:
                error_response = Message(
                    type=MessageType.RESPONSE,
                    sender=self.id,
                    recipient=message.sender,
                    payload={"error": str(e)},
                    correlation_id=message.id,
                )
                await self.send_message(error_response)
    
    async def _handle_command(self, message: Message) -> None:
        """Handle a command message.
        
        Args:
            message: The command message to handle.
        """
        command = message.payload.get("command")
        
        if command == "discover":
            # Get topics from payload or use empty list
            topics = message.payload.get("topics", [])
            
            # Discover documents
            documents = await self.discover_documents(topics)
            
            # Send response
            response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                payload={
                    "documents": [doc.get("title") for doc in documents],
                    "count": len(documents),
                },
                correlation_id=message.id,
            )
            await self.send_message(response)
        else:
            logger.warning(f"Unknown command: {command}")
            
            # Send error response
            error_response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                payload={"error": f"Unknown command: {command}"},
                correlation_id=message.id,
            )
            await self.send_message(error_response)
    
    async def _handle_query(self, message: Message) -> None:
        """Handle a query message.
        
        Args:
            message: The query message to handle.
        """
        query_type = message.payload.get("query_type")
        
        if query_type == "sources":
            # Send response with sources
            response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                payload={
                    "sources": [source.config.type for source in self.sources],
                },
                correlation_id=message.id,
            )
            await self.send_message(response)
        else:
            logger.warning(f"Unknown query type: {query_type}")
            
            # Send error response
            error_response = Message(
                type=MessageType.RESPONSE,
                sender=self.id,
                recipient=message.sender,
                payload={"error": f"Unknown query type: {query_type}"},
                correlation_id=message.id,
            )
            await self.send_message(error_response)
    
    async def _refresh_loop(self) -> None:
        """Refresh documents periodically.
        
        This method runs in a loop, discovering documents at the configured interval.
        """
        while True:
            try:
                # Discover documents
                await self.discover_documents()
                
                # Wait for the next refresh
                await asyncio.sleep(self.config.refresh_interval)
            except asyncio.CancelledError:
                logger.info("Refresh task cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in refresh loop: {e}")
                
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def discover_documents(self, topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Discover documents from all sources.
        
        Args:
            topics: Optional list of topics to filter by.
            
        Returns:
            List of discovered documents.
        """
        logger.info(f"Discovering documents from {len(self.sources)} sources")
        
        all_documents = []
        
        # Discover documents from each source
        for source in self.sources:
            try:
                # Skip if topics are provided and don't match source topics
                if topics and not any(topic in source.config.filters.get("topics", []) for topic in topics):
                    continue
                
                # Discover documents from source
                documents = await source.discover()
                
                # Limit documents per source
                documents = documents[:self.config.max_documents_per_source]
                
                # Save documents to database
                for doc_data in documents:
                    document = Document(
                        title=doc_data["title"],
                        source_url=doc_data["source_url"],
                        source_type=doc_data["source_type"],
                        content=doc_data["content"],
                        doc_metadata=doc_data.get("metadata", {}),
                    )
                    self._db_session.add(document)
                
                # Commit changes
                self._db_session.commit()
                
                # Add to all documents
                all_documents.extend(documents)
                
                logger.info(f"Discovered {len(documents)} documents from {source.config.type}")
            except Exception as e:
                logger.exception(f"Error discovering documents from {source.config.type}: {e}")
        
        # Publish event with document count
        await self.publish_event("curator.documents_discovered", {
            "count": len(all_documents),
            "sources": [source.config.type for source in self.sources],
        })
        
        return all_documents
