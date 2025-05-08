"""Configuration module for NeuroSpark Core."""

import os
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Environment enum."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Log level enum."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LLMProvider(str, Enum):
    """LLM provider enum."""

    OPENAI = "openai"
    LOCAL = "local"


class APISettings(BaseModel):
    """API settings."""

    host: str = Field("0.0.0.0", description="API host")
    port: int = Field(8000, description="API port")
    grpc_port: int = Field(50051, description="gRPC port")

    @field_validator("host", mode="before")
    def validate_host(cls, v: Any) -> str:
        """Validate API host.

        Args:
            v: The value to validate.

        Returns:
            str: The validated value.
        """
        if not v:
            return os.environ.get("API_HOST", "0.0.0.0")
        return v

    @field_validator("port", mode="before")
    def validate_port(cls, v: Any) -> int:
        """Validate API port.

        Args:
            v: The value to validate.

        Returns:
            int: The validated value.
        """
        if not v:
            env_value = os.environ.get("API_PORT")
            if env_value:
                try:
                    return int(env_value)
                except ValueError:
                    pass
            return 8000
        return v

    @field_validator("grpc_port", mode="before")
    def validate_grpc_port(cls, v: Any) -> int:
        """Validate gRPC port.

        Args:
            v: The value to validate.

        Returns:
            int: The validated value.
        """
        if not v:
            env_value = os.environ.get("GRPC_PORT")
            if env_value:
                try:
                    return int(env_value)
                except ValueError:
                    pass
            return 50051
        return v


