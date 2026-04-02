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
    def _is_accessible(path: Path) -> bool:
        """
        Check if a path is accessible and has content.

        Args:
            path: Path to check

        Returns:
            True if path exists, is accessible, and has content
        """
        try:
            if not path.exists():
                return False

            # Check if directory is accessible
            if not path.is_dir():
                return False

            # Try to list contents to verify permissions
            next(path.iterdir())
            return True
        except (PermissionError, OSError, StopIteration):
            return False

    @staticmethod
    def _find_chrome_profiles(base_path: Path) -> List[Path]:
        """
        Find all Chrome/Edge user profile directories.

        Args:
            base_path: Base path to User Data directory

        Returns:
            List of profile cache paths
        """
        profiles = []
        try:
            if not base_path.exists():
                return profiles

            # Always check Default profile
            default_cache = base_path / "Default" / "Cache"
            if default_cache.exists():
                profiles.append(default_cache)

            # Check for other profiles (Profile 1, Profile 2, etc.)
            user_data = base_path / "Default"
            parent = user_data.parent
            if parent.exists():
                for item in parent.iterdir():
                    if item.is_dir() and item.name.startswith("Profile "):
                        cache_path = item / "Cache"
                        if cache_path.exists():
                            profiles.append(cache_path)
        except (PermissionError, OSError):
            pass

        return profiles

    @staticmethod
    def get_temp_locations() -> List[str]:
        """
        Get Windows temporary file locations with accessibility checks.

        Returns:
            List of accessible temp directory paths as strings
        """
        locations = []

        # User temp directories
        temp_env = os.environ.get("TEMP", "")
        if temp_env and WindowsPlatform._is_accessible(Path(temp_env)):
            locations.append(temp_env)

        tmp_env = os.environ.get("TMP", "")
        if tmp_env and WindowsPlatform._is_accessible(Path(tmp_env)):
            locations.append(tmp_env)

        localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
        if localappdata.exists():
            local_temp = localappdata / "Temp"
            if WindowsPlatform._is_accessible(local_temp):
                locations.append(str(local_temp))

        # System temp directories
        windir = Path(os.environ.get("WINDIR", "C:\\Windows"))
        if windir.exists():
            system_temp = windir / "Temp"
            if WindowsPlatform._is_accessible(system_temp):
                locations.append(str(system_temp))

            prefetch = windir / "Prefetch"
            if WindowsPlatform._is_accessible(prefetch):
                locations.append(str(prefetch))

        # Windows Update cache
        software_dist = windir / "SoftwareDistribution" / "Download"
        if WindowsPlatform._is_accessible(software_dist):
            locations.append(str(software_dist))

        return locations

    @staticmethod
    def get_cache_locations() -> List[str]:
        """
        Get Windows cache locations with comprehensive browser and dev tool detection.

        Returns:
            List of accessible cache directory paths as strings
        """
        localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
        appdata = Path(os.environ.get("APPDATA", ""))
        programdata = Path(os.environ.get("PROGRAMDATA", ""))
        userprofile = Path(os.environ.get("USERPROFILE", ""))

        locations = []

        # ========== Browser Caches ==========
        if localappdata.exists():
            # Internet Explorer/Edge Legacy cache
            inet_cache = localappdata / "Microsoft" / "Windows" / "INetCache"
            if WindowsPlatform._is_accessible(inet_cache):
                locations.append(str(inet_cache))

            # ========== Chrome Caches (11 actual cache locations) ==========
            chrome_base = localappdata / "Google" / "Chrome" / "User Data"
            if chrome_base.exists():
                # Chrome main cache directories (use Path objects for proper path joining)
                chrome_cache_dirs = [
                    Path("Default") / "Cache",  # Main cache
                    Path("Default") / "Code Cache",  # Code cache
                    Path("Default") / "GPUCache",  # GPU cache
                    Path("Default") / "Service Worker" / "CacheStorage",  # Service worker cache
                    Path("Default") / "Application Cache" / "Cache",  # Application cache
                    Path("Default") / "IndexedDB",  # IndexedDB database
                    Path("Default") / "Local Storage" / "leveldb",  # Local storage
                    Path("Default") / "Session Storage",  # Session storage
                    Path("Default") / "GraphQL",  # GraphQL cache
                    Path("Default") / "Network" / "Persistent",  # Persistent network cache
                ]

                # Add Default profile caches
                for cache_dir in chrome_cache_dirs:
                    cache_path = chrome_base / cache_dir
                    if WindowsPlatform._is_accessible(cache_path):
                        locations.append(str(cache_path))

                # Add other Chrome profiles (Profile 1, Profile 2, etc.)
                try:
                    default_dir = chrome_base / "Default"
                    if default_dir.parent.exists():
                        for profile_dir in default_dir.parent.iterdir():
                            if profile_dir.is_dir() and profile_dir.name.startswith("Profile "):
                                # Check main cache for this profile
                                profile_cache = profile_dir / "Cache"
                                if WindowsPlatform._is_accessible(profile_cache):
                                    locations.append(str(profile_cache))

                                # Check code cache
                                code_cache = profile_dir / "Code Cache"
                                if WindowsPlatform._is_accessible(code_cache):
                                    locations.append(str(code_cache))
                except (PermissionError, OSError):
                    pass

            # ========== Edge Caches (same structure as Chrome) ==========
            edge_base = localappdata / "Microsoft" / "Edge" / "User Data"
            if edge_base.exists():
                # Edge main cache directories (use Path objects for proper path joining)
                edge_cache_dirs = [
                    Path("Default") / "Cache",
                    Path("Default") / "Code Cache",
                    Path("Default") / "GPUCache",
                    Path("Default") / "Service Worker" / "CacheStorage",
                    Path("Default") / "Application Cache" / "Cache",
                    Path("Default") / "IndexedDB",
                    Path("Default") / "Local Storage" / "leveldb",
                ]

                for cache_dir in edge_cache_dirs:
                    cache_path = edge_base / cache_dir
                    if WindowsPlatform._is_accessible(cache_path):
                        locations.append(str(cache_path))

                # Add other Edge profiles
                try:
                    default_dir = edge_base / "Default"
                    if default_dir.parent.exists():
                        for profile_dir in default_dir.parent.iterdir():
                            if profile_dir.is_dir() and profile_dir.name.startswith("Profile "):
                                profile_cache = profile_dir / "Cache"
                                if WindowsPlatform._is_accessible(profile_cache):
                                    locations.append(str(profile_cache))
                except (PermissionError, OSError):
                    pass

            # ========== Firefox Cache ==========
            if appdata.exists():
                firefox_base = appdata / "Mozilla" / "Firefox" / "Profiles"
                if firefox_base.exists():
                    try:
                        for profile_dir in firefox_base.iterdir():
                            if profile_dir.is_dir():
                                cache_dir = profile_dir / "cache2"
                                if WindowsPlatform._is_accessible(cache_dir):
                                    locations.append(str(cache_dir))
                    except (PermissionError, OSError):
                        pass

        # ========== JetBrains Caches (6.81 GB actual usage) ==========
        if localappdata.exists():
            # JetBrains IDE caches
            jetbrains_cache = localappdata / "JetBrains"
            if jetbrains_cache.exists():
                try:
                    for ide_dir in jetbrains_cache.iterdir():
                        if ide_dir.is_dir():
                            # Each IDE has its own cache directory
                            locations.append(str(ide_dir))
                except (PermissionError, OSError):
                    pass

        # ========== Development Tool Caches ==========
        if userprofile.exists():
            # npm cache
            npm_cache = userprofile / ".npm"  # Legacy
            npm_cache_new = userprofile / "AppData" / "Roaming" / "npm-cache"  # New location
            if WindowsPlatform._is_accessible(npm_cache):
                locations.append(str(npm_cache))
            if WindowsPlatform._is_accessible(npm_cache_new):
                locations.append(str(npm_cache_new))

            # yarn cache
            yarn_cache = userprofile / ".yarn" / "cache"
            if WindowsPlatform._is_accessible(yarn_cache):
                locations.append(str(yarn_cache))

            # yarn global cache
            yarn_global = userprofile / "AppData" / "Local" / "Yarn" / "cache"
            if WindowsPlatform._is_accessible(yarn_global):
                locations.append(str(yarn_global))

            # pnpm cache
            pnpm_store = userprofile / ".pnpm-store"
            if WindowsPlatform._is_accessible(pnpm_store):
                locations.append(str(pnpm_store))

            # pip cache
            pip_cache = userprofile / ".cache" / "pip"
            if WindowsPlatform._is_accessible(pip_cache):
                locations.append(str(pip_cache))

            # poetry cache
            poetry_cache = userprofile / ".cache" / "pypoetry"
            if WindowsPlatform._is_accessible(poetry_cache):
                locations.append(str(poetry_cache))

            # Gradle cache
            gradle_cache = userprofile / ".gradle" / "caches"
            if WindowsPlatform._is_accessible(gradle_cache):
                locations.append(str(gradle_cache))

            # Maven local repository
            maven_repo = userprofile / ".m2" / "repository"
            if WindowsPlatform._is_accessible(maven_repo):
                locations.append(str(maven_repo))

        # ========== Thumbnail Cache ==========
        if localappdata.exists():
            thumbnail_cache = localappdata / "Microsoft" / "Windows" / "Explorer"
            if WindowsPlatform._is_accessible(thumbnail_cache):
                locations.append(str(thumbnail_cache))

        return locations

    @staticmethod
    def get_log_locations() -> List[str]:
        """
        Get Windows log file locations with accessibility checks.

        Returns:
            List of accessible log directory paths as strings
        """
        locations = []

        localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
        if localappdata.exists():
            history = localappdata / "Microsoft" / "Windows" / "History"
            if WindowsPlatform._is_accessible(history):
                locations.append(str(history))

            webcache = localappdata / "Microsoft" / "Windows" / "WebCache"
            if WindowsPlatform._is_accessible(webcache):
                locations.append(str(webcache))

        programdata = Path(os.environ.get("PROGRAMDATA", ""))
        if programdata.exists():
            wer = programdata / "Microsoft" / "Windows" / "WER"
            if WindowsPlatform._is_accessible(wer):
                locations.append(str(wer))

        return locations

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
        """
        Get Docker cache locations on Windows with accessibility checks.

        Docker Desktop on Windows uses WSL2 backend.
        Returns:
            List of accessible Docker cache directory paths as strings
        """
        locations = []

        programdata = Path(os.environ.get("PROGRAMDATA", ""))
        if programdata.exists():
            docker_programdata = programdata / "Docker"
            if WindowsPlatform._is_accessible(docker_programdata):
                locations.append(str(docker_programdata))

        appdata = Path(os.environ.get("APPDATA", ""))
        if appdata.exists():
            docker_appdata = appdata / "Docker"
            if WindowsPlatform._is_accessible(docker_appdata):
                locations.append(str(docker_appdata))

        localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
        if localappdata.exists():
            docker_local = localappdata / "Docker"
            if WindowsPlatform._is_accessible(docker_local):
                locations.append(str(docker_local))

        return locations

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
