"""Pytest configuration for NeuroSpark Core tests."""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Generator

import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def pytest_configure(config: Config) -> None:
    """Configure pytest."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "e2e: mark a test as an end-to-end test")
    config.addinivalue_line("markers", "performance: mark a test as a performance test")
    config.addinivalue_line("markers", "security: mark a test as a security test")
    config.addinivalue_line("markers", "slow: mark a test as slow running")


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Return test configuration."""
    return {
        "database": {
            "url": os.environ.get("TEST_DATABASE_URL", "sqlite:///test.db"),
        },
        "redis": {
            "host": os.environ.get("TEST_REDIS_HOST", "localhost"),
            "port": int(os.environ.get("TEST_REDIS_PORT", "6379")),
            "password": os.environ.get("TEST_REDIS_PASSWORD", ""),
        },
        "qdrant": {
            "host": os.environ.get("TEST_QDRANT_HOST", "localhost"),
            "port": int(os.environ.get("TEST_QDRANT_PORT", "6333")),
        },
        "minio": {
            "endpoint": os.environ.get("TEST_MINIO_ENDPOINT", "localhost:9000"),
            "access_key": os.environ.get("TEST_MINIO_ACCESS_KEY", "minioadmin"),
            "secret_key": os.environ.get("TEST_MINIO_SECRET_KEY", "minioadmin"),
            "bucket_name": os.environ.get("TEST_MINIO_BUCKET", "test-bucket"),
        },
        "elasticsearch": {
            "host": os.environ.get("TEST_ELASTICSEARCH_HOST", "localhost"),
            "port": int(os.environ.get("TEST_ELASTICSEARCH_PORT", "9200")),
            "index_name": os.environ.get("TEST_ELASTICSEARCH_INDEX", "test-index"),
        },
    }


@pytest.fixture
def temp_dir(tmpdir: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    yield Path(tmpdir)


@pytest.fixture
def db_engine(test_config: Dict[str, Any]) -> Generator[Any, None, None]:
    """Create a database engine for tests."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database.models import Base

    # Create an in-memory SQLite database for testing
    engine = create_engine(test_config["database"]["url"])

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Drop all tables after tests
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine: Any) -> Generator[Any, None, None]:
    """Create a database session for tests."""
    from sqlalchemy.orm import sessionmaker

    # Create a session factory
    Session = sessionmaker(bind=db_engine)

    # Create a session
    session = Session()

    yield session

    # Close and rollback the session after tests
    session.rollback()
    session.close()


@pytest.fixture
def redis_client(test_config: Dict[str, Any]) -> Generator[Any, None, None]:
    """Create a Redis client for tests."""
    from unittest.mock import MagicMock

    # Create a mock Redis client for testing
    mock_client = MagicMock()

    yield mock_client


@pytest.fixture
def qdrant_client(test_config: Dict[str, Any]) -> Generator[Any, None, None]:
    """Create a Qdrant client for tests."""
    from unittest.mock import MagicMock

    # Create a mock Qdrant client for testing
    mock_client = MagicMock()

    yield mock_client


@pytest.fixture
def minio_client(test_config: Dict[str, Any]) -> Generator[Any, None, None]:
    """Create a MinIO client for tests."""
    from unittest.mock import MagicMock

    # Create a mock MinIO client for testing
    mock_client = MagicMock()

    yield mock_client


@pytest.fixture
def elasticsearch_client(test_config: Dict[str, Any]) -> Generator[Any, None, None]:
    """Create an Elasticsearch client for tests."""
    from unittest.mock import MagicMock

    # Create a mock Elasticsearch client for testing
    mock_client = MagicMock()

    yield mock_client


@pytest.fixture
def api_client() -> Generator[Any, None, None]:
    """Create a test client for the API."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    # Create a test client
    client = TestClient(app)

    yield client
