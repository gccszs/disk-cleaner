#!/usr/bin/env python3
"""
Interactive Wizard for Disk Cleanup

A comprehensive interactive wizard that guides users through the disk cleanup process.
Features:
- Welcome screen with safety information
- Scan mode selection (Quick/Standard/Deep/Progressive/Custom)
- Categorized display with risk levels
- Multi-level confirmation process
- ASCII-safe output for terminals

This script integrates with existing diskcleaner components:
- InteractiveCleanupUI for display and selection
- ProgressBar for progress indication
- DirectoryScanner for file scanning
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from diskcleaner.config import Config
from diskcleaner.core.interactive import InteractiveCleanupUI
from diskcleaner.core.progress import ProgressBar, IndeterminateProgress
from diskcleaner.core.scanner import DirectoryScanner
from diskcleaner.core.smart_cleanup import SmartCleanupEngine, CleanupReport


class InteractiveWizard:
    """
    Interactive wizard for disk cleanup operations.

    Provides a user-friendly, step-by-step interface for cleaning disk space.
    """

    def __init__(self, target_path: str = "."):
        """
        Initialize the interactive wizard.

        Args:
            target_path: Path to analyze (default: current directory)
        """
        self.target_path = Path(target_path).expanduser().resolve()
        self.config = Config.load()
        self.engine = SmartCleanupEngine(str(self.target_path), self.config)
        self.ui = InteractiveCleanupUI(self.engine)
        self.scan_mode = None
        self.selected_files: Set[str] = set()

    def run(self) -> bool:
        """
        Run the complete wizard workflow.

        Returns:
            True if cleanup was performed, False otherwise.
        """
        try:
            # Step 1: Welcome screen
            if not self._show_welcome():
                return False

            # Step 2: Select scan mode
            self.scan_mode = self._select_scan_mode()
            if not self.scan_mode:
                return False

            # Step 3: Perform scan
            report = self._perform_scan()
            if not report:
                print("\n扫描未返回结果")
                return False

            # Step 4: Display and select files
            self._display_report_and_select(report)

            # Step 5: Multi-level confirmation
            if not self.selected_files:
                print("\n未选择任何文件")
                return False

            if not self._confirm_cleanup():
                return False

            # Step 6: Execute cleanup
            return self._execute_cleanup()

        except KeyboardInterrupt:
            print("\n\n操作已取消")
            return False
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _show_welcome(self) -> bool:
        """
        Display welcome screen with safety information.

        Returns:
            True if user wants to continue, False otherwise.
        """
        print("\n" + "=" * 60)
        print("   磁盘清理向导")
        print("=" * 60)
        print()
        print("欢迎使用磁盘清理工具！")
        print()
        print("功能特性:")
        print("  - 智能分类：按类型、风险、时间三维分析")
        print("  - 安全第一：多重确认，误删保护")
        print("  - 重复文件：快速识别并清理重复内容")
        print("  - 增量扫描：缓存机制，提升性能")
        print()
        print("安全承诺:")
        print("  1. 不会删除任何文件，除非您明确确认")
        print("  2. 所有操作都需要您输入 'YES' 确认")
        print("  3. 危险操作需要额外输入 'I UNDERSTAND'")
        print("  4. 所有删除操作都会记录日志")
        print("  5. 可选备份功能，保护重要文件")
        print()
        print("=" * 60)

        choice = input("\n是否继续？ [Y/n]: ").strip().lower()
        return choice in ("", "y", "yes")

    def _select_scan_mode(self) -> Optional[str]:
        """
        Display scan mode selection menu.

        Returns:
            Selected scan mode, or None if cancelled.
        """
        while True:
            print("\n" + "=" * 60)
            print("   选择扫描模式")
            print("=" * 60)
            print()
            print("1. 快速扫描 (1秒)")
            print("   - 扫描常见临时文件位置")
            print("   - 适合日常清理")
            print()
            print("2. 标准扫描 (2分钟)")
            print("   - 全面扫描当前目录")
            print("   - 包含子目录")
            print("   - 推荐模式")
            print()
            print("3. 深度扫描 (无限制)")
            print("   - 扫描所有文件")
            print("   - 可能需要较长时间")
            print("   - 适合彻底清理")
            print()
            print("4. 渐进式扫描")
            print("   - 使用缓存增量扫描")
            print("   - 后续扫描更快")
            print("   - 适合定期清理")
            print()
            print("5. 自定义扫描")
            print("   - 自定义扫描参数")
            print("   - 高级选项")
            print()
            print("0. 退出")
            print()
            print("=" * 60)

            choice = input("\n请选择 (0-5): ").strip()

            if choice == "0":
                return None
            elif choice in ("1", "2", "3", "4", "5"):
                return self._get_scan_mode_config(choice)
            else:
                print("无效选择，请重试")

    def _get_scan_mode_config(self, mode: str) -> str:
        """
        Get scan mode configuration.

        Args:
            mode: Mode number (1-5)

        Returns:
            Scan mode identifier.
        """
        modes = {
            "1": "quick",
            "2": "standard",
            "3": "deep",
            "4": "progressive",
            "5": "custom",
        }
        return modes.get(mode, "standard")

    def _perform_scan(self) -> Optional[CleanupReport]:
        """
        Perform the scan based on selected mode.

        Returns:
            CleanupReport if successful, None otherwise.
        """
        print(f"\n正在扫描: {self.target_path}")
        print(f"扫描模式: {self._get_scan_mode_name(self.scan_mode)}")
        print()

        # Configure scanner based on mode
        if self.scan_mode == "quick":
            # Quick scan: limit files and time
            scanner = DirectoryScanner(
                str(self.target_path),
                config=self.config,
                max_files=10000,
                max_seconds=1,
                cache_enabled=False,
            )
        elif self.scan_mode == "standard":
            # Standard scan: balanced limits
            scanner = DirectoryScanner(
                str(self.target_path),
                config=self.config,
                max_files=100000,
                max_seconds=120,
                cache_enabled=True,
            )
        elif self.scan_mode == "deep":
            # Deep scan: no limits
            scanner = DirectoryScanner(
                str(self.target_path),
                config=self.config,
                max_files=None,
                max_seconds=None,
                cache_enabled=True,
            )
        elif self.scan_mode == "progressive":
            # Progressive scan: use incremental
            scanner = DirectoryScanner(
                str(self.target_path),
                config=self.config,
                cache_enabled=True,
            )
        else:  # custom
            # Ask user for custom parameters
            max_files = self._ask_custom_param("最大文件数 (默认无限制): ", None)
            max_seconds = self._ask_custom_param("最大扫描时间/秒 (默认无限制): ", None)

            scanner = DirectoryScanner(
                str(self.target_path),
                config=self.config,
                max_files=max_files,
                max_seconds=max_seconds,
                cache_enabled=True,
            )

        # Perform scan with progress indication
        try:
            # Use indeterminate progress for scanning
            with IndeterminateProgress("扫描中", enable=True) as progress:
                # Monkey-patch the scanner to update progress
                original_scan = scanner.scan_generator

                def scan_with_progress():
                    for file_info in original_scan():
                        progress.tick(f"扫描: {file_info.name[:30]}")
                        yield file_info

                scanner.scan_generator = scan_with_progress

                # Analyze with engine
                report = self.engine.analyze()

            print()  # Newline after progress

            # Show scan summary
            self._show_scan_summary(report, scanner)
            return report

        except Exception as e:
            print(f"\n扫描失败: {e}")
            return None

    def _ask_custom_param(self, prompt: str, default: Optional[int]) -> Optional[int]:
        """Ask user for custom parameter."""
        while True:
            response = input(prompt).strip()
            if not response:
                return default
            try:
                value = int(response)
                if value <= 0:
                    print("请输入正整数")
                    continue
                return value
            except ValueError:
                print("请输入有效的数字")

    def _get_scan_mode_name(self, mode: str) -> str:
        """Get display name for scan mode."""
        names = {
            "quick": "快速扫描",
            "standard": "标准扫描",
            "deep": "深度扫描",
            "progressive": "渐进式扫描",
            "custom": "自定义扫描",
        }
        return names.get(mode, "未知模式")

    def _show_scan_summary(self, report: CleanupReport, scanner: DirectoryScanner):
        """Display scan summary."""
        total_files = sum(len(files) for files in report.by_type.values())
        total_size = sum(
            sum(f.size for f in files)
            for files in report.by_type.values()
        )

        print("\n" + "=" * 60)
        print("   扫描完成")
        print("=" * 60)
        print(f"扫描文件数: {total_files:,}")
        print(f"总大小: {self._format_size(total_size)}")

        if scanner.stopped_early:
            print(f"\n注意: 扫描提前停止 ({scanner.stop_reason})")
            print("如需完整扫描，请选择 '深度扫描' 模式")

        print(f"发现重复文件组: {len(report.duplicates)}")
        print("=" * 60)

    def _display_report_and_select(self, report: CleanupReport):
        """
        Display report and let user select files.

        Args:
            report: CleanupReport to display.
        """
        while True:
            # Main menu
            choice = self.ui.display_report_menu(report)
            if choice is None:
                break

            # Display selected view and collect selections
            if choice == "1":  # By type
                selected = self.ui.view_by_type(report)
            elif choice == "2":  # By risk
                selected = self.ui.view_by_risk(report)
            elif choice == "3":  # By age
                selected = self.ui.view_by_age(report)
            elif choice == "4":  # Duplicates
                selected_dup = self.ui.view_duplicates(report)
                # Convert duplicate selections to file paths
                selected = [path for path, _ in selected_dup]
            elif choice == "5":  # Detailed list
                selected = self.ui.view_detailed_list(report)
            elif choice == "6":  # Summary
                self._show_summary_statistics(report)
                continue

            # Merge selections
            if selected:
                self.selected_files.update(selected)
                print(f"\n当前已选择 {len(self.selected_files)} 个文件")

    def _show_summary_statistics(self, report: CleanupReport):
        """Display summary statistics."""
        print("\n" + "=" * 60)
        print("   统计摘要")
        print("=" * 60)

        # Count by risk level
        risk_counts = {}
        for risk, files in report.by_risk.items():
            risk_counts[risk] = len(files)

        print("\n按风险等级:")
        for risk, count in sorted(risk_counts.items(), key=lambda x: -x[1]):
            emoji = self._get_risk_emoji(risk)
            print(f"  {emoji} {risk}: {count} 文件")

        # Count by type
        print("\n按类型 (前5):")
        type_items = sorted(
            report.by_type.items(),
            key=lambda x: sum(f.size for f in x[1]),
            reverse=True
        )[:5]
        for category, files in type_items:
            size = sum(f.size for f in files)
            print(f"  - {category}: {len(files)} 文件, {self._format_size(size)}")

        # Duplicates
        if report.duplicates:
            dup_space = sum(d.reclaimable_space for d in report.duplicates)
            print(f"\n重复文件: {len(report.duplicates)} 组, 可回收 {self._format_size(dup_space)}")

        print("=" * 60)

    def _get_risk_emoji(self, risk: str) -> str:
        """Get emoji for risk level (for agent reports only)."""
        emojis = {
            "safe": "OK",       # Green
            "confirm_needed": "!",  # Yellow
            "protected": "X",   # Red
        }
        return emojis.get(risk, "?")

    def _confirm_cleanup(self) -> bool:
        """
        Multi-level confirmation process.

        Returns:
            True if user confirms, False otherwise.
        """
        if not self.selected_files:
            return False

        # Analyze risk levels
        risk_breakdown = self._analyze_selection_risk()

        # Show cleanup summary grouped by risk
        print("\n" + "=" * 60)
        print("   清理确认")
        print("=" * 60)

        print("\n即将删除的文件按风险分组:")

        # Safe files
        if "safe" in risk_breakdown:
            files, size = risk_breakdown["safe"]
            print(f"\n  [OK] 安全级别: {len(files)} 文件, {self._format_size(size)}")
            print("      临时文件、缓存等，可安全删除")

        # Warning level
        if "confirm_needed" in risk_breakdown:
            files, size = risk_breakdown["confirm_needed"]
            print(f"\n  [!] 警告级别: {len(files)} 文件, {self._format_size(size)}")
            print("      开发工具索引、构建产物等，请确认")

        # Dangerous level
        if "protected" in risk_breakdown:
            files, size = risk_breakdown["protected"]
            print(f"\n  [X] 危险级别: {len(files)} 文件, {self._format_size(size)}")
            print("      用户文档、重要文件等，需逐个确认")

            # Require "I UNDERSTAND" for dangerous files
            print("\n  警告: 您选择了危险级别的文件！")
            confirm = input("  输入 'I UNDERSTAND' 继续: ").strip()
            if confirm != "I UNDERSTAND":
                print("\n操作已取消")
                return False

        # Total summary
        total_size = sum(size for _, size in risk_breakdown.values())
        total_files = sum(len(files) for files, _ in risk_breakdown.values())

        print("\n" + "-" * 60)
        print(f"总计: {total_files} 文件, {self._format_size(total_size)}")
        print("=" * 60)

        # Final confirmation
        print("\n此操作将永久删除选定的文件！")
        confirm = input("确认删除？输入 'YES' 继续: ").strip()

        return confirm == "YES"

    def _analyze_selection_risk(self) -> Dict[str, Tuple[List[Path], int]]:
        """
        Analyze risk levels of selected files.

        Returns:
            Dictionary mapping risk level to (files, total_size).
        """
        # Get full report to check risk levels
        report = self.engine.analyze()

        # Build risk mapping
        risk_map = {}
        for risk, files in report.by_risk.items():
            for file in files:
                risk_map[file.path] = risk

        # Group selected files by risk
        result = {
            "safe": ([], 0),
            "confirm_needed": ([], 0),
            "protected": ([], 0),
        }

        for file_path in self.selected_files:
            path = Path(file_path)
            risk = risk_map.get(file_path, "confirm_needed")

            if path.exists():
                try:
                    size = path.stat().st_size
                    result[risk][0].append(path)
                    result[risk] = (result[risk][0], result[risk][1] + size)
                except OSError:
                    pass

        # Remove empty categories
        return {k: v for k, v in result.items() if v[0]}

    def _execute_cleanup(self) -> bool:
        """
        Execute the cleanup operation.

        Returns:
            True if successful, False otherwise.
        """
        print("\n开始清理...")

        # Use the UI's cleanup method
        success = self.ui.confirm_and_cleanup(
            list(self.selected_files),
            dry_run=False,
            backup=True,
        )

        if success:
            print("\n清理完成！")
            print(f"  删除文件: {len(self.selected_files)} 个")

        return success

    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                if unit == "B":
                    return f"{size_bytes:,} {unit}"
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Interactive wizard for disk cleanup"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to analyze (default: current directory)"
    )

    args = parser.parse_args()

    # Run wizard
    wizard = InteractiveWizard(args.path)
    success = wizard.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
