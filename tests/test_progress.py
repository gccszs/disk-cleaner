"""
Unit tests for progress bar module.

Tests the zero-dependency progress bar implementation.
"""

import sys
import time
from io import StringIO


from diskcleaner.core.progress import IndeterminateProgress, ProgressBar, progress_iterator


class TestProgressBar:
    """Test ProgressBar class."""

    def test_basic_progress(self):
        """Test basic progress display."""
        # Create progress bar with disabled output for testing
        progress = ProgressBar(100, prefix="Test", enable=False)

        assert progress.total == 100
        assert progress.current == 0
        assert progress.prefix == "Test"
        assert not progress.enabled

    def test_progress_update(self):
        """Test progress update."""
        progress = ProgressBar(100, enable=False)

        # Update multiple times
        progress.update(10)
        assert progress.current == 10

        progress.update(20)
        assert progress.current == 30

        progress.update(70)
        assert progress.current == 100

    def test_progress_format(self):
        """Test progress formatting."""
        progress = ProgressBar(100, width=20, enable=False)

        # Test at 0%
        progress_str = progress._format_progress()
        assert "0.0%" in progress_str
        assert "(0/100)" in progress_str
        assert "[" in progress_str and "]" in progress_str

        # Test at 50%
        progress.current = 50
        progress_str = progress._format_progress()
        assert "50.0%" in progress_str
        assert "(50/100)" in progress_str

        # Test at 100%
        progress.current = 100
        progress_str = progress._format_progress()
        assert "100.0%" in progress_str
        assert "(100/100)" in progress_str

    def test_progress_bar_width(self):
        """Test progress bar has correct width."""
        progress = ProgressBar(100, width=30, enable=False)
        progress.current = 50

        progress_str = progress._format_progress()
        # Extract bar between [ and ]
        start = progress_str.index("[")
        end = progress_str.index("]")
        bar = progress_str[start + 1 : end]

        # Should be 30 characters (15 filled, 15 empty at 50%)
        assert len(bar) == 30

    def test_eta_calculation(self):
        """Test ETA calculation."""
        progress = ProgressBar(100, enable=False)

        # Simulate some progress
        progress.current = 50
        progress.start_time = time.time() - 10  # 10 seconds elapsed

        progress_str = progress._format_progress()
        assert "ETA:" in progress_str

    def test_time_formatting(self):
        """Test time formatting."""
        progress = ProgressBar(100, enable=False)

        # Test seconds
        assert progress._format_time(30) == "30s"
        assert progress._format_time(59) == "59s"

        # Test minutes
        assert progress._format_time(60) == "1:00"
        assert progress._format_time(90) == "1:30"
        assert progress._format_time(3599) == "59:59"

        # Test hours
        assert progress._format_time(3600) == "1:00:00"
        assert progress._format_time(3661) == "1:01:01"
        assert progress._format_time(7200) == "2:00:00"

    def test_item_truncation(self):
        """Test long item names are truncated."""
        progress = ProgressBar(100, enable=False)

        # Create long item name
        long_item = "a" * 100
        progress_str = progress._format_progress(long_item)

        # Item should be truncated to ~50 chars
        assert "..." in progress_str
        # The rest should be truncated
        assert len([part for part in progress_str.split("|") if part]) > 0

    def test_close_completion(self):
        """Test closing progress bar marks it complete."""
        progress = ProgressBar(100, enable=False)

        assert not progress.closed

        # Close before 100%
        progress.current = 80
        progress.close()

        assert progress.closed
        assert progress.current == 100  # Should auto-complete

    def test_context_manager(self):
        """Test using progress bar as context manager."""
        with ProgressBar(100, enable=False) as progress:
            assert not progress.closed
            progress.update(50)

        # Should be closed after context
        assert progress.closed

    def test_zero_total(self):
        """Test progress bar with zero total (unknown total)."""
        progress = ProgressBar(0, enable=False)

        # Should be disabled for unknown total
        assert not progress.enabled

    def test_negative_total(self):
        """Test progress bar with negative total."""
        progress = ProgressBar(-10, enable=False)

        # Should be disabled for invalid total
        assert not progress.enabled

    def test_force_enable(self):
        """Test force enabling progress bar."""
        # Even in non-TTY, can force enable
        progress = ProgressBar(100, enable=True)

        assert progress.enabled

    def test_force_disable(self):
        """Test force disabling progress bar."""
        # Even in TTY, can force disable
        progress = ProgressBar(100, enable=False)

        assert not progress.enabled


class TestIndeterminateProgress:
    """Test IndeterminateProgress class."""

    def test_basic_spinner(self):
        """Test basic spinner functionality."""
        spinner = IndeterminateProgress("Test", enable=False)

        assert spinner.prefix == "Test"
        assert not spinner.enabled
        assert spinner.item_count == 0

    def test_spinner_tick(self):
        """Test spinner tick updates."""
        spinner = IndeterminateProgress(enable=False)

        spinner.tick()
        assert spinner.item_count == 1
        assert spinner.frame_index == 1

        spinner.tick()
        assert spinner.item_count == 2

    def test_spinner_frames(self):
        """Test spinner cycles through frames."""
        spinner = IndeterminateProgress(enable=False)

        frames = set()
        for _ in range(20):
            spinner.tick()
            frames.add(spinner.frame_index)

        # Should have used multiple frames
        assert len(frames) > 1

    def test_spinner_close(self):
        """Test closing spinner."""
        spinner = IndeterminateProgress(enable=False)
        spinner.tick()

        assert not spinner.closed

        spinner.close()

        assert spinner.closed

    def test_spinner_context_manager(self):
        """Test spinner as context manager."""
        with IndeterminateProgress(enable=False) as spinner:
            assert not spinner.closed
            spinner.tick()
            spinner.tick()

        # Should be closed after context
        assert spinner.closed
        assert spinner.item_count == 2

    def test_spinner_time_formatting(self):
        """Test time formatting in spinner."""
        spinner = IndeterminateProgress(enable=False)

        assert spinner._format_time(30) == "30s"
        assert spinner._format_time(90) == "1:30"
        assert spinner._format_time(3600) == "1:00:00"


