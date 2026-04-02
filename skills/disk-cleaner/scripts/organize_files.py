#!/usr/bin/env python3
"""
File organization CLI.

Organize files in a directory using intelligent strategies.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from diskcleaner.core.organizer import FileOrganizer
from diskcleaner.core.rules.archive_rules import RuleEngine


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Organize files using intelligent strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview organization of desktop
  python organize_files.py ~/Desktop --strategy desktop --preview

  # Organize downloads by date
  python organize_files.py ~/Downloads --strategy downloads --execute

  # Use general strategy with custom max files
  python organize_files.py ~/Documents --strategy general --max-files 100

Available strategies:
  desktop   - Organize by file type (Images, Documents, Media, etc.)
  downloads - Organize by type and date (Documents/2024-04/)
  project   - Organize by project and semantic grouping
  general   - Mixed strategy (size, age, type)
        """,
    )

    parser.add_argument(
        "path",
        nargs="?",  # Optional when using --list-strategies
        help="Directory path to organize",
    )

    parser.add_argument(
        "--strategy",
        "-s",
        choices=["desktop", "downloads", "project", "general"],
        default="desktop",
        help="Organization strategy to use (default: desktop)",
    )

    parser.add_argument(
        "--preview",
        "-p",
        action="store_true",
        help="Preview changes without executing (dry-run mode)",
    )

    parser.add_argument(
        "--execute",
        "-e",
        action="store_true",
        help="Execute organization plan (actually move files)",
    )

    parser.add_argument(
        "--max-files",
        "-m",
        type=int,
        default=50,
        help="Maximum files to show in preview (default: 50)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress information",
    )

    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="List available strategies and exit",
    )

    return parser.parse_args()


def list_strategies():
    """List available organization strategies."""
    engine = RuleEngine()

    print("Available Organization Strategies:")
    print("=" * 60)

    for name in engine.list_strategies():
        strategy = engine.get_strategy(name)
        print(f"\n{name.upper()}")
        print(f"  Description: {strategy.description}")
        print(f"  Rules: {len(strategy.rules)}")

    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    args = parse_arguments()

    # List strategies mode
    if args.list_strategies:
        list_strategies()
        return 0

    # Validate path is provided
    if not args.path:
        print("Error: path argument is required unless using --list-strategies", file=sys.stderr)
        print("Use --list-strategies to see available organization strategies.", file=sys.stderr)
        return 1

    # Validate path
    target_path = Path(args.path).expanduser()
    if not target_path.exists():
        print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        return 1

    if not target_path.is_dir():
        print(f"Error: Path is not a directory: {args.path}", file=sys.stderr)
        return 1

    # Determine mode
    dry_run = not args.execute

    # If neither --preview nor --execute specified, default to preview
    if not args.preview and not args.execute:
        print("Note: No mode specified. Defaulting to preview mode.")
        print("      Use --execute to actually move files.")
        print()

    # Create organizer
    try:
        organizer = FileOrganizer(
            target_path=str(target_path),
            strategy=args.strategy,
            dry_run=dry_run,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Show strategy info
    if args.verbose:
        print(f"Strategy: {args.strategy}")
        print(f"Target: {target_path}")
        print(f"Mode: {'DRY RUN (preview)' if dry_run else 'EXECUTE'}")
        print()

    # Preview mode
    if args.preview or not args.execute:
        print(organizer.preview_organization(max_files=args.max_files))

        # Preview mode doesn't execute
        if dry_run:
            print("\nPreview complete. No files were moved.")
            print("Use --execute flag to actually organize files.")
            return 0

    # Execute mode
    if args.execute:
        print("Executing organization plan...")
        print()

        # Progress callback
        def progress_callback(current, total):
            if args.verbose:
                percent = (current / total) * 100
                print(f"Progress: {current}/{total} ({percent:.1f}%)", end="\r")

        # Organize files
        try:
            organized, skipped, errors = organizer.organize(
                progress_callback=progress_callback if args.verbose else None,
            )

            if args.verbose:
                print()  # New line after progress

            # Show results
            print("Organization Complete!")
            print(f"  Files organized: {organized}")
            print(f"  Files skipped: {skipped}")
            print(f"  Errors: {errors}")

            if errors > 0:
                return 1

            return 0

        except Exception as e:
            print(f"Error during organization: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
