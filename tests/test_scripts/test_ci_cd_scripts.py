"""Tests for CI/CD scripts."""

import os
import subprocess
import pytest


@pytest.mark.unit
def test_ci_script_exists():
    """Test that the CI script exists."""
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "run_ci.sh",
    )
    assert os.path.exists(script_path)
    assert os.access(script_path, os.X_OK)


@pytest.mark.unit
def test_cd_script_exists():
    """Test that the CD script exists."""
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "run_cd.sh",
    )
    assert os.path.exists(script_path)
    assert os.access(script_path, os.X_OK)


@pytest.mark.unit
def test_ci_script_help():
    """Test that the CI script can be executed with --help."""
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "run_ci.sh",
    )
    
    # Run the script with --help
    try:
        result = subprocess.run(
            [script_path, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        # The script doesn't have a --help option, so it should return non-zero
        assert result.returncode != 0
    except subprocess.CalledProcessError:
        # This is expected
        pass


@pytest.mark.unit
def test_cd_script_help():
    """Test that the CD script can be executed with --help."""
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "run_cd.sh",
    )
    
    # Run the script with --help
    try:
        result = subprocess.run(
            [script_path, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        # The script doesn't have a --help option, so it should return non-zero
        assert result.returncode != 0
    except subprocess.CalledProcessError:
        # This is expected
        pass
