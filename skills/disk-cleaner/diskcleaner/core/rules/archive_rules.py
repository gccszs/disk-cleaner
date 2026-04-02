"""
Archive rules for file organization.

Defines predefined strategies and rule engine for
intelligent file categorization and organization.
"""

import fnmatch
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from diskcleaner.core.scanner import FileInfo


class RuleType(Enum):
    """Types of archive rules."""

    EXTENSION = "extension"
    PATTERN = "pattern"
    AGE = "age"
    SIZE = "size"
    PATH = "path"
    CUSTOM = "custom"


@dataclass
class ArchiveRule:
    """
    A rule for organizing files.

    Attributes:
        name: Rule name for identification.
        description: Human-readable description.
        rule_type: Type of rule (extension, pattern, age, etc.).
        destination: Target directory path (relative to base).
        priority: Higher priority rules are evaluated first.
        condition: Function that returns True if file matches rule.
        transform: Optional function to transform destination path.
    """

    name: str
    description: str
    rule_type: RuleType
    destination: str
    priority: int = 0
    condition: Optional[Callable[[FileInfo], bool]] = None
    transform: Optional[Callable[[str, FileInfo], str]] = None

    def matches(self, file: FileInfo) -> bool:
        """
        Check if file matches this rule.

        Args:
            file: FileInfo object to check.

        Returns:
            True if file matches rule, False otherwise.
        """
        if self.condition is None:
            return True

        return self.condition(file)

    def get_destination(self, file: FileInfo) -> str:
        """
        Get destination path for file.

        Args:
            file: FileInfo object.

        Returns:
            Destination path (possibly transformed).
        """
        dest = self.destination

        if self.transform:
            dest = self.transform(dest, file)

        return dest


class ArchiveStrategy(ABC):
    """
    Abstract base class for archive strategies.

    Each strategy defines a set of rules for organizing files
    in a specific way (e.g., desktop, downloads, project).
    """

    def __init__(self, name: str, description: str):
        """
        Initialize strategy.

        Args:
            name: Strategy name.
            description: Human-readable description.
        """
        self.name = name
        self.description = description
        self.rules: List[ArchiveRule] = []

    @abstractmethod
    def get_rules(self) -> List[ArchiveRule]:
        """
        Get all rules for this strategy.

        Returns:
            List of ArchiveRule objects sorted by priority.
        """
        pass

    def organize_file(self, file: FileInfo) -> Optional[str]:
        """
        Determine where to organize a file.

        Args:
            file: FileInfo object to organize.

        Returns:
            Destination path, or None if no rule matches.
        """
        for rule in self.get_rules():
            if rule.matches(file):
                return rule.get_destination(file)

        return None


class DesktopStrategy(ArchiveStrategy):
    """
    Desktop organization strategy.

    Organizes files by type into categories:
    - Images
    - Documents
    - Media
    - Archives
    - Code
    - Other
    """

    def __init__(self):
        super().__init__(
            name="desktop",
            description="Organize desktop files by type",
        )
        self.rules = self._build_rules()

    def _build_rules(self) -> List[ArchiveRule]:
        """Build desktop organization rules."""
        rules = []

        # Images
        rules.append(
            ArchiveRule(
                name="images",
                description="Image files (PNG, JPG, GIF, etc.)",
                rule_type=RuleType.EXTENSION,
                destination="Images",
                priority=100,
                condition=lambda f: f.name.lower().endswith(
                    (
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".gif",
                        ".bmp",
                        ".svg",
                        ".webp",
                        ".ico",
                    )
                ),
            )
        )

        # Documents
        rules.append(
            ArchiveRule(
                name="documents",
                description="Document files (PDF, DOC, TXT, etc.)",
                rule_type=RuleType.EXTENSION,
                destination="Documents",
                priority=90,
                condition=lambda f: f.name.lower().endswith(
                    (
                        ".pdf",
                        ".doc",
                        ".docx",
                        ".txt",
                        ".rtf",
                        ".odt",
                        ".xls",
                        ".xlsx",
                        ".ppt",
                        ".pptx",
                        ".csv",
                    )
                ),
            )
        )

        # Media (audio/video)
        rules.append(
            ArchiveRule(
                name="media",
                description="Audio and video files",
                rule_type=RuleType.EXTENSION,
                destination="Media",
                priority=80,
                condition=lambda f: f.name.lower().endswith(
                    (
                        ".mp4",
                        ".mkv",
                        ".avi",
                        ".mov",
                        ".mp3",
                        ".flac",
                        ".wav",
                        ".m4a",
                        ".wmv",
                    )
                ),
            )
        )

        # Archives
        rules.append(
            ArchiveRule(
                name="archives",
                description="Compressed archives",
                rule_type=RuleType.EXTENSION,
                destination="Archives",
                priority=70,
                condition=lambda f: f.name.lower().endswith(
                    (".zip", ".tar", ".gz", ".rar", ".7z", ".bz2")
                ),
            )
        )

        # Code files
        rules.append(
            ArchiveRule(
                name="code",
                description="Programming source code",
                rule_type=RuleType.EXTENSION,
                destination="Code",
                priority=60,
                condition=lambda f: f.name.lower().endswith(
                    (
                        ".py",
                        ".js",
                        ".ts",
                        ".java",
                        ".c",
                        ".cpp",
                        ".h",
                        ".cs",
                        ".go",
                        ".rs",
                        ".php",
                        ".rb",
                        ".swift",
                        ".kt",
                        ".scala",
                        ".sh",
                        ".bat",
                        ".ps1",
                        ".html",
                        ".css",
                        ".json",
                        ".xml",
                        ".yaml",
                        ".yml",
                    )
                ),
            )
        )

        # Executables and installers
        rules.append(
            ArchiveRule(
                name="executables",
                description="Executable files and installers",
                rule_type=RuleType.EXTENSION,
                destination="Installers",
                priority=50,
                condition=lambda f: f.name.lower().endswith(
                    (".exe", ".msi", ".app", ".dmg", ".deb", ".rpm", ".apk")
                ),
            )
        )

        return sorted(rules, key=lambda r: r.priority, reverse=True)

    def get_rules(self) -> List[ArchiveRule]:
        """Get desktop rules."""
        return self.rules


