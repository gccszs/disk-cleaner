#!/usr/bin/env python3
"""
Skill Bootstrap Module - Intelligent Bootstrap Module

This module ensures disk-cleaner skill package runs correctly in any environment,
without requiring pre-installed diskcleaner package.

Features:
- Auto-detect skill package location
- Dynamically add module paths to sys.path
- Cross-platform compatibility handling
- Graceful error handling and fallback options
- Environment detection and diagnostic information
"""

import os
import platform
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

# Safe fallback characters for emoji (for environments that don't support emoji)
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
    Safe print function, automatically handles encoding issues

    Automatically replaces emoji with ASCII characters in environments like Windows GBK
    that don't support emoji
    """
    if file is None:
        file = sys.stdout

    try:
        print(message, file=file)
        file.flush()
    except UnicodeEncodeError:
        # Encoding error, replace emoji and Chinese characters
        safe_message = message
        for emoji, fallback in EMOJI_FALLBACKS.items():
            safe_message = safe_message.replace(emoji, fallback)

        # If still has encoding issues, try replacing all non-ASCII characters
        try:
            print(safe_message, file=file)
            file.flush()
        except UnicodeEncodeError:
            # Last resort: keep only ASCII
            safe_message = safe_message.encode("ascii", "replace").decode("ascii")
            print(safe_message, file=file)
            file.flush()


def init_windows_console():
    """
    Initialize Windows console, try setting UTF-8 encoding

    This needs to be called before importing any modules
    """
    if platform.system().lower() == "windows":
        try:
            # Try setting console code page to UTF-8
            import ctypes
            import ctypes.wintypes

            # Set console output to UTF-8
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # CP_UTF8

            # Reset stdout/stderr
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
            # Use default settings on failure
            pass


class SkillBootstrap:
    """Skill package bootstrap - ensures skill package can run independently"""

    def __init__(self):
        self.skill_root: Optional[Path] = None
        self.platform = platform.system().lower()
        self.python_version = sys.version_info
        self.debug = os.environ.get("DISK_CLEANER_DEBUG", "").lower() == "true"

    def log(self, message: str) -> None:
        """Debug log output"""
        if self.debug:
            safe_print(f"[Bootstrap] {message}", file=sys.stderr)

    def print(self, message: str):
        """Safe print method"""
        safe_print(message)

    def detect_skill_root(self) -> Optional[Path]:
        """
        Intelligently detect skill package root directory - Universal/Platform/IDE agnostic

        Search strategy (priority order):
        1. Environment variable DISK_CLEANER_SKILL_PATH (manually specified)
        2. Parent directory of script location
        3. Current working directory and its parents
        4. Universal skill directory in user home
        5. Platform-specific directories
        6. Paths in sys.path
        """
        if self.skill_root:
            return self.skill_root

        # Method 0: Check environment variable (highest priority)
        env_path = os.environ.get("DISK_CLEANER_SKILL_PATH")
        if env_path:
            candidate = Path(env_path)
            if self._is_valid_skill_root(candidate):
                self.skill_root = candidate
                self.log(f"Detected skill root from environment variable: {candidate}")
                return candidate
            else:
                self.log(f"Environment variable path invalid: {env_path}")

        # Method 1: Infer from script location
        try:
            import inspect

            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_file = frame.f_back.f_globals.get("__file__")
                if caller_file:
                    script_path = Path(caller_file).resolve()
                    # Parent of scripts/ directory is skill root
                    if script_path.parent.name == "scripts":
                        candidate = script_path.parent.parent
                        if self._is_valid_skill_root(candidate):
                            self.skill_root = candidate
                            self.log(f"Detected skill root from script location: {candidate}")
                            return candidate
        except Exception as e:
            self.log(f"Script location detection failed: {e}")

        # Method 2: Detect from current working directory and its parents
        cwd = Path.cwd()
        search_in_cwd = [
            cwd / "disk-cleaner",
            cwd / "skills" / "disk-cleaner",
            cwd / ".skills" / "disk-cleaner",
            cwd / "agent-skills" / "disk-cleaner",
            cwd / ".agent-skills" / "disk-cleaner",
        ]

        # Add parent directories (max 3 levels)
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
                self.log(f"Detected skill root from working directory: {candidate}")
                return candidate

        # Method 3: Universal skill locations in user home
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
                self.log(f"Detected skill root from user skill directory: {candidate}")
                return candidate

        # Method 4: Platform and IDE specific directories
        platform_specific = []

        if self.platform == "windows":
            # Windows specific
            appdata = os.environ.get("APPDATA", "")
            localappdata = os.environ.get("LOCALAPPDATA", "")
            if appdata:
                platform_specific.append(Path(appdata) / "skills" / "disk-cleaner")
            if localappdata:
                platform_specific.append(Path(localappdata) / "skills" / "disk-cleaner")
        else:
            # Unix-like (macOS, Linux) specific
            platform_specific.extend(
                [
                    home / ".local" / "share" / "skills" / "disk-cleaner",
                    home / ".config" / "skills" / "disk-cleaner",
                    Path("/usr/local/share/skills/disk-cleaner"),
                    Path("/opt/skills/disk-cleaner"),
                ]
            )

        # IDE specific directories (universal)
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
                self.log(f"Detected skill root from platform/IDE directory: {candidate}")
                return candidate

        # Method 5: Check existing paths in sys.path
        for path_entry in sys.path:
            if path_entry and path_entry not in ["", "."]:
                test_path = Path(path_entry)
                # Check if directly in skill root
                if self._is_valid_skill_root(test_path):
                    self.skill_root = test_path
                    self.log(f"Detected skill root from sys.path: {test_path}")
                    return test_path
                # Check parent
                if self._is_valid_skill_root(test_path.parent):
                    self.skill_root = test_path.parent
                    self.log(f"Detected skill root from sys.path parent: {test_path.parent}")
                    return test_path.parent

        self.log("Could not auto-detect skill root directory")
        self.log("Please set environment variable DISK_CLEANER_SKILL_PATH=/path/to/skill")
        return None

    def _is_valid_skill_root(self, path: Path) -> bool:
        """Check if path is a valid skill root directory"""
        if not path or not path.exists():
            return False

        # Check key files and directories
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
        Setup module import path

        Returns:
            True if setup successful, False otherwise
        """
        skill_root = self.detect_skill_root()

        if not skill_root:
            self.log("Cannot find skill root, trying installed diskcleaner")
            # Try direct import (if already installed)
            return self._try_import_installed()

        # Add skill root to sys.path
        skill_root_str = str(skill_root)
        if skill_root_str not in sys.path:
            sys.path.insert(0, skill_root_str)
            self.log(f"Added to sys.path: {skill_root_str}")

        # Verify import
        return self._verify_import()

    def _try_import_installed(self) -> bool:
        """Try using installed diskcleaner package"""
        try:
            import diskcleaner

            self.log(f"Using installed diskcleaner: {diskcleaner.__version__}")
            return True
        except (ImportError, AttributeError):
            return False

    def _verify_import(self) -> bool:
        """Verify diskcleaner module can be imported correctly"""
        try:
            # Try importing key modules
            from diskcleaner.core.progress import ProgressBar
            from diskcleaner.core.scanner import DirectoryScanner

            self.log("Successfully imported diskcleaner module")
            return True
        except ImportError as e:
            self.log(f"Import failed: {e}")
            return False

    def get_environment_info(self) -> dict:
        """Get environment diagnostic information"""
        info = {
            "platform": self.platform,
            "python_version": (
                f"{self.python_version.major}."
                f"{self.python_version.minor}.{self.python_version.micro}"
            ),
            "python_executable": sys.executable,
            "skill_root": str(self.skill_root) if self.skill_root else None,
            "sys_path": sys.path[:5],  # First 5 paths
        }

        # Check key modules
        info["modules"] = {}
        for module_name in ["diskcleaner", "diskcleaner.core.progress", "diskcleaner.core.scanner"]:
            try:
                __import__(module_name)
                info["modules"][module_name] = "available"
            except ImportError:
                info["modules"][module_name] = "missing"

        return info

    def diagnose_import_failure(self) -> str:
        """Diagnose import failure reason and provide fix suggestions"""
        lines = [
            "=" * 60,
            "DISK CLEANER SKILL PACKAGE DIAGNOSTIC REPORT",
            "=" * 60,
        ]

        info = self.get_environment_info()

        # Basic info
        lines.extend(
            [
                "",
                "[i] Environment Info:",
                f"  Platform: {info['platform']}",
                f"  Python: {info['python_version']}",
                f"  Python path: {info['python_executable']}",
            ]
        )

        # Skill root
        if info["skill_root"]:
            lines.append(f"  Skill root: {info['skill_root']}")
        else:
            lines.append("  Skill root: Not found [!]")

        # Module status
        lines.append("")
        lines.append("[PKG] Module Status:")
        for module, status in info["modules"].items():
            icon = "[OK]" if status == "available" else "[X]"
            lines.append(f"  {icon} {module}: {status}")

        # Diagnostic suggestions
        lines.append("")
        lines.append("[i] Fix Suggestions:")

        if not info["skill_root"]:
            lines.extend(
                [
                    "",
                    "Skill root not found. Please try the following methods:",
                    "",
                    "Method 1: Ensure running script from correct directory",
                    "  cd skills/disk-cleaner/scripts",
                    "  python analyze_disk.py",
                    "",
                    "Method 2: Add skills/disk-cleaner to PYTHONPATH",
                    "  export PYTHONPATH=/path/to/skills/disk-cleaner:$PYTHONPATH",
                    "",
                    "Method 3: Reinstall skill package",
                    "  Ensure extracted to correct directory",
                ]
            )

        elif info["modules"].get("diskcleaner") == "missing":
            lines.extend(
                [
                    "",
                    "diskcleaner module missing. Please check:",
                    "  1. Whether skill package completely extracted",
                    f"  2. Whether diskcleaner directory exists at: {info['skill_root']}",
                    "  3. Whether directory contains __init__.py file",
                ]
            )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def setup_stdout_encoding(self) -> None:
        """
        Intelligently set stdout encoding

        Cross-platform handling:
        - Windows: Try UTF-8, fallback to system default
        - Unix: Default to UTF-8
        - Handle non-TTY environments (redirection, pipes)
        """
        if not sys.stdout.isatty():
            # Non-interactive environment, use default encoding
            return

        if self.platform == "windows":
            try:
                # Windows: Try setting to UTF-8
                if hasattr(sys.stdout, "buffer"):
                    import io

                    # First try using UTF-8
                    try:
                        # Test if UTF-8 is available
                        test_writer = io.TextIOWrapper(
                            sys.stdout.buffer, encoding="utf-8", errors="strict"
                        )
                        # Try writing an emoji test
                        test_writer.write("\u2705")
                        test_writer.flush()

                        # If successful, use UTF-8
                        sys.stdout = io.TextIOWrapper(
                            sys.stdout.buffer,
                            encoding="utf-8",
                            errors="replace",  # Use replace to avoid subsequent errors
                        )
                        if hasattr(sys.stderr, "buffer"):
                            sys.stderr = io.TextIOWrapper(
                                sys.stderr.buffer, encoding="utf-8", errors="replace"
                            )
                        self.log("Set Windows console to UTF-8 encoding")
                    except (UnicodeEncodeError, OSError):
                        # UTF-8 unavailable, use system default encoding (usually GBK)
                        self.log("UTF-8 unavailable, using system default encoding")
                        # Don't modify stdout, keep system default
            except Exception as e:
                self.log(f"Encoding setup failed, using system default: {e}")
                # On failure, do nothing and use system default

        # Unix systems usually default to UTF-8, no special handling needed


