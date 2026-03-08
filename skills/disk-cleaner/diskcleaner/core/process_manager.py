"""
Process manager for handling locked files.

Provides cross-platform process detection and termination capabilities
with interactive user interface.
"""

import os
import platform
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

from diskcleaner.core.scanner import FileInfo


@dataclass
class ProcessInfo:
    """Information about a process."""

    pid: int
    name: str
    cmdline: Optional[str] = None
    username: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None

    def __str__(self) -> str:
        """Return string representation."""
        if self.cmdline:
            cmdline_short = self.cmdline[:50] + "..." if len(self.cmdline) > 50 else self.cmdline
            return "Process {} (PID: {}, CMD: {})".format(self.name, self.pid, cmdline_short)
        return "Process {} (PID: {})".format(self.name, self.pid)


class ProcessManager:
    """
    Cross-platform process manager for handling locked files.

    Features:
    - Detect processes locking files
    - Display detailed process information
    - Terminate processes with confirmation
    - Support for Windows, Linux, macOS
    """

    def __init__(self):
        """Initialize process manager."""
        self.platform = platform.system()

    def get_locking_processes(self, file_path: str) -> List[ProcessInfo]:
        """
        Get all processes that are locking a file.

        Args:
            file_path: Path to the file.

        Returns:
            List of ProcessInfo objects.
        """
        if self.platform == "Windows":
            return self._get_locking_processes_windows(file_path)
        elif self.platform in ["Linux", "Darwin"]:
            return self._get_locking_processes_unix(file_path)
        else:
            return []

    def _get_locking_processes_windows(self, file_path: str) -> List[ProcessInfo]:
        """
        Get processes locking a file on Windows.

        Uses handle.exe from Sysinternals or tasklist as fallback.

        Args:
            file_path: Path to the file.

        Returns:
            List of ProcessInfo objects.
        """
        processes = []

        # Try using handle.exe first (more reliable)
        try:
            result = subprocess.run(
                ["handle.exe", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse handle.exe output
            lines = result.stdout.split("\n")
            for line in lines:
                if file_path.lower() in line.lower():
                    # Extract PID and process name
                    # Typical format: "chrome.exe        pid: 12345   type: File"
                    parts = line.split()
                    if len(parts) >= 3 and "pid:" in parts[2]:
                        name = parts[0]
                        pid_str = parts[2].replace("pid:", "").strip()
                        try:
                            pid = int(pid_str)
                            processes.append(ProcessInfo(pid=pid, name=name))
                        except ValueError:
                            continue
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Fallback to tasklist/openfiles method
            try:
                # Use openfiles command (Windows 7+)
                result = subprocess.run(
                    ["openfiles", "/query", "/v", file_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                lines = result.stdout.split("\n")
                for line in lines:
                    if file_path.lower() in line.lower():
                        # Parse and extract PID
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.lower() == "pid:" and i + 1 < len(parts):
                                try:
                                    pid = int(parts[i + 1].rstrip(","))
                                    # Try to get process name
                                    name = self._get_process_name_windows(pid)
                                    processes.append(ProcessInfo(pid=pid, name=name))
                                except ValueError:
                                    continue
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                pass

        return processes

    def _get_locking_processes_unix(self, file_path: str) -> List[ProcessInfo]:
        """
        Get processes locking a file on Unix-like systems.

        Uses lsof command.

        Args:
            file_path: Path to the file.

        Returns:
            List of ProcessInfo objects.
        """
        processes = []

        try:
            result = subprocess.run(
                ["lsof", "-t", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # lsof -t returns list of PIDs
            pid_strings = result.stdout.strip().split("\n")
            for pid_str in pid_strings:
                if not pid_str:
                    continue
                try:
                    pid = int(pid_str)
                    # Get process details
                    proc_info = self._get_process_details_unix(pid)
                    if proc_info:
                        processes.append(proc_info)
                except ValueError:
                    continue

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return processes

    def _get_process_name_windows(self, pid: int) -> str:
        """Get process name on Windows."""
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Parse CSV output
            line = result.stdout.strip()
            if line and '","' in line:
                # Format: "chrome.exe","12345","Console","1","150,000 K"
                parts = line.split('","')
                if parts:
                    name = parts[0].strip('"')
                    return name

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return "Unknown"

    def _get_process_details_unix(self, pid: int) -> Optional[ProcessInfo]:
        """Get detailed process info on Unix."""
        try:
            # Get process name and command
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "comm,cmd,user,%cpu,rss"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            lines = result.stdout.strip().split("\n")
            if len(lines) < 2:
                return None

            # Skip header
            parts = lines[1].split(None, 4)
            if len(parts) < 5:
                return None

            name = parts[0]
            cmdline = parts[1] if len(parts) > 1 else None
            username = parts[2] if len(parts) > 2 else None

            try:
                cpu_percent = float(parts[3]) if len(parts) > 3 else None
            except ValueError:
                cpu_percent = None

            try:
                # RSS is in KB, convert to MB
                memory_kb = int(parts[4]) if len(parts) > 4 else 0
                memory_mb = memory_kb / 1024.0
            except ValueError:
                memory_mb = None

            return ProcessInfo(
                pid=pid,
                name=name,
                cmdline=cmdline,
                username=username,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
            )

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def terminate_process(self, process: ProcessInfo, timeout: int = 10) -> bool:
        """
        Terminate a process.

        Args:
            process: ProcessInfo object.
            timeout: Timeout in seconds.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.platform == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(process.pid)],
                    check=True,
                    timeout=timeout,
                    capture_output=True,
                )
            else:
                subprocess.run(
                    ["kill", "-9", str(process.pid)],
                    check=True,
                    timeout=timeout,
                    capture_output=True,
                )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def get_process_details(self, process: ProcessInfo) -> str:
        """
        Get detailed information about a process.

        Args:
            process: ProcessInfo object.

        Returns:
            Formatted string with process details.
        """
        lines = [
            "=" * 60,
            "进程详细信息",
            "=" * 60,
            "PID: {}".format(process.pid),
            "名称: {}".format(process.name),
        ]

        if process.username:
            lines.append("用户: {}".format(process.username))
        if process.cmdline:
            lines.append("命令: {}".format(process.cmdline))
        if process.cpu_percent is not None:
            lines.append("CPU: {:.1f}%".format(process.cpu_percent))
        if process.memory_mb is not None:
            lines.append("内存: {:.1f} MB".format(process.memory_mb))

        lines.append("=" * 60)

        return "\n".join(lines)

    def can_terminate_process(self, process: ProcessInfo) -> Tuple[bool, str]:
        """
        Check if a process can be terminated safely.

        Args:
            process: ProcessInfo object.

        Returns:
            Tuple of (can_terminate, reason).
        """
        # Check if process is critical system process
        critical_processes = {
            "windows": [
                "system",
                "smss.exe",
                "csrss.exe",
                "wininit.exe",
                "winlogon.exe",
                "services.exe",
                "lsass.exe",
                "svchost.exe",
            ],
            "linux": ["init", "kthreadd", "systemd", "ksoftirqd"],
            "darwin": ["launchd", "kernel_task"],
        }

        platform_key = self.platform.lower()
        if platform_key == "darwin":
            platform_key = "linux"

        if platform_key in critical_processes:
            name_lower = process.name.lower()
            for critical in critical_processes[platform_key]:
                if critical in name_lower or name_lower in critical:
                    return False, "关键系统进程，不应终止"

        # Check if we have permissions
        if process.username:
            import getpass

            current_user = getpass.getuser()
            if process.username != current_user and process.username != "root":
                # We're on Unix and don't own the process
                if self.platform != "Windows":
                    return False, "需要管理员权限终止此进程"

        return True, "可以终止"

    def check_and_handle_locked_files(
        self,
        files: List[FileInfo],
        auto_terminate: bool = False,
    ) -> Tuple[List[str], List[FileInfo]]:
        """
        Check for locked files and optionally terminate processes.

        Args:
            files: List of FileInfo objects to check.
            auto_terminate: If True, auto-terminate without asking.

        Returns:
            Tuple of (unlocked_file_paths, locked_file_list).
        """
        unlocked = []
        locked = []

        for file_info in files:
            try:
                # Try to open file exclusively
                fd = os.open(file_info.path, os.O_EXCL | os.O_RDWR)
                os.close(fd)
                unlocked.append(file_info.path)
            except OSError:
                # File is locked
                locking_processes = self.get_locking_processes(file_info.path)
                if locking_processes:
                    file_info.locking_processes = locking_processes  # type: ignore
                    locked.append(file_info)

                    if auto_terminate:
                        for process in locking_processes:
                            can_term, reason = self.can_terminate_process(process)
                            if can_term:
                                self.terminate_process(process)

        return unlocked, locked