class DownloadsStrategy(ArchiveStrategy):
    """
    Downloads organization strategy.

    Organizes files by type and date:
    - Documents/2024-04/
    - Images/2024-04/
    - Installers/2024-04/
    - Archives/2024-04/
    - Other/
    """

    def __init__(self):
        super().__init__(
            name="downloads",
            description="Organize downloads by type and date",
        )
        self.rules = self._build_rules()

    def _build_rules(self) -> List[ArchiveRule]:
        """Build downloads organization rules."""
        rules = []

        # Helper to add date prefix
        def add_date_prefix(dest: str, file: FileInfo) -> str:
            date_str = datetime.fromtimestamp(file.mtime).strftime("%Y-%m")
            return f"{dest}/{date_str}"

        # Documents with date
        rules.append(
            ArchiveRule(
                name="documents_by_date",
                description="Documents organized by date",
                rule_type=RuleType.EXTENSION,
                destination="Documents",
                priority=100,
                condition=lambda f: f.name.lower().endswith(
                    (
                        ".pdf",
                        ".doc",
                        ".docx",
                        ".txt",
                        ".xls",
                        ".xlsx",
                        ".ppt",
                        ".pptx",
                    )
                ),
                transform=add_date_prefix,
            )
        )

        # Images with date
        rules.append(
            ArchiveRule(
                name="images_by_date",
                description="Images organized by date",
                rule_type=RuleType.EXTENSION,
                destination="Images",
                priority=90,
                condition=lambda f: f.name.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp")
                ),
                transform=add_date_prefix,
            )
        )

        # Media with date
        rules.append(
            ArchiveRule(
                name="media_by_date",
                description="Audio/video organized by date",
                rule_type=RuleType.EXTENSION,
                destination="Media",
                priority=80,
                condition=lambda f: f.name.lower().endswith(
                    (".mp4", ".mkv", ".avi", ".mov", ".mp3", ".flac", ".wav")
                ),
                transform=add_date_prefix,
            )
        )

        # Installers with date
        rules.append(
            ArchiveRule(
                name="installers_by_date",
                description="Installers organized by date",
                rule_type=RuleType.EXTENSION,
                destination="Installers",
                priority=70,
                condition=lambda f: f.name.lower().endswith(
                    (".exe", ".msi", ".app", ".dmg", ".deb", ".rpm")
                ),
                transform=add_date_prefix,
            )
        )

        # Archives with date
        rules.append(
            ArchiveRule(
                name="archives_by_date",
                description="Archives organized by date",
                rule_type=RuleType.EXTENSION,
                destination="Archives",
                priority=60,
                condition=lambda f: f.name.lower().endswith(
                    (".zip", ".tar", ".gz", ".rar", ".7z")
                ),
                transform=add_date_prefix,
            )
        )

        return sorted(rules, key=lambda r: r.priority, reverse=True)

    def get_rules(self) -> List[ArchiveRule]:
        """Get downloads rules."""
        return self.rules


