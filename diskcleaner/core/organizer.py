"""
File organizer with plan generation and execution.

Integrates scanner, classifier, and archive rules to
organize files intelligently with dry-run support.
"""

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from diskcleaner.config import Config
from diskcleaner.core.classifier import FileClassifier
from diskcleaner.core.rules.archive_rules import RuleEngine
from diskcleaner.core.scanner import DirectoryScanner, FileInfo
from diskcleaner.core.safety import SafetyChecker


@dataclass
class OrganizationAction:
    """
    A single file organization action.

    Attributes:
        source_path: Source file path.
        destination_path: Destination file path.
        action_type: Type of action (move, copy, skip).
        reason: Reason for action (e.g., rule name, skip reason).
        file_info: FileInfo object for the file.
    """

    source_path: str
    destination_path: str
    action_type: str  # "move", "copy", "skip"
    reason: str
    file_info: FileInfo

    def __str__(self) -> str:
        """String representation for ASCII safety."""
        return f"{self.action_type.upper()}: {self.source_path} -> {self.destination_path}"


@dataclass
class OrganizationPlan:
    """
    Complete organization plan.

    Attributes:
        target_path: Base path being organized.
        strategy: Strategy name used.
        actions: List of actions to perform.
        total_size: Total size of files to organize.
        file_count: Number of files to organize.
        created_at: Timestamp when plan was created.
    """

    target_path: str
    strategy: str
    actions: List[OrganizationAction] = field(default_factory=list)
    total_size: int = 0
    file_count: int = 0
    created_at: float = field(default_factory=datetime.now().timestamp)

    def add_action(self, action: OrganizationAction):
        """
        Add an action to the plan.

        Args:
            action: OrganizationAction to add.
        """
        self.actions.append(action)
        self.file_count += 1
        self.total_size += action.file_info.size

    def get_summary(self) -> Dict[str, int]:
        """
        Get summary statistics.

        Returns:
            Dictionary with action counts and sizes.
        """
        summary = {
            "total_actions": len(self.actions),
            "move_actions": 0,
            "copy_actions": 0,
            "skip_actions": 0,
            "total_size": self.total_size,
            "file_count": self.file_count,
        }

        for action in self.actions:
            if action.action_type == "move":
                summary["move_actions"] += 1
            elif action.action_type == "copy":
                summary["copy_actions"] += 1
            elif action.action_type == "skip":
                summary["skip_actions"] += 1

        return summary

    def get_actions_by_destination(self) -> Dict[str, List[OrganizationAction]]:
        """
        Group actions by destination.

        Returns:
            Dictionary mapping destinations to action lists.
        """
        grouped: Dict[str, List[OrganizationAction]] = {}

        for action in self.actions:
            if action.destination_path not in grouped:
                grouped[action.destination_path] = []
            grouped[action.destination_path].append(action)

        return grouped


