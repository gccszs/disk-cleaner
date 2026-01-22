"""
Tests for smart cleanup engine.
"""

import tempfile
from pathlib import Path

from diskcleaner.core import CleanupReport, SmartCleanupEngine


def test_smart_cleanup_basic_analysis():
    """Test basic cleanup analysis functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files of different types
        (temp_path / "test.log").write_text("x" * 1000)
        (temp_path / "test.tmp").write_text("y" * 500)
        (temp_path / "document.pdf").write_text("z" * 2000)

        # Run analysis
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Verify report structure
        assert isinstance(report, CleanupReport)
        assert report.total_files == 3
        assert report.total_size == 3500
        assert report.scan_time >= 0
        print("Basic analysis: PASS")


def test_smart_cleanup_with_duplicates():
    """Test cleanup analysis with duplicate detection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create duplicate files
        (temp_path / "file1.txt").write_text("duplicate content")
        (temp_path / "file2.txt").write_text("duplicate content")
        (temp_path / "unique.txt").write_text("unique content")

        # Run analysis with duplicates
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=True, safety_check=False)

        # Should find one duplicate group
        assert len(report.duplicates) == 1
        assert report.duplicates[0].count == 2
        assert report.duplicate_reclaimable > 0
        print("With duplicates: PASS")


def test_smart_cleanup_with_safety_check():
    """Test cleanup analysis with safety checks enabled."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "safe.log").write_text("x" * 100)
        (temp_path / "safe.tmp").write_text("y" * 200)

        # Run analysis with safety check
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=True)

        # All files should be marked as safe or confirm_needed
        total_checked = sum(len(files) for files in report.by_risk.values())
        assert total_checked <= report.total_files
        print("With safety check: PASS")


def test_smart_cleanup_classification():
    """Test that files are properly classified."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create different file types
        (temp_path / "test.log").write_text("x" * 100)
        (temp_path / "test.tmp").write_text("y" * 100)
        (temp_path / "doc.pdf").write_text("z" * 100)

        # Run analysis
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Check classification by type exists
        assert "by_type" in report.__dict__
        assert "by_risk" in report.__dict__
        assert "by_age" in report.__dict__

        # Should have categorized files
        assert len(report.by_type) > 0
        assert len(report.by_risk) > 0
        print("Classification: PASS")


def test_smart_cleanup_reclaimable_calculation():
    """Test reclaimable space calculations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create files
        (temp_path / "file1.log").write_text("a" * 1000)
        (temp_path / "file2.log").write_text("b" * 1000)
        (temp_path / "file3.tmp").write_text("c" * 500)

        # Run analysis
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Total reclaimable should be sum of all files
        assert report.reclaimable_space == report.total_size
        assert report.total_reclaimable == report.reclaimable_space
        print("Reclaimable calculation: PASS")


def test_smart_cleanup_get_summary():
    """Test report summary generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "test.log").write_text("x" * 1000)

        # Run analysis
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Get summary
        summary = engine.get_summary(report)

        # Verify summary contains key information
        assert "磁盘清理分析报告" in summary
        assert "扫描路径" in summary
        assert "文件统计" in summary
        assert "可回收空间" in summary
        # Check for path (Windows may expand paths differently, so check for key parts)
        assert temp_path.name in summary or "Temp" in summary
        print("Summary generation: PASS")


def test_smart_cleanup_get_files_by_type():
    """Test retrieving files by type."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create log files
        (temp_path / "test1.log").write_text("x" * 100)
        (temp_path / "test2.log").write_text("y" * 100)

        # Run analysis
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Get files by type (classifier uses English type names)
        log_files = engine.get_files_by_type(report, "Logs")

        # Should find at least the log files
        assert len(log_files) >= 2
        print("Get files by type: PASS")


def test_smart_cleanup_get_files_by_risk():
    """Test retrieving files by risk level."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create temp files (will be confirm_needed risk)
        (temp_path / "test1.tmp").write_text("x" * 100)
        (temp_path / "test2.tmp").write_text("y" * 100)

        # Run analysis
        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Get confirm_needed files (tmp files are categorized as confirm_needed)
        confirm_files = engine.get_files_by_risk(report, "confirm_needed")

        # Should find temp files as confirm_needed
        assert len(confirm_files) >= 2
        print("Get files by risk: PASS")


def test_smart_cleanup_format_size():
    """Test size formatting."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        engine = SmartCleanupEngine(str(temp_path), cache_enabled=False)

        # Test various sizes
        assert "B" in engine._format_size(100)
        assert "KB" in engine._format_size(1024)
        assert "MB" in engine._format_size(1024 * 1024)
        assert "GB" in engine._format_size(1024 * 1024 * 1024)
        print("Format size: PASS")


def test_smart_cleanup_empty_directory():
    """Test behavior with empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run analysis on empty directory
        engine = SmartCleanupEngine(temp_dir, cache_enabled=False)
        report = engine.analyze(include_duplicates=False, safety_check=False)

        # Should handle gracefully
        assert report.total_files == 0
        assert report.total_size == 0
        assert len(report.duplicates) == 0
        print("Empty directory: PASS")


if __name__ == "__main__":
    print("Running smart cleanup engine tests...\n")
    test_smart_cleanup_basic_analysis()
    test_smart_cleanup_with_duplicates()
    test_smart_cleanup_with_safety_check()
    test_smart_cleanup_classification()
    test_smart_cleanup_reclaimable_calculation()
    test_smart_cleanup_get_summary()
    test_smart_cleanup_get_files_by_type()
    test_smart_cleanup_get_files_by_risk()
    test_smart_cleanup_format_size()
    test_smart_cleanup_empty_directory()
    print("\nAll smart cleanup engine tests passed!")
