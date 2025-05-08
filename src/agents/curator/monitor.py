"""Gradio-based monitoring interface for the Curator Agent.

This module provides a real-time monitoring interface for the Curator Agent using Gradio.
It allows users to visualize the agent's activity, discovered documents, and source statistics.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.agents.base import AgentDependencies, Message, MessageType
from src.agents.curator.agent import CuratorAgent, CuratorAgentConfig
from src.agents.curator.sources.base import SourceConfig
from src.common.config import Settings
from src.database.connection import get_session_sync
from src.database.models import Document
from src.message_bus.redis_streams import RedisStreamClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("curator_monitor.log"),
    ],
)

logger = logging.getLogger(__name__)


class CuratorMonitor:
    """Monitoring interface for the Curator Agent."""

    def __init__(self, settings: Settings, redis_client: RedisStreamClient):
        """Initialize the curator monitor.
        
        Args:
            settings: Application settings.
            redis_client: Redis client for message bus.
        """
        self.settings = settings
        self.redis_client = redis_client
        self.documents = []
        self.source_stats = {}
        self.last_update = datetime.utcnow()
        self.agent_status = "Offline"
        self.db_session = next(get_session_sync())
    
    async def start_monitoring(self):
        """Start monitoring the Curator Agent."""
        logger.info("Starting Curator Agent monitoring")
        
        # Subscribe to Curator Agent events
        await self.redis_client.subscribe("event.curator.documents_discovered")
        await self.redis_client.subscribe("event.agent.started")
        await self.redis_client.subscribe("event.agent.stopped")
        
        # Start message processing loop
        asyncio.create_task(self._process_messages())
        
        # Start data refresh loop
        asyncio.create_task(self._refresh_data())
    
    async def _process_messages(self):
        """Process messages from the message bus."""
        while True:
            try:
                # Get message from subscribed topics
                message_data = await self.redis_client.get_message()
                if not message_data:
                    await asyncio.sleep(0.1)
                    continue
                
                # Parse message
                topic = message_data.get("topic", "")
                message = message_data.get("message", {})
                
                # Process message based on topic
                if topic == "event.curator.documents_discovered":
                    await self._handle_documents_discovered(message)
                elif topic == "event.agent.started" and message.get("payload", {}).get("name", "").startswith("Curator"):
                    self.agent_status = "Online"
                elif topic == "event.agent.stopped" and message.get("payload", {}).get("name", "").startswith("Curator"):
                    self.agent_status = "Offline"
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                await asyncio.sleep(1)
    
    async def _handle_documents_discovered(self, message: Dict[str, Any]):
        """Handle documents discovered event.
        
        Args:
            message: The event message.
        """
        payload = message.get("payload", {})
        count = payload.get("count", 0)
        sources = payload.get("sources", [])
        
        # Update source stats
        for source in sources:
            if source not in self.source_stats:
                self.source_stats[source] = 0
            self.source_stats[source] += count // len(sources)
        
        # Update last update time
        self.last_update = datetime.utcnow()
    
    async def _refresh_data(self):
        """Refresh data from the database periodically."""
        while True:
            try:
                # Query recent documents
                documents = self.db_session.query(Document).order_by(
                    Document.created_at.desc()
                ).limit(100).all()
                
                # Convert to list of dictionaries
                self.documents = [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "source_type": doc.source_type,
                        "source_url": doc.source_url,
                        "created_at": doc.created_at.isoformat(),
                    }
                    for doc in documents
                ]
                
                # Wait before next refresh
                await asyncio.sleep(5)
            except Exception as e:
                logger.exception(f"Error refreshing data: {e}")
                await asyncio.sleep(5)
    
    def get_documents_df(self) -> pd.DataFrame:
        """Get documents as a DataFrame.
        
        Returns:
            DataFrame of documents.
        """
        return pd.DataFrame(self.documents)
    
    def get_source_stats_df(self) -> pd.DataFrame:
        """Get source statistics as a DataFrame.
        
        Returns:
            DataFrame of source statistics.
        """
        return pd.DataFrame([
            {"source": source, "count": count}
            for source, count in self.source_stats.items()
        ])
    
    def get_source_stats_plot(self) -> go.Figure:
        """Get source statistics plot.
        
        Returns:
            Plotly figure of source statistics.
        """
        df = self.get_source_stats_df()
        if df.empty:
            # Create empty plot
            fig = go.Figure()
            fig.update_layout(
                title="Documents by Source",
                xaxis_title="Source",
                yaxis_title="Count",
            )
            return fig
        
        fig = px.bar(
            df,
            x="source",
            y="count",
            title="Documents by Source",
            labels={"source": "Source", "count": "Count"},
            color="source",
        )
        return fig
    
    def get_documents_by_time_plot(self) -> go.Figure:
        """Get documents by time plot.
        
        Returns:
            Plotly figure of documents by time.
        """
        df = self.get_documents_df()
        if df.empty:
            # Create empty plot
            fig = go.Figure()
            fig.update_layout(
                title="Documents by Time",
                xaxis_title="Time",
                yaxis_title="Count",
            )
            return fig
        
        # Convert created_at to datetime
        df["created_at"] = pd.to_datetime(df["created_at"])
        
        # Group by hour
        df["hour"] = df["created_at"].dt.floor("H")
        hourly_counts = df.groupby("hour").size().reset_index(name="count")
        
        fig = px.line(
            hourly_counts,
            x="hour",
            y="count",
            title="Documents by Time",
            labels={"hour": "Time", "count": "Count"},
        )
        return fig


async def create_monitor():
    """Create and start the Curator Monitor."""
    # Load settings
    settings = Settings()
    
    # Connect to Redis
    redis_client = RedisStreamClient(url=settings.redis_url)
    await redis_client.connect()
    
    # Create monitor
    monitor = CuratorMonitor(settings, redis_client)
    
    # Start monitoring
    await monitor.start_monitoring()
    
    return monitor


def create_gradio_interface(monitor: CuratorMonitor):
    """Create Gradio interface for the Curator Monitor.
    
    Args:
        monitor: The Curator Monitor instance.
    """
    with gr.Blocks(title="Curator Agent Monitor") as demo:
        gr.Markdown("# Curator Agent Monitor")
        
        with gr.Row():
            with gr.Column():
                status_indicator = gr.Textbox(
                    label="Agent Status",
                    value=monitor.agent_status,
                    interactive=False,
                )
                last_update_indicator = gr.Textbox(
                    label="Last Update",
                    value=monitor.last_update.isoformat(),
                    interactive=False,
                )
            
            with gr.Column():
                source_stats_plot = gr.Plot(
                    value=monitor.get_source_stats_plot(),
                    label="Documents by Source",
                )
        
        with gr.Row():
            documents_by_time_plot = gr.Plot(
                value=monitor.get_documents_by_time_plot(),
                label="Documents by Time",
            )
        
        with gr.Row():
            documents_table = gr.DataFrame(
                value=monitor.get_documents_df(),
                label="Recent Documents",
            )
        
        # Update UI every 5 seconds
        def update_ui():
            return {
                status_indicator: monitor.agent_status,
                last_update_indicator: monitor.last_update.isoformat(),
                source_stats_plot: monitor.get_source_stats_plot(),
                documents_by_time_plot: monitor.get_documents_by_time_plot(),
                documents_table: monitor.get_documents_df(),
            }
        
        demo.load(update_ui, inputs=None, outputs=[
            status_indicator,
            last_update_indicator,
            source_stats_plot,
            documents_by_time_plot,
            documents_table,
        ], every=5)
    
    return demo


async def main():
    """Run the Curator Monitor."""
    # Create monitor
    monitor = await create_monitor()
    
    # Create Gradio interface
    demo = create_gradio_interface(monitor)
    
    # Launch Gradio interface
    demo.launch()


if __name__ == "__main__":
    asyncio.run(main())
