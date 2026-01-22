"""
Tests for interactive cleanup UI.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from diskcleaner.core import InteractiveCleanupUI, SmartCleanupEngine


def test_interactive_ui_initialization():
    """Test UI initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = SmartCleanupEngine(temp_dir, cache_enabled=False)
        ui = InteractiveCleanupUI(engine)

        assert ui.engine is engine
        assert len(ui.selected_files) == 0
        print("UI initialization: PASS")


def test_view_by_type():
    """Test view by type functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "test.log").write_text("x" * 100)
        (temp_path / "test.tmp").write_text("y" * 100)

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)
        ui = InteractiveCleanupUI(engine)

        # Mock user input to exit immediately
        with patch("builtins.input", return_value="0"):
            selected = ui.view_by_type(report)

        assert isinstance(selected, list)
        print("View by type: PASS")


def test_view_by_risk():
    """Test view by risk functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        (temp_path / "test.log").write_text("x" * 100)

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)
        ui = InteractiveCleanupUI(engine)

        # Mock user input to exit immediately
        with patch("builtins.input", return_value="0"):
            selected = ui.view_by_risk(report)

        assert isinstance(selected, list)
        print("View by risk: PASS")


def test_view_by_age():
    """Test view by age functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        (temp_path / "old.txt").write_text("old content")

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)
        ui = InteractiveCleanupUI(engine)

        # Mock user input to exit immediately
        with patch("builtins.input", return_value="0"):
            selected = ui.view_by_age(report)

        assert isinstance(selected, list)
        print("View by age: PASS")


def test_view_duplicates():
    """Test view duplicates functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create duplicate files
        (temp_path / "file1.txt").write_text("same content")
        (temp_path / "file2.txt").write_text("same content")

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=True, safety_check=False)
        ui = InteractiveCleanupUI(engine)

        # Mock user input to exit immediately
        with patch("builtins.input", return_value="0"):
            selected = ui.view_duplicates(report)

        assert isinstance(selected, list)
        print("View duplicates: PASS")


def test_view_detailed_list():
    """Test detailed list view functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        for i in range(5):
            (temp_path / f"file{i}.txt").write_text(f"content {i}")

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)
        ui = InteractiveCleanupUI(engine)

        # Mock user input to exit immediately
        with patch("builtins.input", return_value="0"):
            selected = ui.view_detailed_list(report)

        assert isinstance(selected, list)
        print("View detailed list: PASS")


def test_confirm_and_cleanup_dry_run():
    """Test cleanup confirmation in dry run mode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test file
        test_file = temp_path / "test.txt"
        test_file.write_text("test content")

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        ui = InteractiveCleanupUI(engine)

        # Test dry run mode
        result = ui.confirm_and_cleanup([str(test_file)], dry_run=True)

        assert result is False  # Dry run should return False
        assert test_file.exists()  # File should still exist
        print("Dry run cleanup: PASS")


def test_confirm_and_cleanup_cancelled():
    """Test cleanup when user cancels."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test file
        test_file = temp_path / "test.txt"
        test_file.write_text("test content")

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        ui = InteractiveCleanupUI(engine)

        # Mock user input to cancel (not "YES")
        with patch("builtins.input", return_value="NO"):
            result = ui.confirm_and_cleanup([str(test_file)], dry_run=False)

        assert result is False  # Cancelled should return False
        assert test_file.exists()  # File should still exist
        print("Cancelled cleanup: PASS")


def test_format_size():
    """Test size formatting."""
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = SmartCleanupEngine(temp_dir, cache_enabled=False)
        ui = InteractiveCleanupUI(engine)

        assert "B" in ui._format_size(100)
        assert "KB" in ui._format_size(1024)
        assert "MB" in ui._format_size(1024 * 1024)
        assert "GB" in ui._format_size(1024 * 1024 * 1024)
        print("Format size: PASS")


def test_calculate_average_age():
    """Test average age calculation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "file1.txt").write_text("test")

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)
        ui = InteractiveCleanupUI(engine)

        # Get files from report
        files = list(report.by_type.values())[0] if report.by_type else []

        if files:
            avg_age = ui._calculate_average_age(files)
            assert avg_age >= 0
            print("Calculate average age: PASS")
        else:
            print("Calculate average age: SKIPPED (no files)")


def test_display_report_menu():
    """Test report menu display."""
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = SmartCleanupEngine(temp_dir, cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)
        ui = InteractiveCleanupUI(engine)

        # Mock user input to exit
        with patch("builtins.input", return_value="0"):
            choice = ui.display_report_menu(report)

        assert choice is None  # Should return None on exit
        print("Display report menu: PASS")


if __name__ == "__main__":
    print("Running interactive UI tests...\n")
    test_interactive_ui_initialization()
    test_view_by_type()
    test_view_by_risk()
    test_view_by_age()
    test_view_duplicates()
    test_view_detailed_list()
    test_confirm_and_cleanup_dry_run()
    test_confirm_and_cleanup_cancelled()
    test_format_size()
    test_calculate_average_age()
    test_display_report_menu()
    print("\nAll interactive UI tests passed!")
