"""Test the CI configuration."""

import os
import yaml
import pytest


def test_ci_config_exists():
    """Test that the CI configuration file exists."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ci_config_path = os.path.join(project_root, ".github", "workflows", "ci.yml")
    assert os.path.exists(ci_config_path), "CI configuration file not found"


def test_ci_config_is_valid_yaml():
    """Test that the CI configuration file is valid YAML."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ci_config_path = os.path.join(project_root, ".github", "workflows", "ci.yml")
    
    with open(ci_config_path, "r") as f:
        try:
            ci_config = yaml.safe_load(f)
            assert ci_config is not None, "CI configuration is empty"
        except yaml.YAMLError as e:
            pytest.fail(f"CI configuration is not valid YAML: {e}")


def test_ci_config_has_required_jobs():
    """Test that the CI configuration has the required jobs."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ci_config_path = os.path.join(project_root, ".github", "workflows", "ci.yml")
    
    with open(ci_config_path, "r") as f:
        ci_config = yaml.safe_load(f)
    
    required_jobs = ["lint", "test", "docker-build", "docker-compose", "security-scan"]
    
    for job in required_jobs:
        assert job in ci_config["jobs"], f"Job '{job}' not found in CI configuration"


def test_ci_config_docker_build_matrix():
    """Test that the CI configuration has a matrix for Docker builds."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ci_config_path = os.path.join(project_root, ".github", "workflows", "ci.yml")
    
    with open(ci_config_path, "r") as f:
        ci_config = yaml.safe_load(f)
    
    assert "docker-build" in ci_config["jobs"]
    assert "strategy" in ci_config["jobs"]["docker-build"]
    assert "matrix" in ci_config["jobs"]["docker-build"]["strategy"]
    assert "service" in ci_config["jobs"]["docker-build"]["strategy"]["matrix"]
    
    required_services = [
        "base",
        "api",
        "curator",
        "vectoriser",
        "professor",
        "reviewer",
        "tutor",
        "auditor",
        "custodian",
        "governor",
    ]
    
    for service in required_services:
        assert service in ci_config["jobs"]["docker-build"]["strategy"]["matrix"]["service"], \
            f"Service '{service}' not found in Docker build matrix"


if __name__ == "__main__":
    test_ci_config_exists()
    test_ci_config_is_valid_yaml()
    test_ci_config_has_required_jobs()
    test_ci_config_docker_build_matrix()
