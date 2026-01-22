"""
Configuration management
"""

from diskcleaner.config.loader import Config
from diskcleaner.config.defaults import get_default_config

__all__ = [
    "Config",
    "get_default_config",
]
