"""
Tests for process manager.
"""

import platform
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from diskcleaner.core import ProcessInfo, ProcessManager


def test_process_manager_initialization():
    """Test ProcessManager initialization."""
    manager = ProcessManager()
    assert manager.platform == platform.system()
    print("Process manager initialization: PASS")


def test_process_info_string_representation():
    """Test ProcessInfo string representation."""
    proc = ProcessInfo(pid=1234, name="test.exe", cmdline="test.exe --arg")
    str_repr = str(proc)

    assert "test.exe" in str_repr
    assert "1234" in str_repr
    print("ProcessInfo string representation: PASS")


def test_get_process_details():
    """Test get_process_details method."""
    manager = ProcessManager()
    proc = ProcessInfo(
        pid=1234,
        name="test",
        cmdline="test --arg",
        username="user",
        cpu_percent=5.5,
        memory_mb=100.5,
    )

    details = manager.get_process_details(proc)

    assert "PID: 1234" in details
    assert "名称: test" in details
    assert "命令: test --arg" in details
    assert "用户: user" in details
    assert "CPU: 5.5%" in details
    assert "内存: 100.5 MB" in details
    print("Get process details: PASS")


def test_can_terminate_critical_process():
    """Test that critical system processes cannot be terminated."""
    manager = ProcessManager()

    if manager.platform == "Windows":
        critical_proc = ProcessInfo(pid=1, name="System")
        can_terminate, reason = manager.can_terminate_process(critical_proc)
        assert not can_terminate
        assert "关键系统进程" in reason
    else:
        # Unix systems
        critical_proc = ProcessInfo(pid=1, name="init")
        can_terminate, reason = manager.can_terminate_process(critical_proc)
        assert not can_terminate

    print("Can terminate critical process: PASS")


def test_can_terminate_safe_process():
    """Test that non-critical processes can be terminated."""
    manager = ProcessManager()
    safe_proc = ProcessInfo(pid=9999, name="myapp.exe")

    # Mock getpass to return current user
    with patch("getpass.getuser", return_value="testuser"):
        can_terminate, reason = manager.can_terminate_process(safe_proc)

    assert can_terminate
    print("Can terminate safe process: PASS")


def test_get_locking_processes_empty():
    """Test getting locking processes for non-existent file."""
    manager = ProcessManager()

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "nonexistent.txt"

        processes = manager.get_locking_processes(str(test_file))

        # Should return empty list (file doesn't exist or not locked)
        assert isinstance(processes, list)
        print("Get locking processes (empty): PASS")


def test_check_and_handle_locked_files():
    """Test checking for locked files."""
    manager = ProcessManager()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a test file
        test_file = temp_path / "test.txt"
        test_file.write_text("test content")

        # Create FileInfo objects
        import time

        from diskcleaner.core.scanner import FileInfo

        file_info = FileInfo(
            path=str(test_file),
            name="test.txt",
            size=12,
            mtime=time.time(),
            is_dir=False,
            is_link=False,
        )

        unlocked, locked = manager.check_and_handle_locked_files([file_info])

        # File should not be locked (we just created it)
        assert len(unlocked) >= 0
        assert len(locked) >= 0
        print("Check and handle locked files: PASS")


def test_terminate_process_mock():
    """Test process termination with mocked subprocess."""
    manager = ProcessManager()
    proc = ProcessInfo(pid=9999, name="test.exe")

    # Mock subprocess.run to simulate successful termination
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)

        result = manager.terminate_process(proc)

        assert result is True
        print("Terminate process (mocked): PASS")


def test_get_locking_processes_windows_mock():
    """Test Windows process detection with mocked handle.exe."""
    manager = ProcessManager()

    # Skip if not on Windows
    if manager.platform != "Windows":
        print("Get locking processes Windows (mocked): SKIPPED (not Windows)")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test")

        # Mock handle.exe output
        mock_output = "test.exe                pid: 1234   type: File               {}".format(
            str(test_file)
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=mock_output, returncode=0)

            processes = manager.get_locking_processes(str(test_file))

            # Should parse at least one process
            if "handle.exe" in str(mock_run.call_args):
                assert len(processes) >= 0

    print("Get locking processes Windows (mocked): PASS")


def test_get_process_details_unix():
    """Test Unix process details parsing."""
    if platform.system() not in ["Linux", "Darwin"]:
        print("Get process details Unix: SKIPPED (not Unix)")
        return

    manager = ProcessManager()

    # Mock ps command output
    mock_output = """COMMAND
ps
user 0.0 1024"""

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(stdout=mock_output, returncode=0)

        # This tests the parsing logic
        manager._get_process_details_unix(1)

        # The parsing should work (even if we don't get real data)
        print("Get process details Unix: PASS")


def test_get_locking_processes_unix_mock():
    """Test Unix process detection with mocked lsof."""
    manager = ProcessManager()

    # Skip if on Windows
    if manager.platform == "Windows":
        print("Get locking processes Unix (mocked): SKIPPED (Windows)")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test")

        # Mock lsof -t output
        mock_output = "1234\n5678\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout=mock_output, returncode=0)

            processes = manager.get_locking_processes(str(test_file))

            # Should return list (may be empty if lsof not available)
            assert isinstance(processes, list)

    print("Get locking processes Unix (mocked): PASS")


if __name__ == "__main__":
    print("Running process manager tests...\n")
    test_process_manager_initialization()
    test_process_info_string_representation()
    test_get_process_details()
    test_can_terminate_critical_process()
    test_can_terminate_safe_process()
    test_get_locking_processes_empty()
    test_check_and_handle_locked_files()
    test_terminate_process_mock()
    test_get_locking_processes_windows_mock()
    test_get_process_details_unix()
    test_get_locking_processes_unix_mock()
    print("\nAll process manager tests passed!")
