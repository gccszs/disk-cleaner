"""
Cache management for incremental scanning.

This module provides caching functionality to speed up repeated scans
by storing file metadata and detecting changes.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class FileSnapshot:
    """Snapshot of a single file's metadata."""

    path: str
    size: int
    mtime: float
    inode: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "FileSnapshot":
        """Create from dictionary."""
        return cls(**data)

    def __hash__(self) -> int:
        """Make FileSnapshot hashable for caching."""
        return hash((self.path, self.size, self.mtime, self.inode))


@dataclass
class ScanSnapshot:
    """Snapshot of an entire directory scan."""

    path: str
    timestamp: float
    files: List[FileSnapshot] = field(default_factory=list)
    total_size: int = 0
    file_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": self.path,
            "timestamp": self.timestamp,
            "files": [f.to_dict() for f in self.files],
            "total_size": self.total_size,
            "file_count": self.file_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ScanSnapshot":
        """Create from dictionary."""
        return cls(
            path=data["path"],
            timestamp=data["timestamp"],
            files=[FileSnapshot.from_dict(f) for f in data.get("files", [])],
            total_size=data.get("total_size", 0),
            file_count=data.get("file_count", 0),
        )


class CacheManager:
    """Manages scan cache for incremental scanning."""

    def __init__(self, cache_dir: str = "~/.disk-cleaner/cache"):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files. Supports ~ expansion.
        """
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, scan_path: str) -> Path:
        """
        Get cache file path for a given scan path.

        Args:
            scan_path: The path that was scanned.

        Returns:
            Path to cache file.
        """
        # Use MD5 hash of path as cache filename
        path_hash = hashlib.md5(str(scan_path).encode()).hexdigest()
        return self.cache_dir / f"{path_hash}.json"

    def get_scan_cache(self, path: str, max_age_days: int = 7) -> Optional[ScanSnapshot]:
        """
        Retrieve cached scan results.

        Args:
            path: The path to look up in cache.
            max_age_days: Maximum age of cache in days (default: 7).

        Returns:
            ScanSnapshot if cache exists and is valid, None otherwise.
        """
        cache_file = self._get_cache_path(path)

        # Check if cache exists
        if not cache_file.exists():
            return None

        # Check if cache has expired
        cache_age = time.time() - cache_file.stat().st_mtime
        max_age_seconds = max_age_days * 24 * 3600
        if cache_age > max_age_seconds:
            # Cache expired, delete it
            cache_file.unlink()
            return None

        # Load and return cache
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ScanSnapshot.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache, delete it
            cache_file.unlink()
            return None

    def save_scan_cache(self, path: str, snapshot: ScanSnapshot) -> None:
        """
        Save scan results to cache.

        Args:
            path: The path that was scanned.
            snapshot: The scan snapshot to cache.
        """
        cache_file = self._get_cache_path(path)

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, indent=2)
        except (OSError, IOError):
            # Silently fail if we can't write cache
            # This shouldn't break the scan, just disable caching
            pass

    def is_file_changed(self, current: FileSnapshot, cached: FileSnapshot) -> bool:
        """
        Check if a file has changed since last scan.

        Args:
            current: Current file snapshot.
            cached: Cached file snapshot.

        Returns:
            True if file has changed, False otherwise.
        """
        # Check size first (fastest)
        if current.size != cached.size:
            return True

        # Check modification time
        if current.mtime != cached.mtime:
            return True

        # Check inode if available (Unix systems)
        if current.inode is not None and cached.inode is not None:
            if current.inode != cached.inode:
                return True

        return False

    def clear_cache(self, path: Optional[str] = None) -> None:
        """
        Clear cache.

        Args:
            path: If specified, only clear cache for this path.
                  If None, clear all cache.
        """
        if path is not None:
            cache_file = self._get_cache_path(path)
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats (total_files, total_size_mb).
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "total_files": len(cache_files),
            "total_size_mb": int(round(total_size / (1024 * 1024), 2)),
        }
