"""
Configuration loader with multi-level priority support.

Loads configuration from multiple sources with priority:
1. Command-line arguments (highest)
2. Project directory (.disk-cleaner.yaml)
3. User config (~/.disk-cleaner/config.yaml)
4. Default config (lowest)
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from diskcleaner.config.defaults import get_default_config


class Config:
    """
    Configuration manager with multi-level priority support.

    Usage:
        config = Config.load(
            path="/path/to/project",
            cli_args={"age_threshold": 90}
        )
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize configuration.

        Args:
            config: Configuration dictionary.
        """
        self._config = config

    @classmethod
    def load(
        cls,
        path: Optional[str] = None,
        cli_args: Optional[Dict[str, Any]] = None,
    ) -> "Config":
        """
        Load configuration with proper priority merging.

        Args:
            path: Project path to look for .disk-cleaner.yaml
            cli_args: Command-line arguments (highest priority)

        Returns:
            Config instance with merged configuration.
        """
        # Start with default config
        config = get_default_config()

        # Load and merge user config
        user_config = cls._load_user_config()
        config = cls._merge_configs(config, user_config)

        # Load and merge project config
        if path:
            project_config = cls._load_project_config(path)
            config = cls._merge_configs(config, project_config)

        # Apply command-line arguments (highest priority)
        if cli_args:
            config = cls._apply_cli_args(config, cli_args)

        return cls(config)

    @staticmethod
    def _load_user_config() -> Dict[str, Any]:
        """
        Load user configuration from ~/.disk-cleaner/config.yaml.

        Returns:
            User config dict, or empty dict if not found.
        """
        config_path = Path.home() / ".disk-cleaner" / "config.yaml"

        if not config_path.exists():
            return {}

        return Config._load_yaml_file(config_path)

    @staticmethod
    def _load_project_config(project_path: str) -> Dict[str, Any]:
        """
        Load project configuration from .disk-cleaner.yaml.

        Args:
            project_path: Path to project directory.

        Returns:
            Project config dict, or empty dict if not found.
        """
        project_dir = Path(project_path)

        # Look for .disk-cleaner.yaml in project root
        config_path = project_dir / ".disk-cleaner.yaml"

        if not config_path.exists():
            # Also try disk-cleaner.yaml (without dot)
            config_path = project_dir / "disk-cleaner.yaml"
            if not config_path.exists():
                return {}

        return Config._load_yaml_file(config_path)

    @staticmethod
    def _load_yaml_file(file_path: Path) -> Dict[str, Any]:
        """
        Load YAML file without external dependencies.

        Args:
            file_path: Path to YAML file.

        Returns:
            Parsed YAML as dict, or empty dict on error.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple YAML parser for our config format
            # This avoids requiring pyyaml dependency
            return Config._parse_simple_yaml(content)
        except (OSError, IOError):
            return {}

    @staticmethod
    def _parse_simple_yaml(content: str) -> Dict[str, Any]:
        """
        Parse simplified YAML format.

        This is a basic YAML parser that handles our config format.
        It supports:
        - Key-value pairs
        - Nested dictionaries
        - Lists
        - Comments (#)

        Args:
            content: YAML content as string.

        Returns:
            Parsed configuration as dict.
        """
        config: Dict[str, Any] = {}
        stack: list = [config]
        current = config
        indent_size = 0

        for line in content.split("\n"):
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Calculate indentation
            indent = len(line) - len(line.lstrip())

            # Adjust stack based on indentation
            if indent == 0:
                stack = [config]
                current = config
            elif indent > indent_size:
                # Deeper level, but we should have already created the parent
                pass
            elif indent < indent_size:
                # Shallower level, pop stack
                while len(stack) > 1 and indent < len(stack[-1]) * 2:
                    stack.pop()
                current = stack[-1]

            indent_size = indent

            # Parse key-value pair
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                key = key.strip()
                value = value.strip()

                if not value:
                    # This is a parent key for nested values
                    current[key] = {}
                    stack.append(current[key])
                    current = current[key]
                elif value.startswith("[") and value.endswith("]"):
                    # List value
                    list_str = value[1:-1]
                    current[key] = [item.strip().strip('"\'') for item in list_str.split(",")]
                else:
                    # Simple value
                    # Try to parse as Python literal
                    value = value.strip('"\'')
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.lower() == "null" or value.lower() == "none":
                        value = None
                    elif value.isdigit():
                        value = int(value)
                    else:
                        # Try float
                        try:
                            value = float(value)
                        except ValueError:
                            pass

                    current[key] = value

        return config

    @staticmethod
    def _merge_configs(
        base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two config dictionaries.

        Args:
            base: Base configuration.
            override: Override configuration (higher priority).

        Returns:
            Merged configuration.
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                result[key] = Config._merge_configs(result[key], value)
            else:
                # Override with higher priority value
                result[key] = value

        return result

    @staticmethod
    def _apply_cli_args(
        config: Dict[str, Any], cli_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply command-line arguments to config.

        Args:
            config: Current configuration.
            cli_args: Command-line arguments.

        Returns:
            Updated configuration.
        """
        # CLI args have highest priority, direct override
        for key, value in cli_args.items():
            # Support nested keys with dot notation
            if "." in key:
                parts = key.split(".")
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                config[key] = value

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation for nested values).
            default: Default value if key not found.

        Returns:
            Configuration value, or default if not found.
        """
        # Support dot notation for nested keys
        parts = key.split(".")
        current = self._config

        try:
            for part in parts:
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation).
            value: Value to set.
        """
        parts = key.split(".")
        current = self._config

        # Navigate to parent
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set value
        current[parts[-1]] = value

    @property
    def protected_paths(self) -> List[str]:
        """Get protected paths list."""
        return self.get("protected.paths", [])

    @property
    def protected_patterns(self) -> List[str]:
        """Get protected file patterns."""
        return self.get("protected.patterns", [])

    @property
    def protected_extensions(self) -> List[str]:
        """Get protected file extensions."""
        return self.get("safety.protected_extensions", [])

    @property
    def check_file_locks(self) -> bool:
        """Check if file lock detection is enabled."""
        return self.get("safety.check_file_locks", True)

    @property
    def verify_permissions(self) -> bool:
        """Check if permission verification is enabled."""
        return self.get("safety.verify_permissions", True)

    @property
    def use_incremental_scan(self) -> bool:
        """Check if incremental scanning is enabled."""
        return self.get("scan.use_incremental", True)

    @property
    def cache_dir(self) -> str:
        """Get cache directory path."""
        return self.get("scan.cache_dir", "~/.disk-cleaner/cache")

    @property
    def cache_ttl(self) -> int:
        """Get cache TTL in days."""
        return self.get("scan.cache_ttl", 7)

    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self._config.copy()
