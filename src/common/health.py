"""Health check utilities for NeuroSpark Core."""

import os
import time
import logging
from typing import Dict, Any, Optional, Callable
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HealthCheck:
    """Health check manager for agents and services."""

    def __init__(self, agent_name: str, health_file: Optional[str] = None):
        """Initialize the health check manager.
        
        Args:
            agent_name: The name of the agent.
            health_file: The path to the health file. If None, defaults to /tmp/{agent_name}_health.
        """
        self.agent_name = agent_name
        self.health_file = health_file or f"/tmp/{agent_name}_health"
        self.start_time = time.time()
        self.status = "starting"
        self.details: Dict[str, Any] = {}
        self.dependencies: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._stop_event = threading.Event()
        self._health_thread = None
    
    def register_dependency(self, name: str, check_func: Callable[[], Dict[str, Any]]) -> None:
        """Register a dependency health check.
        
        Args:
            name: The name of the dependency.
            check_func: A function that returns the health status of the dependency.
        """
        self.dependencies[name] = check_func
    
    def update_status(self, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Update the health status.
        
        Args:
            status: The new status.
            details: Additional details about the status.
        """
        self.status = status
        if details:
            self.details.update(details)
        
        # Update the health file
        self._update_health_file()
    
    def _update_health_file(self) -> None:
        """Update the health file with the current timestamp."""
        try:
            with open(self.health_file, "w") as f:
                f.write(str(time.time()))
        except Exception as e:
            logger.error(f"Failed to update health file: {e}")
    
    def get_health(self) -> Dict[str, Any]:
        """Get the current health status.
        
        Returns:
            Dict[str, Any]: The health status.
        """
        uptime = time.time() - self.start_time
        
        # Check dependencies
        dependency_status = {}
        for name, check_func in self.dependencies.items():
            try:
                dependency_status[name] = check_func()
            except Exception as e:
                logger.error(f"Failed to check dependency {name}: {e}")
                dependency_status[name] = {
                    "status": "unhealthy",
                    "details": {"error": str(e)},
                }
        
        return {
            "status": self.status,
            "uptime": uptime,
            "details": self.details,
            "dependencies": dependency_status,
        }
    
    def start_health_check_thread(self, interval: int = 30) -> None:
        """Start a thread to periodically update the health file.
        
        Args:
            interval: The interval in seconds between health file updates.
        """
        def _health_check_thread():
            while not self._stop_event.is_set():
                self._update_health_file()
                time.sleep(interval)
        
        self._health_thread = threading.Thread(target=_health_check_thread, daemon=True)
        self._health_thread.start()
    
    def stop_health_check_thread(self) -> None:
        """Stop the health check thread."""
        if self._health_thread:
            self._stop_event.set()
            self._health_thread.join(timeout=1.0)
            self._health_thread = None
