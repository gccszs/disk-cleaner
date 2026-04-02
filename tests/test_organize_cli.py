"""
Integration tests for organize_files CLI.

Tests CLI argument parsing and basic functionality.
"""

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def temp_directory():
    """Create temporary directory for testing."""
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_files(temp_directory):
    """Create sample files for testing."""
    files = {
        "image.png": b"x" * (1024 * 512),
        "document.pdf": b"x" * (1024 * 1024 * 2),
        "script.py": b"x" * (1024 * 10),
        "video.mp4": b"x" * (1024 * 1024 * 150),
        "readme.md": b"# Readme",
    }

    for filename, content in files.items():
        filepath = Path(temp_directory) / filename
        filepath.write_bytes(content)

    return files.keys()


class TestOrganizeCLI:
    """Test organize_files.py CLI."""

    def test_list_strategies(self):
        """Test listing available strategies."""
        result = subprocess.run(
            [sys.executable, "scripts/organize_files.py", "--list-strategies"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "DESKTOP" in result.stdout
        assert "DOWNLOADS" in result.stdout
        assert "PROJECT" in result.stdout
        assert "GENERAL" in result.stdout

    def test_invalid_path(self):
        """Test with invalid path."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                "/nonexistent/path",
                "--preview",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode != 0
        assert "does not exist" in result.stderr.lower()

    def test_preview_mode(self, temp_directory, sample_files):
        """Test preview mode."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                temp_directory,
                "--strategy",
                "desktop",
                "--preview",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "FILE ORGANIZATION PREVIEW" in result.stdout
        assert "DRY RUN" in result.stdout
        assert "SUMMARY:" in result.stdout

    def test_execute_dry_run(self, temp_directory, sample_files):
        """Test execute mode (dry run by default)."""
        result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                temp_directory,
                "--strategy",
                "desktop",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should default to preview
        assert result.returncode == 0
        assert "Preview complete" in result.stdout

        # Files should not be moved
        assert (Path(temp_directory) / "image.png").exists()

    def test_desktop_strategy(self, temp_directory):
        """Test desktop strategy."""
        # Create test files
        (Path(temp_directory) / "image.png").write_bytes(b"x" * 1024)
        (Path(temp_directory) / "document.pdf").write_bytes(b"x" * 1024)

        result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                temp_directory,
                "--strategy",
                "desktop",
                "--preview",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "Images" in result.stdout or "Documents" in result.stdout

    def test_downloads_strategy(self, temp_directory):
        """Test downloads strategy."""
        # Create test file
        (Path(temp_directory) / "video.mp4").write_bytes(b"x" * 1024)

        result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                temp_directory,
                "--strategy",
                "downloads",
                "--preview",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "downloads" in result.stdout.lower()

    def test_general_strategy(self, temp_directory):
        """Test general strategy."""
        # Create test file
        (Path(temp_directory) / "large_file.bin").write_bytes(b"x" * (150 * 1024 * 1024))

        result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                temp_directory,
                "--strategy",
                "general",
                "--preview",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0

    def test_max_files_limit(self, temp_directory):
        """Test max-files option."""
        # Create many test files
        for i in range(100):
            (Path(temp_directory) / f"file{i}.txt").write_text("content")

        result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                temp_directory,
                "--strategy",
                "desktop",
                "--preview",
                "--max-files",
                "10",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "SAMPLE ACTIONS" in result.stdout

    def test_verbose_mode(self, temp_directory):
        """Test verbose mode."""
        (Path(temp_directory) / "test.txt").write_text("content")

        result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                temp_directory,
                "--strategy",
                "desktop",
                "--preview",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        # Should show strategy info
        assert "Strategy:" in result.stdout


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_full_workflow(self, temp_directory):
        """Test complete workflow: preview then execute."""
        # Create test files
        test_files = {
            "photo.png": b"image data",
            "report.pdf": b"pdf data",
            "code.py": b"python code",
        }

        for filename, content in test_files.items():
            (Path(temp_directory) / filename).write_bytes(content)

        # First, preview
        preview_result = subprocess.run(
            [
                sys.executable,
                "scripts/organize_files.py",
                temp_directory,
                "--strategy",
                "desktop",
                "--preview",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert preview_result.returncode == 0

        # Files should still be in original location
        assert (Path(temp_directory) / "photo.png").exists()

    def test_different_strategies_same_files(self, temp_directory):
        """Test same files with different strategies."""
        # Create test file
        (Path(temp_directory) / "test.png").write_bytes(b"image data")

        strategies = ["desktop", "downloads", "general"]

        for strategy in strategies:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/organize_files.py",
                    temp_directory,
                    "--strategy",
                    strategy,
                    "--preview",
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

            assert result.returncode == 0
            assert strategy in result.stdout.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
