"""Test the base Dockerfile."""

import os
import subprocess
import pytest


@pytest.mark.skip(reason="Docker build issues")
def test_base_dockerfile_builds():
    """Test that the base Dockerfile builds successfully."""
    # Get the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Build the base image
    result = subprocess.run(
        [
            "docker", "build",
            "-f", os.path.join(project_root, "docker", "Dockerfile.base"),
            "-t", "neurospark-base:test",
            project_root
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Check that the build was successful
    assert result.returncode == 0, f"Docker build failed: {result.stderr}"

    # Verify the image exists
    result = subprocess.run(
        ["docker", "image", "ls", "neurospark-base:test", "--format", "{{.Repository}}"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "neurospark-base" in result.stdout, "Image not found after build"

    # Clean up the test image
    subprocess.run(
        ["docker", "image", "rm", "neurospark-base:test"],
        capture_output=True,
        check=False,
    )


if __name__ == "__main__":
    test_base_dockerfile_builds()
