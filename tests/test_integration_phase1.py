"""
Basic integration tests for Phase 1 core modules.
"""

import os
import tempfile
from pathlib import Path

from diskcleaner.core import DirectoryScanner, FileClassifier, SafetyChecker
from diskcleaner.config import Config


def test_config_loading():
    """Test configuration loading."""
    config = Config.load()
    assert config.protected_paths
    assert config.protected_extensions
    assert config.check_file_locks is True
    print("Config loading: PASS")


def test_scanner():
    """Test directory scanner."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "test.txt").write_text("hello")
        (temp_path / "test.log").write_text("x" * 1000)

        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        assert len(files) == 2
        assert any(f.name == "test.txt" for f in files)
        assert any(f.name == "test.log" for f in files)

        print(f"Scanner: PASS (found {len(files)} files)")


def test_classifier():
    """Test file classifier."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        (temp_path / "test.log").write_text("x" * 100)
        (temp_path / "test.tmp").write_text("temp")
        (temp_path / "document.pdf").write_text("pdf")

        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        classifier = FileClassifier()
        classification = classifier.classify(files)

        assert "by_type" in classification
        assert "by_risk" in classification
        assert "by_age" in classification

        print(f"Classifier: PASS ({len(classification['by_type'])} types)")


def test_safety_checker():
    """Test safety checker."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test file
        test_file = temp_path / "test.txt"
        test_file.write_text("safe to delete")

        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        safety = SafetyChecker()
        results = safety.verify_all(files)

        assert len(results) > 0
        assert all(file for file, status in results if status.value == "safe")

        print(f"Safety checker: PASS ({len(results)} files checked)")


if __name__ == "__main__":
    print("Running Phase 1 integration tests...\n")
    test_config_loading()
    test_scanner()
    test_classifier()
    test_safety_checker()
    print("\nAll tests passed!")
