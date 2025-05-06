"""Feature flag system for NeuroSpark Core."""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class FeatureFlags:
    """Feature flag system for NeuroSpark Core."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        if cls._instance is None:
            cls._instance = super(FeatureFlags, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        config_path: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        """Initialize the feature flag system.

        Args:
            config_path: Path to the feature flags configuration file.
            environment: The environment to use for feature flags.
        """
        if hasattr(self, '_initialized') and self._initialized:
            # If a new config_path or environment is provided, update and reload
            if config_path and config_path != self._config_path:
                self._config_path = config_path
                self._load_flags()
            if environment and environment != self._environment:
                self._environment = environment
                self._load_flags()
            return

        self._initialized = True
        self._flags = {}
        self._environment = environment or os.environ.get("ENVIRONMENT", "development")

        if config_path:
            self._config_path = config_path
        else:
            # Default to the feature_flags.json file in the project root
            project_root = Path(__file__).parent.parent.parent
            self._config_path = str(project_root / "config" / "feature_flags.json")

        self._load_flags()

    def _load_flags(self) -> None:
        """Load feature flags from the configuration file."""
        try:
            if not os.path.exists(self._config_path):
                logger.warning(f"Feature flags configuration file not found: {self._config_path}")
                return

            with open(self._config_path, "r") as f:
                config = json.load(f)

            # Load global flags
            global_flags = config.get("global", {})
            self._flags.update(global_flags)

            # Load environment-specific flags
            env_flags = config.get(self._environment, {})
            self._flags.update(env_flags)

            logger.info(f"Loaded {len(self._flags)} feature flags for environment: {self._environment}")
        except Exception as e:
            logger.error(f"Error loading feature flags: {e}")

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled.

        Args:
            flag_name: The name of the feature flag.

        Returns:
            True if the feature flag is enabled, False otherwise.
        """
        return self._flags.get(flag_name, False)

    def get_value(self, flag_name: str, default: Any = None) -> Any:
        """Get the value of a feature flag.

        Args:
            flag_name: The name of the feature flag.
            default: The default value to return if the flag is not found.

        Returns:
            The value of the feature flag, or the default value if not found.
        """
        return self._flags.get(flag_name, default)

    def get_all_flags(self) -> Dict[str, Any]:
        """Get all feature flags.

        Returns:
            A dictionary of all feature flags.
        """
        return self._flags.copy()

    def reload(self) -> None:
        """Reload feature flags from the configuration file."""
        self._load_flags()


# Create a singleton instance
feature_flags = FeatureFlags()


def is_feature_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled.

    Args:
        flag_name: The name of the feature flag.

    Returns:
        True if the feature flag is enabled, False otherwise.
    """
    return feature_flags.is_enabled(flag_name)


def get_feature_value(flag_name: str, default: Any = None) -> Any:
    """Get the value of a feature flag.

    Args:
        flag_name: The name of the feature flag.
        default: The default value to return if the flag is not found.

    Returns:
        The value of the feature flag, or the default value if not found.
    """
    return feature_flags.get_value(flag_name, default)


def reload_feature_flags() -> None:
    """Reload feature flags from the configuration file."""
    feature_flags.reload()
