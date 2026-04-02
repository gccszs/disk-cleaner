#!/usr/bin/env python3
"""
File organization demo.

Demonstrates basic usage of the file organizer.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diskcleaner.core.organizer import FileOrganizer


def demo_desktop_organization():
    """Demonstrate desktop file organization."""
    print("=" * 80)
    print("DEMO: Desktop File Organization")
    print("=" * 80)
    print()

    # Example: Organize desktop
    organizer = FileOrganizer(
        target_path="~/Desktop",  # Will be expanded to actual path
        strategy="desktop",
        dry_run=True,  # Preview mode
    )

    # Preview organization
    preview = organizer.preview_organization(max_files=10)
    print(preview)

    print("\nIn preview mode - no files are actually moved.")
    print("Set dry_run=False to actually organize files.")


def demo_downloads_organization():
    """Demonstrate downloads file organization."""
    print("=" * 80)
    print("DEMO: Downloads File Organization")
    print("=" * 80)
    print()

    # Example: Organize downloads by date
    organizer = FileOrganizer(
        target_path="~/Downloads",
        strategy="downloads",
        dry_run=True,
    )

    # Preview organization
    preview = organizer.preview_organization(max_files=10)
    print(preview)

    print("\nDownloads strategy organizes files by type and date.")
    print("Example: Documents/2026-04/document.pdf")


def demo_custom_strategy():
    """Demonstrate using a custom rule."""
    print("=" * 80)
    print("DEMO: Custom Rules")
    print("=" * 80)
    print()

    from diskcleaner.core.rules.archive_rules import (
        RuleEngine,
        ArchiveRule,
        RuleType,
    )

    # Create rule engine
    engine = RuleEngine()

    # Add custom rule to desktop strategy
    custom_rule = ArchiveRule(
        name="my_data_files",
        description="My custom data files",
        rule_type=RuleType.CUSTOM,
        destination="MyData",
        priority=200,  # Higher priority than built-in rules
        condition=lambda f: f.name.endswith(".dat"),
    )

    engine.add_custom_rule("desktop", custom_rule)

    print("Added custom rule for .dat files")
    print(f"Strategy now has {len(engine.get_strategy('desktop').rules)} rules")


def demo_plan_execution():
    """Demonstrate plan generation and execution."""
    print("=" * 80)
    print("DEMO: Plan Generation and Execution")
    print("=" * 80)
    print()

    # Create organizer
    organizer = FileOrganizer(
        target_path="~/Documents",
        strategy="general",
        dry_run=True,
    )

    # Generate plan
    print("Generating organization plan...")
    plan = organizer.generate_plan()

    # Show summary
    summary = plan.get_summary()
    print(f"\nPlan Summary:")
    print(f"  Total actions: {summary['total_actions']}")
    print(f"  Move actions: {summary['move_actions']}")
    print(f"  Skip actions: {summary['skip_actions']}")
    print(f"  Total size: {summary['total_size']} bytes")

    # Show grouped actions
    grouped = plan.get_actions_by_destination()
    print(f"\nDestinations: {len(grouped)}")

    for dest, actions in list(grouped.items())[:3]:
        print(f"  {dest}: {len(actions)} files")


if __name__ == "__main__":
    print("\nFile Organization Demo")
    print("=" * 80)
    print()

    # Note: These demos use dry-run mode
    # In production, set dry_run=False to actually move files

    print("This demo shows file organization capabilities.")
    print("All operations are in dry-run mode (no files are moved).")
    print()

    # Run demos
    try:
        demo_desktop_organization()
        print("\n" + "=" * 80 + "\n")

        demo_downloads_organization()
        print("\n" + "=" * 80 + "\n")

        demo_custom_strategy()
        print("\n" + "=" * 80 + "\n")

        demo_plan_execution()

    except Exception as e:
        print(f"Demo error: {e}")
        print("\nNote: Some paths may not exist on your system.")
        print("Adjust paths in the demo code to match your system.")
