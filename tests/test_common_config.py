"""Test the configuration module."""

import os
import pytest
from unittest.mock import patch

from src.common.config import (
    Settings,
    Environment,
    LogLevel,
    LLMProvider,
    APISettings,
    DatabaseSettings,
    QdrantSettings,
    ElasticSettings,
    MinioSettings,
    RedisSettings,
    LLMSettings,
    ExternalAPISettings,
    AgentSettings,
    ResourceLimits,
)


def test_environment_enum():
    """Test Environment enum."""
    assert Environment.DEVELOPMENT == "development"
    assert Environment.STAGING == "staging"
    assert Environment.PRODUCTION == "production"


def test_log_level_enum():
    """Test LogLevel enum."""
    assert LogLevel.DEBUG == "DEBUG"
    assert LogLevel.INFO == "INFO"
    assert LogLevel.WARNING == "WARNING"
    assert LogLevel.ERROR == "ERROR"
    assert LogLevel.CRITICAL == "CRITICAL"


def test_llm_provider_enum():
    """Test LLMProvider enum."""
    assert LLMProvider.OPENAI == "openai"
    assert LLMProvider.LOCAL == "local"


def test_api_settings():
    """Test APISettings."""
    settings = APISettings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.grpc_port == 50051


def test_database_settings():
    """Test DatabaseSettings."""
    settings = DatabaseSettings()
    assert settings.host == "postgres"
    assert settings.port == 5432
    assert settings.db == "neurospark"
    assert settings.user == "postgres"
    assert settings.password == "postgres_password"
    assert settings.url == "postgresql://postgres:postgres_password@postgres:5432/neurospark"


def test_qdrant_settings():
    """Test QdrantSettings."""
    settings = QdrantSettings()
    assert settings.host == "qdrant"
    assert settings.port == 6333
    assert settings.grpc_port == 6334
    assert settings.url == "http://qdrant:6333"


def test_elastic_settings():
    """Test ElasticSettings."""
    settings = ElasticSettings()
    assert settings.host == "elasticlite"
    assert settings.port == 9200
    assert settings.url == "http://elasticlite:9200"


def test_minio_settings():
    """Test MinioSettings."""
    settings = MinioSettings()
    assert settings.host == "minio"
    assert settings.port == 9000
    assert settings.root_user == "minioadmin"
    assert settings.root_password == "minioadmin"
    assert settings.bucket == "neurospark"
    assert settings.url == "http://minio:9000"


def test_redis_settings():
    """Test RedisSettings."""
    settings = RedisSettings()
    assert settings.host == "redis"
    assert settings.port == 6379
    assert settings.password == "redis_password"
    assert settings.url == "redis://:redis_password@redis:6379/0"


def test_llm_settings():
    """Test LLMSettings."""
    settings = LLMSettings()
    assert settings.provider == LLMProvider.OPENAI
    assert settings.openai_api_key is None
    assert settings.openai_model == "gpt-4o"


def test_external_api_settings():
    """Test ExternalAPISettings."""
    settings = ExternalAPISettings()
    assert settings.openalex_api_key is None
    assert settings.newsapi_api_key is None
    assert settings.serpapi_api_key is None


def test_agent_settings():
    """Test AgentSettings."""
    settings = AgentSettings()
    assert settings.curator_poll_interval == 3600
    assert settings.custodian_schedule == "0 2 * * *"
    assert settings.reviewer_threshold == 0.75


def test_resource_limits():
    """Test ResourceLimits."""
    settings = ResourceLimits()
    assert settings.max_tokens_per_request == 4000
    assert settings.max_concurrent_requests == 10


def test_settings():
    """Test Settings."""
    settings = Settings()
    assert settings.environment == Environment.DEVELOPMENT
    assert settings.log_level == LogLevel.INFO
    assert isinstance(settings.api, APISettings)
    assert isinstance(settings.database, DatabaseSettings)
    assert isinstance(settings.qdrant, QdrantSettings)
    assert isinstance(settings.elastic, ElasticSettings)
    assert isinstance(settings.minio, MinioSettings)
    assert isinstance(settings.redis, RedisSettings)
    assert isinstance(settings.llm, LLMSettings)
    assert isinstance(settings.external_apis, ExternalAPISettings)
    assert isinstance(settings.agents, AgentSettings)
    assert isinstance(settings.resource_limits, ResourceLimits)


def test_settings_get_service_urls():
    """Test Settings.get_service_urls()."""
    settings = Settings()
    urls = settings.get_service_urls()
    assert urls["database"] == "postgresql://postgres:postgres_password@postgres:5432/neurospark"
    assert urls["qdrant"] == "http://qdrant:6333"
    assert urls["elastic"] == "http://elasticlite:9200"
    assert urls["minio"] == "http://minio:9000"
    assert urls["redis"] == "redis://:redis_password@redis:6379/0"


@patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
def test_llm_settings_with_openai_key():
    """Test LLMSettings with OpenAI API key."""
    settings = Settings()
    assert settings.llm.openai_api_key == "test_key"


@patch.dict(os.environ, {"OPENAI_API_KEY": ""})
def test_llm_settings_without_openai_key():
    """Test LLMSettings without OpenAI API key."""
    with pytest.raises(ValueError, match="OpenAI API key is required when using OpenAI provider"):
        Settings()


@patch.dict(os.environ, {"LLM__PROVIDER": "local"})
def test_llm_settings_with_local_provider():
    """Test LLMSettings with local provider."""
    settings = Settings()
    assert settings.llm.provider == LLMProvider.LOCAL
    # No API key required for local provider
    assert settings.llm.openai_api_key is None
