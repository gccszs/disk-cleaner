"""
Directory scanner with incremental scanning support.

Scans directories to collect file information with support for
incremental updates using cached metadata.
"""

import os
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Optional, Set

from diskcleaner.core.cache import CacheManager, FileSnapshot, ScanSnapshot
from diskcleaner.config import Config


@dataclass
class FileInfo:
    """Information about a single file."""

    path: str
    name: str
    size: int
    mtime: float
    is_dir: bool
    is_link: bool
    inode: Optional[int] = None
    depth: int = 0

    def to_snapshot(self) -> FileSnapshot:
        """Convert to FileSnapshot for caching."""
        return FileSnapshot(
            path=self.path,
            size=self.size,
            mtime=self.mtime,
            inode=self.inode,
        )


class DirectoryScanner:
    """
    Directory scanner with incremental scanning support.

    Features:
    - Incremental scanning using cache
    - Parallel scanning capability (optional)
    - Configurable depth limits
    - Symbolic link handling
    """

    def __init__(
        self,
        target_path: str,
        config: Optional[Config] = None,
        cache_enabled: bool = True,
    ):
        """
        Initialize scanner.

        Args:
            target_path: Path to scan.
            config: Configuration object.
            cache_enabled: Enable incremental scanning with cache.
        """
        self.target_path = Path(target_path).expanduser().resolve()
        self.config = config or Config()
        self.cache_enabled = cache_enabled

        # Initialize cache manager
        self.cache_manager = CacheManager(
            cache_dir=self.config.cache_dir
        ) if cache_enabled else None

        # Scan settings
        self.follow_symlinks = self.config.get("scan.follow_symlinks", False)
        self.max_depth = self.config.get("scan.max_depth", None)
        self.parallel_jobs = self.config.get("scan.parallel_jobs", 4)

    def scan(self) -> List[FileInfo]:
        """
        Perform a full directory scan.

        Returns:
            List of FileInfo objects.
        """
        files = []

        for file_info in self.scan_generator():
            files.append(file_info)

        return files

    def scan_incremental(self) -> tuple[List[FileInfo], List[str], List[str]]:
        """
        Perform incremental scan using cache.

        Returns:
            Tuple of (all_files, new_files, changed_files):
            - all_files: All files in directory (including unchanged)
            - new_files: Files added since last scan
            - changed_files: Files modified since last scan

        """
        start_time = time.time()

        # Try to load cached scan
        cached_snapshot = None
        if self.cache_enabled and self.cache_manager:
            cached_snapshot = self.cache_manager.get_scan_cache(
                str(self.target_path),
                max_age_days=self.config.cache_ttl,
            )

        # If no cache, do full scan
        if cached_snapshot is None:
            files = self.scan()
            elapsed = time.time() - start_time

            # Save to cache
            if self.cache_enabled and self.cache_manager:
                snapshot = ScanSnapshot(
                    path=str(self.target_path),
                    timestamp=time.time(),
                    files=[f.to_snapshot() for f in files],
                    total_size=sum(f.size for f in files),
                    file_count=len(files),
                )
                self.cache_manager.save_scan_cache(str(self.target_path), snapshot)

            return files, files, []  # All files are "new"

        # Incremental scan: compare with cache
        cached_files = {f.path: f for f in cached_snapshot.files}
        current_files = []
        new_files = []
        changed_files = []

        for file_info in self.scan_generator():
            current_files.append(file_info)

            cached = cached_files.get(file_info.path)

            if cached is None:
                # New file
                new_files.append(file_info.path)
            elif self.cache_manager.is_file_changed(
                file_info.to_snapshot(),
                cached
            ):
                # Changed file
                changed_files.append(file_info.path)

        # Detect deleted files
        deleted_files = []
        current_paths = {f.path for f in current_files}
        for cached_path in cached_files:
            if cached_path not in current_paths:
                deleted_files.append(cached_path)

        # Update cache
        elapsed = time.time() - start_time
        if self.cache_enabled and self.cache_manager:
            snapshot = ScanSnapshot(
                path=str(self.target_path),
                timestamp=time.time(),
                files=[f.to_snapshot() for f in current_files],
                total_size=sum(f.size for f in current_files),
                file_count=len(current_files),
            )
            self.cache_manager.save_scan_cache(str(self.target_path), snapshot)

        return current_files, new_files, changed_files

    def scan_generator(self) -> Generator[FileInfo, None, None]:
        """
        Scan directory and yield FileInfo objects.

        This is a generator that yields files as they are scanned,
        which is more memory-efficient for large directories.

        Yields:
            FileInfo objects.
        """
        if not self.target_path.exists():
            raise FileNotFoundError(f"Path not found: {self.target_path}")

        if not self.target_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.target_path}")

        # Start scanning from root
        yield from self._scan_directory(self.target_path, depth=0)

    def _scan_directory(
        self,
        directory: Path,
        depth: int,
        visited: Optional[Set[int]] = None,
    ) -> Generator[FileInfo, None, None]:
        """
        Scan a single directory recursively.

        Args:
            directory: Directory to scan.
            depth: Current depth.
            visited: Set of visited inodes to prevent cycles.

        Yields:
            FileInfo objects.
        """
        if visited is None:
            visited = set()

        # Check depth limit
        if self.max_depth is not None and depth > self.max_depth:
            return

        try:
            entries = directory.iterdir()
        except PermissionError:
            # Skip directories we can't read
            return

        for entry in entries:
            try:
                stat_info = entry.lstat()

                # Get inode for cycle detection (Unix only)
                inode = None
                if hasattr(stat_info, "st_ino"):
                    inode = stat_info.st_ino

                # Check for symlink cycles
                is_link = entry.is_symlink()
                if is_link:
                    if not self.follow_symlinks:
                        continue

                    # Check if we've visited this inode
                    if inode is not None and inode in visited:
                        continue
                    visited.add(inode)

                is_dir = entry.is_dir()

                # Create FileInfo
                file_info = FileInfo(
                    path=str(entry),
                    name=entry.name,
                    size=stat_info.st_size if not is_dir else 0,
                    mtime=stat_info.st_mtime,
                    is_dir=is_dir,
                    is_link=is_link,
                    inode=inode,
                    depth=depth,
                )

                yield file_info

                # Recurse into subdirectories
                if is_dir and not is_link:
                    yield from self._scan_directory(entry, depth + 1, visited)

            except (PermissionError, OSError) as e:
                # Skip files we can't access
                continue

    def get_directory_size(self, path: Optional[str] = None) -> int:
        """
        Calculate total size of a directory.

        Args:
            path: Path to calculate. If None, uses target_path.

        Returns:
            Total size in bytes.
        """
        target = Path(path) if path else self.target_path

        if not target.exists():
            return 0

        if target.is_file():
            return target.stat().st_size

        total_size = 0
        for file_info in self.scan_generator():
            if not file_info.is_dir:
                total_size += file_info.size

        return total_size

    def get_file_count(self, path: Optional[str] = None) -> int:
        """
        Count total files in a directory.

        Args:
            path: Path to count. If None, uses target_path.

        Returns:
            Number of files.
        """
        target = Path(path) if path else self.target_path

        if not target.exists():
            return 0

        if target.is_file():
            return 1

        count = 0
        for file_info in self.scan_generator():
            if not file_info.is_dir:
                count += 1

        return count

    def find_large_files(
        self,
        min_size_mb: float = 10.0,
        limit: int = 20,
    ) -> List[FileInfo]:
        """
        Find large files in directory.

        Args:
            min_size_mb: Minimum file size in MB.
            limit: Maximum number of files to return.

        Returns:
            List of large files, sorted by size (descending).
        """
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        large_files = []

        for file_info in self.scan_generator():
            if not file_info.is_dir and file_info.size >= min_size_bytes:
                large_files.append(file_info)

        # Sort by size (descending)
        large_files.sort(key=lambda f: f.size, reverse=True)

        return large_files[:limit]
