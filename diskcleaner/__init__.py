"""
disk-cleaner - Cross-platform disk space management toolkit

A comprehensive toolkit for monitoring, analyzing, and cleaning disk space
safely across Windows, Linux, and macOS.
"""

__version__ = "2.0.0-dev"
__author__ = "Disk Cleaner Contributors"

from diskcleaner.core import DirectoryScanner, FileClassifier, SafetyChecker
from diskcleaner.config import Config

__all__ = [
    "DirectoryScanner",
    "FileClassifier",
    "SafetyChecker",
    "Config",
]
