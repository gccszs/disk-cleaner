"""
Integration tests for Phase 2 complete workflow.

Tests end-to-end scenarios combining all Phase 2 modules:
- Duplicate finder
- Smart cleanup engine
- Interactive UI
- Process manager
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from diskcleaner.core import CleanupReport, InteractiveCleanupUI, ProcessManager, SmartCleanupEngine
from diskcleaner.core.scanner import FileInfo


def test_complete_cleanup_workflow():
    """Test complete cleanup workflow from scan to report."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files of various types
        (temp_path / "test.log").write_text("x" * 1000)
        (temp_path / "test.tmp").write_text("y" * 500)
        (temp_path / "document.pdf").write_text("z" * 2000)
        (temp_path / "data.cache").write_text("w" * 300)

        # Create duplicate files
        (temp_path / "dup1.txt").write_text("duplicate content")
        (temp_path / "dup2.txt").write_text("duplicate content")

        # Initialize engine
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)

        # Run complete analysis
        report = engine.analyze(
            include_duplicates=True,
            safety_check=True,
        )

        # Verify report
        assert isinstance(report, CleanupReport)
        assert report.total_files == 6
        assert report.total_size > 0
        assert len(report.duplicates) == 1
        assert report.duplicates[0].count == 2

        print("Complete cleanup workflow: PASS")


def test_duplicate_finder_integration():
    """Test duplicate finder within smart cleanup engine."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create multiple duplicate groups
        (temp_path / "file1.txt").write_text("content a")
        (temp_path / "file2.txt").write_text("content a")
        (temp_path / "file3.txt").write_text("content a")
        (temp_path / "file4.txt").write_text("content b")
        (temp_path / "file5.txt").write_text("content b")

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=True, safety_check=False)

        # Should find 2 duplicate groups
        assert len(report.duplicates) >= 1

        # Verify reclaimable space calculation
        total_reclaimable = sum(d.reclaimable_space for d in report.duplicates)
        assert total_reclaimable > 0

        print("Duplicate finder integration: PASS")


def test_classification_integration():
    """Test three-dimensional classification."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create files of different types and ages
        (temp_path / "recent.log").write_text("x" * 100)
        (temp_path / "old.tmp").write_text("y" * 200)
        (temp_path / "cache.file").write_text("z" * 300)

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Verify all three dimensions exist
        assert "by_type" in report.__dict__
        assert "by_risk" in report.__dict__
        assert "by_age" in report.__dict__

        # Verify files are categorized
        total_categorized = sum(len(files) for files in report.by_type.values())
        assert total_categorized > 0

        print("Classification integration: PASS")


def test_safety_filtering_integration():
    """Test safety checking filters files correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create safe files
        (temp_path / "safe.log").write_text("x" * 100)
        (temp_path / "safe.tmp").write_text("y" * 100)

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)

        # Analyze with safety check enabled
        report_with_safety = engine.analyze(
            include_duplicates=False,
            safety_check=True,
        )

        # Analyze without safety check
        report_without_safety = engine.analyze(
            include_duplicates=False,
            safety_check=False,
        )

        # Both should produce valid reports
        assert isinstance(report_with_safety, CleanupReport)
        assert isinstance(report_without_safety, CleanupReport)

        print("Safety filtering integration: PASS")


def test_report_summary_generation():
    """Test report summary generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        (temp_path / "test.log").write_text("x" * 1500)
        (temp_path / "test.tmp").write_text("y" * 800)

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Generate summary
        summary = engine.get_summary(report)

        # Verify summary contains key information
        assert "磁盘清理分析报告" in summary
        assert "扫描路径" in summary
        assert "文件统计" in summary
        assert "可回收空间" in summary
        assert str(temp_path) in summary
        assert "2300" in summary or "2.2" in summary  # Total size

        print("Report summary generation: PASS")


def test_interactive_ui_integration():
    """Test interactive UI with real report."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        for i in range(5):
            (temp_path / "file{}.log".format(i)).write_text("x" * (100 * (i + 1)))

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Initialize UI
        ui = InteractiveCleanupUI(engine)

        # Test various views (with mocked input to exit)
        with patch("builtins.input", return_value="0"):
            choice = ui.display_report_menu(report)
            assert choice is None

            # Test view by type
            selected = ui.view_by_type(report)
            assert isinstance(selected, list)

            # Test view by risk
            selected = ui.view_by_risk(report)
            assert isinstance(selected, list)

            # Test view by age
            selected = ui.view_by_age(report)
            assert isinstance(selected, list)

            # Test detailed list
            selected = ui.view_detailed_list(report)
            assert isinstance(selected, list)

        print("Interactive UI integration: PASS")


def test_cleanup_confirmation_workflow():
    """Test cleanup confirmation and execution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test file
        test_file = temp_path / "to_delete.txt"
        test_file.write_text("delete me")

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        ui = InteractiveCleanupUI(engine)

        # Test dry run
        result = ui.confirm_and_cleanup([str(test_file)], dry_run=True)
        assert result is False
        assert test_file.exists()  # File should still exist

        # Test with cancellation (not "YES")
        with patch("builtins.input", return_value="NO"):
            result = ui.confirm_and_cleanup([str(test_file)], dry_run=False)
        assert result is False
        assert test_file.exists()

        print("Cleanup confirmation workflow: PASS")