class FileOrganizer:
    """
    File organizer with plan generation and execution.

    Features:
    - Multiple organization strategies
    - Dry-run mode for preview
    - Safety checks before operations
    - Progress tracking
    - Conflict detection
    """

    def __init__(
        self,
        target_path: str,
        strategy: str = "desktop",
        config: Optional[Config] = None,
        dry_run: bool = True,
    ):
        """
        Initialize file organizer.

        Args:
            target_path: Path to organize.
            strategy: Organization strategy name.
            config: Configuration object.
            dry_run: If True, don't actually move files (preview mode).
        """
        self.target_path = Path(target_path).expanduser().resolve()
        self.strategy_name = strategy
        self.config = config or Config.load()
        self.dry_run = dry_run

        # Initialize components
        self.scanner = DirectoryScanner(str(self.target_path), config=self.config)
        self.classifier = FileClassifier(config=self.config)
        self.safety_checker = SafetyChecker(config=self.config)
        self.rule_engine = RuleEngine()

        # Validate strategy
        if not self.rule_engine.get_strategy(strategy):
            raise ValueError(f"Unknown strategy: {strategy}")

        # Statistics
        self.organized_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def scan_files(self) -> List[FileInfo]:
        """
        Scan target directory for files.

        Returns:
            List of FileInfo objects.
        """
        return self.scanner.scan()

    def generate_plan(
        self,
        files: Optional[List[FileInfo]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> OrganizationPlan:
        """
        Generate organization plan.

        Args:
            files: List of FileInfo objects (scans if None).
            progress_callback: Optional callback for progress updates.

        Returns:
            OrganizationPlan with actions to perform.
        """
        # Scan files if not provided
        if files is None:
            files = self.scan_files()

        plan = OrganizationPlan(
            target_path=str(self.target_path),
            strategy=self.strategy_name,
        )

        # Get strategy
        strategy = self.rule_engine.get_strategy(self.strategy_name)
        if not strategy:
            raise ValueError(f"Unknown strategy: {self.strategy_name}")

        # Process each file
        total_files = len(files)

        for i, file in enumerate(files):
            # Skip directories
            if file.is_dir:
                continue

            # Update progress
            if progress_callback:
                progress_callback(i + 1, total_files)

            # Get destination from strategy
            destination = strategy.organize_file(file)

            if destination is None:
                # No rule matched - skip
                action = OrganizationAction(
                    source_path=file.path,
                    destination_path="",
                    action_type="skip",
                    reason="No matching rule",
                    file_info=file,
                )
                plan.add_action(action)
                continue

            # Build full destination path
            dest_path = self.target_path / destination

            # Check for conflicts
            conflict_reason = self._check_conflicts(file, dest_path)
            if conflict_reason:
                action = OrganizationAction(
                    source_path=file.path,
                    destination_path=str(dest_path),
                    action_type="skip",
                    reason=f"Conflict: {conflict_reason}",
                    file_info=file,
                )
                plan.add_action(action)
                continue

            # Safety check
            safety_status = self.safety_checker.verify_file(file)
            if safety_status.value != "safe":
                action = OrganizationAction(
                    source_path=file.path,
                    destination_path=str(dest_path),
                    action_type="skip",
                    reason=f"Safety check: {safety_status.value}",
                    file_info=file,
                )
                plan.add_action(action)
                continue

            # Create move action
            dest_file_path = dest_path / file.name
            action = OrganizationAction(
                source_path=file.path,
                destination_path=str(dest_file_path),
                action_type="move",
                reason=f"Rule: {destination}",
                file_info=file,
            )
            plan.add_action(action)

        return plan

    def _check_conflicts(self, file: FileInfo, dest_path: Path) -> Optional[str]:
        """
        Check for file conflicts at destination.

        Args:
            file: FileInfo object.
            dest_path: Destination directory path.

        Returns:
            Conflict reason string, or None if no conflict.
        """
        dest_file_path = dest_path / file.name

        # Check if destination file exists
        if dest_file_path.exists():
            # Check if it's the same file
            if str(dest_file_path) == file.path:
                return "Source and destination are the same"

            # Check if files are identical
            if dest_file_path.stat().st_size == file.size:
                return "Duplicate file (same size)"

            return "File with same name exists"

        return None

    def execute_plan(
        self,
        plan: OrganizationPlan,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[int, int, int]:
        """
        Execute organization plan.

        Args:
            plan: OrganizationPlan to execute.
            progress_callback: Optional callback for progress updates.

        Returns:
            Tuple of (organized_count, skipped_count, error_count).
        """
        organized = 0
        skipped = 0
        errors = 0

        total_actions = len(plan.actions)

        for i, action in enumerate(plan.actions):
            # Update progress
            if progress_callback:
                progress_callback(i + 1, total_actions)

            if action.action_type == "skip":
                skipped += 1
                continue

            if action.action_type == "move":
                try:
                    if not self.dry_run:
                        self._move_file(action)
                    organized += 1
                except Exception as e:
                    errors += 1
                    # Log error but continue
                    print(f"Error moving {action.source_path}: {e}")

            elif action.action_type == "copy":
                try:
                    if not self.dry_run:
                        self._copy_file(action)
                    organized += 1
                except Exception as e:
                    errors += 1
                    print(f"Error copying {action.source_path}: {e}")

        return organized, skipped, errors

    def _move_file(self, action: OrganizationAction):
        """
        Move a file to its destination.

        Args:
            action: OrganizationAction with move operation.
        """
        source = Path(action.source_path)
        destination = Path(action.destination_path)

        # Create destination directory
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Handle duplicates
        if destination.exists():
            # Add timestamp to filename
            stem = source.stem
            suffix = source.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{stem}_{timestamp}{suffix}"
            destination = destination.parent / new_name

        # Move file
        shutil.move(str(source), str(destination))

    def _copy_file(self, action: OrganizationAction):
        """
        Copy a file to its destination.

        Args:
            action: OrganizationAction with copy operation.
        """
        source = Path(action.source_path)
        destination = Path(action.destination_path)

        # Create destination directory
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Handle duplicates
        if destination.exists():
            # Add timestamp to filename
            stem = source.stem
            suffix = source.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{stem}_{timestamp}{suffix}"
            destination = destination.parent / new_name

        # Copy file
        shutil.copy2(str(source), str(destination))

    def preview_organization(
        self,
        max_files: int = 50,
    ) -> str:
        """
        Preview organization plan (ASCII-safe output).

        Args:
            max_files: Maximum number of files to show in preview.

        Returns:
            Formatted preview string.
        """
        # Generate plan
        plan = self.generate_plan()

        # Build preview
        lines = []
        lines.append("=" * 80)
        lines.append(f"FILE ORGANIZATION PREVIEW")
        lines.append(f"Strategy: {self.strategy_name}")
        lines.append(f"Target: {self.target_path}")
        lines.append(f"Mode: {'DRY RUN (no changes)' if self.dry_run else 'EXECUTE'}")
        lines.append("=" * 80)
        lines.append("")

        # Show summary
        summary = plan.get_summary()
        lines.append("SUMMARY:")
        lines.append(f"  Total files to process: {summary['file_count']}")
        lines.append(f"  Files to organize: {summary['move_actions'] + summary['copy_actions']}")
        lines.append(f"  Files to skip: {summary['skip_actions']}")
        lines.append(f"  Total size: {self._format_size(summary['total_size'])}")
        lines.append("")

        # Show actions by destination
        grouped = plan.get_actions_by_destination()

        lines.append("DESTINATIONS:")
        for dest, actions in sorted(grouped.items()):
            if dest:  # Skip empty destinations
                dest_size = sum(a.file_info.size for a in actions)
                lines.append(f"  {dest}: {len(actions)} files ({self._format_size(dest_size)})")
        lines.append("")

        # Show sample actions
        lines.append(f"SAMPLE ACTIONS (showing first {min(max_files, len(plan.actions))}):")
        for i, action in enumerate(plan.actions[:max_files]):
            lines.append(f"  [{i+1}] {action}")

        if len(plan.actions) > max_files:
            remaining = len(plan.actions) - max_files
            lines.append(f"  ... and {remaining} more actions")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _format_size(self, size_bytes: int) -> str:
        """
        Format size in human-readable format.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string.
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def organize(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[int, int, int]:
        """
        Organize files (generate and execute plan).

        Args:
            progress_callback: Optional callback for progress updates.

        Returns:
            Tuple of (organized_count, skipped_count, error_count).
        """
        # Generate plan
        plan = self.generate_plan(progress_callback=progress_callback)

        # Execute plan
        organized, skipped, errors = self.execute_plan(
            plan,
            progress_callback=progress_callback,
        )

        # Update statistics
        self.organized_count = organized
        self.skipped_count = skipped
        self.error_count = errors

        return organized, skipped, errors

    def get_statistics(self) -> Dict[str, int]:
        """
        Get organization statistics.

        Returns:
            Dictionary with statistics.
        """
        return {
            "organized": self.organized_count,
            "skipped": self.skipped_count,
            "errors": self.error_count,
        }
