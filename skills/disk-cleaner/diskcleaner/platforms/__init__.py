"""
Platform-specific functionality
"""

from diskcleaner.platforms.linux import LinuxPlatform
from diskcleaner.platforms.macos import MacOSPlatform
from diskcleaner.platforms.windows import WindowsPlatform

__all__ = [
    "WindowsPlatform",
    "LinuxPlatform",
    "MacOSPlatform",
]
