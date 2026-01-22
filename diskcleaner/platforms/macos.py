"""
macOS-specific platform functionality.
"""

from typing import List


class MacOSPlatform:
    """macOS platform-specific operations."""

    @staticmethod
    def get_temp_locations() -> List[str]:
        """Get macOS temporary file locations."""
        return [
            "/tmp",
            "/private/tmp",
            "/private/var/tmp",
            "/var/folders",
        ]

    @staticmethod
    def get_user_cache_locations() -> List[str]:
        """Get user cache locations."""
        return [
            "~/Library/Caches",
            "~/Library/Logs",
        ]
