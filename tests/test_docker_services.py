"""Test the service-specific Dockerfiles."""

import os
import subprocess
import pytest


@pytest.mark.parametrize(
    "service",
    [
        "api",
        "curator",
        "vectoriser",
        "professor",
        "reviewer",
        "tutor",
        "auditor",
        "custodian",
        "governor",
    ],
)
def test_service_dockerfile_builds(service):
    """Test that the service-specific Dockerfile builds successfully."""
    # Skip actual build in CI to save time, just check file exists
    if os.environ.get("CI") == "true":
        dockerfile_path = os.path.join(
            os.path.dirname(__file__), "..", "docker", f"Dockerfile.{service}"
        )
        assert os.path.exists(dockerfile_path), f"Dockerfile for {service} not found"
        return

    # Get the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # First build the base image if it doesn't exist
    result = subprocess.run(
        ["docker", "image", "ls", "neurospark-base:latest", "--format", "{{.Repository}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    
    if "neurospark-base" not in result.stdout:
        subprocess.run(
            [
                "docker", "build",
                "-f", os.path.join(project_root, "docker", "Dockerfile.base"),
                "-t", "neurospark-base:latest",
                project_root
            ],
            check=True,
        )
    
    # Build the service image
    result = subprocess.run(
        [
            "docker", "build",
            "-f", os.path.join(project_root, "docker", f"Dockerfile.{service}"),
            "-t", f"neurospark-{service}:test",
            project_root
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    
    # Check that the build was successful
    assert result.returncode == 0, f"Docker build for {service} failed: {result.stderr}"
    
    # Verify the image exists
    result = subprocess.run(
        ["docker", "image", "ls", f"neurospark-{service}:test", "--format", "{{.Repository}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    
    assert f"neurospark-{service}" in result.stdout, f"Image for {service} not found after build"
    
    # Clean up the test image
    subprocess.run(
        ["docker", "image", "rm", f"neurospark-{service}:test"],
        capture_output=True,
        check=False,
    )


if __name__ == "__main__":
    for service in [
        "api",
        "curator",
        "vectoriser",
        "professor",
        "reviewer",
        "tutor",
        "auditor",
        "custodian",
        "governor",
    ]:
        test_service_dockerfile_builds(service)
