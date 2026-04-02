"""
Unit tests for file organizer module.

Tests plan generation, execution, and dry-run mode.
"""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diskcleaner.core.organizer import FileOrganizer, OrganizationAction, OrganizationPlan
from diskcleaner.core.scanner import FileInfo


@pytest.fixture
def temp_directory():
    """Create temporary directory for testing."""
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_organizer(temp_directory):
    """Create FileOrganizer instance for testing."""
    return FileOrganizer(
        target_path=temp_directory,
        strategy="desktop",
        dry_run=True,
    )


@pytest.fixture
def sample_files(temp_directory):
    """Create sample files for testing."""
    files = []

    # Create test files
    test_files = [
        ("image.png", 1024 * 512),
        ("document.pdf", 1024 * 1024 * 2),
        ("script.py", 1024 * 10),
        ("video.mp4", 1024 * 1024 * 150),
    ]

    for filename, size in test_files:
        filepath = Path(temp_directory) / filename
        filepath.write_bytes(b"0" * size)

        files.append(
            FileInfo(
                path=str(filepath),
                name=filename,
                size=size,
                mtime=0,
                is_dir=False,
                is_link=False,
            )
        )

    return files


class TestOrganizationAction:
    """Test OrganizationAction class."""

    def test_action_creation(self):
        """Test creating an action."""
        file_info = FileInfo(
            path="/test/file.txt",
            name="file.txt",
            size=1024,
            mtime=0,
            is_dir=False,
            is_link=False,
        )

        action = OrganizationAction(
            source_path="/test/file.txt",
            destination_path="/test/organized/file.txt",
            action_type="move",
            reason="Test rule",
            file_info=file_info,
        )

        assert action.source_path == "/test/file.txt"
        assert action.destination_path == "/test/organized/file.txt"
        assert action.action_type == "move"
        assert action.reason == "Test rule"

    def test_action_string_representation(self):
        """Test string representation."""
        file_info = FileInfo(
            path="/test/file.txt",
            name="file.txt",
            size=1024,
            mtime=0,
            is_dir=False,
            is_link=False,
        )

        action = OrganizationAction(
            source_path="/test/file.txt",
            destination_path="/test/organized/file.txt",
            action_type="move",
            reason="Test",
            file_info=file_info,
        )

        str_repr = str(action)
        assert "MOVE" in str_repr
        assert "/test/file.txt" in str_repr


class TestOrganizationPlan:
    """Test OrganizationPlan class."""

    def test_plan_creation(self):
        """Test creating a plan."""
        plan = OrganizationPlan(
            target_path="/test",
            strategy="desktop",
        )

        assert plan.target_path == "/test"
        assert plan.strategy == "desktop"
        assert len(plan.actions) == 0
        assert plan.file_count == 0
        assert plan.total_size == 0

    def test_add_action(self, sample_files):
        """Test adding actions to plan."""
        plan = OrganizationPlan(
            target_path="/test",
            strategy="desktop",
        )

        action = OrganizationAction(
            source_path=sample_files[0].path,
            destination_path="/test/Images/image.png",
            action_type="move",
            reason="Rule: Images",
            file_info=sample_files[0],
        )

        plan.add_action(action)

        assert len(plan.actions) == 1
        assert plan.file_count == 1
        assert plan.total_size == sample_files[0].size

    def test_get_summary(self, sample_files):
        """Test getting plan summary."""
        plan = OrganizationPlan(
            target_path="/test",
            strategy="desktop",
        )

        # Add various actions
        plan.add_action(
            OrganizationAction(
                source_path=sample_files[0].path,
                destination_path="/test/Images/image.png",
                action_type="move",
                reason="Rule",
                file_info=sample_files[0],
            )
        )

        plan.add_action(
            OrganizationAction(
                source_path=sample_files[1].path,
                destination_path="/test/Documents/doc.pdf",
                action_type="copy",
                reason="Rule",
                file_info=sample_files[1],
            )
        )

        plan.add_action(
            OrganizationAction(
                source_path=sample_files[2].path,
                destination_path="",
                action_type="skip",
                reason="No rule",
                file_info=sample_files[2],
            )
        )

        summary = plan.get_summary()

        assert summary["total_actions"] == 3
        assert summary["move_actions"] == 1
        assert summary["copy_actions"] == 1
        assert summary["skip_actions"] == 1

    def test_get_actions_by_destination(self, sample_files):
        """Test grouping actions by destination."""
        plan = OrganizationPlan(
            target_path="/test",
            strategy="desktop",
        )

        # Add actions to same destination
        for i in range(2):
            plan.add_action(
                OrganizationAction(
                    source_path=f"/test/file{i}.txt",
                    destination_path="/test/Images",
                    action_type="move",
                    reason="Rule",
                    file_info=sample_files[0],
                )
            )

        grouped = plan.get_actions_by_destination()

        assert "/test/Images" in grouped
        assert len(grouped["/test/Images"]) == 2


