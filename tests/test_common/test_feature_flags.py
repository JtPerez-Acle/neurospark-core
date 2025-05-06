"""Tests for feature flag system."""

import os
import json
import tempfile
import pytest

from src.common.feature_flags import (
    FeatureFlags,
    is_feature_enabled,
    get_feature_value,
    reload_feature_flags,
)


@pytest.fixture
def feature_flags_config():
    """Create a temporary feature flags configuration file."""
    config = {
        "global": {
            "global_flag": True,
            "global_value": "global",
        },
        "development": {
            "dev_flag": True,
            "dev_value": "development",
            "global_value": "overridden",
        },
        "production": {
            "prod_flag": True,
            "prod_value": "production",
        },
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    yield config_path
    
    # Clean up
    os.unlink(config_path)


@pytest.mark.unit
def test_feature_flags_singleton():
    """Test that FeatureFlags is a singleton."""
    flags1 = FeatureFlags()
    flags2 = FeatureFlags()
    
    assert flags1 is flags2


@pytest.mark.unit
def test_feature_flags_load(feature_flags_config):
    """Test loading feature flags from a configuration file."""
    # Create a new instance with the test configuration
    flags = FeatureFlags(config_path=feature_flags_config, environment="development")
    
    # Check global flags
    assert flags.is_enabled("global_flag") is True
    
    # Check environment-specific flags
    assert flags.is_enabled("dev_flag") is True
    assert flags.is_enabled("prod_flag") is False
    
    # Check values
    assert flags.get_value("global_value") == "overridden"
    assert flags.get_value("dev_value") == "development"
    assert flags.get_value("prod_value") is None
    
    # Check default value
    assert flags.get_value("non_existent", "default") == "default"


@pytest.mark.unit
def test_feature_flags_reload(feature_flags_config):
    """Test reloading feature flags."""
    # Create a new instance with the test configuration
    flags = FeatureFlags(config_path=feature_flags_config, environment="development")
    
    # Check initial values
    assert flags.is_enabled("global_flag") is True
    assert flags.get_value("global_value") == "overridden"
    
    # Modify the configuration file
    with open(feature_flags_config, "r") as f:
        config = json.load(f)
    
    config["global"]["global_flag"] = False
    config["development"]["global_value"] = "new_value"
    
    with open(feature_flags_config, "w") as f:
        json.dump(config, f)
    
    # Reload the flags
    flags.reload()
    
    # Check updated values
    assert flags.is_enabled("global_flag") is False
    assert flags.get_value("global_value") == "new_value"


@pytest.mark.unit
def test_feature_flags_helper_functions(feature_flags_config):
    """Test feature flag helper functions."""
    # Create a new instance with the test configuration
    FeatureFlags(config_path=feature_flags_config, environment="development")
    
    # Check helper functions
    assert is_feature_enabled("global_flag") is True
    assert is_feature_enabled("dev_flag") is True
    assert is_feature_enabled("prod_flag") is False
    
    assert get_feature_value("global_value") == "overridden"
    assert get_feature_value("dev_value") == "development"
    assert get_feature_value("prod_value") is None
    assert get_feature_value("non_existent", "default") == "default"
    
    # Modify the configuration file
    with open(feature_flags_config, "r") as f:
        config = json.load(f)
    
    config["global"]["global_flag"] = False
    config["development"]["global_value"] = "new_value"
    
    with open(feature_flags_config, "w") as f:
        json.dump(config, f)
    
    # Reload the flags
    reload_feature_flags()
    
    # Check updated values
    assert is_feature_enabled("global_flag") is False
    assert get_feature_value("global_value") == "new_value"
