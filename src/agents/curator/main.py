"""Main module for the Curator Agent.

This module provides the entry point for running the Curator Agent as a standalone
service.
"""

import asyncio
import logging
import os
import signal
import sys
import uuid
from typing import Dict, List, Optional, Any

from src.agents.base import AgentDependencies
from src.agents.curator.agent import CuratorAgent, CuratorAgentConfig
from src.agents.curator.sources.base import SourceConfig
from src.common.config import Settings
from src.database.connection import create_database
from src.message_bus.redis_streams import RedisStreamClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("curator_agent.log"),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Run the Curator Agent."""
    logger.info("Starting Curator Agent")

    # Load settings
    settings = Settings()

    # Create database tables if they don't exist
    create_database()

    # Connect to Redis
    redis_client = RedisStreamClient(url=settings.redis.url)
    await redis_client.connect()

    # Create agent dependencies
    dependencies = AgentDependencies(
        settings=settings,
        message_bus=redis_client,
    )

    # Create agent configuration
    config = CuratorAgentConfig(
        refresh_interval=settings.agent_settings.curator_poll_interval,
        max_documents_per_source=50,
        sources=[
            SourceConfig(
                type="openalex",
                filters={
                    "topics": ["machine learning", "artificial intelligence", "neural networks"],
                    "date_range": "last_month"
                },
                credentials={
                    "api_key": settings.external_api_settings.openalex_api_key
                } if settings.external_api_settings.openalex_api_key else None
            ),
            SourceConfig(
                type="newsapi",
                filters={
                    "topics": ["technology", "science", "ai", "machine learning"],
                    "date_range": "last_week"
                },
                credentials={
                    "api_key": settings.external_api_settings.newsapi_api_key
                } if settings.external_api_settings.newsapi_api_key else None
            ),
            SourceConfig(
                type="serpapi",
                filters={
                    "topics": ["machine learning tutorial", "AI news", "neural networks guide"],
                    "date_range": "last_day"
                },
                credentials={
                    "api_key": settings.external_api_settings.serpapi_api_key
                } if settings.external_api_settings.serpapi_api_key else None
            )
        ]
    )

    # Create agent
    agent = CuratorAgent(
        agent_id=f"curator-{uuid.uuid4().hex[:8]}",
        name="Curator Agent",
        dependencies=dependencies,
        config=config,
    )

    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(agent, redis_client)))

    # Start agent
    await agent.start()

    # Create health check file
    health_file = "/tmp/curator_health"
    try:
        with open(health_file, "w") as f:
            f.write("healthy")
        logger.info(f"Created health check file at {health_file}")
    except Exception as e:
        logger.warning(f"Failed to create health check file: {e}")

    # Run initial document discovery
    try:
        # Discover documents from all sources
        documents = await agent.discover_documents()

        # If we found at least one document, consider it a success
        if documents:
            logger.info(f"Successfully discovered {len(documents)} documents. Exiting with success.")
            # Clean up and exit
            await shutdown(agent, redis_client)
            return
        else:
            logger.warning("No documents were discovered from any source.")
    except Exception as e:
        logger.exception(f"Error during initial document discovery: {e}")

    # If we get here, either no documents were found or an error occurred
    # Keep the agent running for a while in case it's a temporary issue
    try:
        # Run for a limited time (5 minutes) then exit
        for _ in range(10):  # 10 iterations * 30 seconds = 5 minutes
            # Update health check file
            try:
                with open(health_file, "w") as f:
                    f.write("healthy")
            except Exception as e:
                logger.warning(f"Failed to update health check file: {e}")

            await asyncio.sleep(30)

        logger.info("Exiting after waiting period")
    except asyncio.CancelledError:
        logger.info("Agent task cancelled")
    finally:
        # Clean up health check file
        try:
            if os.path.exists(health_file):
                os.remove(health_file)
                logger.info(f"Removed health check file at {health_file}")
        except Exception as e:
            logger.warning(f"Failed to remove health check file: {e}")

        # Clean up and exit
        await shutdown(agent, redis_client)


async def shutdown(agent, redis_client):
    """Shutdown the agent gracefully."""
    logger.info("Shutting down Curator Agent")

    # Stop the agent
    await agent.stop()

    # Disconnect from Redis
    await redis_client.disconnect()

    # Exit the process
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