# Global bootstrap instance
_bootstrap_instance: Optional[SkillBootstrap] = None


def get_bootstrap() -> SkillBootstrap:
    """Get bootstrap instance (singleton pattern)"""
    global _bootstrap_instance
    if _bootstrap_instance is None:
        _bootstrap_instance = SkillBootstrap()
    return _bootstrap_instance


def setup_skill_environment(
    require_modules: bool = True, fix_encoding: bool = True
) -> Tuple[bool, Optional[SkillBootstrap]]:
    """
    Setup skill runtime environment

    Args:
        require_modules: If True, display diagnostics and exit when module import fails
        fix_encoding: If True, automatically fix stdout encoding

    Returns:
        (Success flag, bootstrap instance)

    Example:
        >>> success, bootstrap = setup_skill_environment()
        >>> if not success:
        >>>     sys.exit(1)
    """
    bootstrap = get_bootstrap()

    # Fix encoding
    if fix_encoding:
        bootstrap.setup_stdout_encoding()

    # Setup import path
    success = bootstrap.setup_import_path()

    if require_modules and not success:
        print(bootstrap.diagnose_import_failure(), file=sys.stderr)
        return False, bootstrap

    return success, bootstrap


def import_diskcleaner_modules():
    """
    Convenience function to import diskcleaner modules

    Returns:
        (Success flag, modules dictionary)

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
        from diskcleaner.config import Config
        from diskcleaner.core.cache import CacheManager
        from diskcleaner.core.classifier import FileClassifier
        from diskcleaner.core.progress import ProgressBar
        from diskcleaner.core.safety import SafetyChecker
        from diskcleaner.core.scanner import DirectoryScanner
        from diskcleaner.core.duplicate_finder import DuplicateFinder

        modules.update(
            {
                "ProgressBar": ProgressBar,
                "DirectoryScanner": DirectoryScanner,
                "Config": Config,
                "CacheManager": CacheManager,
                "FileClassifier": FileClassifier,
                "SafetyChecker": SafetyChecker,
                "DuplicateFinder": DuplicateFinder,
            }
        )

        return True, modules
    except ImportError as e:
        bootstrap.log(f"Module import failed: {e}")
        return False, modules


# When running as script directly, display diagnostic information
if __name__ == "__main__":
    # Initialize console encoding on Windows
    init_windows_console()

    import argparse

    parser = argparse.ArgumentParser(description="Disk Cleaner skill package diagnostic tool")
    parser.add_argument("--debug", action="store_true", help="Show debug information")
    parser.add_argument("--test-import", action="store_true", help="Test module import")

    args = parser.parse_args()

    if args.debug:
        os.environ["DISK_CLEANER_DEBUG"] = "true"

    bootstrap = get_bootstrap()

    if args.test_import:
        safe_print("Testing module import...")
        success, modules = import_diskcleaner_modules()
        if success:
            safe_print("[OK] Module import successful!")
            for name in modules.keys():
                safe_print(f"  - {name}")
        else:
            safe_print("[X] Module import failed!")
            safe_print(bootstrap.diagnose_import_failure())
            sys.exit(1)
    else:
        safe_print(bootstrap.diagnose_import_failure())
