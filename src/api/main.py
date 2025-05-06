"""Main API module for NeuroSpark Core."""

import os
import time
import logging
from typing import Dict, Any, List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NeuroSpark Core API",
    description="API for the NeuroSpark Core platform",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start time for uptime calculation
start_time = time.time()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    uptime: float
    services: Dict[str, Dict[str, Any]]


class ServiceStatus(BaseModel):
    """Service status model."""

    name: str
    status: str
    details: Dict[str, Any] = {}


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.
    
    Returns:
        HealthResponse: Health check response with status and service information.
    """
    # Calculate uptime
    uptime = time.time() - start_time
    
    # Check services
    services = {
        "postgres": check_postgres_health(),
        "redis": check_redis_health(),
        "qdrant": check_qdrant_health(),
        "elasticlite": check_elasticlite_health(),
        "minio": check_minio_health(),
    }
    
    # Determine overall status
    status = "healthy"
    for service in services.values():
        if service["status"] != "healthy":
            status = "degraded"
            break
    
    return HealthResponse(
        status=status,
        version="0.1.0",
        uptime=uptime,
        services=services,
    )


@app.get("/health/{service}", response_model=Dict[str, Any])
async def service_health_check(service: str) -> Dict[str, Any]:
    """Health check endpoint for a specific service.
    
    Args:
        service: The service to check.
        
    Returns:
        Dict[str, Any]: Service health check response.
        
    Raises:
        HTTPException: If the service is not found.
    """
    health_checks = {
        "postgres": check_postgres_health,
        "redis": check_redis_health,
        "qdrant": check_qdrant_health,
        "elasticlite": check_elasticlite_health,
        "minio": check_minio_health,
    }
    
    if service not in health_checks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service}' not found",
        )
    
    return health_checks[service]()


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint.
    
    Returns:
        Dict[str, str]: Welcome message.
    """
    return {"message": "Welcome to NeuroSpark Core API"}


@app.get("/agents", response_model=List[str])
async def list_agents() -> List[str]:
    """List all available agents.
    
    Returns:
        List[str]: List of agent names.
    """
    return [
        "curator",
        "vectoriser",
        "professor",
        "reviewer",
        "tutor",
        "auditor",
        "custodian",
        "governor",
    ]


def check_postgres_health() -> Dict[str, Any]:
    """Check Postgres health.
    
    Returns:
        Dict[str, Any]: Postgres health status.
    """
    # In a real implementation, this would check the actual Postgres connection
    try:
        # Placeholder for actual implementation
        return {
            "status": "healthy",
            "details": {
                "version": "16.0",
                "connections": 5,
            },
        }
    except Exception as e:
        logger.error(f"Postgres health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": {
                "error": str(e),
            },
        }


def check_redis_health() -> Dict[str, Any]:
    """Check Redis health.
    
    Returns:
        Dict[str, Any]: Redis health status.
    """
    # In a real implementation, this would check the actual Redis connection
    try:
        # Placeholder for actual implementation
        return {
            "status": "healthy",
            "details": {
                "version": "7.0.5",
                "used_memory": "1.2 MB",
            },
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": {
                "error": str(e),
            },
        }


def check_qdrant_health() -> Dict[str, Any]:
    """Check Qdrant health.
    
    Returns:
        Dict[str, Any]: Qdrant health status.
    """
    # In a real implementation, this would check the actual Qdrant connection
    try:
        # Placeholder for actual implementation
        return {
            "status": "healthy",
            "details": {
                "version": "1.4.0",
                "collections": 3,
            },
        }
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": {
                "error": str(e),
            },
        }


def check_elasticlite_health() -> Dict[str, Any]:
    """Check ElasticLite health.
    
    Returns:
        Dict[str, Any]: ElasticLite health status.
    """
    # In a real implementation, this would check the actual ElasticLite connection
    try:
        # Placeholder for actual implementation
        return {
            "status": "healthy",
            "details": {
                "version": "8.9.0",
                "indices": 2,
            },
        }
    except Exception as e:
        logger.error(f"ElasticLite health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": {
                "error": str(e),
            },
        }


def check_minio_health() -> Dict[str, Any]:
    """Check MinIO health.
    
    Returns:
        Dict[str, Any]: MinIO health status.
    """
    # In a real implementation, this would check the actual MinIO connection
    try:
        # Placeholder for actual implementation
        return {
            "status": "healthy",
            "details": {
                "version": "RELEASE.2023-07-21T21-12-44Z",
                "buckets": 1,
            },
        }
    except Exception as e:
        logger.error(f"MinIO health check failed: {e}")
        return {
            "status": "unhealthy",
            "details": {
                "error": str(e),
            },
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
    )