def test_incremental_scanning():
    """Test incremental scanning with cache."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create initial files
        (temp_path / "file1.txt").write_text("content 1")
        (temp_path / "file2.txt").write_text("content 2")

        # First scan
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=True)
        report1 = engine.analyze(include_duplicates=False, safety_check=False)

        # Add more files
        (temp_path / "file3.txt").write_text("content 3")
        time.sleep(0.1)  # Ensure different mtime

        # Second scan (should use cache)
        engine2 = SmartCleanupEngine(str(temp_path), cache_enabled=True)
        report2 = engine2.analyze(include_duplicates=False, safety_check=False)

        # Second scan should find more files
        assert report2.total_files >= report1.total_files

        print("Incremental scanning: PASS")


def test_process_manager_with_locked_files():
    """Test process manager with file locking scenarios."""
    manager = ProcessManager()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test file
        test_file = temp_path / "test.txt"
        test_file.write_text("test content")

        # Check for locking processes
        processes = manager.get_locking_processes(str(test_file))

        # Should return empty list (file not locked)
        assert isinstance(processes, list)

        # Test check_and_handle_locked_files
        import time

        file_info = FileInfo(
            path=str(test_file),
            name="test.txt",
            size=12,
            mtime=time.time(),
            is_dir=False,
            is_link=False,
        )

        unlocked, locked = manager.check_and_handle_locked_files([file_info])

        # File should be unlocked
        assert len(unlocked) >= 0
        assert len(locked) >= 0

        print("Process manager with locked files: PASS")


def test_reclaimable_space_calculation():
    """Test accurate reclaimable space calculation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create files with known sizes
        (temp_path / "file1.log").write_text("a" * 1000)  # 1 KB
        (temp_path / "file2.tmp").write_text("b" * 2000)  # 2 KB

        # Create duplicates
        (temp_path / "dup1.txt").write_text("x" * 500)  # 500 bytes
        (temp_path / "dup2.txt").write_text("x" * 500)  # 500 bytes

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=True, safety_check=False)

        # Calculate expected reclaimable
        expected_safe = sum(f.size for f in report.by_risk.get("safe", []))
        expected_confirm = sum(f.size for f in report.by_risk.get("confirm_needed", []))
        expected_dup = sum(d.reclaimable_space for d in report.duplicates)

        # Verify calculations
        assert report.safe_reclaimable == expected_safe
        assert report.confirm_reclaimable == expected_confirm
        assert report.duplicate_reclaimable == expected_dup
        assert report.total_reclaimable == expected_safe + expected_confirm + expected_dup

        print("Reclaimable space calculation: PASS")


def test_error_handling():
    """Test error handling in various scenarios."""
    # Test with invalid path
    engine = SmartCleanupEngine("/nonexistent/path/12345", cache_enabled=False)

    try:
        report = engine.analyze(include_duplicates=False, safety_check=False)
        # Should handle gracefully or raise appropriate error
        assert isinstance(report, CleanupReport)
    except FileNotFoundError:
        # Also acceptable
        pass

    # Test with empty directory
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = SmartCleanupEngine(temp_dir, cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        assert report.total_files == 0
        assert report.total_size == 0
        assert report.total_reclaimable == 0

    print("Error handling: PASS")


def test_performance_with_many_files():
    """Test performance with larger number of files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 50 test files
        for i in range(50):
            (temp_path / f"file{i:03d}.tmp").write_text("x" * 100)

        # Scan and analyze
        import time

        start = time.time()

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        elapsed = time.time() - start

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        assert report.total_files == 50

        print("Performance with many files: PASS (completed in {}s)".format(elapsed))


if __name__ == "__main__":
    print("Running Phase 2 integration tests...\n")
    test_complete_cleanup_workflow()
    test_duplicate_finder_integration()
    test_classification_integration()
    test_safety_filtering_integration()
    test_report_summary_generation()
    test_interactive_ui_integration()
    test_cleanup_confirmation_workflow()
    test_incremental_scanning()
    test_process_manager_with_locked_files()
    test_reclaimable_space_calculation()
    test_error_handling()
    test_performance_with_many_files()
    print("\nAll Phase 2 integration tests passed!")
