"""
Core functionality modules
"""

from diskcleaner.core.cache import CacheManager
from diskcleaner.core.classifier import FileClassifier
from diskcleaner.core.duplicate_finder import DuplicateFinder, DuplicateGroup
from diskcleaner.core.safety import SafetyChecker
from diskcleaner.core.scanner import DirectoryScanner

__all__ = [
    "DirectoryScanner",
    "FileClassifier",
    "SafetyChecker",
    "CacheManager",
    "DuplicateFinder",
    "DuplicateGroup",
]
