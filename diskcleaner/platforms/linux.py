"""
Linux-specific platform functionality.
"""

from typing import List


class LinuxPlatform:
    """Linux platform-specific operations."""

    @staticmethod
    def get_temp_locations() -> List[str]:
        """Get Linux temporary file locations."""
        return [
            "/tmp",
            "/var/tmp",
            "/var/cache",
        ]

    @staticmethod
    def get_package_manager_cache() -> List[str]:
        """Get package manager cache locations."""
        return [
            "/var/cache/apt/archives",
            "/var/cache/dnf",
            "/var/cache/pacman/pkg",
        ]
