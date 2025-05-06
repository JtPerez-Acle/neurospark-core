"""Test the health check utilities."""

import os
import time
import tempfile
import pytest

from src.common.health import HealthCheck


def test_health_check_init():
    """Test HealthCheck initialization."""
    health_check = HealthCheck("test_agent")
    assert health_check.agent_name == "test_agent"
    assert health_check.health_file == "/tmp/test_agent_health"
    assert health_check.status == "starting"
    assert health_check.details == {}
    assert health_check.dependencies == {}


def test_health_check_custom_file():
    """Test HealthCheck with custom health file."""
    with tempfile.NamedTemporaryFile() as temp_file:
        health_check = HealthCheck("test_agent", health_file=temp_file.name)
        assert health_check.health_file == temp_file.name


def test_health_check_update_status():
    """Test updating health status."""
    with tempfile.NamedTemporaryFile() as temp_file:
        health_check = HealthCheck("test_agent", health_file=temp_file.name)

        # Update status
        health_check.update_status("healthy", {"version": "1.0.0"})

        # Check status and details
        assert health_check.status == "healthy"
        assert health_check.details == {"version": "1.0.0"}

        # Check health file was updated
        assert os.path.exists(temp_file.name)
        with open(temp_file.name, "r") as f:
            content = f.read()
            # The content is a timestamp which is a float, not an integer
            assert float(content.strip()) > 0


def test_health_check_register_dependency():
    """Test registering a dependency."""
    health_check = HealthCheck("test_agent")

    # Define a mock dependency check function
    def mock_check():
        return {"status": "healthy", "details": {"version": "1.0.0"}}

    # Register the dependency
    health_check.register_dependency("mock_dependency", mock_check)

    # Check dependency was registered
    assert "mock_dependency" in health_check.dependencies
    assert health_check.dependencies["mock_dependency"]() == {
        "status": "healthy",
        "details": {"version": "1.0.0"},
    }


def test_health_check_get_health():
    """Test getting health status."""
    health_check = HealthCheck("test_agent")

    # Define mock dependency check functions
    def mock_healthy():
        return {"status": "healthy", "details": {"version": "1.0.0"}}

    def mock_unhealthy():
        return {"status": "unhealthy", "details": {"error": "Connection failed"}}

    # Register dependencies
    health_check.register_dependency("healthy_dependency", mock_healthy)
    health_check.register_dependency("unhealthy_dependency", mock_unhealthy)

    # Update status
    health_check.update_status("healthy", {"version": "1.0.0"})

    # Get health status
    health = health_check.get_health()

    # Check health status
    assert health["status"] == "healthy"
    assert "uptime" in health
    assert health["details"] == {"version": "1.0.0"}
    assert "dependencies" in health
    assert health["dependencies"]["healthy_dependency"]["status"] == "healthy"
    assert health["dependencies"]["unhealthy_dependency"]["status"] == "unhealthy"


def test_health_check_thread():
    """Test health check thread."""
    with tempfile.NamedTemporaryFile() as temp_file:
        health_check = HealthCheck("test_agent", health_file=temp_file.name)

        # Start health check thread
        health_check.start_health_check_thread(interval=1)

        # Wait for a bit
        time.sleep(2)

        # Check health file was updated
        assert os.path.exists(temp_file.name)

        # Get modification time
        mtime1 = os.path.getmtime(temp_file.name)

        # Wait for another update
        time.sleep(2)

        # Check file was updated again
        mtime2 = os.path.getmtime(temp_file.name)
        assert mtime2 > mtime1

        # Stop health check thread
        health_check.stop_health_check_thread()