class TestFileOrganizer:
    """Test FileOrganizer class."""

    def test_organizer_initialization(self, temp_directory):
        """Test organizer initialization."""
        organizer = FileOrganizer(
            target_path=temp_directory,
            strategy="desktop",
            dry_run=True,
        )

        assert organizer.target_path == Path(temp_directory).resolve()
        assert organizer.strategy_name == "desktop"
        assert organizer.dry_run is True

    def test_scan_files(self, sample_organizer, temp_directory):
        """Test scanning files."""
        # Create test files
        for i in range(3):
            (Path(temp_directory) / f"file{i}.txt").write_text("content")

        files = sample_organizer.scan_files()

        assert len(files) >= 3

    def test_generate_plan(self, sample_organizer, sample_files):
        """Test generating organization plan."""
        plan = sample_organizer.generate_plan(sample_files)

        assert plan.strategy == "desktop"
        assert len(plan.actions) > 0

    def test_generate_plan_with_progress(self, sample_organizer, sample_files):
        """Test generating plan with progress callback."""
        progress_updates = []

        def callback(current, total):
            progress_updates.append((current, total))

        plan = sample_organizer.generate_plan(sample_files, callback)

        assert len(progress_updates) > 0
        assert plan.strategy == "desktop"

    def test_check_conflicts(self, sample_organizer, temp_directory):
        """Test conflict detection."""
        # Create a file
        test_file = Path(temp_directory) / "test.txt"
        test_file.write_text("original")

        file_info = FileInfo(
            path=str(test_file),
            name="test.txt",
            size=8,
            mtime=0,
            is_dir=False,
            is_link=False,
        )

        # Check for conflict with same path
        dest_path = Path(temp_directory)
        conflict = sample_organizer._check_conflicts(file_info, dest_path)

        assert conflict is not None
        assert "same" in conflict.lower()

    def test_execute_plan_dry_run(self, sample_organizer, sample_files):
        """Test executing plan in dry-run mode."""
        plan = sample_organizer.generate_plan(sample_files)

        organized, skipped, errors = sample_organizer.execute_plan(plan)

        # In dry-run mode, organized should equal move actions
        assert organized >= 0
        assert skipped >= 0
        assert errors == 0

    def test_preview_organization(self, sample_organizer, temp_directory):
        """Test preview generation."""
        # Create some test files
        for name in ["image.png", "doc.pdf", "script.py"]:
            (Path(temp_directory) / name).write_text("content")

        preview = sample_organizer.preview_organization()

        assert "FILE ORGANIZATION PREVIEW" in preview
        assert "Strategy: desktop" in preview
        assert "DRY RUN" in preview
        assert "SUMMARY:" in preview

    def test_format_size(self, sample_organizer):
        """Test size formatting."""
        assert sample_organizer._format_size(1024) == "1.0 KB"
        assert sample_organizer._format_size(1024 * 1024) == "1.0 MB"
        assert sample_organizer._format_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_organize_method(self, sample_organizer, sample_files):
        """Test high-level organize method."""
        organized, skipped, errors = sample_organizer.organize()

        assert organized >= 0
        assert skipped >= 0
        assert errors == 0

        stats = sample_organizer.get_statistics()
        assert stats["organized"] == organized
        assert stats["skipped"] == skipped
        assert stats["errors"] == errors

    def test_unknown_strategy(self, temp_directory):
        """Test using unknown strategy."""
        with pytest.raises(ValueError):
            FileOrganizer(
                target_path=temp_directory,
                strategy="unknown_strategy",
            )


@pytest.mark.integration
class TestIntegration:
    """Integration tests for organizer."""

    def test_full_workflow(self, temp_directory):
        """Test complete organization workflow."""
        # Create test files
        test_files = {
            "image.png": "image data",
            "document.pdf": "pdf data",
            "script.py": "python code",
            "video.mp4": "video data",
        }

        for filename, content in test_files.items():
            (Path(temp_directory) / filename).write_text(content)

        # Create organizer
        organizer = FileOrganizer(
            target_path=temp_directory,
            strategy="desktop",
            dry_run=True,
        )

        # Generate preview
        preview = organizer.preview_organization()
        assert "preview" in preview.lower()

        # Generate plan
        plan = organizer.generate_plan()
        assert len(plan.actions) > 0

        # Execute plan
        organized, skipped, errors = organizer.execute_plan(plan)
        assert organized > 0 or skipped > 0

    def test_different_strategies(self, temp_directory):
        """Test different organization strategies."""
        # Create test file
        (Path(temp_directory) / "test.txt").write_text("content")

        strategies = ["desktop", "downloads", "general"]

        for strategy in strategies:
            organizer = FileOrganizer(
                target_path=temp_directory,
                strategy=strategy,
                dry_run=True,
            )

            plan = organizer.generate_plan()
            assert plan.strategy == strategy


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
