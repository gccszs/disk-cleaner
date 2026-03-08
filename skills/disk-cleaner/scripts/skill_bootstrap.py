#!/usr/bin/env python3
"""
Skill Bootstrap Module - 智能引导模块

这个模块确保 disk-cleaner 技能包能够在任何环境下正确运行，
无需预先安装 diskcleaner 包。

功能：
- 自动检测技能包位置
- 动态添加模块路径到 sys.path
- 跨平台兼容性处理
- 优雅的错误处理和降级方案
- 环境检测和诊断信息
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, Tuple, Any


# emoji 的安全替代字符（用于不支持 emoji 的环境）
EMOJI_FALLBACKS = {
    "✅": "[OK]",
    "❌": "[X]",
    "⚠️": "[!]",
    "🎉": "[*]",
    "📋": "[i]",
    "📁": "[DIR]",
    "📦": "[PKG]",
    "🔐": "[KEY]",
    "🧪": "[TEST]",
    "🔍": "[?]",
    "💡": "[i]",
    "❓": "[?]",
}


def safe_print(message: str, file=None):
    """
    安全打印函数，自动处理编码问题

    在 Windows GBK 等不支持 emoji 的环境下，自动替换为 ASCII 字符
    """
    if file is None:
        file = sys.stdout

    try:
        print(message, file=file)
        file.flush()
    except UnicodeEncodeError:
        # 编码错误，替换 emoji 和中文
        safe_message = message
        for emoji, fallback in EMOJI_FALLBACKS.items():
            safe_message = safe_message.replace(emoji, fallback)

        # 如果还有编码问题，尝试替换所有非 ASCII 字符
        try:
            print(safe_message, file=file)
            file.flush()
        except UnicodeEncodeError:
            # 最后的回退：只保留 ASCII
            safe_message = safe_message.encode("ascii", "replace").decode("ascii")
            print(safe_message, file=file)
            file.flush()


def init_windows_console():
    """
    初始化 Windows 控制台，尝试设置 UTF-8 编码

    这需要在导入任何模块之前调用
    """
    if platform.system().lower() == "windows":
        try:
            # 尝试设置控制台代码页为 UTF-8
            import ctypes
            import ctypes.wintypes

            # 设置控制台输出为 UTF-8
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # CP_UTF8

            # 重新设置 stdout/stderr
            if hasattr(sys.stdout, "buffer"):
                import io

                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
                )
            if hasattr(sys.stderr, "buffer"):
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
                )
        except Exception:
            # 失败时使用默认设置
            pass


class SkillBootstrap:
    """技能包引导器 - 确保技能包能够独立运行"""

    def __init__(self):
        self.skill_root: Optional[Path] = None
        self.platform = platform.system().lower()
        self.python_version = sys.version_info
        self.debug = os.environ.get("DISK_CLEANER_DEBUG", "").lower() == "true"

    def log(self, message: str) -> None:
        """调试日志输出"""
        if self.debug:
            safe_print(f"[Bootstrap] {message}", file=sys.stderr)

    def print(self, message: str):
        """安全的打印方法"""
        safe_print(message)

    def detect_skill_root(self) -> Optional[Path]:
        """
        智能检测技能包根目录 - 通用/平台/IDE 无关

        搜索策略（优先级顺序）：
        1. 环境变量 DISK_CLEANER_SKILL_PATH（手动指定）
        2. 脚本所在目录的父目录
        3. 当前工作目录及其父目录
        4. 用户主目录的通用技能目录
        5. 平台特定目录
        6. sys.path 中的路径
        """
        if self.skill_root:
            return self.skill_root

        # 方法0: 检查环境变量（最高优先级）
        env_path = os.environ.get("DISK_CLEANER_SKILL_PATH")
        if env_path:
            candidate = Path(env_path)
            if self._is_valid_skill_root(candidate):
                self.skill_root = candidate
                self.log(f"从环境变量检测到技能根目录: {candidate}")
                return candidate
            else:
                self.log(f"环境变量路径无效: {env_path}")

        # 方法1: 从脚本位置推断
        try:
            import inspect

            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_file = frame.f_back.f_globals.get("__file__")
                if caller_file:
                    script_path = Path(caller_file).resolve()
                    # scripts/ 目录的父目录就是技能根目录
                    if script_path.parent.name == "scripts":
                        candidate = script_path.parent.parent
                        if self._is_valid_skill_root(candidate):
                            self.skill_root = candidate
                            self.log(f"从脚本位置检测到技能根目录: {candidate}")
                            return candidate
        except Exception as e:
            self.log(f"脚本位置检测失败: {e}")

        # 方法2: 从当前工作目录及其父目录检测
        cwd = Path.cwd()
        search_in_cwd = [
            cwd / "disk-cleaner",
            cwd / "skills" / "disk-cleaner",
            cwd / ".skills" / "disk-cleaner",
            cwd / "agent-skills" / "disk-cleaner",
            cwd / ".agent-skills" / "disk-cleaner",
        ]

        # 添加父目录（最多3级）
        for level, parent in enumerate([cwd, *cwd.parents][:3]):
            search_in_cwd.extend(
                [
                    parent / "skills" / "disk-cleaner",
                    parent / ".skills" / "disk-cleaner",
                    parent / "agent-skills" / "disk-cleaner",
                ]
            )

        for candidate in search_in_cwd:
            if self._is_valid_skill_root(candidate):
                self.skill_root = candidate
                self.log(f"从工作目录检测到技能根目录: {candidate}")
                return candidate

        # 方法3: 用户主目录的通用技能位置
        home = Path.home()
        user_skill_dirs = [
            home / "skills" / "disk-cleaner",
            home / ".skills" / "disk-cleaner",
            home / "agent-skills" / "disk-cleaner",
            home / ".agent-skills" / "disk-cleaner",
            home / "skill-packages" / "disk-cleaner",
        ]

        for candidate in user_skill_dirs:
            if self._is_valid_skill_root(candidate):
                self.skill_root = candidate
                self.log(f"从用户技能目录检测到技能根目录: {candidate}")
                return candidate

        # 方法4: 平台和IDE特定目录
        platform_specific = []

        if self.platform == "windows":
            # Windows 特定
            appdata = os.environ.get("APPDATA", "")
            localappdata = os.environ.get("LOCALAPPDATA", "")
            if appdata:
                platform_specific.append(Path(appdata) / "skills" / "disk-cleaner")
            if localappdata:
                platform_specific.append(Path(localappdata) / "skills" / "disk-cleaner")
        else:
            # Unix-like (macOS, Linux) 特定
            platform_specific.extend(
                [
                    home / ".local" / "share" / "skills" / "disk-cleaner",
                    home / ".config" / "skills" / "disk-cleaner",
                    Path("/usr/local/share/skills/disk-cleaner"),
                    Path("/opt/skills/disk-cleaner"),
                ]
            )

        # IDE特定目录（通用）
        ide_specific = [
            home / ".cursor" / "skills" / "disk-cleaner",
            home / ".windsurf" / "skills" / "disk-cleaner",
            home / ".continue" / "skills" / "disk-cleaner",
            home / ".aider" / "skills" / "disk-cleaner",
        ]
        platform_specific.extend(ide_specific)

        for candidate in platform_specific:
            if self._is_valid_skill_root(candidate):
                self.skill_root = candidate
                self.log(f"从平台/IDE目录检测到技能根目录: {candidate}")
                return candidate

        # 方法5: 检查 sys.path 中已有的路径
        for path_entry in sys.path:
            if path_entry and path_entry not in ["", "."]:
                test_path = Path(path_entry)
                # 检查是否直接在技能根目录中
                if self._is_valid_skill_root(test_path):
                    self.skill_root = test_path
                    self.log(f"从sys.path检测到技能根目录: {test_path}")
                    return test_path
                # 检查父目录
                if self._is_valid_skill_root(test_path.parent):
                    self.skill_root = test_path.parent
                    self.log(f"从sys.path父目录检测到技能根目录: {test_path.parent}")
                    return test_path.parent

        self.log("未能自动检测到技能根目录")
        self.log("请设置环境变量 DISK_CLEANER_SKILL_PATH=/path/to/skill")
        return None

    def _is_valid_skill_root(self, path: Path) -> bool:
        """检查路径是否是有效的技能根目录"""
        if not path or not path.exists():
            return False

        # 检查关键文件和目录
        indicators = [
            path / "SKILL.md",
            path / "scripts",
            path / "diskcleaner",
            path / "diskcleaner" / "__init__.py",
            path / "diskcleaner" / "core" / "progress.py",
        ]

        return all(indicator.exists() for indicator in indicators)

    def setup_import_path(self) -> bool:
        """
        设置模块导入路径

        Returns:
            True if setup successful, False otherwise
        """
        skill_root = self.detect_skill_root()

        if not skill_root:
            self.log("无法找到技能根目录，尝试使用已安装的 diskcleaner")
            # 尝试直接导入（如果已安装）
            return self._try_import_installed()

        # 将技能根目录添加到 sys.path
        skill_root_str = str(skill_root)
        if skill_root_str not in sys.path:
            sys.path.insert(0, skill_root_str)
            self.log(f"添加到 sys.path: {skill_root_str}")

        # 验证导入
        return self._verify_import()

    def _try_import_installed(self) -> bool:
        """尝试使用已安装的 diskcleaner 包"""
        try:
            import diskcleaner

            self.log(f"使用已安装的 diskcleaner: {diskcleaner.__version__}")
            return True
        except (ImportError, AttributeError):
            return False

    def _verify_import(self) -> bool:
        """验证 diskcleaner 模块是否可以正确导入"""
        try:
            # 尝试导入关键模块
            from diskcleaner.core.progress import ProgressBar
            from diskcleaner.core.scanner import DirectoryScanner

            self.log("成功导入 diskcleaner 模块")
            return True
        except ImportError as e:
            self.log(f"导入失败: {e}")
            return False

    def get_environment_info(self) -> dict:
        """获取环境诊断信息"""
        info = {
            "platform": self.platform,
            "python_version": (
                f"{self.python_version.major}."
                f"{self.python_version.minor}.{self.python_version.micro}"
            ),
            "python_executable": sys.executable,
            "skill_root": str(self.skill_root) if self.skill_root else None,
            "sys_path": sys.path[:5],  # 前5个路径
        }

        # 检查关键模块
        info["modules"] = {}
        for module_name in ["diskcleaner", "diskcleaner.core.progress", "diskcleaner.core.scanner"]:
            try:
                __import__(module_name)
                info["modules"][module_name] = "available"
            except ImportError:
                info["modules"][module_name] = "missing"

        return info

    def diagnose_import_failure(self) -> str:
        """诊断导入失败的原因并提供修复建议"""
        lines = [
            "=" * 60,
            "DISK CLEANER 技能包诊断报告",
            "=" * 60,
        ]

        info = self.get_environment_info()

        # 基本信息
        lines.extend(
            [
                "",
                "📋 环境信息:",
                f"  平台: {info['platform']}",
                f"  Python: {info['python_version']}",
                f"  Python路径: {info['python_executable']}",
            ]
        )

        # 技能根目录
        if info["skill_root"]:
            lines.append(f"  技能根目录: {info['skill_root']}")
        else:
            lines.append("  技能根目录: 未找到 ⚠️")

        # 模块状态
        lines.append("")
        lines.append("📦 模块状态:")
        for module, status in info["modules"].items():
            icon = "✅" if status == "available" else "❌"
            lines.append(f"  {icon} {module}: {status}")

        # 诊断建议
        lines.append("")
        lines.append("💡 修复建议:")

        if not info["skill_root"]:
            lines.extend(
                [
                    "",
                    "技能根目录未找到。请尝试以下方法：",
                    "",
                    "方法1: 确保从正确的目录运行脚本",
                    "  cd skills/disk-cleaner/scripts",
                    "  python analyze_disk.py",
                    "",
                    "方法2: 将 skills/disk-cleaner 添加到 PYTHONPATH",
                    f"  export PYTHONPATH=/path/to/skills/disk-cleaner:$PYTHONPATH",
                    "",
                    "方法3: 重新安装技能包",
                    "  确保解压到正确的目录",
                ]
            )

        elif info["modules"].get("diskcleaner") == "missing":
            lines.extend(
                [
                    "",
                    "diskcleaner 模块缺失。请检查：",
                    "  1. 技能包是否完整解压",
                    f"  2. diskcleaner 目录是否存在于: {info['skill_root']}",
                    "  3. 目录中是否包含 __init__.py 文件",
                ]
            )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def setup_stdout_encoding(self) -> None:
        """
        智能设置标准输出编码

        跨平台处理：
        - Windows: 尝试使用 UTF-8，失败则使用系统默认
        - Unix: 默认使用 UTF-8
        - 处理非 TTY 环境（重定向、管道）
        """
        if not sys.stdout.isatty():
            # 非交互环境，使用默认编码
            return

        if self.platform == "windows":
            try:
                # Windows: 尝试设置为 UTF-8
                if hasattr(sys.stdout, "buffer"):
                    import io

                    # 先尝试使用 UTF-8
                    try:
                        # 测试 UTF-8 是否可用
                        test_writer = io.TextIOWrapper(
                            sys.stdout.buffer, encoding="utf-8", errors="strict"
                        )
                        # 尝试写入一个 emoji 测试
                        test_writer.write("\u2705")
                        test_writer.flush()

                        # 如果成功，使用 UTF-8
                        sys.stdout = io.TextIOWrapper(
                            sys.stdout.buffer,
                            encoding="utf-8",
                            errors="replace",  # 使用 replace 避免后续错误
                        )
                        if hasattr(sys.stderr, "buffer"):
                            sys.stderr = io.TextIOWrapper(
                                sys.stderr.buffer, encoding="utf-8", errors="replace"
                            )
                        self.log("设置 Windows 控制台为 UTF-8 编码")
                    except (UnicodeEncodeError, OSError):
                        # UTF-8 不可用，使用系统默认编码（通常是 GBK）
                        self.log("UTF-8 不可用，使用系统默认编码")
                        # 不修改 stdout，保持系统默认
            except Exception as e:
                self.log(f"编码设置失败，使用系统默认: {e}")
                # 失败时不做任何事，使用系统默认

        # Unix 系统通常默认就是 UTF-8，无需特殊处理


# 全局引导器实例
_bootstrap_instance: Optional[SkillBootstrap] = None


def get_bootstrap() -> SkillBootstrap:
    """获取引导器实例（单例模式）"""
    global _bootstrap_instance
    if _bootstrap_instance is None:
        _bootstrap_instance = SkillBootstrap()
    return _bootstrap_instance


def setup_skill_environment(
    require_modules: bool = True, fix_encoding: bool = True
) -> Tuple[bool, Optional[SkillBootstrap]]:
    """
    设置技能运行环境

    Args:
        require_modules: 如果为 True，模块导入失败时显示诊断并退出
        fix_encoding: 如果为 True，自动修复标准输出编码

    Returns:
        (成功标志, 引导器实例)

    Example:
        >>> success, bootstrap = setup_skill_environment()
        >>> if not success:
        >>>     sys.exit(1)
    """
    bootstrap = get_bootstrap()

    # 修复编码
    if fix_encoding:
        bootstrap.setup_stdout_encoding()

    # 设置导入路径
    success = bootstrap.setup_import_path()

    if require_modules and not success:
        print(bootstrap.diagnose_import_failure(), file=sys.stderr)
        return False, bootstrap

    return success, bootstrap


def import_diskcleaner_modules():
    """
    导入 diskcleaner 模块的便捷函数

    Returns:
        (成功标志, 模块字典)

    Example:
        >>> success, modules = import_diskcleaner_modules()
        >>> if success:
        >>>     ProgressBar = modules['ProgressBar']
        >>>     DirectoryScanner = modules['DirectoryScanner']
    """
    success, bootstrap = setup_skill_environment(require_modules=False)

    if not success:
        return False, {}

    modules = {}

    try:
        from diskcleaner.core.progress import ProgressBar
        from diskcleaner.core.scanner import DirectoryScanner
        from diskcleaner.config import Config
        from diskcleaner.core.cache import CacheManager
        from diskcleaner.core.classifier import FileClassifier
        from diskcleaner.core.safety import SafetyChecker

        modules.update(
            {
                "ProgressBar": ProgressBar,
                "DirectoryScanner": DirectoryScanner,
                "Config": Config,
                "CacheManager": CacheManager,
                "FileClassifier": FileClassifier,
                "SafetyChecker": SafetyChecker,
            }
        )

        return True, modules
    except ImportError as e:
        bootstrap.log(f"模块导入失败: {e}")
        return False, modules


# 当作为脚本直接运行时，显示诊断信息
if __name__ == "__main__":
    # 在 Windows 上初始化控制台编码
    init_windows_console()

    import argparse

    parser = argparse.ArgumentParser(description="Disk Cleaner 技能包诊断工具")
    parser.add_argument("--debug", action="store_true", help="显示调试信息")
    parser.add_argument("--test-import", action="store_true", help="测试模块导入")

    args = parser.parse_args()

    if args.debug:
        os.environ["DISK_CLEANER_DEBUG"] = "true"

    bootstrap = get_bootstrap()

    if args.test_import:
        safe_print("测试模块导入...")
        success, modules = import_diskcleaner_modules()
        if success:
            safe_print("✅ 模块导入成功!")
            for name in modules.keys():
                safe_print(f"  - {name}")
        else:
            safe_print("❌ 模块导入失败!")
            safe_print(bootstrap.diagnose_import_failure())
            sys.exit(1)
    else:
        safe_print(bootstrap.diagnose_import_failure())
