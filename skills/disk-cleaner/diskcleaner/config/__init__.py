"""
Configuration management
"""

from diskcleaner.config.defaults import get_default_config
from diskcleaner.config.loader import Config

__all__ = [
    "Config",
    "get_default_config",
]
