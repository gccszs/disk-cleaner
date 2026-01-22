"""
Interactive user interface for cleanup operations.

Provides menu-driven interaction for viewing and selecting files to clean.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Tuple

from diskcleaner.core.scanner import FileInfo
from diskcleaner.core.smart_cleanup import CleanupReport, SmartCleanupEngine


class InteractiveCleanupUI:
    """
    Interactive interface for cleanup operations.

    Features:
    - View selection menu (type/risk/age/detailed)
    - Hierarchical display with date ranges and average age
    - File list detail view
    - User selection logic
    """

    def __init__(self, engine: SmartCleanupEngine):
        """
        Initialize interactive UI.

        Args:
            engine: SmartCleanupEngine instance.
        """
        self.engine = engine
        self.selected_files: Set[str] = set()

    def display_report_menu(self, report: CleanupReport) -> Optional[str]:
        """
        Display main menu for report viewing.

        Args:
            report: CleanupReport to display.

        Returns:
            Selected view option, or None if exited.
        """
        while True:
            print("\n" + "=" * 60)
            print("清理报告查看选项")
            print("=" * 60)
            print("1. 按类型查看")
            print("2. 按风险等级查看")
            print("3. 按时间查看")
            print("4. 查看重复文件")
            print("5. 详细列表")
            print("6. 查看统计摘要")
            print("0. 返回")
            print("=" * 60)

            choice = input("请选择 (0-6): ").strip()

            if choice == "0":
                return None
            elif choice in ("1", "2", "3", "4", "5", "6"):
                return choice
            else:
                print("无效选择，请重试")

    def view_by_type(self, report: CleanupReport) -> List[str]:
        """
        Display files grouped by type and allow selection.

        Args:
            report: CleanupReport to display.

        Returns:
            List of selected file paths.
        """
        selected: Set[str] = set()
        categories = sorted(
            report.by_type.items(),
            key=lambda x: sum(f.size for f in x[1]),
            reverse=True,
        )

        while True:
            print("\n" + "=" * 60)
            print("按类型分类")
            print("=" * 60)

            for idx, (category, files) in enumerate(categories, 1):
                if files:
                    total_size = sum(f.size for f in files)
                    selected_count = sum(1 for f in files if f.path in selected)
                    print(
                        f"{idx}. {category}: {len(files)} 文件, "
                        f"{self._format_size(total_size)} "
                        f"({selected_count}/{len(files)} 已选)"
                    )

            print("\n操作:")
            print("  输入编号查看类别详情")
            print("  a. 全选")
            print("  c. 清除选择")
            print("  s. 显示已选文件")
            print("  0. 返回")

            choice = input("\n请选择: ").strip().lower()

            if choice == "0":
                break
            elif choice == "a":
                # Select all
                for _, files in categories:
                    for f in files:
                        selected.add(f.path)
                print(f"\n已选择 {len(selected)} 个文件")
            elif choice == "c":
                # Clear selection
                selected.clear()
                print("\n已清除所有选择")
            elif choice == "s":
                # Show selected files
                self._display_selected_files(list(selected))
            elif choice.isdigit() and 1 <= int(choice) <= len(categories):
                # Show category details
                idx = int(choice) - 1
                category, files = categories[idx]
                self._display_category_details(category, files, selected)
            else:
                print("无效选择")

        return list(selected)

    def view_by_risk(self, report: CleanupReport) -> List[str]:
        """
        Display files grouped by risk level and allow selection.

        Args:
            report: CleanupReport to display.

        Returns:
            List of selected file paths.
        """
        selected: Set[str] = set()

        # Define risk level order and descriptions
        risk_levels = [
            ("safe", "安全删除", report.by_risk.get("safe", [])),
            (
                "confirm_needed",
                "需要确认",
                report.by_risk.get("confirm_needed", []),
            ),
            (
                "protected",
                "受保护",
                report.by_risk.get("protected", []),
            ),
        ]

        while True:
            print("\n" + "=" * 60)
            print("按风险等级分类")
            print("=" * 60)

            for idx, (key, label, files) in enumerate(risk_levels, 1):
                if files:
                    total_size = sum(f.size for f in files)
                    selected_count = sum(1 for f in files if f.path in selected)
                    print(
                        f"{idx}. {label}: {len(files)} 文件, "
                        f"{self._format_size(total_size)} "
                        f"({selected_count}/{len(files)} 已选)"
                    )

            print("\n操作:")
            print("  输入编号查看类别详情")
            print("  a. 全选安全文件")
            print("  c. 清除选择")
            print("  s. 显示已选文件")
            print("  0. 返回")

            choice = input("\n请选择: ").strip().lower()

            if choice == "0":
                break
            elif choice == "a":
                # Select all safe files
                for f in report.by_risk.get("safe", []):
                    selected.add(f.path)
                print(f"\n已选择 {len(selected)} 个文件")
            elif choice == "c":
                selected.clear()
                print("\n已清除所有选择")
            elif choice == "s":
                self._display_selected_files(list(selected))
            elif choice.isdigit() and 1 <= int(choice) <= len(risk_levels):
                idx = int(choice) - 1
                key, label, files = risk_levels[idx]
                if files:
                    self._display_category_details(label, files, selected)
            else:
                print("无效选择")

        return list(selected)

    def view_by_age(self, report: CleanupReport) -> List[str]:
        """
        Display files grouped by age and allow selection.

        Args:
            report: CleanupReport to display.

        Returns:
            List of selected file paths.
        """
        selected: Set[str] = set()
        age_groups = sorted(
            report.by_age.items(),
            key=lambda x: self._get_age_order(x[0]),
        )

        while True:
            print("\n" + "=" * 60)
            print("按时间分类")
            print("=" * 60)

            for idx, (age_group, files) in enumerate(age_groups, 1):
                if files:
                    total_size = sum(f.size for f in files)
                    avg_age = self._calculate_average_age(files)
                    selected_count = sum(1 for f in files if f.path in selected)
                    print(
                        f"{idx}. {age_group}: {len(files)} 文件, "
                        f"{self._format_size(total_size)}, "
                        f"平均年龄 {avg_age:.0f} 天 "
                        f"({selected_count}/{len(files)} 已选)"
                    )

            print("\n操作:")
            print("  输入编号查看类别详情")
            print("  a. 全选陈旧文件(>30天)")
            print("  c. 清除选择")
            print("  s. 显示已选文件")
            print("  0. 返回")

            choice = input("\n请选择: ").strip().lower()

            if choice == "0":
                break
            elif choice == "a":
                # Select old files (> 30 days)
                for age_group, files in age_groups:
                    if "30天以上" in age_group or "90" in age_group:
                        for f in files:
                            selected.add(f.path)
                print(f"\n已选择 {len(selected)} 个文件")
            elif choice == "c":
                selected.clear()
                print("\n已清除所有选择")
            elif choice == "s":
                self._display_selected_files(list(selected))
            elif choice.isdigit() and 1 <= int(choice) <= len(age_groups):
                idx = int(choice) - 1
                age_group, files = age_groups[idx]
                if files:
                    self._display_category_details(age_group, files, selected)
            else:
                print("无效选择")

        return list(selected)

    def view_duplicates(self, report: CleanupReport) -> List[Tuple[str, int]]:
        """
        Display duplicate file groups and allow selection.

        Args:
            report: CleanupReport to display.

        Returns:
            List of (file_path, group_index) tuples for selected duplicates.
        """
        selected: Set[Tuple[str, int]] = set()

        if not report.duplicates:
            print("\n未发现重复文件")
            return []

        while True:
            print("\n" + "=" * 60)
            print("重复文件组")
            print("=" * 60)

            for idx, dup_group in enumerate(report.duplicates[:20], 1):  # Show first 20
                selected_in_group = sum(1 for f in dup_group.files if (f.path, idx) in selected)
                print(
                    f"{idx}. {dup_group.count} 个重复文件, "
                    f"{self._format_size(dup_group.size)} 每个, "
                    f"可回收 {self._format_size(dup_group.reclaimable_space)} "
                    f"({selected_in_group}/{dup_group.count} 已选)"
                )

            if len(report.duplicates) > 20:
                print(f"\n... 还有 {len(report.duplicates) - 20} 组重复文件")

            print("\n操作:")
            print("  输入编号查看组详情")
            print("  a. 全选重复文件(每组保留1个)")
            print("  c. 清除选择")
            print("  s. 显示已选文件")
            print("  0. 返回")

            choice = input("\n请选择: ").strip().lower()

            if choice == "0":
                break
            elif choice == "a":
                # Select all duplicates (keeping 1 per group)
                for idx, dup_group in enumerate(report.duplicates, 1):
                    # Select all but the first file in each group
                    for file in dup_group.files[1:]:
                        selected.add((file.path, idx))
                print(f"\n已选择 {len(selected)} 个重复文件")
            elif choice == "c":
                selected.clear()
                print("\n已清除所有选择")
            elif choice == "s":
                self._display_selected_duplicates(
                    [(path, idx) for path, idx in selected], report.duplicates
                )
            elif choice.isdigit() and 1 <= int(choice) <= min(len(report.duplicates), 20):
                idx = int(choice)
                dup_group = report.duplicates[idx - 1]
                self._display_duplicate_group_details(idx, dup_group, selected)
            else:
                print("无效选择")

        return [(path, idx) for path, idx in selected]

    def view_detailed_list(self, report: CleanupReport) -> List[str]:
        """
        Display detailed list of all files with pagination.

        Args:
            report: CleanupReport to display.

        Returns:
            List of selected file paths.
        """
        selected: Set[str] = set()
        all_files = []
        for files in report.by_type.values():
            all_files.extend(files)

        # Sort by size (descending)
        all_files.sort(key=lambda f: f.size, reverse=True)

        page_size = 20
        current_page = 0
        total_pages = (len(all_files) + page_size - 1) // page_size

        while True:
            print("\n" + "=" * 60)
            print(f"详细文件列表 (第 {current_page + 1}/{total_pages} 页)")
            print("=" * 60)

            start = current_page * page_size
            end = min(start + page_size, len(all_files))
            page_files = all_files[start:end]

            print(f"{'序号':<6} {'文件名':<30} {'大小':>12} {'修改时间':<20} {'状态':<6}")
            print("-" * 80)

            for i, file in enumerate(page_files, start + 1):
                status = "✓" if file.path in selected else " "
                mtime_str = datetime.fromtimestamp(file.mtime).strftime("%Y-%m-%d %H:%M")
                print(
                    f"{i:<6} {file.name[:30]:<30} "
                    f"{self._format_size(file.size):>12} "
                    f"{mtime_str:<20} "
                    f"[{status}]"
                )

            print("\n操作:")
            print("  输入编号选择/取消选择文件")
            print("  n. 下一页")
            print("  p. 上一页")
            print("  a. 全选当前页")
            print("  c. 清除所有选择")
            print("  s. 显示已选文件")
            print("  0. 返回")

            choice = input(f"\n请选择 (第{current_page + 1}页): ").strip().lower()

            if choice == "0":
                break
            elif choice == "n" and current_page < total_pages - 1:
                current_page += 1
            elif choice == "p" and current_page > 0:
                current_page -= 1
            elif choice == "a":
                # Select all on current page
                for file in page_files:
                    selected.add(file.path)
                print(f"已选择当前页 {len(page_files)} 个文件")
            elif choice == "c":
                selected.clear()
                print("\n已清除所有选择")
            elif choice == "s":
                self._display_selected_files(list(selected))
            elif choice.isdigit():
                # Toggle file selection
                idx = int(choice) - 1
                if 0 <= idx < len(all_files):
                    file = all_files[idx]
                    if file.path in selected:
                        selected.remove(file.path)
                    else:
                        selected.add(file.path)
            else:
                print("无效选择")

        return list(selected)

    def _display_category_details(
        self, category: str, files: List[FileInfo], selected: Set[str]
    ) -> None:
        """Display details of files in a category."""
        print(f"\n{category} - 文件列表")
        print("-" * 80)

        for i, file in enumerate(files[:20], 1):  # Show first 20
            status = "✓" if file.path in selected else " "
            mtime_str = datetime.fromtimestamp(file.mtime).strftime("%Y-%m-%d %H:%M")
            print(
                f"{i:3}. [{status}] {file.name:<40} "
                f"{self._format_size(file.size):>12} "
                f"{mtime_str}"
            )

        if len(files) > 20:
            print(f"\n... 还有 {len(files) - 20} 个文件")

        print("\n操作: 输入编号选择/取消选择，或 0 返回")
        choice = input("请选择: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= min(len(files), 20):
            idx = int(choice) - 1
            file = files[idx]
            if file.path in selected:
                selected.remove(file.path)
                print(f"\n已取消选择: {file.name}")
            else:
                selected.add(file.path)
                print(f"\n已选择: {file.name}")

    def _display_duplicate_group_details(
        self, group_idx: int, dup_group, selected: Set[Tuple[str, int]]
    ) -> None:
        """Display details of duplicate files in a group."""
        print(f"\n重复文件组 #{group_idx}")
        print(f"文件大小: {self._format_size(dup_group.size)}")
        print(f"哈希值: {dup_group.hash_value[:16]}...")
        print("-" * 80)

        for i, file in enumerate(dup_group.files, 1):
            status = "✓" if (file.path, group_idx) in selected else " "
            print(f"{i}. [{status}] {file.path}")

        print("\n操作: 输入编号选择/取消选择文件，或 0 返回")
        choice = input("请选择: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(dup_group.files):
            idx = int(choice) - 1
            file = dup_group.files[idx]
            if (file.path, group_idx) in selected:
                selected.remove((file.path, group_idx))
                print(f"\n已取消选择: {file.path}")
            else:
                selected.add((file.path, group_idx))
                print(f"\n已选择: {file.path}")

    def _display_selected_files(self, selected_paths: List[str]) -> None:
        """Display list of selected files."""
        if not selected_paths:
            print("\n未选择任何文件")
            return

        print(f"\n已选择的文件 ({len(selected_paths)} 个):")
        print("-" * 80)

        total_size = 0
        for i, path in enumerate(selected_paths[:20], 1):
            file = Path(path)
            print(f"{i:3}. {path}")
            if file.exists():
                total_size += file.stat().st_size

        if len(selected_paths) > 20:
            print(f"\n... 还有 {len(selected_paths) - 20} 个文件")

        print(f"\n总计: {len(selected_paths)} 个文件, {self._format_size(total_size)}")

    def _display_selected_duplicates(
        self, selected: List[Tuple[str, int]], duplicates: list
    ) -> None:
        """Display list of selected duplicate files."""
        if not selected:
            print("\n未选择任何重复文件")
            return

        print(f"\n已选择的重复文件 ({len(selected)} 个):")
        print("-" * 80)

        for path, group_idx in selected[:20]:
            print(f"组 #{group_idx}: {path}")

        if len(selected) > 20:
            print(f"\n... 还有 {len(selected) - 20} 个文件")

    def _calculate_average_age(self, files: List[FileInfo]) -> float:
        """Calculate average age of files in days."""
        if not files:
            return 0.0

        now = datetime.now()
        total_age = sum((now - datetime.fromtimestamp(f.mtime)).days for f in files)
        return total_age / len(files)

    def _get_age_order(self, age_group: str) -> int:
        """Get sort order for age groups."""
        if "7天" in age_group:
            return 1
        elif "30天" in age_group:
            return 2
        elif "90天" in age_group:
            return 3
        else:
            return 4

    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                if unit == "B":
                    return f"{size_bytes:,} {unit}"
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def confirm_and_cleanup(
        self,
        files_to_delete: List[str],
        dry_run: bool = True,
        backup: bool = True,
    ) -> bool:
        """
        Display cleanup summary and request final confirmation.

        Args:
            files_to_delete: List of file paths to delete.
            dry_run: If True, only show what would be deleted.
            backup: If True, create backups before deleting.

        Returns:
            True if cleanup was performed, False if cancelled.
        """
        if not files_to_delete:
            print("\n未选择要删除的文件")
            return False

        # Calculate statistics
        total_size = 0
        valid_files = []

        for file_path in files_to_delete:
            path = Path(file_path)
            if path.exists():
                try:
                    total_size += path.stat().st_size
                    valid_files.append(file_path)
                except OSError:
                    pass

        if not valid_files:
            print("\n选定的文件不存在或无法访问")
            return False

        # Display cleanup summary
        self._display_cleanup_summary(valid_files, total_size, dry_run)

        # Request final confirmation
        if dry_run:
            print("\n[预览模式] 不会实际删除文件")
            print("如要执行删除，请重新运行时不使用 --dry-run 参数")
            return False

        confirmation = input("\n确认删除以上文件？(输入 YES 继续): ").strip()

        if confirmation != "YES":
            print("\n操作已取消")
            return False

        # Perform cleanup
        print("\n开始清理...")
        success = self._execute_cleanup(valid_files, backup)

        if success:
            print("\n✓ 清理完成！")
            print("  删除文件数: {}".format(len(valid_files)))
            print("  释放空间: {}".format(self._format_size(total_size)))
            return True
        else:
            print("\n✗ 清理过程中出现错误")
            return False

    def _display_cleanup_summary(self, files: List[str], total_size: int, dry_run: bool) -> None:
        """Display cleanup summary before confirmation."""
        print("\n" + "=" * 60)
        print("清理摘要")
        print("=" * 60)
        print("将删除 {} 个文件".format(len(files)))
        print("释放空间: {}".format(self._format_size(total_size)))
        print("模式: {}".format(
            "预览 (不会实际删除)" if dry_run else "执行删除"
        ))
        print("=" * 60)

        # Show first 20 files
        print("\n文件列表:")
        for i, file_path in enumerate(files[:20], 1):
            path = Path(file_path)
            size = path.stat().st_size if path.exists() else 0
            print(f"{i:3}. {file_path} ({self._format_size(size)})")

        if len(files) > 20:
            print(f"\n... 还有 {len(files) - 20} 个文件")

        print("\n" + "=" * 60)

    def _execute_cleanup(self, files: List[str], backup: bool) -> bool:
        """
        Execute cleanup operation.

        Args:
            files: List of file paths to delete.
            backup: If True, create backups before deleting.

        Returns:
            True if all files were processed successfully.
        """
        from diskcleaner.core.safety import SafetyChecker

        safety_checker = SafetyChecker()
        success_count = 0
        failed_files = []

        for file_path in files:
            try:
                path = Path(file_path)

                # Create backup if requested
                if backup:
                    backup_path = safety_checker.backup_file(file_path)
                    if backup_path:
                        pass  # Backup created successfully

                # Delete file
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()

                success_count += 1

                # Log deletion
                self._log_deletion(file_path)

            except OSError as e:
                failed_files.append((file_path, str(e)))

        # Report results
        if failed_files:
            print(f"\n警告: {len(failed_files)} 个文件删除失败:")
            for file_path, error in failed_files[:10]:
                print(f"  {file_path}: {error}")
            if len(failed_files) > 10:
                print(f"  ... 还有 {len(failed_files) - 10} 个失败")

        return len(failed_files) == 0

    def _log_deletion(self, file_path: str) -> None:
        """Log file deletion to cleanup log."""
        log_dir = Path.home() / ".disk-cleaner" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "cleanup.log"

        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | DELETED | {file_path}\n"

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except OSError:
            pass  # Silently fail if can't write log
