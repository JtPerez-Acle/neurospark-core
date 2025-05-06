"""Test the docker-compose.yml file."""

import os
import subprocess
import pytest
import yaml


def test_docker_compose_file_exists():
    """Test that the docker-compose.yml file exists."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docker_compose_path = os.path.join(project_root, "docker-compose.yml")
    assert os.path.exists(docker_compose_path), "docker-compose.yml file not found"


def test_docker_compose_file_is_valid():
    """Test that the docker-compose.yml file is valid YAML."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docker_compose_path = os.path.join(project_root, "docker-compose.yml")
    
    with open(docker_compose_path, "r") as f:
        try:
            docker_compose = yaml.safe_load(f)
            assert docker_compose is not None, "docker-compose.yml is empty"
            assert "services" in docker_compose, "No services defined in docker-compose.yml"
        except yaml.YAMLError as e:
            pytest.fail(f"docker-compose.yml is not valid YAML: {e}")


def test_docker_compose_services():
    """Test that all required services are defined in docker-compose.yml."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docker_compose_path = os.path.join(project_root, "docker-compose.yml")
    
    with open(docker_compose_path, "r") as f:
        docker_compose = yaml.safe_load(f)
    
    required_services = [
        "api",
        "curator",
        "vectoriser",
        "professor",
        "reviewer",
        "tutor",
        "auditor",
        "custodian",
        "governor",
        "postgres",
        "qdrant",
        "elasticlite",
        "minio",
        "redis",
    ]
    
    for service in required_services:
        assert service in docker_compose["services"], f"Service '{service}' not defined in docker-compose.yml"


def test_docker_compose_config():
    """Test that docker-compose config is valid."""
    # Skip in CI to avoid Docker dependency
    if os.environ.get("CI") == "true":
        pytest.skip("Skipping in CI environment")
        
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Create a minimal .env file if it doesn't exist
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("# Minimal .env for testing\n")
    
    # Run docker-compose config to validate the configuration
    result = subprocess.run(
        ["docker-compose", "config", "--quiet"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    
    assert result.returncode == 0, f"docker-compose config failed: {result.stderr}"


if __name__ == "__main__":
    test_docker_compose_file_exists()
    test_docker_compose_file_is_valid()
    test_docker_compose_services()
    test_docker_compose_config()