class DatabaseSettings(BaseModel):
    """Database settings."""

    host: str = Field("postgres", description="Database host")
    port: int = Field(5432, description="Database port")
    db: str = Field("neurospark", description="Database name")
    user: str = Field("postgres", description="Database user")
    password: str = Field("postgres_password", description="Database password")

    @property
    def url(self) -> str:
        """Get the database URL.

        Returns:
            str: The database URL.
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @field_validator("host", mode="before")
    def validate_host(cls, v: Any) -> str:
        """Validate database host.

        Args:
            v: The value to validate.

        Returns:
            str: The validated value.
        """
        if not v:
            return os.environ.get("POSTGRES_HOST", "postgres")
        return v

    @field_validator("port", mode="before")
    def validate_port(cls, v: Any) -> int:
        """Validate database port.

        Args:
            v: The value to validate.

        Returns:
            int: The validated value.
        """
        if not v:
            env_value = os.environ.get("POSTGRES_PORT")
            if env_value:
                try:
                    return int(env_value)
                except ValueError:
                    pass
            return 5432
        return v

    @field_validator("db", mode="before")
    def validate_db(cls, v: Any) -> str:
        """Validate database name.

        Args:
            v: The value to validate.

        Returns:
            str: The validated value.
        """
        if not v:
            return os.environ.get("POSTGRES_DB", "neurospark")
        return v

    @field_validator("user", mode="before")
    def validate_user(cls, v: Any) -> str:
        """Validate database user.

        Args:
            v: The value to validate.

        Returns:
            str: The validated value.
        """
        if not v:
            return os.environ.get("POSTGRES_USER", "postgres")
        return v

    @field_validator("password", mode="before")
    def validate_password(cls, v: Any) -> str:
        """Validate database password.

        Args:
            v: The value to validate.

        Returns:
            str: The validated value.
        """
        if not v:
            return os.environ.get("POSTGRES_PASSWORD", "postgres_password")
        return v


class QdrantSettings(BaseModel):
    """Qdrant settings."""

    host: str = Field("qdrant", description="Qdrant host")
    port: int = Field(6333, description="Qdrant port")
    grpc_port: int = Field(6334, description="Qdrant gRPC port")

    @property
    def url(self) -> str:
        """Get the Qdrant URL.

        Returns:
            str: The Qdrant URL.
        """
        return f"http://{self.host}:{self.port}"


class ElasticSettings(BaseModel):
    """ElasticLite settings."""

    host: str = Field("elasticlite", description="ElasticLite host")
    port: int = Field(9200, description="ElasticLite port")

    @property
    def url(self) -> str:
        """Get the ElasticLite URL.

        Returns:
            str: The ElasticLite URL.
        """
        return f"http://{self.host}:{self.port}"


class MinioSettings(BaseModel):
    """MinIO settings."""

    host: str = Field("minio", description="MinIO host")
    port: int = Field(9000, description="MinIO port")
    root_user: str = Field("minioadmin", description="MinIO root user")
    root_password: str = Field("minioadmin", description="MinIO root password")
    bucket: str = Field("neurospark", description="MinIO bucket")

    @property
    def url(self) -> str:
        """Get the MinIO URL.

        Returns:
            str: The MinIO URL.
        """
        return f"http://{self.host}:{self.port}"


class RedisSettings(BaseModel):
    """Redis settings."""

    host: str = Field("redis", description="Redis host")
    port: int = Field(6379, description="Redis port")
    password: str = Field("redis_password", description="Redis password")
    redis_url: Optional[str] = Field(None, description="Redis URL")

    @property
    def url(self) -> str:
        """Get the Redis URL.

        Returns:
            str: The Redis URL.
        """
        if self.redis_url:
            return self.redis_url
        return f"redis://:{self.password}@{self.host}:{self.port}/0"

    @field_validator("redis_url", mode="before")
    def validate_redis_url(cls, v: Any) -> Optional[str]:
        """Validate Redis URL.

        Args:
            v: The value to validate.

        Returns:
            Optional[str]: The validated value.
        """
        if not v:
            return os.environ.get("REDIS_URL")
        return v


class LLMSettings(BaseModel):
    """LLM settings."""

    provider: LLMProvider = Field(LLMProvider.OPENAI, description="LLM provider")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_model: str = Field("gpt-4o", description="OpenAI model")

    @field_validator("openai_api_key", mode="before")
    def validate_openai_api_key(cls, v: Any) -> Optional[str]:
        """Validate OpenAI API key.

        Args:
            v: The value to validate.

        Returns:
            Optional[str]: The validated value.
        """
        if not v:
            return os.environ.get("OPENAI_API_KEY")
        return v


class ExternalAPISettings(BaseModel):
    """External API settings."""

    openalex_api_key: Optional[str] = Field(None, description="OpenAlex API key")
    newsapi_api_key: Optional[str] = Field(None, description="NewsAPI API key")
    serpapi_api_key: Optional[str] = Field(None, description="SerpAPI API key")

    @field_validator("serpapi_api_key", mode="before")
    def validate_serpapi_api_key(cls, v: Any) -> Optional[str]:
        """Validate SerpAPI API key.

        Args:
            v: The value to validate.

        Returns:
            Optional[str]: The validated value.
        """
        if not v:
            return os.environ.get("SERPAPI_API_KEY")
        return v

    @field_validator("newsapi_api_key", mode="before")
    def validate_newsapi_api_key(cls, v: Any) -> Optional[str]:
        """Validate NewsAPI API key.

        Args:
            v: The value to validate.

        Returns:
            Optional[str]: The validated value.
        """
        if not v:
            return os.environ.get("NEWSAPI_API_KEY")
        return v

    @field_validator("openalex_api_key", mode="before")
    def validate_openalex_api_key(cls, v: Any) -> Optional[str]:
        """Validate OpenAlex API key.

        Args:
            v: The value to validate.

        Returns:
            Optional[str]: The validated value.
        """
        if not v:
            return os.environ.get("OPENALEX_API_KEY")
        return v


class AgentSettings(BaseModel):
    """Agent settings."""

    curator_poll_interval: int = Field(3600, description="Curator poll interval in seconds")
    custodian_schedule: str = Field("0 2 * * *", description="Custodian schedule in cron format")
    reviewer_threshold: float = Field(0.75, description="Reviewer faith score threshold")

    @field_validator("curator_poll_interval", mode="before")
    def validate_curator_poll_interval(cls, v: Any) -> int:
        """Validate curator poll interval.

        Args:
            v: The value to validate.

        Returns:
            int: The validated value.
        """
        if not v:
            env_value = os.environ.get("CURATOR_POLL_INTERVAL")
            if env_value:
                try:
                    return int(env_value)
                except ValueError:
                    pass
            return 3600
        return v


class ResourceLimits(BaseModel):
    """Resource limits."""

    max_tokens_per_request: int = Field(4000, description="Maximum tokens per request")
    max_concurrent_requests: int = Field(10, description="Maximum concurrent requests")


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # General settings
    environment: Environment = Field(Environment.DEVELOPMENT, description="Environment")
    log_level: LogLevel = Field(LogLevel.INFO, description="Log level")

    # Service settings
    api: APISettings = Field(default_factory=APISettings, description="API settings")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings, description="Database settings")
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings, description="Qdrant settings")
    elastic: ElasticSettings = Field(default_factory=ElasticSettings, description="ElasticLite settings")
    minio: MinioSettings = Field(default_factory=MinioSettings, description="MinIO settings")
    redis: RedisSettings = Field(default_factory=RedisSettings, description="Redis settings")

    # LLM settings
    llm: LLMSettings = Field(default_factory=LLMSettings, description="LLM settings")

    # External API settings
    external_api_settings: ExternalAPISettings = Field(default_factory=ExternalAPISettings, description="External API settings")

    # Agent settings
    agent_settings: AgentSettings = Field(default_factory=AgentSettings, description="Agent settings")

    # Resource limits
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits, description="Resource limits")

    # Configuration directory
    config_dir: str = Field(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config"), description="Configuration directory")

    # This validator is no longer needed as we have a validator in the LLMSettings class
    # @field_validator("llm", mode="before")
    # def validate_llm(cls, v: Any) -> Dict[str, Any]:
    #     """Validate LLM settings.
    #
    #     Args:
    #         v: The value to validate.
    #
    #     Returns:
    #         Dict[str, Any]: The validated value.
    #
    #     Raises:
    #         ValueError: If the OpenAI API key is missing when using OpenAI.
    #     """
    #     if isinstance(v, dict):
    #         if v.get("provider") == LLMProvider.OPENAI and not v.get("openai_api_key"):
    #             v["openai_api_key"] = os.environ.get("OPENAI_API_KEY")
    #             if not v["openai_api_key"]:
    #                 raise ValueError("OpenAI API key is required when using OpenAI provider")
    #     return v

    def get_service_urls(self) -> Dict[str, str]:
        """Get all service URLs.

        Returns:
            Dict[str, str]: A dictionary of service URLs.
        """
        return {
            "database": self.database.url,
            "qdrant": self.qdrant.url,
            "elastic": self.elastic.url,
            "minio": self.minio.url,
            "redis": self.redis.url,
        }


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings.

    Returns:
        Settings: The application settings.
    """
    return settings