class ProjectStrategy(ArchiveStrategy):
    """
    Project organization strategy.

    Organizes files by project and semantic grouping:
    - Projects/{project-name}/Source
    - Projects/{project-name}/Docs
    - Projects/{project-name}/Assets
    - Projects/{project-name}/Build
    """

    def __init__(self):
        super().__init__(
            name="project",
            description="Organize files by project",
        )
        self.rules = self._build_rules()

    def _build_rules(self) -> List[ArchiveRule]:
        """Build project organization rules."""
        rules = []

        # Detect project from path
        def detect_project(file: FileInfo) -> Optional[str]:
            """Try to detect project name from file path."""
            path_parts = Path(file.path).parts

            # Common project indicators
            project_indicators = [
                "src",
                "source",
                "project",
                "projects",
                "dev",
                "development",
                "code",
                "workspace",
                "work",
            ]

            # Find project directory
            for i, part in enumerate(path_parts):
                if part.lower() in project_indicators and i + 1 < len(path_parts):
                    return path_parts[i + 1]

            # Check for known project structures
            for i, part in enumerate(path_parts):
                # Look for git repository
                if part == ".git" and i > 0:
                    return path_parts[i - 1]

            return None

        def get_project_dest(dest: str, file: FileInfo) -> str:
            """Transform destination to include project name."""
            project = detect_project(file)
            if project:
                return f"Projects/{project}/{dest}"
            return f"Projects/Unknown/{dest}"

        # Source code
        rules.append(
            ArchiveRule(
                name="project_source",
                description="Project source code",
                rule_type=RuleType.CUSTOM,
                destination="Source",
                priority=100,
                condition=lambda f: f.name.lower().endswith(
                    (
                        ".py",
                        ".js",
                        ".ts",
                        ".java",
                        ".c",
                        ".cpp",
                        ".h",
                        ".cs",
                        ".go",
                        ".rs",
                        ".php",
                        ".rb",
                    )
                ),
                transform=get_project_dest,
            )
        )

        # Documentation
        rules.append(
            ArchiveRule(
                name="project_docs",
                description="Project documentation",
                rule_type=RuleType.CUSTOM,
                destination="Docs",
                priority=90,
                condition=lambda f: f.name.lower().endswith(
                    (".md", ".rst", ".txt", ".pdf", ".doc", ".docx")
                )
                or f.name.lower().startswith("readme"),
                transform=get_project_dest,
            )
        )

        # Assets
        rules.append(
            ArchiveRule(
                name="project_assets",
                description="Project assets (images, fonts, etc.)",
                rule_type=RuleType.CUSTOM,
                destination="Assets",
                priority=80,
                condition=lambda f: f.name.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2", ".ttf")
                ),
                transform=get_project_dest,
            )
        )

        # Build artifacts
        rules.append(
            ArchiveRule(
                name="project_build",
                description="Project build artifacts",
                rule_type=RuleType.CUSTOM,
                destination="Build",
                priority=70,
                condition=lambda f: any(
                    pattern in f.path.lower()
                    for pattern in ["build", "dist", "target", "out", "bin", "obj"]
                )
                or f.name.lower().endswith((".o", ".so", ".dll", ".exe")),
                transform=get_project_dest,
            )
        )

        return sorted(rules, key=lambda r: r.priority, reverse=True)

    def get_rules(self) -> List[ArchiveRule]:
        """Get project rules."""
        return self.rules


class GeneralStrategy(ArchiveStrategy):
    """
    General organization strategy.

    Mixed strategy combining type, size, and age:
    - Large files (>100MB) -> Large Files/
    - Recent files (<7 days) -> Recent/
    - Old files (>90 days) -> Archive/
    - By type -> Documents, Images, Media, etc.
    """

    def __init__(self):
        super().__init__(
            name="general",
            description="General purpose organization",
        )
        self.rules = self._build_rules()

    def _build_rules(self) -> List[ArchiveRule]:
        """Build general organization rules."""
        rules = []
        large_threshold = 100 * 1024 * 1024  # 100 MB

        # Large files
        rules.append(
            ArchiveRule(
                name="large_files",
                description="Files larger than 100MB",
                rule_type=RuleType.SIZE,
                destination="Large Files",
                priority=100,
                condition=lambda f: f.size > large_threshold,
            )
        )

        # Recent files
        rules.append(
            ArchiveRule(
                name="recent_files",
                description="Files modified in last 7 days",
                rule_type=RuleType.AGE,
                destination="Recent",
                priority=90,
                condition=lambda f: (datetime.now().timestamp() - f.mtime)
                < timedelta(days=7).total_seconds(),
            )
        )

        # Old files
        rules.append(
            ArchiveRule(
                name="archive_files",
                description="Files not modified in 90 days",
                rule_type=RuleType.AGE,
                destination="Archive",
                priority=80,
                condition=lambda f: (datetime.now().timestamp() - f.mtime)
                > timedelta(days=90).total_seconds(),
            )
        )

        # Documents
        rules.append(
            ArchiveRule(
                name="documents",
                description="Document files",
                rule_type=RuleType.EXTENSION,
                destination="Documents",
                priority=70,
                condition=lambda f: f.name.lower().endswith(
                    (".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx")
                ),
            )
        )

        # Images
        rules.append(
            ArchiveRule(
                name="images",
                description="Image files",
                rule_type=RuleType.EXTENSION,
                destination="Images",
                priority=60,
                condition=lambda f: f.name.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp")
                ),
            )
        )

        # Media
        rules.append(
            ArchiveRule(
                name="media",
                description="Audio and video files",
                rule_type=RuleType.EXTENSION,
                destination="Media",
                priority=50,
                condition=lambda f: f.name.lower().endswith(
                    (".mp4", ".mkv", ".avi", ".mov", ".mp3", ".flac", ".wav")
                ),
            )
        )

        # Archives
        rules.append(
            ArchiveRule(
                name="archives",
                description="Compressed archives",
                rule_type=RuleType.EXTENSION,
                destination="Archives",
                priority=40,
                condition=lambda f: f.name.lower().endswith(
                    (".zip", ".tar", ".gz", ".rar", ".7z")
                ),
            )
        )

        return sorted(rules, key=lambda r: r.priority, reverse=True)

    def get_rules(self) -> List[ArchiveRule]:
        """Get general rules."""
        return self.rules


