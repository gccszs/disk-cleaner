"""
macOS-specific platform functionality.

Provides macOS-specific temporary files, caches, and system cleanup locations.
"""

import os
from typing import Dict, List


class MacOSPlatform:
    """macOS platform-specific operations."""

    @staticmethod
    def get_temp_locations() -> List[str]:
        """Get macOS temporary file locations."""
        locations = [
            "/tmp",
            "/private/tmp",
            "/private/var/tmp",
        ]

        # Per-user temp folders
        var_folders = "/var/folders"
        if os.path.exists(var_folders):
            locations.append(var_folders)

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_cache_locations() -> List[str]:
        """Get macOS cache locations."""
        locations = []

        # User cache
        user_cache = os.path.expanduser("~/Library/Caches")
        if os.path.exists(user_cache):
            locations.append(user_cache)
            # Add common application caches
            for app_dir in os.listdir(user_cache):
                app_path = os.path.join(user_cache, app_dir)
                if os.path.isdir(app_path):
                    locations.append(app_path)

        # System cache
        system_cache = "/Library/Caches"
        if os.path.exists(system_cache):
            locations.append(system_cache)

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_log_locations() -> List[str]:
        """Get macOS log file locations."""
        locations = []

        # User logs
        user_logs = os.path.expanduser("~/Library/Logs")
        if os.path.exists(user_logs):
            locations.append(user_logs)

        # System logs
        system_logs = "/Library/Logs"
        if os.path.exists(system_logs):
            locations.append(system_logs)

        # Older macOS logs
        old_logs = "/var/log"
        if os.path.exists(old_logs):
            locations.append(old_logs)

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_system_maintenance_items() -> Dict[str, Dict[str, str]]:
        """Get macOS-specific system maintenance suggestions."""
        return {
            "user_cache": {
                "name": "用户缓存",
                "path": os.path.expanduser("~/Library/Caches"),
                "description": "应用程序缓存文件",
                "risk": "safe",
                "size_hint": "几百MB到数GB",
            },
            "ios_backups": {
                "name": "iOS设备备份",
                "path": os.path.expanduser("~/Library/Application Support/MobileSync/Backup"),
                "description": "iPhone/iPad备份（删除前请确认）",
                "risk": "confirm",
                "size_hint": "每个备份数GB",
            },
            "xcode_derived_data": {
                "name": "Xcode Derived Data",
                "path": os.path.expanduser("~/Library/Developer/Xcode/DerivedData"),
                "description": "Xcode编译中间文件",
                "risk": "safe",
                "size_hint": "几百MB到数GB",
            },
            "homebrew_cache": {
                "name": "Homebrew缓存",
                "path": "/Library/Caches/Homebrew",
                "description": "Homebrew包管理器下载的文件",
                "risk": "safe",
                "size_hint": "几百MB",
                "cleanup_command": "brew cleanup",
            },
            "trash": {
                "name": "废纸篓",
                "path": "~/.Trash",
                "description": "已删除的文件（清空前请确认）",
                "risk": "confirm",
                "size_hint": "取决于删除的文件",
            },
        }

    @staticmethod
    def get_docker_locations() -> List[str]:
        """Get Docker cache locations on macOS."""
        locations = []

        # Docker Desktop on macOS
        docker_mac = os.path.expanduser("~/Library/Containers/com.docker.docker")
        if os.path.exists(docker_mac):
            locations.append(docker_mac)

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_homebrew_locations() -> List[str]:
        """Get Homebrew cache locations."""
        locations = [
            "/Library/Caches/Homebrew",
            "/usr/local/Cellar",  # Intel Macs
            "/opt/homebrew/Cellar",  # Apple Silicon Macs
        ]

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def check_disk_space(path: str = "/") -> Dict[str, float]:
        """Check disk space for macOS filesystems."""
        try:
            stat = os.statvfs(path)

            total = stat.f_frsize * stat.f_blocks
            free = stat.f_frsize * stat.f_bavail
            used = total - free

            return {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 2) if total > 0 else 0,
            }
        except (OSError, AttributeError):
            return {
                "total_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "usage_percent": 0,
            }
