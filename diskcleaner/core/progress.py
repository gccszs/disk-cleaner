"""
Zero-dependency progress bar implementation.

This module provides a simple, zero-dependency progress bar for disk cleaner operations.
Features:
- Real-time progress display with percentage
- ETA calculation
- Current item display
- Auto-disable in non-TTY environments
- Refresh rate limiting to avoid flicker
"""

import sys
import time
from typing import Optional


class ProgressBar:
    """
    A simple, zero-dependency progress bar.

    Usage:
        >>> progress = ProgressBar(100, prefix="Scanning")
        >>> for i in range(100):
        ...     # Do work
        ...     progress.update(1, f"file_{i}.txt")
        >>> progress.close()

    Display format:
        Scanning [████████░░░░░░] 45.2% (1234/2718) | ETA: 0:15 | /tmp/file.log
    """

    def __init__(
        self, total: int, prefix: str = "", width: int = 40, enable: Optional[bool] = None
    ):
        """
        Initialize progress bar.

        Args:
            total: Total number of items to process
            prefix: Text to display before the progress bar
            width: Width of the progress bar in characters
            enable: Force enable/disable. None = auto-detect TTY
        """
        self.total = total
        self.current = 0
        self.prefix = prefix
        self.width = width
        self.start_time = time.time()
        self.last_update_time = 0
        self.last_display_length = 0
        self.closed = False

        # Auto-detect TTY if not specified
        if enable is None:
            self.enabled = sys.stdout.isatty()
        else:
            self.enabled = enable

        # Minimum refresh interval (seconds) to avoid flicker
        self.min_refresh_interval = 0.1

        # For unknown total (indeterminate progress)
        if total <= 0:
            self.total = 0
            self.enabled = False  # Disable for unknown total

    def update(self, n: int = 1, item: str = ""):
        """
        Update progress.

        Args:
            n: Number of items processed since last update
            item: Current item being processed (optional)
        """
        # Always update counter, even if disabled
        self.current = min(self.current + n, self.total)  # Cap at total
        current_time = time.time()

        if not self.enabled or self.closed:
            return

        # Rate limiting: only update if enough time has passed
        # or if we're at 100%
        time_since_last_update = current_time - self.last_update_time
        is_complete = self.current >= self.total

        if time_since_last_update < self.min_refresh_interval and not is_complete:
            return

        # Build progress string
        progress_str = self._format_progress(item)

        # Clear previous line by writing spaces
        if self.last_display_length > 0:
            clear_str = "\r" + " " * self.last_display_length + "\r"
            sys.stdout.write(clear_str)

        # Write new progress
        sys.stdout.write(f"\r{progress_str}")
        sys.stdout.flush()

        # Update state
        self.last_update_time = current_time
        self.last_display_length = len(progress_str)

        # Newline when complete
        if is_complete:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self.closed = True

    def _format_progress(self, item: str = "") -> str:
        """Format the progress display string."""
        if self.total == 0:
            return f"{self.prefix}: {self.current} items processed"

        # Calculate percentage
        percent = self.current / self.total
        percent_str = f"{percent * 100:.1f}%"

        # Build progress bar
        filled = int(self.width * percent)
        bar = "█" * filled + "░" * (self.width - filled)

        # Calculate ETA
        elapsed = time.time() - self.start_time
        if self.current > 0 and percent < 1.0 and elapsed > 0:
            items_per_second = self.current / elapsed
            remaining_items = self.total - self.current
            eta_seconds = remaining_items / items_per_second if items_per_second > 0 else 0
            eta_str = self._format_time(eta_seconds)
        else:
            eta_str = "0:00"

        # Build components
        parts = [
            self.prefix,
            f"[{bar}]",
            f"{percent_str}",
            f"({self.current}/{self.total})",
            f"ETA: {eta_str}",
        ]

        # Add current item if provided
        if item:
            # Truncate long item names
            max_item_length = 50
            if len(item) > max_item_length:
                item = "..." + item[-(max_item_length - 3):]
            parts.append(f"| {item}")

        return " ".join(parts)

    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS or HH:MM:SS format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}:{mins:02d}:{secs:02d}"

    def close(self):
        """Finalize the progress bar."""
        if self.closed:
            return

        # Ensure we show 100%
        if self.current < self.total:
            self.current = self.total

        if self.enabled:
            progress_str = self._format_progress()
            sys.stdout.write(f"\r{progress_str}\n")
            sys.stdout.flush()

        self.closed = True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


class IndeterminateProgress:
    """
    Indeterminate progress bar for operations with unknown total.

    Shows a spinning indicator instead of percentage.

    Usage:
        >>> progress = IndeterminateProgress("Processing")
        >>> while True:
        ...     # Do work
        ...     progress.tick()
        ...     if done:
        ...         break
        >>> progress.close()
    """

    # Spinner frames
    _spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, prefix: str = "", enable: Optional[bool] = None):
        """
        Initialize indeterminate progress.

        Args:
            prefix: Text to display before the spinner
            enable: Force enable/disable. None = auto-detect TTY
        """
        self.prefix = prefix
        self.enabled = enable if enable is not None else sys.stdout.isatty()
        self.closed = False
        self.frame_index = 0
        self.item_count = 0
        self.start_time = time.time()
        self.last_update_time = 0

    def tick(self, item: str = ""):
        """
        Update the spinner.

        Args:
            item: Current item being processed (optional)
        """
        # Always update counter and frame, even if disabled
        self.item_count += 1
        current_time = time.time()

        # Update frame index regardless of enabled status
        self.frame_index = (self.frame_index + 1) % len(self._spinner_frames)

        if not self.enabled or self.closed:
            return

        # Rate limiting
        if current_time - self.last_update_time < 0.1:
            return

        # Get current frame
        frame = self._spinner_frames[self.frame_index]

        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)

        # Build display
        parts = [self.prefix, f"{frame}", f"({self.item_count} items)", f"elapsed: {elapsed_str}"]

        if item:
            max_item_length = 50
            if len(item) > max_item_length:
                item = "..." + item[-(max_item_length - 3):]
            parts.append(f"| {item}")

        display_str = " ".join(parts)

        # Update display
        sys.stdout.write(f"\r{display_str}")
        sys.stdout.flush()

        self.last_update_time = current_time

    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS or HH:MM:SS format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}:{mins:02d}:{secs:02d}"

    def close(self):
        """Finalize the progress display."""
        if self.closed:
            return

        if self.enabled:
            elapsed = time.time() - self.start_time
            elapsed_str = self._format_time(elapsed)

            # Show completion message
            sys.stdout.write(
                f"\r{self.prefix} ✓ Completed ({self.item_count} items in {elapsed_str})\n"
            )
            sys.stdout.flush()

        self.closed = True

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def progress_iterator(items, prefix: str = "", enable: Optional[bool] = None):
    """
    Wrap an iterator with automatic progress tracking.

    Usage:
        >>> for item in progress_iterator(my_list, "Processing"):
        ...     process(item)

    Args:
        items: Iterable to process
        prefix: Progress bar prefix
        enable: Force enable/disable progress bar

    Yields:
        Items from the input iterable
    """
    # Try to get length for determinate progress
    try:
        total = len(items)
        progress = ProgressBar(total, prefix, enable=enable)
    except (TypeError, AttributeError):
        # Fallback to indeterminate progress
        progress = IndeterminateProgress(prefix, enable=enable)

    with progress:
        for item in items:
            yield item
            if isinstance(progress, ProgressBar):
                progress.update(1, str(item)[:50])
            else:
                progress.tick(str(item)[:50])
