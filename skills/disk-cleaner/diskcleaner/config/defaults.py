"""
Default configuration for disk-cleaner.

This module provides default configuration values that can be overridden
 by user config files or command-line arguments.
"""

from typing import Dict, List


def get_default_config() -> Dict:
    """
    Get default configuration.

    Returns:
        Dictionary with default configuration values.
    """
    return {
        # Protected paths and files
        "protected": {
            "paths": [
                # Windows
                "C:\\Windows",
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                "C:\\ProgramData",
                # Linux/macOS
                "/usr",
                "/bin",
                "/sbin",
                "/lib",
                "/System",
                "/Library",
            ],
            "patterns": [
                "*.database",
                "*.db",
                "*.sqlite",
                "*.sqlite3",
                "config.*",
                "*.config",
                "*.conf",
            ],
        },
        # Cleaning rules
        "rules": [
            {
                "name": "Old logs",
                "pattern": "*.log",
                "category": "Logs",
                "risk": "safe",
                "age_threshold": 60,  # days
            },
            {
                "name": "Build artifacts",
                "pattern": "node_modules/",
                "category": "Build",
                "risk": "safe",
                "age_threshold": 0,
            },
            {
                "name": "Python cache",
                "pattern": "__pycache__/",
                "category": "Cache",
                "risk": "safe",
                "age_threshold": 0,
            },
            {
                "name": "Python bytecode",
                "pattern": "*.pyc",
                "category": "Cache",
                "risk": "safe",
                "age_threshold": 0,
            },
            {
                "name": "Temporary files",
                "pattern": "*.tmp",
                "category": "Temp",
                "risk": "safe",
                "age_threshold": 0,
            },
        ],
        # Ignore rules (exclude from scanning)
        "ignore": [
            ".git/*",
            ".svn/*",
            ".hg/*",
            "node_modules/@types",
            "*.lock",
        ],
        # Safety settings
        "safety": {
            "check_file_locks": True,
            "verify_permissions": True,
            "backup_before_delete": False,
            "protected_extensions": [
                # Windows executables
                ".exe",
                ".dll",
                ".sys",
                ".drv",
                ".bat",
                ".cmd",
                ".ps1",
                ".vbs",
                # Unix executables
                ".sh",
                ".bash",
                ".zsh",
                ".fish",
                # macOS
                ".app",
                ".dmg",
                ".pkg",
                # Linux
                ".deb",
                ".rpm",
                # Installers and images
                ".msi",
                ".iso",
                ".vhd",
                ".vhdx",
                ".vmdk",
            ],
        },
        # Scan settings
        "scan": {
            "use_incremental": True,
            "cache_dir": "~/.disk-cleaner/cache",
            "cache_ttl": 7,  # days
            "parallel_jobs": 4,
            "follow_symlinks": False,
            "max_depth": None,  # None = unlimited
        },
        # Platform-specific features
        "platform_features": {
            "enabled": True,
            "auto_include": False,  # Don't auto-include in cleanup list
        },
        # Notifications
        "notifications": {
            "enabled": False,
            "webhook_url": "",
            "on_completion": True,
            "on_error": True,
        },
        # Display settings
        "display": {
            "show_hidden": False,
            "human_readable": True,
            "date_format": "%Y-%m-%d %H:%M",
            "max_file_list": 100,  # Max files to display in detailed view
        },
    }


def get_protected_extensions() -> List[str]:
    """
    Get list of protected file extensions.

    Returns:
        List of file extensions that should never be deleted.
    """
    return get_default_config()["safety"]["protected_extensions"]


def get_protected_paths() -> List[str]:
    """
    Get list of protected system paths.

    Returns:
        List of paths that should never be scanned/deleted.
    """
    return get_default_config()["protected"]["paths"]