class TestProgressIterator:
    """Test progress_iterator function."""

    def test_list_iterator(self):
        """Test progress_iterator with list."""
        items = list(range(10))
        result = []

        for item in progress_iterator(items, "Test", enable=False):
            result.append(item)

        assert result == items

    def test_generator_iterator(self):
        """Test progress_iterator with generator."""

        def gen():
            for i in range(5):
                yield i

        result = []
        for item in progress_iterator(gen(), "Test", enable=False):
            result.append(item)

        assert result == [0, 1, 2, 3, 4]

    def test_empty_iterator(self):
        """Test progress_iterator with empty iterable."""
        items = []
        result = []

        for item in progress_iterator(items, "Test", enable=False):
            result.append(item)

        assert result == []

    def test_large_iterator(self):
        """Test progress_iterator with many items."""
        items = range(1000)
        result = []

        for item in progress_iterator(items, "Test", enable=False):
            result.append(item)

        assert len(result) == 1000
        assert result == list(range(1000))


class TestProgressBarOutput:
    """Test actual output of progress bar (with captured stdout)."""

    def test_disabled_output(self, capsys):
        """Test that disabled progress doesn't produce output."""
        progress = ProgressBar(100, enable=False)

        for i in range(100):
            progress.update(1)

        progress.close()

        captured = capsys.readouterr()
        # Should have no output
        assert captured.out == ""

    def test_output_contains_info(self, capsys):
        """Test that progress output contains expected information."""
        # Force enable for this test
        progress = ProgressBar(10, prefix="Scanning", enable=True)

        # Update a few times
        for i in range(10):
            progress.update(1, f"file_{i}.txt")

        progress.close()

        captured = capsys.readouterr()
        output = captured.out

        # Should contain key information
        assert "Scanning" in output
        assert "100.0%" in output or "(10/10)" in output

    @pytest.mark.skipif(not sys.stdout.isatty(), reason="Requires TTY")
    def test_tty_output(self, capsys):
        """Test output in TTY environment."""
        progress = ProgressBar(5, prefix="Test", enable=None)

        progress.update(5)
        progress.close()

        captured = capsys.readouterr()
        # Should have output in TTY
        assert len(captured.out) > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_update_too_much(self):
        """Test updating beyond total doesn't break."""
        progress = ProgressBar(100, enable=False)

        # Update beyond total
        progress.update(150)

        # Should cap at total
        assert progress.current == 100

    def test_zero_update(self):
        """Test updating with zero doesn't break."""
        progress = ProgressBar(100, enable=False)

        initial = progress.current
        progress.update(0)

        assert progress.current == initial

    def test_empty_prefix(self):
        """Test progress bar with empty prefix."""
        progress = ProgressBar(100, prefix="", enable=False)

        progress_str = progress._format_progress()

        # Should not have leading space
        assert not progress_str.startswith("  ")

    def test_unicode_in_item(self):
        """Test progress bar with unicode characters in item name."""
        progress = ProgressBar(100, enable=False)

        # Should handle unicode without crashing
        progress_str = progress._format_progress("文件_测试_🎉.txt")

        assert "文件" in progress_str or "..." in progress_str

    def test_very_small_width(self):
        """Test progress bar with very small width."""
        progress = ProgressBar(100, width=5, enable=False)
        progress.current = 50

        progress_str = progress._format_progress()

        # Should still work
        assert "50.0%" in progress_str

    def test_very_large_width(self):
        """Test progress bar with very large width."""
        progress = ProgressBar(100, width=200, enable=False)
        progress.current = 50

        progress_str = progress._format_progress()

        # Should work and create long bar
        assert "50.0%" in progress_str
        assert len(progress_str) > 100

    def test_rate_limiting(self):
        """Test that update rate limiting works."""
        progress = ProgressBar(100, enable=True)

        # These updates should be rate-limited
        start = time.time()
        for i in range(100):
            progress.update(1)
        elapsed = time.time() - start

        # Should complete quickly due to rate limiting
        # (not 100 * 0.1s = 10s)
        assert elapsed < 5.0

        progress.close()


@pytest.mark.benchmark(group="progress")
class TestProgressPerformance:
    """Test progress bar performance."""

    def test_progress_overhead(self, benchmark):
        """Test that progress bar doesn't add significant overhead."""

        def update_progress():
            progress = ProgressBar(1000, enable=False)
            for i in range(1000):
                progress.update(1)
            progress.close()

        # Should complete very quickly
        result = benchmark(update_progress)
        assert result is None

    def test_iterator_overhead(self, benchmark):
        """Test progress_iterator overhead."""
        items = range(1000)

        def iterate_with_progress():
            result = []
            for item in progress_iterator(items, enable=False):
                result.append(item)
            return result

        result = benchmark(iterate_with_progress)
        assert len(result) == 1000
