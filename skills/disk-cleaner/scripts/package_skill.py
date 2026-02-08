#!/usr/bin/env python3
"""
Package the disk-cleaner skill into a .skill file.

This script creates a clean .skill package containing only the necessary files
for the skill to function, excluding tests, documentation, and development files.
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path


def create_skill_package(output_path: str = None):
    """Create a .skill package with only necessary files."""

    # Find project root (repository root)
    # Script is at: <repo>/skills/disk-cleaner/scripts/package_skill.py
    # Project root is three levels up
    project_root = Path(__file__).parent.parent.parent.parent

    # Find skill root (skills/disk-cleaner/)
    skill_root = Path(__file__).parent.parent

    # Files and directories to include (relative paths)
    # Core module is at project root, skill files are at skill root
    core_items = [
        (project_root / "diskcleaner", "diskcleaner"),
    ]

    skill_items = [
        (skill_root / "SKILL.md", "SKILL.md"),
        (skill_root / "scripts", "scripts"),
        (skill_root / "references", "references"),
    ]

    all_items = core_items + skill_items

    # Patterns to exclude
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        ".pyc",
        "*.pyo",
        ".pytest_cache",
        "*.egg-info",
        ".mypy_cache",
        ".benchmarks",
    ]

    # Create temporary directory for packaging
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_dir = Path(temp_dir) / "disk-cleaner"
        skill_dir.mkdir()

        # Copy included items
        for src, dst_name in all_items:
            dst = skill_dir / dst_name

            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*exclude_patterns))
            elif src.exists():
                shutil.copy2(src, dst)

        # Create .skill file (which is a zip file)
        if output_path is None:
            output_path = project_root / "skills" / "disk-cleaner" / "disk-cleaner.skill"

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in skill_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(skill_dir)
                    zipf.write(file_path, arcname)

        print(f"[OK] Skill package created: {output_path}")

        # Show package contents
        print("\nPackage contents:")
        with zipfile.ZipFile(output_path, "r") as zipf:
            for name in sorted(zipf.namelist()):
                print(f"  {name}")

        # Show file size
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\nPackage size: {size_mb:.2f} MB")

        return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Package disk-cleaner skill")
    parser.add_argument("--output", "-o", help="Output path for .skill file", default=None)

    args = parser.parse_args()
    create_skill_package(args.output)
