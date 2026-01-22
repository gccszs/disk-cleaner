"""
Smart cleanup engine integrating all core modules.

Combines scanner, classifier, duplicate finder, and safety checker
to provide intelligent cleanup recommendations.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from diskcleaner.config import Config
from diskcleaner.core.classifier import FileClassifier
from diskcleaner.core.duplicate_finder import DuplicateFinder, DuplicateGroup
from diskcleaner.core.safety import SafetyChecker
from diskcleaner.core.scanner import DirectoryScanner, FileInfo


@dataclass
class CleanupReport:
    """
    Comprehensive cleanup analysis report.

    Contains categorized cleanup recommendations with statistics.
    """

    # Categorized files
    by_type: Dict[str, List[FileInfo]]
    by_risk: Dict[str, List[FileInfo]]
    by_age: Dict[str, List[FileInfo]]

    # Duplicate files
    duplicates: List[DuplicateGroup]

    # Statistics
    total_files: int
    total_size: int
    reclaimable_space: int

    # Scan metadata
    scan_time: float
    timestamp: float

    @property
    def safe_reclaimable(self) -> int:
        """Space that can be reclaimed from SAFE risk files."""
        return sum(f.size for f in self.by_risk.get("safe", []))

    @property
    def confirm_reclaimable(self) -> int:
        """Space that can be reclaimed from CONFIRM_NEEDED risk files."""
        return sum(f.size for f in self.by_risk.get("confirm_needed", []))

    @property
    def duplicate_reclaimable(self) -> int:
        """Space that can be reclaimed from duplicate files."""
        return sum(d.reclaimable_space for d in self.duplicates)

    @property
    def total_reclaimable(self) -> int:
        """Total space that can be reclaimed."""
        return self.safe_reclaimable + self.confirm_reclaimable + self.duplicate_reclaimable


class SmartCleanupEngine:
    """
    Smart cleanup engine integrating all core modules.

    Features:
    - Incremental scanning with cache
    - Three-dimensional classification (type, risk, age)
    - Duplicate file detection with adaptive strategy
    - Comprehensive safety checks
    - Detailed cleanup reports
    """

    def __init__(
        self,
        target_path: str,
        config: Optional[Config] = None,
        cache_enabled: bool = True,
    ):
        """
        Initialize smart cleanup engine.

        Args:
            target_path: Path to analyze.
            config: Configuration object.
            cache_enabled: Enable incremental scanning with cache.
        """
        self.target_path = Path(target_path).expanduser().resolve()
        self.config = config or Config.load()
        self.cache_enabled = cache_enabled

        # Initialize core modules
        self.scanner = DirectoryScanner(
            str(self.target_path), config=self.config, cache_enabled=cache_enabled
        )
        self.classifier = FileClassifier(config=self.config)
        self.duplicate_finder = DuplicateFinder(strategy="adaptive")
        self.safety = SafetyChecker(config=self.config)

    def analyze(
        self,
        include_duplicates: bool = True,
        safety_check: bool = True,
    ) -> CleanupReport:
        """
        Perform comprehensive cleanup analysis.

        Args:
            include_duplicates: Whether to detect duplicate files.
            safety_check: Whether to perform safety checks.

        Returns:
            CleanupReport with categorized recommendations.
        """
        start_time = time.time()

        # Step 1: Scan directory (incremental if cache enabled)
        if self.cache_enabled:
            files, _new_files, _changed_files = self.scanner.scan_incremental()
        else:
            files = self.scanner.scan()

        # Filter out directories
        file_list = [f for f in files if not f.is_dir]

        # Step 2: Three-dimensional classification
        classification = self.classifier.classify(file_list)

        # Step 3: Find duplicates (optional)
        duplicates = []
        if include_duplicates:
            duplicates = self.duplicate_finder.find_duplicates(file_list)

        # Step 4: Safety check (optional)
        if safety_check:
            # Check all files and mark safe/unsafe
            safety_results = self.safety.verify_all(file_list)

            # Filter out unsafe files from recommendations
            safe_files = {
                f.path for f, status in safety_results if status.value in ("safe", "confirm_needed")
            }

            # Filter classifications to only include safe files
            for category in classification["by_type"]:
                classification["by_type"][category] = [
                    f for f in classification["by_type"][category] if f.path in safe_files
                ]

            for risk_level in classification["by_risk"]:
                classification["by_risk"][risk_level] = [
                    f for f in classification["by_risk"][risk_level] if f.path in safe_files
                ]

            for age_group in classification["by_age"]:
                classification["by_age"][age_group] = [
                    f for f in classification["by_age"][age_group] if f.path in safe_files
                ]

            # Filter duplicates to only include safe files
            if duplicates:
                safe_duplicates = []
                for dup_group in duplicates:
                    safe_dup_files = [f for f in dup_group.files if f.path in safe_files]
                    if len(safe_dup_files) > 1:
                        # Create new duplicate group with only safe files
                        safe_duplicates.append(
                            DuplicateGroup(
                                files=safe_dup_files,
                                size=dup_group.size,
                                hash_value=dup_group.hash_value,
                            )
                        )
                duplicates = safe_duplicates

        # Step 5: Calculate statistics
        total_files = len(file_list)
        total_size = sum(f.size for f in file_list)
        reclaimable_space = (
            sum(f.size for f in classification["by_risk"].get("safe", []))
            + sum(f.size for f in classification["by_risk"].get("confirm_needed", []))
            + sum(d.reclaimable_space for d in duplicates)
        )

        scan_time = time.time() - start_time

        # Step 6: Create report
        report = CleanupReport(
            by_type=classification["by_type"],
            by_risk=classification["by_risk"],
            by_age=classification["by_age"],
            duplicates=duplicates,
            total_files=total_files,
            total_size=total_size,
            reclaimable_space=reclaimable_space,
            scan_time=scan_time,
            timestamp=time.time(),
        )

        return report

    def get_summary(self, report: CleanupReport) -> str:
        """
        Get human-readable summary of cleanup report.

        Args:
            report: CleanupReport to summarize.

        Returns:
            Formatted summary string.
        """
        lines = [
            "=" * 60,
            "磁盘清理分析报告",
            "=" * 60,
            f"扫描路径: {self.target_path}",
            f"扫描时间: {datetime.fromtimestamp(report.timestamp).strftime('%Y-%m-%d %H:%M:%S')}",
            f"耗时: {report.scan_time:.2f} 秒",
            "",
            "文件统计:",
            f"  总文件数: {report.total_files:,}",
            f"  总大小: {self._format_size(report.total_size)}",
            "",
            "可回收空间:",
            "  安全删除: {} ({:,} 文件)".format(
                self._format_size(report.safe_reclaimable),
                len(report.by_risk.get("safe", [])),
            ),
            "  需确认: {} ({:,} 文件)".format(
                self._format_size(report.confirm_reclaimable),
                len(report.by_risk.get("confirm_needed", [])),
            ),
            "  重复文件: {} ({} 组)".format(
                self._format_size(report.duplicate_reclaimable), len(report.duplicates)
            ),
            "  ————————————————",
            "  总计可回收: {}".format(self._format_size(report.total_reclaimable)),
            "",
        ]

        # Add breakdown by type if any files found
        if report.by_type:
            lines.append("按类型分类:")
            for file_type, type_files in sorted(
                report.by_type.items(),
                key=lambda x: sum(f.size for f in x[1]),
                reverse=True,
            ):
                if type_files:
                    total_size = sum(f.size for f in type_files)
                    size_str = self._format_size(total_size)
                    lines.append("  {}: {} 文件, {}".format(
                        file_type, len(type_files), size_str
                    ))

        # Add duplicate info if found
        if report.duplicates:
            lines.append("")
            lines.append("重复文件组 (前5组):")
            for i, dup in enumerate(report.duplicates[:5], 1):
                lines.append(
                    f"  {i}. {dup.count} 个重复文件, {self._format_size(dup.size)} 每个, "
                    f"可回收 {self._format_size(dup.reclaimable_space)}"
                )
                for j, file in enumerate(dup.files[:3], 1):
                    lines.append(f"     {j}. {file.path}")
                if len(dup.files) > 3:
                    lines.append(f"     ... 还有 {len(dup.files) - 3} 个文件")

        lines.append("")
        lines.append(60 * "=")

        return "\n".join(lines)

    def _format_size(self, size_bytes: int) -> str:
        """
        Format byte size to human-readable string.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string (e.g., "1.23 GB").
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                if unit == "B":
                    return f"{size_bytes:,} {unit}"
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def get_files_by_type(self, report: CleanupReport, file_type: str) -> List[FileInfo]:
        """
        Get files of a specific type from report.

        Args:
            report: CleanupReport.
            file_type: Type category name.

        Returns:
            List of FileInfo objects of that type.
        """
        return report.by_type.get(file_type, [])

    def get_files_by_risk(self, report: CleanupReport, risk_level: str) -> List[FileInfo]:
        """
        Get files of a specific risk level from report.

        Args:
            report: CleanupReport.
            risk_level: Risk level ('safe', 'confirm_needed', 'protected').

        Returns:
            List of FileInfo objects with that risk level.
        """
        return report.by_risk.get(risk_level, [])

    def get_files_by_age(self, report: CleanupReport, age_group: str) -> List[FileInfo]:
        """
        Get files of a specific age group from report.

        Args:
            report: CleanupReport.
            age_group: Age group name (e.g., "很旧 (90天以上)").

        Returns:
            List of FileInfo objects in that age group.
        """
        return report.by_age.get(age_group, [])
