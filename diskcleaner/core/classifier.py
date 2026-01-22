"""
File classifier with multi-dimensional categorization.

Classifies files by type, risk level, and age for intelligent
cleanup recommendations.
"""

import fnmatch
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from diskcleaner.config import Config
from diskcleaner.core.scanner import FileInfo


class RiskLevel(Enum):
    """Risk level for file deletion."""

    SAFE = "safe"
    CONFIRM_NEEDED = "confirm_needed"
    PROTECTED = "protected"


class FileClassifier:
    """
    Classifies files into categories for intelligent cleanup.

    Provides three-dimensional classification:
    1. By type (temp, logs, cache, build artifacts, etc.)
    2. By risk level (safe, confirm_needed, protected)
    3. By age (recent, mid-term, old)
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize classifier.

        Args:
            config: Configuration object.
        """
        self.config = config or Config.load()

        # Load protected patterns and extensions
        self.protected_patterns = self.config.protected_patterns
        self.protected_extensions = self.config.protected_extensions
        self.protected_paths = self.config.protected_paths

        # Load custom rules
        self.custom_rules = self.config.get("rules", [])

        # Define type categories
        self.type_categories = {
            "临时/构建产物": [
                "*.tmp",
                "*.temp",
                "*.cache",
                "__pycache__",
                "node_modules",
                ".pytest_cache",
                ".mypy_cache",
                "*.pyc",
                "*.pyo",
            ],
            "日志文件": ["*.log"],
            "缓存文件": [
                "*.cache",
                ".cache",
                "Thumbs.db",
                ".DS_Store",
            ],
            "备份文件": [
                "*.bak",
                "*.backup",
                "*~",
                "*.old",
            ],
            "下载文件": None,  # Special handling by path
            "媒体文件": [
                "*.mp4",
                "*.mkv",
                "*.avi",
                "*.mov",
                "*.mp3",
                "*.flac",
                "*.jpg",
                "*.jpeg",
                "*.png",
                "*.gif",
                "*.bmp",
            ],
            "文档文件": [
                "*.pdf",
                "*.doc",
                "*.docx",
                "*.xls",
                "*.xlsx",
                "*.ppt",
                "*.pptx",
                "*.odt",
            ],
            "压缩文件": [
                "*.zip",
                "*.tar",
                "*.gz",
                "*.rar",
                "*.7z",
            ],
        }

    def classify(
        self,
        files: List[FileInfo],
    ) -> Dict[str, Dict[str, List[FileInfo]]]:
        """
        Classify files by type, risk, and age.

        Args:
            files: List of FileInfo objects to classify.

        Returns:
            Dictionary with three classification dimensions:
            {
                "by_type": {category_name: [files]},
                "by_risk": {risk_level: [files]},
                "by_age": {age_group: [files]}
            }
        """
        result = {
            "by_type": {},
            "by_risk": {
                RiskLevel.SAFE.value: [],
                RiskLevel.CONFIRM_NEEDED.value: [],
                RiskLevel.PROTECTED.value: [],
            },
            "by_age": {
                "最近创建 (7天内)": [],
                "近期文件 (30天内)": [],
                "陈旧文件 (90天内)": [],
                "很旧 (90天以上)": [],
            },
        }

        for file in files:
            # Skip directories
            if file.is_dir:
                continue

            # Classify by type
            type_category = self._classify_type(file)
            if type_category not in result["by_type"]:
                result["by_type"][type_category] = []
            result["by_type"][type_category].append(file)

            # Classify by risk
            risk_level = self._classify_risk(file)
            result["by_risk"][risk_level.value].append(file)

            # Classify by age
            age_group = self._classify_age(file)
            result["by_age"][age_group].append(file)

        return result

    def _classify_type(self, file: FileInfo) -> str:
        """
        Classify file by type.

        Args:
            file: FileInfo object.

        Returns:
            Type category name.
        """
        # Check custom rules first
        for rule in self.custom_rules:
            pattern = rule.get("pattern", "")
            if self._matches_pattern(file, pattern):
                return rule.get("category", "其他文件")

        # Check built-in categories
        for category, patterns in self.type_categories.items():
            if patterns is None:
                continue

            for pattern in patterns:
                if self._matches_pattern(file, pattern):
                    return category

        # Special handling for downloads
        if "downloads" in file.path.lower():
            return "下载文件"

        return "其他文件"

    def _classify_risk(self, file: FileInfo) -> RiskLevel:
        """
        Classify file by risk level.

        Args:
            file: FileInfo object.

        Returns:
            RiskLevel enum value.
        """
        # Check if path is protected
        for protected_path in self.protected_paths:
            if file.path.startswith(protected_path):
                return RiskLevel.PROTECTED

        # Check if extension is protected
        for ext in self.protected_extensions:
            if file.name.lower().endswith(ext.lower()):
                return RiskLevel.PROTECTED

        # Check if pattern matches protected patterns
        for pattern in self.protected_patterns:
            if fnmatch.fnmatch(file.name, pattern):
                return RiskLevel.PROTECTED

        # Classify by file type
        file_type = self._classify_type(file)

        # Safe to delete categories
        safe_categories = ["临时/构建产物", "日志文件", "缓存文件"]
        if file_type in safe_categories:
            return RiskLevel.SAFE

        # Confirm needed for user data
        confirm_categories = ["下载文件", "媒体文件", "文档文件"]
        if file_type in confirm_categories:
            return RiskLevel.CONFIRM_NEEDED

        # Default to confirm needed
        return RiskLevel.CONFIRM_NEEDED

    def _classify_age(self, file: FileInfo) -> str:
        """
        Classify file by age.

        Args:
            file: FileInfo object.

        Returns:
            Age group name.
        """
        now = datetime.now()
        file_time = datetime.fromtimestamp(file.mtime)
        age = now - file_time

        if age < timedelta(days=7):
            return "最近创建 (7天内)"
        elif age < timedelta(days=30):
            return "近期文件 (30天内)"
        elif age < timedelta(days=90):
            return "陈旧文件 (90天内)"
        else:
            return "很旧 (90天以上)"

    def _matches_pattern(self, file: FileInfo, pattern: str) -> bool:
        """
        Check if file matches a pattern.

        Args:
            file: FileInfo object.
            pattern: Pattern to match (can be * wildcards or directory names).

        Returns:
            True if file matches pattern.
        """
        # Check filename
        if fnmatch.fnmatch(file.name, pattern):
            return True

        # Check path components
        path_parts = Path(file.path).parts
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True

        # Check full path
        if fnmatch.fnmatch(file.path, pattern):
            return True

        # Check if pattern is a directory name in path
        if pattern.rstrip("/") in path_parts:
            return True

        return False

    def get_type_stats(
        self,
        files: List[FileInfo],
    ) -> Dict[str, Dict[str, int]]:
        """
        Get statistics by file type.

        Args:
            files: List of FileInfo objects.

        Returns:
            Dictionary with stats for each type:
            {
                "type_name": {
                    "count": 10,
                    "total_size": 1024000
                }
            }
        """
        classification = self.classify(files)
        stats = {}

        for type_name, type_files in classification["by_type"].items():
            stats[type_name] = {
                "count": len(type_files),
                "total_size": sum(f.size for f in type_files),
            }

        return stats

    def get_risk_stats(
        self,
        files: List[FileInfo],
    ) -> Dict[str, Dict[str, int]]:
        """
        Get statistics by risk level.

        Args:
            files: List of FileInfo objects.

        Returns:
            Dictionary with stats for each risk level.
        """
        classification = self.classify(files)
        stats = {}

        for risk_level, risk_files in classification["by_risk"].items():
            stats[risk_level] = {
                "count": len(risk_files),
                "total_size": sum(f.size for f in risk_files),
            }

        return stats
