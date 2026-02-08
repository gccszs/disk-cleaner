#!/usr/bin/env python3
"""
Disk Cleaner Scheduler - Automated cleanup scheduling

Supports scheduled cleanup tasks with configurable intervals.
Cross-platform scheduler using platform-specific mechanisms.
"""

import json
import os
import platform
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


class CleanupScheduler:
    """Scheduler for automated disk cleanup tasks."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._get_default_config_path()
        self.platform = platform.system()
        self.tasks = self._load_tasks()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        config_dir = os.path.expanduser("~/.disk-cleaner")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "scheduler.json")

    def _load_tasks(self) -> List[Dict]:
        """Load scheduled tasks from configuration."""
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                return json.load(f).get("tasks", [])
        return []

    def _save_tasks(self, tasks: List[Dict]):
        """Save scheduled tasks to configuration."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump({"tasks": tasks}, f, indent=2)

    def add_task(
        self,
        name: str,
        path: str,
        schedule: str,
        cleanup_type: str = "smart",
        options: Dict = None,
    ):
        """Add a new scheduled cleanup task."""
        task = {
            "name": name,
            "path": path,
            "schedule": schedule,
            "cleanup_type": cleanup_type,
            "options": options or {},
            "enabled": True,
            "last_run": None,
            "next_run": self._calculate_next_run(schedule),
        }

        self.tasks.append(task)
        self._save_tasks(self.tasks)

    def _calculate_next_run(self, schedule: str) -> str:
        """Calculate next run time based on schedule."""
        now = datetime.now()

        # Simple interval parsing (e.g., "24h" for every 24 hours)
        if schedule.endswith("h"):
            hours = int(schedule[:-1])
            next_run = now + timedelta(hours=hours)
            return next_run.isoformat()

        # Default to daily
        next_run = now + timedelta(days=1)
        return next_run.isoformat()

    def list_tasks(self) -> List[Dict]:
        """List all scheduled tasks."""
        return self.tasks

    def remove_task(self, task_name: str):
        """Remove a scheduled task by name."""
        self.tasks = [t for t in self.tasks if t["name"] != task_name]
        self._save_tasks(self.tasks)

    def run_task(self, task: Dict, dry_run: bool = True):
        """Execute a single cleanup task."""
        path = task["path"]
        cleanup_type = task["cleanup_type"]

        print(f"\n{'='*60}")
        print(f"Running task: {task['name']}")
        print(f"Path: {path}")
        print(f"Type: {cleanup_type}")
        print(f"Mode: {'DRY RUN' if dry_run else 'CLEAN'}")
        print(f"{'='*60}\n")

        # Import cleanup modules
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from diskcleaner.core import SmartCleanupEngine

        # Run cleanup
        engine = SmartCleanupEngine(path, cache_enabled=True)
        report = engine.analyze(include_duplicates=True, safety_check=True)

        # Display results
        summary = engine.get_summary(report)
        print(summary)

        if not dry_run:
            print("\n⚠️  Actual cleanup not yet implemented in scheduler mode")
            print("   Use --force to enable (coming soon)")

        # Update last run time
        task["last_run"] = datetime.now().isoformat()
        task["next_run"] = self._calculate_next_run(task["schedule"])
        self._save_tasks(self.tasks)

    def run_due_tasks(self, dry_run: bool = True):
        """Run all tasks that are due."""
        now = datetime.now()
        due_tasks = []

        for task in self.tasks:
            if not task.get("enabled", True):
                continue

            next_run = task.get("next_run")
            if next_run and datetime.fromisoformat(next_run) <= now:
                due_tasks.append(task)

        if not due_tasks:
            print("No tasks due to run.")
            return

        print(f"Running {len(due_tasks)} due task(s)...\n")

        for task in due_tasks:
            try:
                self.run_task(task, dry_run=dry_run)
            except Exception as e:
                print(f"Error running task '{task['name']}': {e}")

    def install_system_scheduler(self):
        """Install as system scheduler (cron/task scheduler)."""
        if self.platform == "Linux":
            self._install_cron()
        elif self.platform == "Darwin":
            self._install_launchd()
        elif self.platform == "Windows":
            self._install_task_scheduler()
        else:
            print(f"Platform {self.platform} not supported for system scheduling")

    def _install_cron(self):
        """Install as cron job on Linux."""
        print("Cron installation not yet implemented.")
        print("Manual cron entry example:")
        print("0 2 * * * /usr/bin/python3 -m diskcleaner.scheduler --run-tasks")

    def _install_launchd(self):
        """Install as launchd service on macOS."""
        print("Launchd installation not yet implemented.")

    def _install_task_scheduler(self):
        """Install as Windows Task Scheduler task."""
        print("Task Scheduler installation not yet implemented.")


def print_tasks(tasks: List[Dict]):
    """Print scheduled tasks in a formatted table."""
    if not tasks:
        print("No scheduled tasks.")
        return

    print(f"\n{'='*80}")
    print(f"{'SCHEDULED TASKS':^80}")
    print(f"{'='*80}\n")

    for i, task in enumerate(tasks, 1):
        status = "✅ Enabled" if task.get("enabled", True) else "❌ Disabled"
        print(f"{i}. {task['name']} [{status}]")
        print(f"   Path: {task['path']}")
        print(f"   Schedule: {task['schedule']}")
        print(f"   Type: {task['cleanup_type']}")
        print(f"   Last run: {task.get('last_run', 'Never')}")
        print(f"   Next run: {task.get('next_run', 'Not scheduled')}")
        print()


def main():
    # Fix Windows console encoding for emoji support
    import sys

    if sys.platform == "win32":
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

    import argparse

    parser = argparse.ArgumentParser(description="Disk Cleaner Scheduler")
    parser.add_argument("--config", "-c", help="Configuration file path")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add task
    add_parser = subparsers.add_parser("add", help="Add a new scheduled task")
    add_parser.add_argument("name", help="Task name")
    add_parser.add_argument("path", help="Path to clean")
    add_parser.add_argument("schedule", help="Schedule (e.g., 24h for every 24 hours)")
    add_parser.add_argument(
        "--type",
        "-t",
        default="smart",
        choices=["smart", "temp", "cache", "logs"],
        help="Cleanup type (default: smart)",
    )

    # List tasks
    subparsers.add_parser("list", help="List scheduled tasks")

    # Remove task
    remove_parser = subparsers.add_parser("remove", help="Remove a task")
    remove_parser.add_argument("name", help="Task name to remove")

    # Run tasks
    run_parser = subparsers.add_parser("run", help="Run due tasks")
    run_parser.add_argument(
        "--force", action="store_true", help="Actually delete files (disables dry-run)"
    )

    # Install system scheduler
    subparsers.add_parser("install", help="Install as system scheduler")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    scheduler = CleanupScheduler(config_path=args.config)

    if args.command == "add":
        scheduler.add_task(
            name=args.name, path=args.path, schedule=args.schedule, cleanup_type=args.type
        )
        print(f"✅ Task '{args.name}' added successfully")
        print(f"   Schedule: {args.schedule}")
        print(f"   Next run: {scheduler.tasks[-1]['next_run']}")

    elif args.command == "list":
        tasks = scheduler.list_tasks()
        print_tasks(tasks)

    elif args.command == "remove":
        scheduler.remove_task(args.name)
        print(f"✅ Task '{args.name}' removed")

    elif args.command == "run":
        dry_run = not args.force
        scheduler.run_due_tasks(dry_run=dry_run)

    elif args.command == "install":
        scheduler.install_system_scheduler()

    return 0


if __name__ == "__main__":
    sys.exit(main())
