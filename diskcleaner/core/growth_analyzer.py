"""
Disk Growth Analyzer - Track and analyze disk space growth trends

This module provides functionality to:
1. Store historical disk usage data in JSON format
2. Calculate growth rates and trends
3. Predict future disk usage
4. Generate growth reports

Features:
- JSON-based persistent storage
- Cross-platform compatibility
- ASCII-safe output
- Trend analysis and prediction
"""

import json
import os
import platform
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GrowthAnalyzer:
    """
    Analyze disk space growth trends over time.

    Features:
    - Store historical disk usage data
    - Calculate growth rates (daily, weekly, monthly)
    - Predict when disk will be full
    - Identify unusual growth patterns
    """

    def __init__(self, data_file: str = None):
        """
        Initialize growth analyzer.

        Args:
            data_file: Path to JSON file for storing historical data.
                      If None, uses default location in user home directory.
        """
        if data_file is None:
            # Default: store in user's home directory
            home_dir = Path.home()
            data_dir = home_dir / ".diskcleaner"
            data_dir.mkdir(exist_ok=True)
            data_file = str(data_dir / "growth_history.json")

        self.data_file = Path(data_file)
        self.data_dir = self.data_file.parent

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """
        Load historical data from JSON file.

        Returns:
            Dictionary with historical data
        """
        if not self.data_file.exists():
            return {"snapshots": []}

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate data structure
            if not isinstance(data, dict) or "snapshots" not in data:
                print(f"[!] Invalid data file format, creating new one", file=sys.stderr)
                return {"snapshots": []}

            return data

        except (json.JSONDecodeError, IOError) as e:
            print(f"[!] Error loading history: {e}", file=sys.stderr)
            return {"snapshots": []}

    def _save_history(self) -> bool:
        """
        Save historical data to JSON file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup of existing file
            if self.data_file.exists():
                backup_file = self.data_file.with_suffix(".bak")
                import shutil
                shutil.copy2(self.data_file, backup_file)

            # Save new data
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)

            return True

        except (IOError, OSError) as e:
            print(f"[!] Error saving history: {e}", file=sys.stderr)
            return False

    def add_snapshot(
        self,
        path: str,
        used_bytes: int,
        total_bytes: int,
        free_bytes: int,
        metadata: Dict = None,
    ) -> bool:
        """
        Add a new disk usage snapshot.

        Args:
            path: Disk path or mount point
            used_bytes: Used space in bytes
            total_bytes: Total space in bytes
            free_bytes: Free space in bytes
            metadata: Optional metadata (e.g., scan time, file counts)

        Returns:
            True if snapshot was added successfully
        """
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "path": path,
            "used_bytes": used_bytes,
            "total_bytes": total_bytes,
            "free_bytes": free_bytes,
            "used_percent": round((used_bytes / total_bytes * 100), 2) if total_bytes > 0 else 0,
            "platform": platform.system(),
        }

        # Add optional metadata
        if metadata:
            snapshot["metadata"] = metadata

        # Add to history
        self.history["snapshots"].append(snapshot)

        # Sort by timestamp
        self.history["snapshots"].sort(key=lambda x: x["timestamp"])

        # Limit history to last 1000 snapshots to prevent file from growing too large
        if len(self.history["snapshots"]) > 1000:
            self.history["snapshots"] = self.history["snapshots"][-1000:]

        # Save to disk
        return self._save_history()

    def get_snapshots(
        self,
        path: str = None,
        days: int = None,
        limit: int = None,
    ) -> List[Dict]:
        """
        Get snapshots from history.

        Args:
            path: Filter by path (if None, returns all)
            days: Only return snapshots from last N days
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot dictionaries
        """
        snapshots = self.history["snapshots"]

        # Filter by path
        if path:
            snapshots = [s for s in snapshots if s["path"] == path]

        # Filter by time
        if days:
            cutoff_time = datetime.now() - timedelta(days=days)
            snapshots = [
                s for s in snapshots
                if datetime.fromisoformat(s["timestamp"]) >= cutoff_time
            ]

        # Limit results
        if limit:
            snapshots = snapshots[-limit:]

        return snapshots

    def calculate_growth_rate(
        self,
        path: str = None,
        period: str = "daily",
    ) -> Dict:
        """
        Calculate growth rate for a specific period.

        Args:
            path: Disk path to analyze (if None, uses most common path)
            period: Time period ('daily', 'weekly', 'monthly')

        Returns:
            Dictionary with growth rate statistics
        """
        snapshots = self.get_snapshots(path=path, days=365)  # Last year

        if len(snapshots) < 2:
            return {
                "error": "Not enough data points (need at least 2 snapshots)",
                "snapshots_count": len(snapshots),
            }

        # Use most common path if not specified
        if path is None:
            path_counts = {}
            for s in snapshots:
                path_counts[s["path"]] = path_counts.get(s["path"], 0) + 1
            path = max(path_counts.keys(), key=lambda k: path_counts[k])
            snapshots = [s for s in snapshots if s["path"] == path]

        # Calculate time differences and growth
        growth_data = []
        for i in range(1, len(snapshots)):
            current = snapshots[i]
            previous = snapshots[i - 1]

            current_time = datetime.fromisoformat(current["timestamp"])
            previous_time = datetime.fromisoformat(previous["timestamp"])

            time_diff = (current_time - previous_time).total_seconds()  # seconds
            used_diff = current["used_bytes"] - previous["used_bytes"]

            if time_diff > 0:
                # Growth rate in bytes per second
                growth_rate = used_diff / time_diff
                growth_data.append({
                    "timestamp": current["timestamp"],
                    "time_diff_seconds": time_diff,
                    "used_diff_bytes": used_diff,
                    "growth_rate_per_second": growth_rate,
                })

        if not growth_data:
            return {
                "error": "No growth data available",
                "snapshots_count": len(snapshots),
            }

        # Calculate average growth rate for the period
        avg_growth_per_second = sum(g["growth_rate_per_second"] for g in growth_data) / len(growth_data)

        # Convert to requested period
        seconds_per_period = {
            "daily": 86400,
            "weekly": 604800,
            "monthly": 2592000,  # 30 days
        }

        period_seconds = seconds_per_period.get(period, 86400)
        avg_growth_per_period = avg_growth_per_second * period_seconds

        # Calculate statistics
        growth_rates = [g["growth_rate_per_second"] for g in growth_data]

        # Find min/max growth rates
        min_growth = min(growth_rates)
        max_growth = max(growth_rates)

        # Calculate trend (acceleration/deceleration)
        if len(growth_data) >= 3:
            recent_rate = growth_data[-1]["growth_rate_per_second"]
            earlier_rate = growth_data[0]["growth_rate_per_second"]
            acceleration = recent_rate - earlier_rate
        else:
            acceleration = 0

        return {
            "path": path,
            "period": period,
            "snapshots_analyzed": len(snapshots),
            "growth_data_points": len(growth_data),
            "avg_growth_bytes_per_period": round(avg_growth_per_period, 2),
            "avg_growth_mb_per_period": round(avg_growth_per_period / (1024**2), 2),
            "avg_growth_gb_per_period": round(avg_growth_per_period / (1024**3), 2),
            "min_growth_bytes_per_period": round(min_growth * period_seconds, 2),
            "max_growth_bytes_per_period": round(max_growth * period_seconds, 2),
            "acceleration_bytes_per_second_sq": round(acceleration, 2),
            "trend": "accelerating" if acceleration > 0 else "decelerating" if acceleration < 0 else "stable",
        }

    def predict_full_date(self, path: str = None) -> Dict:
        """
        Predict when the disk will be full based on growth rate.

        Args:
            path: Disk path to analyze

        Returns:
            Dictionary with prediction information
        """
        snapshots = self.get_snapshots(path=path, days=365)

        if len(snapshots) < 2:
            return {
                "error": "Not enough data for prediction (need at least 2 snapshots)",
            }

        # Get latest snapshot
        latest = snapshots[-1]

        # Calculate growth rate
        growth_rate = self.calculate_growth_rate(path=path, period="daily")

        if "error" in growth_rate:
            return growth_rate

        # Calculate days until full
        free_bytes = latest["free_bytes"]
        daily_growth = growth_rate["avg_growth_bytes_per_period"]

        if daily_growth <= 0:
            return {
                "error": "No positive growth detected",
                "current_usage_percent": latest["used_percent"],
                "message": "Disk usage is stable or decreasing",
            }

        days_until_full = free_bytes / daily_growth

        # Calculate full date
        full_date = datetime.now() + timedelta(days=days_until_full)

        return {
            "path": latest["path"],
            "current_used_bytes": latest["used_bytes"],
            "current_free_bytes": latest["free_bytes"],
            "current_total_bytes": latest["total_bytes"],
            "current_usage_percent": latest["used_percent"],
            "daily_growth_bytes": round(daily_growth, 2),
            "daily_growth_mb": round(daily_growth / (1024**2), 2),
            "daily_growth_gb": round(daily_growth / (1024**3), 2),
            "days_until_full": round(days_until_full, 1),
            "predicted_full_date": full_date.isoformat(),
            "predicted_full_date_human": full_date.strftime("%Y-%m-%d"),
            "weeks_until_full": round(days_until_full / 7, 1),
            "months_until_full": round(days_until_full / 30, 1),
        }

    def generate_report(self, path: str = None) -> Dict:
        """
        Generate comprehensive growth analysis report.

        Args:
            path: Disk path to analyze

        Returns:
            Dictionary with complete growth analysis
        """
        snapshots = self.get_snapshots(path=path)

        if not snapshots:
            return {
                "error": "No historical data available",
                "message": "Run disk analysis multiple times over days/weeks to see trends",
            }

        # Use most recent snapshot path if not specified
        if path is None:
            latest = snapshots[-1]
            path = latest["path"]

        # Calculate growth rates for different periods
        daily_rate = self.calculate_growth_rate(path=path, period="daily")
        weekly_rate = self.calculate_growth_rate(path=path, period="weekly")
        monthly_rate = self.calculate_growth_rate(path=path, period="monthly")

        # Predict full date
        prediction = self.predict_full_date(path=path)

        # Compile report
        report = {
            "analysis_date": datetime.now().isoformat(),
            "path": path,
            "snapshots_count": len(snapshots),
            "date_range": {
                "earliest": snapshots[0]["timestamp"],
                "latest": snapshots[-1]["timestamp"],
            },
            "growth_rates": {
                "daily": daily_rate,
                "weekly": weekly_rate,
                "monthly": monthly_rate,
            },
            "prediction": prediction,
            "latest_snapshot": snapshots[-1],
        }

        return report

    def cleanup_old_data(self, days: int = 365) -> int:
        """
        Remove snapshots older than specified days.

        Args:
            days: Keep only snapshots from last N days

        Returns:
            Number of snapshots removed
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        original_count = len(self.history["snapshots"])
        self.history["snapshots"] = [
            s for s in self.history["snapshots"]
            if datetime.fromisoformat(s["timestamp"]) >= cutoff_time
        ]

        removed_count = original_count - len(self.history["snapshots"])

        if removed_count > 0:
            self._save_history()

        return removed_count


def format_size(bytes_size: int) -> str:
    """
    Format byte size to human-readable string.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 GB", "500 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"