class RuleEngine:
    """
    Rule engine for file organization.

    Manages strategies and rules, provides matching
    and destination resolution for files.
    """

    def __init__(self):
        """Initialize rule engine."""
        self.strategies: Dict[str, ArchiveStrategy] = {}
        self._register_builtin_strategies()

    def _register_builtin_strategies(self):
        """Register built-in strategies."""
        self.strategies["desktop"] = DesktopStrategy()
        self.strategies["downloads"] = DownloadsStrategy()
        self.strategies["project"] = ProjectStrategy()
        self.strategies["general"] = GeneralStrategy()

    def register_strategy(self, strategy: ArchiveStrategy):
        """
        Register a custom strategy.

        Args:
            strategy: ArchiveStrategy instance.
        """
        self.strategies[strategy.name] = strategy

    def get_strategy(self, name: str) -> Optional[ArchiveStrategy]:
        """
        Get strategy by name.

        Args:
            name: Strategy name.

        Returns:
            ArchiveStrategy instance or None.
        """
        return self.strategies.get(name)

    def list_strategies(self) -> List[str]:
        """
        List available strategies.

        Returns:
            List of strategy names.
        """
        return list(self.strategies.keys())

    def organize_file(
        self, file: FileInfo, strategy_name: str
    ) -> Optional[str]:
        """
        Organize a file using specified strategy.

        Args:
            file: FileInfo object.
            strategy_name: Name of strategy to use.

        Returns:
            Destination path, or None if no rule matches.
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        return strategy.organize_file(file)

    def organize_files(
        self, files: List[FileInfo], strategy_name: str
    ) -> Dict[str, List[FileInfo]]:
        """
        Organize multiple files using strategy.

        Args:
            files: List of FileInfo objects.
            strategy_name: Name of strategy to use.

        Returns:
            Dictionary mapping destinations to file lists.
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        organized: Dict[str, List[FileInfo]] = {}

        for file in files:
            dest = strategy.organize_file(file)
            if dest:
                if dest not in organized:
                    organized[dest] = []
                organized[dest].append(file)

        return organized

    def add_custom_rule(
        self,
        strategy_name: str,
        rule: ArchiveRule,
    ):
        """
        Add a custom rule to a strategy.

        Args:
            strategy_name: Strategy to modify.
            rule: Rule to add.
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        strategy.rules.append(rule)
        # Re-sort by priority
        strategy.rules.sort(key=lambda r: r.priority, reverse=True)

    def create_rule_from_dict(
        self, rule_dict: Dict
    ) -> ArchiveRule:
        """
        Create ArchiveRule from dictionary.

        Args:
            rule_dict: Dictionary with rule configuration.

        Returns:
            ArchiveRule instance.

        Example:
            {
                "name": "my_rule",
                "description": "My custom rule",
                "type": "extension",
                "destination": "MyFolder",
                "priority": 50,
                "patterns": ["*.txt", "*.md"]
            }
        """
        rule_type = RuleType(rule_dict.get("type", "custom"))

        # Build condition based on type
        condition = None
        patterns = rule_dict.get("patterns", [])

        if rule_type == RuleType.EXTENSION and patterns:
            extensions = tuple(p.replace("*", "") for p in patterns)
            condition = lambda f, ext=extensions: f.name.lower().endswith(ext)

        elif rule_type == RuleType.PATTERN and patterns:
            condition = lambda f, pats=patterns: any(
                fnmatch.fnmatch(f.name, pat) for pat in pats
            )

        return ArchiveRule(
            name=rule_dict["name"],
            description=rule_dict.get("description", ""),
            rule_type=rule_type,
            destination=rule_dict["destination"],
            priority=rule_dict.get("priority", 0),
            condition=condition,
        )
