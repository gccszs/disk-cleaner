"""
File organization rules module.

Provides predefined strategies for organizing files
and custom rule engine for flexible categorization.
"""

from .archive_rules import (
    ArchiveRule,
    ArchiveStrategy,
    DesktopStrategy,
    DownloadsStrategy,
    ProjectStrategy,
    GeneralStrategy,
    RuleEngine,
)

__all__ = [
    "ArchiveRule",
    "ArchiveStrategy",
    "DesktopStrategy",
    "DownloadsStrategy",
    "ProjectStrategy",
    "GeneralStrategy",
    "RuleEngine",
]
