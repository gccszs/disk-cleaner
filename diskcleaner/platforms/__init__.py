"""
Platform-specific functionality
"""

from diskcleaner.platforms.windows import WindowsPlatform
from diskcleaner.platforms.linux import LinuxPlatform
from diskcleaner.platforms.macos import MacOSPlatform

__all__ = [
    "WindowsPlatform",
    "LinuxPlatform",
    "MacOSPlatform",
]
