"""
Windows-specific platform functionality.

Provides Windows-specific temporary files, caches, and system cleanup locations.
"""

import os
from pathlib import Path
from typing import Dict, List


class WindowsPlatform:
    """Windows platform-specific operations."""

    @staticmethod
    def get_temp_locations() -> List[str]:
        """Get Windows temporary file locations."""
        locations = [
            os.environ.get("TEMP", ""),
            os.environ.get("TMP", ""),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
        ]

        # System temp directories
        windir = os.environ.get("WINDIR", "C:\\Windows")
        locations.extend(
            [
                os.path.join(windir, "Temp"),
                os.path.join(windir, "Prefetch"),
            ]
        )

        # Windows Update cache
        locations.append(os.path.join(windir, "SoftwareDistribution", "Download"))

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_cache_locations() -> List[str]:
        """Get Windows cache locations."""
        localappdata = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")

        locations = []

        # Browser caches
        if localappdata:
            locations.extend(
                [
                    os.path.join(localappdata, "Microsoft", "Windows", "INetCache"),
                    os.path.join(localappdata, "Google", "Chrome", "User Data", "Default", "Cache"),
                    os.path.join(
                        localappdata, "Microsoft", "Edge", "User Data", "Default", "Cache"
                    ),
                    os.path.join(appdata, "Mozilla", "Firefox", "Profiles"),
                ]
            )

        # Thumbnail cache
        if localappdata:
            locations.append(os.path.join(localappdata, "Microsoft", "Windows", "Explorer"))

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_log_locations() -> List[str]:
        """Get Windows log file locations."""
        locations = []

        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            locations.extend(
                [
                    os.path.join(localappdata, "Microsoft", "Windows", "History"),
                    os.path.join(localappdata, "Microsoft", "Windows", "WebCache"),
                ]
            )

        programdata = os.environ.get("PROGRAMDATA", "")
        if programdata:
            locations.append(os.path.join(programdata, "Microsoft", "Windows", "WER"))

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_system_maintenance_items() -> Dict[str, Dict[str, str]]:
        """Get Windows-specific system maintenance suggestions."""
        return {
            "windows_update": {
                "name": "Windows Update Cache",
                "path": os.path.join(
                    os.environ.get("WINDIR", "C:\\Windows"), "SoftwareDistribution", "Download"
                ),
                "description": "Windows Update下载的临时文件",
                "risk": "safe",
                "size_hint": "几百MB到数GB",
            },
            "recycle_bin": {
                "name": "回收站",
                "path": os.path.join(os.environ.get("SYSTEMDRIVE", "C:"), "$Recycle.Bin"),
                "description": "已删除的文件（清空前请确认）",
                "risk": "confirm",
                "size_hint": "取决于删除的文件",
            },
            "prefetch": {
                "name": "Prefetch缓存",
                "path": os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Prefetch"),
                "description": "应用程序预读数据（可安全删除）",
                "risk": "safe",
                "size_hint": "几十MB",
            },
        }

    @staticmethod
    def get_docker_locations() -> List[str]:
        """Get Docker cache locations on Windows."""
        locations = []

        # Docker Desktop on Windows uses WSL2 backend
        programdata = os.environ.get("PROGRAMDATA", "")
        if programdata:
            locations.append(os.path.join(programdata, "Docker"))

        appdata = os.environ.get("APPDATA", "")
        if appdata:
            locations.append(os.path.join(appdata, "Docker"))

        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            locations.append(os.path.join(localappdata, "Docker"))

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def check_disk_space(drive: str = None) -> Dict[str, float]:
        """Check disk space for Windows drives."""
        import ctypes

        if not drive:
            drive = os.environ.get("SYSTEMDRIVE", "C:")

        total_bytes = ctypes.c_ulonglong(0)
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(drive),
            None,
            ctypes.byref(total_bytes),
            ctypes.byref(free_bytes),
        )

        total = total_bytes.value
        free = free_bytes.value
        used = total - free

        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 2) if total > 0 else 0,
        }
