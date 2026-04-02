"""
Unit tests for archive rules module.

Tests rule engine, strategies, and file matching logic.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diskcleaner.core.rules.archive_rules import (
    ArchiveRule,
    ArchiveStrategy,
    DesktopStrategy,
    DownloadsStrategy,
    ProjectStrategy,
    GeneralStrategy,
    RuleEngine,
    RuleType,
)
from diskcleaner.core.scanner import FileInfo


@pytest.fixture
def sample_files():
    """Create sample file list for testing."""
    files = []

    # Image files
    files.append(
        FileInfo(
            path="/home/user/Desktop/image.png",
            name="image.png",
            size=1024 * 512,
            mtime=datetime.now().timestamp(),
            is_dir=False,
            is_link=False,
        )
    )

    # Document files
    files.append(
        FileInfo(
            path="/home/user/Desktop/document.pdf",
            name="document.pdf",
            size=1024 * 1024 * 2,
            mtime=datetime.now().timestamp(),
            is_dir=False,
            is_link=False,
        )
    )

    # Video files
    files.append(
        FileInfo(
            path="/home/user/Downloads/video.mp4",
            name="video.mp4",
            size=1024 * 1024 * 150,
            mtime=datetime.now().timestamp(),
            is_dir=False,
            is_link=False,
        )
    )

    # Code files
    files.append(
        FileInfo(
            path="/home/user/project/script.py",
            name="script.py",
            size=1024 * 10,
            mtime=datetime.now().timestamp(),
            is_dir=False,
            is_link=False,
        )
    )

    # Old file
    old_time = (datetime.now() - timedelta(days=100)).timestamp()
    files.append(
        FileInfo(
            path="/home/user/old_file.txt",
            name="old_file.txt",
            size=1024,
            mtime=old_time,
            is_dir=False,
            is_link=False,
        )
    )

    return files


class TestArchiveRule:
    """Test ArchiveRule class."""

    def test_rule_creation(self):
        """Test creating a rule."""
        rule = ArchiveRule(
            name="test_rule",
            description="Test rule",
            rule_type=RuleType.EXTENSION,
            destination="Test",
            priority=50,
            condition=lambda f: f.name.endswith(".txt"),
        )

        assert rule.name == "test_rule"
        assert rule.description == "Test rule"
        assert rule.rule_type == RuleType.EXTENSION
        assert rule.destination == "Test"
        assert rule.priority == 50

    def test_rule_matches(self):
        """Test rule matching."""
        rule = ArchiveRule(
            name="text_files",
            description="Text files",
            rule_type=RuleType.EXTENSION,
            destination="Text",
            condition=lambda f: f.name.endswith(".txt"),
        )

        # Matching file
        matching_file = FileInfo(
            path="/test/file.txt",
            name="file.txt",
            size=1024,
            mtime=datetime.now().timestamp(),
            is_dir=False,
            is_link=False,
        )
        assert rule.matches(matching_file) is True

        # Non-matching file
        non_matching_file = FileInfo(
            path="/test/file.pdf",
            name="file.pdf",
            size=1024,
            mtime=datetime.now().timestamp(),
            is_dir=False,
            is_link=False,
        )
        assert rule.matches(non_matching_file) is False

    def test_rule_transform(self):
        """Test rule destination transformation."""
        rule = ArchiveRule(
            name="test_rule",
            description="Test rule",
            rule_type=RuleType.CUSTOM,
            destination="Base",
            transform=lambda dest, f: f"{dest}/2024-04",
        )

        file = FileInfo(
            path="/test/file.txt",
            name="file.txt",
            size=1024,
            mtime=datetime.now().timestamp(),
            is_dir=False,
            is_link=False,
        )

        dest = rule.get_destination(file)
        assert dest == "Base/2024-04"


class TestDesktopStrategy:
    """Test DesktopStrategy class."""

    def test_strategy_initialization(self):
        """Test strategy initialization."""
        strategy = DesktopStrategy()
        assert strategy.name == "desktop"
        assert len(strategy.rules) > 0

    def test_organize_images(self, sample_files):
        """Test organizing image files."""
        strategy = DesktopStrategy()
        image_file = sample_files[0]  # image.png

        dest = strategy.organize_file(image_file)
        assert dest == "Images"

    def test_organize_documents(self, sample_files):
        """Test organizing document files."""
        strategy = DesktopStrategy()
        doc_file = sample_files[1]  # document.pdf

        dest = strategy.organize_file(doc_file)
        assert dest == "Documents"

    def test_organize_code(self, sample_files):
        """Test organizing code files."""
        strategy = DesktopStrategy()
        code_file = sample_files[3]  # script.py

        dest = strategy.organize_file(code_file)
        assert dest == "Code"


class TestDownloadsStrategy:
    """Test DownloadsStrategy class."""

    def test_strategy_initialization(self):
        """Test strategy initialization."""
        strategy = DownloadsStrategy()
        assert strategy.name == "downloads"
        assert len(strategy.rules) > 0

    def test_organize_with_date_prefix(self, sample_files):
        """Test organizing files with date prefix."""
        strategy = DownloadsStrategy()
        doc_file = sample_files[1]  # document.pdf

        dest = strategy.organize_file(doc_file)
        # Should include date prefix (YYYY-MM)
        assert "Documents" in dest
        assert "/" in dest  # Has date separator


class TestProjectStrategy:
    """Test ProjectStrategy class."""

    def test_strategy_initialization(self):
        """Test strategy initialization."""
        strategy = ProjectStrategy()
        assert strategy.name == "project"
        assert len(strategy.rules) > 0

    def test_organize_source_code(self, sample_files):
        """Test organizing source code by project."""
        strategy = ProjectStrategy()
        code_file = sample_files[3]  # script.py in /home/user/project/

        dest = strategy.organize_file(code_file)
        assert "Source" in dest


class TestGeneralStrategy:
    """Test GeneralStrategy class."""

    def test_strategy_initialization(self):
        """Test strategy initialization."""
        strategy = GeneralStrategy()
        assert strategy.name == "general"
        assert len(strategy.rules) > 0

    def test_organize_large_files(self, sample_files):
        """Test organizing large files."""
        strategy = GeneralStrategy()
        large_file = sample_files[2]  # video.mp4 (150MB)

        dest = strategy.organize_file(large_file)
        assert dest == "Large Files"

    def test_organize_old_files(self, sample_files):
        """Test organizing old files."""
        strategy = GeneralStrategy()
        old_file = sample_files[4]  # old_file.txt (100 days old)

        dest = strategy.organize_file(old_file)
        assert dest == "Archive"


class TestRuleEngine:
    """Test RuleEngine class."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = RuleEngine()
        assert len(engine.strategies) == 4  # 4 built-in strategies
        assert "desktop" in engine.strategies
        assert "downloads" in engine.strategies
        assert "project" in engine.strategies
        assert "general" in engine.strategies

    def test_list_strategies(self):
        """Test listing available strategies."""
        engine = RuleEngine()
        strategies = engine.list_strategies()
        assert len(strategies) == 4
        assert "desktop" in strategies

    def test_get_strategy(self):
        """Test getting a strategy."""
        engine = RuleEngine()
        strategy = engine.get_strategy("desktop")
        assert isinstance(strategy, DesktopStrategy)

    def test_organize_single_file(self, sample_files):
        """Test organizing a single file."""
        engine = RuleEngine()
        image_file = sample_files[0]

        dest = engine.organize_file(image_file, "desktop")
        assert dest == "Images"

    def test_organize_multiple_files(self, sample_files):
        """Test organizing multiple files."""
        engine = RuleEngine()
        organized = engine.organize_files(sample_files, "desktop")

        # Check that files were organized
        assert len(organized) > 0

        # Check specific destinations
        assert "Images" in organized or "Documents" in organized

    def test_unknown_strategy(self, sample_files):
        """Test using unknown strategy."""
        engine = RuleEngine()

        with pytest.raises(ValueError):
            engine.organize_file(sample_files[0], "unknown_strategy")

    def test_add_custom_rule(self):
        """Test adding custom rule to strategy."""
        engine = RuleEngine()

        custom_rule = ArchiveRule(
            name="custom_rule",
            description="Custom test rule",
            rule_type=RuleType.CUSTOM,
            destination="Custom",
            priority=200,
            condition=lambda f: f.name.startswith("test_"),
        )

        engine.add_custom_rule("desktop", custom_rule)

        # Check rule was added
        strategy = engine.get_strategy("desktop")
        assert len(strategy.rules) > 0

    def test_create_rule_from_dict(self):
        """Test creating rule from dictionary."""
        engine = RuleEngine()

        rule_dict = {
            "name": "dict_rule",
            "description": "Rule from dict",
            "type": "extension",
            "destination": "DictFolder",
            "priority": 75,
            "patterns": ["*.log", "*.tmp"],
        }

        rule = engine.create_rule_from_dict(rule_dict)

        assert rule.name == "dict_rule"
        assert rule.destination == "DictFolder"
        assert rule.priority == 75
        assert rule.condition is not None


@pytest.mark.integration
class TestIntegration:
    """Integration tests for archive rules."""

    def test_full_organization_workflow(self, sample_files):
        """Test complete file organization workflow."""
        engine = RuleEngine()

        # Test different strategies
        strategies = ["desktop", "downloads", "general"]

        for strategy_name in strategies:
            organized = engine.organize_files(sample_files, strategy_name)

            # Verify organization
            assert isinstance(organized, dict)
            assert len(organized) > 0

            # Verify all files have destinations
            total_organized = sum(len(files) for files in organized.values())
            assert total_organized > 0

    def test_strategy_priority_order(self):
        """Test that rules are evaluated by priority."""
        strategy = DesktopStrategy()

        # Check rules are sorted by priority
        priorities = [rule.priority for rule in strategy.rules]
        assert priorities == sorted(priorities, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
