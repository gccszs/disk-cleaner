"""
Linux-specific platform functionality.

Provides Linux-specific temporary files, caches, and system cleanup locations.
"""

import os
from typing import Dict, List


class LinuxPlatform:
    """Linux platform-specific operations."""

    @staticmethod
    def get_temp_locations() -> List[str]:
        """Get Linux temporary file locations."""
        locations = ["/tmp", "/var/tmp"]

        # User-specific temp
        user_cache = os.path.expanduser("~/.cache")
        if os.path.exists(user_cache):
            locations.append(user_cache)

        return [loc for loc in locations if os.path.exists(loc)]

    @staticmethod
    def get_cache_locations() -> List[str]:
        """Get Linux cache locations."""
        locations = ["/var/cache"]

        # User cache
        user_cache = os.path.expanduser("~/.cache")
        if os.path.exists(user_cache):
            # Add common application caches
            try:
                for app_dir in os.listdir(user_cache):
                    app_path = os.path.join(user_cache, app_dir)
                    if os.path.isdir(app_path):
                        locations.append(app_path)
            except (OSError, PermissionError):
                # Skip if we can't read cache directory
                pass

        # Thumbnail cache
        thumb_cache = os.path.expanduser("~/.thumbnails")
        if os.path.exists(thumb_cache):
            locations.append(thumb_cache)

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_log_locations() -> List[str]:
        """Get Linux log file locations."""
        locations = ["/var/log"]

        # User logs
        user_logs = os.path.expanduser("~/.local/share/logs")
        if os.path.exists(user_logs):
            locations.append(user_logs)

        # Journal logs if systemd is used
        if os.path.exists("/var/log/journal"):
            locations.append("/var/log/journal")

        return [loc for loc in locations if loc and os.path.exists(loc)]

    @staticmethod
    def get_system_maintenance_items() -> Dict[str, Dict[str, str]]:
        """Get Linux-specific system maintenance suggestions."""
        return {
            "apt_cache": {
                "name": "APT Cache",
                "path": "/var/cache/apt/archives",
                "description": "APT包管理器下载的包文件",
                "risk": "safe",
                "size_hint": "几百MB",
                "cleanup_command": "sudo apt-get clean",
            },
            "journal_logs": {
                "name": "Systemd Journal",
                "path": "/var/log/journal",
                "description": "系统日志（可以限制大小）",
                "risk": "confirm",
                "size_hint": "几十MB到数GB",
                "cleanup_command": "sudo journalctl --vacuum-size=500M",
            },
            "old_kernels": {
                "name": "旧内核版本",
                "path": "/boot",
                "description": "已安装的旧Linux内核",
                "risk": "confirm",
                "size_hint": "每个内核200-500MB",
                "note": "保留当前和上一个版本",
            },
            "snap_cache": {
                "name": "Snap缓存",
                "path": "/var/lib/snapd/snaps",
                "description": "Snap包旧版本",
                "risk": "safe",
                "size_hint": "几百MB到数GB",
                "cleanup_command": "sudo snap set system refresh.retain=2",
            },
        }

    @staticmethod
    def get_package_manager_cache() -> Dict[str, Dict[str, str]]:
        """Get package manager cache locations and cleanup commands."""
        return {
            "apt": {
                "cache_dir": "/var/cache/apt/archives",
                "clean_command": "sudo apt-get clean",
                "autoremove_command": "sudo apt-get autoremove",
            },
            "yum": {
                "cache_dir": "/var/cache/yum",
                "clean_command": "sudo yum clean all",
            },
            "dnf": {
                "cache_dir": "/var/cache/dnf",
                "clean_command": "sudo dnf clean all",
            },
            "pacman": {
                "cache_dir": "/var/cache/pacman/pkg",
                "clean_command": "sudo pacman -Sc",
            },
        }

    @staticmethod
    def get_docker_locations() -> List[str]:
        """Get Docker cache locations on Linux."""
        locations = [
            "/var/lib/docker",
        ]

        # Docker overlay2 storage
        docker_overlay = "/var/lib/docker/overlay2"
        if os.path.exists(docker_overlay):
            locations.append(docker_overlay)

        return [loc for loc in locations if os.path.exists(loc)]

    @staticmethod
    def check_disk_space(path: str = "/") -> Dict[str, float]:
        """Check disk space for Linux filesystems."""
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
