r"""
Windows-specific platform functionality.
"""

from typing import Dict, List


class WindowsPlatform:
    """Windows platform-specific operations."""

    @staticmethod
    def get_temp_locations() -> List[str]:
        """Get Windows temporary file locations."""
        return [
            "%TEMP%",
            "%TMP%",
            r"%LOCALAPPDATA%\Temp",
            r"C:\Windows\Temp",
            r"C:\Windows\Prefetch",
        ]

    @staticmethod
    def get_cache_locations() -> List[str]:
        """Get Windows cache locations."""
        return [
            r"%LOCALAPPDATA%\Microsoft\Windows\INetCache",
            r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache",
            r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache",
        ]
