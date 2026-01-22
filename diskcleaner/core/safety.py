"""
Safety checker for file deletion operations.

Provides comprehensive safety checks including file lock detection,
permission verification, and process termination capabilities.
"""

import os
import platform
import shutil
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from diskcleaner.config import Config
from diskcleaner.core.scanner import FileInfo


class FileStatus(Enum):
    """Status of a file for deletion."""
    SAFE = "safe"
    LOCKED = "locked"
    NO_PERMISSION = "no_permission"
    PROTECTED = "protected"
    ERROR = "error"


class SafetyChecker:
    """
    Performs safety checks before file deletion.

    Features:
    - Protected path and extension checking
    - File lock detection (cross-platform)
    - Permission verification
    - Process termination (optional)
    - Backup creation (optional)
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize safety checker.

        Args:
            config: Configuration object.
        """
        self.config = config or Config.load()
        self.platform = platform.system()

        # Load settings
        self.check_locks = self.config.check_file_locks
        self.verify_perms = self.config.verify_permissions
        self.backup_enabled = self.config.get("safety.backup_before_delete", False)

        # Protected paths and extensions
        self.protected_paths = self.config.protected_paths
        self.protected_extensions = self.config.protected_extensions
        self.protected_patterns = self.config.protected_patterns

        # Backup directory
        self.backup_dir = Path.home() / ".disk-cleaner" / "backup"

    def verify_all(self, files: List[FileInfo]) -> List[Tuple[FileInfo, FileStatus]]:
        """
        Verify all files are safe to delete.

        Args:
            files: List of FileInfo objects.

        Returns:
            List of (FileInfo, FileStatus) tuples.
        """
        results = []

        for file in files:
            if file.is_dir:
                # Skip directories for now (handle separately)
                continue

            status = self.verify_file(file)
            results.append((file, status))

        return results

    def verify_file(self, file: FileInfo) -> FileStatus:
        """
        Verify if a single file is safe to delete.

        Args:
            file: FileInfo object.

        Returns:
            FileStatus indicating if file is safe to delete.
        """
        # Check protected paths
        if self._is_protected_path(file.path):
            return FileStatus.PROTECTED

        # Check protected extensions
        if self._is_protected_extension(file.name):
            return FileStatus.PROTECTED

        # Check protected patterns
        if self._is_protected_pattern(file.name):
            return FileStatus.PROTECTED

        # Check file locks
        if self.check_locks:
            if self._is_locked(file.path):
                return FileStatus.LOCKED

        # Check permissions
        if self.verify_perms:
            if not self._has_write_permission(file.path):
                return FileStatus.NO_PERMISSION

        return FileStatus.SAFE

    def _is_protected_path(self, path: str) -> bool:
        """
        Check if path is in protected list.

        Args:
            path: File path to check.

        Returns:
            True if path is protected.
        """
        # Normalize path
        path = os.path.normpath(path)

        for protected in self.protected_paths:
            protected = os.path.normpath(protected)
            if path.startswith(protected):
                return True

        return False

    def _is_protected_extension(self, filename: str) -> bool:
        """
        Check if file has protected extension.

        Args:
            filename: File name to check.

        Returns:
            True if extension is protected.
        """
        # Get extension (lowercase)
        ext = os.path.splitext(filename)[1].lower()

        return ext in self.protected_extensions

    def _is_protected_pattern(self, filename: str) -> bool:
        """
        Check if filename matches protected pattern.

        Args:
            filename: File name to check.

        Returns:
            True if pattern matches.
        """
        import fnmatch

        for pattern in self.protected_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def _is_locked(self, path: str) -> bool:
        """
        Check if file is locked by a process.

        Args:
            path: File path to check.

        Returns:
            True if file is locked.
        """
        if self.platform == "Windows":
            return self._is_locked_windows(path)
        elif self.platform in ["Linux", "Darwin"]:
            return self._is_locked_unix(path)

        return False

    def _is_locked_windows(self, path: str) -> bool:
        """
        Check if file is locked on Windows.

        Args:
            path: File path to check.

        Returns:
            True if file is locked.
        """
        try:
            # Try to open file with exclusive access
            # This will fail if another process has it open
            fd = os.open(path, os.O_EXCL | os.O_RDWR)
            os.close(fd)
            return False
        except (OSError, IOError):
            return True

    def _is_locked_unix(self, path: str) -> bool:
        """
        Check if file is locked on Unix/Linux/macOS.

        Uses lsof command to detect open files.

        Args:
            path: File path to check.

        Returns:
            True if file is locked.
        """
        try:
            # Use lsof to check if file is open
            result = subprocess.run(
                ["lsof", "-t", path],
                capture_output=True,
                timeout=5,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # lsof not available or timeout, assume not locked
            return False

    def _has_write_permission(self, path: str) -> bool:
        """
        Check if we have write permission for file.

        Args:
            path: File path to check.

        Returns:
            True if we have write permission.
        """
        return os.access(path, os.W_OK)

    def get_locking_process(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about process locking the file.

        Args:
            path: File path to check.

        Returns:
            Dictionary with process info, or None if not locked.
        """
        if self.platform == "Windows":
            return self._get_locking_process_windows(path)
        elif self.platform in ["Linux", "Darwin"]:
            return self._get_locking_process_unix(path)

        return None

    def _get_locking_process_windows(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get process info on Windows.

        Uses handle.exe from Sysinternals if available,
        otherwise returns limited info.

        Args:
            path: File path to check.

        Returns:
            Dictionary with process info, or None.
        """
        try:
            # Try using handle.exe (if installed)
            result = subprocess.run(
                ["handle", path],
                capture_output=True,
                timeout=10,
                text=True,
            )

            if result.returncode == 0:
                # Parse output to extract PID and process name
                # Output format: python.exe        pid: 12345   type: File
                for line in result.stdout.split("\n"):
                    if path.lower() in line.lower():
                        parts = line.split()
                        if len(parts) >= 4:
                            return {
                                "name": parts[0],
                                "pid": int(parts[2].rstrip(",")),
                                "type": parts[4],
                            }
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass

        # Fallback: return generic info
        return {
            "name": "unknown",
            "pid": -1,
            "type": "File",
        }

    def _get_locking_process_unix(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get process info on Unix/Linux/macOS.

        Args:
            path: File path to check.

        Returns:
            Dictionary with process info, or None.
        """
        try:
            # Get PID using lsof
            result = subprocess.run(
                ["lsof", "-t", path],
                capture_output=True,
                timeout=5,
                text=True,
            )

            if result.returncode == 0:
                pid = int(result.stdout.strip())

                # Get process name using ps
                cmd_result = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "comm="],
                    capture_output=True,
                    timeout=5,
                    text=True,
                )

                if cmd_result.returncode == 0:
                    return {
                        "name": cmd_result.stdout.strip(),
                        "pid": pid,
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass

        return None

    def terminate_process(self, pid: int) -> bool:
        """
        Terminate a process by PID.

        Args:
            pid: Process ID to terminate.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.platform == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    check=True,
                    timeout=10,
                    capture_output=True,
                )
            else:
                subprocess.run(
                    ["kill", "-9", str(pid)],
                    check=True,
                    timeout=10,
                    capture_output=True,
                )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def show_process_details(self, process: Dict[str, Any]) -> str:
        """
        Get detailed information about a process.

        Args:
            process: Process info dictionary.

        Returns:
            Formatted string with process details.
        """
        details = f"Process: {process['name']} (PID: {process['pid']})\n"

        try:
            if self.platform == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {process['pid']}", "/FO", "CSV"],
                    capture_output=True,
                    timeout=5,
                    text=True,
                )
                details += f"\n{result.stdout}"
            else:
                result = subprocess.run(
                    ["ps", "-p", str(process['pid']), "-o", "etime,%cpu,rss,cmd"],
                    capture_output=True,
                    timeout=5,
                    text=True,
                )
                details += f"\n{result.stdout}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return details

    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Create backup of a file before deletion.

        Args:
            file_path: Path to file to backup.

        Returns:
            Path to backup file, or None if failed.
        """
        if not self.backup_enabled:
            return None

        try:
            # Create backup directory for today
            today = datetime.now().strftime("%Y-%m-%d")
            backup_dir = self.backup_dir / today
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create backup filename
            original_name = Path(file_path).name
            backup_path = backup_dir / original_name

            # Handle duplicate names
            counter = 1
            while backup_path.exists():
                stem = Path(file_path).stem
                suffix = Path(file_path).suffix
                backup_path = backup_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            # Copy file
            shutil.copy2(file_path, backup_path)

            # Log backup
            self._log_backup(file_path, backup_path)

            return str(backup_path)

        except (OSError, IOError) as e:
            # Log error but don't fail
            return None

    def _log_backup(self, original: str, backup: str) -> None:
        """
        Log backup operation.

        Args:
            original: Original file path.
            backup: Backup file path.
        """
        log_dir = Path.home() / ".disk-cleaner" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "backup.log"

        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {original} -> {backup}\n"

        try:
            with open(str(log_file), "a", encoding="utf-8") as f:
                f.write(log_entry)
        except (OSError, IOError):
            pass
