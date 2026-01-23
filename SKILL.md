---
name: disk-cleaner
description: "High-performance cross-platform disk space monitoring, analysis, and cleaning toolkit with v2.0 optimization enhancements. Use when Claude needs to: (1) Analyze disk space usage and identify large files/directories consuming space, (2) Clean temporary files, caches, logs, and other junk files safely, (3) Monitor disk usage with configurable warning/critical thresholds, (4) Generate detailed reports on disk health and cleanup recommendations. Features advanced optimization: 3-5x faster scanning with os.scandir(), concurrent multi-threaded I/O, intelligent sampling for large directories, memory-adaptive processing, and cross-platform compatibility (Windows/macOS/Linux). Specializes in Windows C drive cleanup while maintaining full compatibility with Unix systems. Provides interactive CLI, automated scripts, detailed reporting modes, and comprehensive test coverage (244 tests). All operations prioritize safety with built-in protection for system files."
---

# Disk Cleaner Skill v2.0

High-performance cross-platform disk management toolkit with advanced optimization features for monitoring, analyzing, and cleaning disk space safely.

## 🚀 What's New in v2.0

### Performance Enhancements
- **3-5x faster scanning** with os.scandir() optimization
- **Concurrent multi-threaded scanning** for I/O-bound operations
- **Intelligent sampling** with QuickProfiler (estimates in 0.5-1s instead of full scan)
- **Memory-adaptive processing** with automatic memory monitoring
- **Optimized duplicate detection** with parallel hashing and caching

### Reliability Improvements
- **244 comprehensive tests** across all platforms
- **Cross-platform compatibility** verified on Windows, macOS, Linux
- **Python 3.8-3.12 support** with full test coverage
- **Robust error handling** for permission issues and edge cases
- **Graceful degradation** when scanning protected directories

## Quick Start

### ⚠️ Important Notes

**Path Compatibility:**
- **Always use forward slashes (`/`)** - works on all platforms (Windows, Linux, macOS)
- Python's `pathlib` handles path differences automatically
- Example: `--path "D:/Projects"` ✅ | `--path "D:\Projects"` ⚠️ (may fail in some shells)

**Safety First:**
- All cleaning operations default to `--dry-run` (safe simulation)
- Always review the report before using `--force` to actually delete files
- System directories (Windows, Program Files, etc.) are always protected

### Analyze Disk Space

```bash
# Analyze current drive (C:\ on Windows, / on Unix)
python scripts/analyze_disk.py

# Analyze specific path (use forward slashes for cross-platform compatibility)
python scripts/analyze_disk.py --path "D:/Projects"

# Get top 50 largest items
python scripts/analyze_disk.py --top 50

# Large drive scanning (increase limits for 500GB+ drives)
python scripts/analyze_disk.py --path "D:/" --file-limit 2000000 --time-limit 600

# Output as JSON for automation
python scripts/analyze_disk.py --json

# Save report to file
python scripts/analyze_disk.py --output disk_report.json
```

**Key Parameters:**
- `--path PATH` | `-p PATH` - Path to analyze (default: current drive)
- `--top N` | `-n N` - Show top N largest items (default: 20)
- `--file-limit N` - Maximum files to scan (default: 1,000,000)
- `--time-limit N` - Maximum scan time in seconds (default: 300)
- `--json` - Output as JSON (machine-readable)
- `--output FILE` | `-o FILE` - Save report to file
- `--no-progress` - Disable progress bars (useful for scripting)

### Clean Junk Files

```bash
# Preview cleaning (SAFE - default mode)
python scripts/clean_disk.py --dry-run

# Actually clean files after reviewing the report
python scripts/clean_disk.py --force

# Clean specific categories
python scripts/clean_disk.py --temp       # Clean temp files only
python scripts/clean_disk.py --cache      # Clean cache only
python scripts/clean_disk.py --logs       # Clean logs only
python scripts/clean_disk.py --recycle    # Clean recycle bin only
python scripts/clean_disk.py --downloads 90  # Clean downloads older than 90 days

# Clean custom path (e.g., secondary drive temp folder)
python scripts/clean_disk.py --path "D:/Temp" --dry-run

# Combine system and custom path cleaning
python scripts/clean_disk.py --temp --path "D:/Downloads" --dry-run
```

**Key Parameters:**
- `--dry-run` - Simulate without deleting (default: True, SAFE)
- `--force` - Actually delete files (disables dry-run)
- `--temp` - Clean only temporary files
- `--cache` - Clean only cache files
- `--logs` - Clean only log files
- `--recycle` - Clean only recycle bin
- `--downloads DAYS` - Clean downloads older than N days
- `--path PATH` | `-p PATH` - Clean specific custom path
- `--json` - Output as JSON
- `--output FILE` | `-o FILE` - Save report to file
- `--no-progress` - Disable progress bars

### Monitor Disk Usage

```bash
# Check current status (all drives)
python scripts/monitor_disk.py

# Continuous monitoring (every 60 seconds)
python scripts/monitor_disk.py --watch

# Custom warning/critical thresholds
python scripts/monitor_disk.py --warning 70 --critical 85

# Alert mode (CI/CD friendly - non-zero exit on threshold exceeded)
python scripts/monitor_disk.py --alerts-only

# Custom monitoring interval
python scripts/monitor_disk.py --watch --interval 300
```

**Key Parameters:**
- `--watch` - Enable continuous monitoring mode
- `--warning N` - Warning threshold in percent (default: 80)
- `--critical N` - Critical threshold in percent (default: 90)
- `--alerts-only` - Only show warnings (exit code 1=warning, 2=critical)
- `--interval N` - Check interval in seconds (default: 60)
- `--json` - Output as JSON

## Performance Features

### High-Speed Scanning
The scanner uses advanced optimizations for rapid directory traversal:

- **os.scandir() optimization**: 3-5x faster than Path.glob/iterdir()
- **Bounded queue processing**: Efficient concurrent scanning
- **Adaptive worker threads**: CPU count × 4 for I/O-bound operations
- **Smart path exclusion**: Skip system directories automatically

### Intelligent Sampling (QuickProfiler)
For large directories, use sampling to get instant estimates:

```python
from diskcleaner.optimization.scan import QuickProfiler

profiler = QuickProfiler(sample_time=1.0)  # 1 second sampling
profile = profiler.profile(path)  # Returns: estimated file count, size, depth, time

# Example output for 442K files:
# - Estimated: 450,000 files (within 2%)
# - Estimated scan time: 14 seconds
# - Actual scan time: 14 seconds
```

### Memory Management
Automatic memory monitoring prevents system overload:

```python
from diskcleaner.optimization.memory import MemoryMonitor

monitor = MemoryMonitor(threshold_mb=1000)
if monitor.should_pause():
    # Reduce concurrency
    workers = monitor.get_optimal_workers(current_workers)
```

## Script Reference

### analyze_disk.py

Main disk analysis tool that identifies space consumption patterns.

**Key capabilities:**
- High-speed scanning with os.scandir() (3-5x faster)
- Scan large directories (100K+ files) in seconds
- Cross-platform path exclusion (Windows/macOS/Linux)
- Detailed statistics and reports

**Common use cases:**
```
"Analyze my C drive and show what's taking up space"
"What are the largest directories in my home folder?"
"Show me temp files taking up space"
"Scan this 400GB directory quickly"
```

### clean_disk.py

Safe junk file removal with multiple safety mechanisms.

**Safety features:**
- Protected paths (never deletes system directories)
- Protected extensions (never deletes executables)
- Dry-run mode by default
- Detailed logging of all operations
- Handles empty categories gracefully

**Categories cleaned:**
- **temp**: Temporary files (%TEMP%, /tmp, etc.)
- **cache**: Application and browser caches
- **logs**: Log files (older than 30 days default)
- **recycle**: Recycle bin / trash
- **downloads**: Old download files (configurable age)

**Important:** Always run with `--dry-run` first to preview changes.

### monitor_disk.py

Continuous or one-shot disk usage monitoring.

**Features:**
- Multi-drive monitoring (all mount points)
- Configurable warning/critical thresholds
- Continuous monitoring mode with alerts
- JSON output for automation
- Non-zero exit codes for CI/CD integration

**Exit codes:**
- 0: All drives OK
- 1: Warning threshold exceeded
- 2: Critical threshold exceeded

## Platform-Specific Information

See [temp_locations.md](references/temp_locations.md) for:
- Complete list of temporary file locations by platform
- Browser cache locations
- Development tool caches
- Safety guidelines for each platform

**Platform-specific optimizations:**
- **Windows**: Excludes C:\Windows, C:\Program Files, etc.
- **macOS**: Excludes /System, /Library, /private/var/vm (VM swap)
- **Linux**: Excludes /proc, /sys, /dev, /run

**When to read this file:**
- User asks about specific platform cleanup locations
- Need to understand what gets cleaned on each OS
- Customizing cleanup for specific applications

## Safety Rules

The scripts implement multiple safety layers:

1. **Protected Paths**: System directories never touched
2. **Protected Extensions**: Executables and system files protected
3. **Dry Run Default**: Must use `--force` for actual deletion
4. **Age Filters**: Logs cleaned only after 30+ days
5. **Error Handling**: Permission errors don't stop execution
6. **Graceful Degradation**: Handles edge cases (empty categories, missing paths)

**Protected extensions:**
```
.exe, .dll, .sys, .drv, .bat, .cmd, .ps1, .sh, .bash, .zsh,
.app, .dmg, .pkg, .deb, .rpm, .msi, .iso, .vhd, .vhdx
```

## Typical Workflows

### Workflow 1: Investigate and Clean C Drive

When user says "My C drive is full":

1. **Analyze current state:**
   ```bash
   python scripts/analyze_disk.py
   ```

2. **Preview cleanup (SAFE):**
   ```bash
   python scripts/clean_disk.py --dry-run
   ```

3. **Review report, confirm with user**

4. **Execute cleanup:**
   ```bash
   python scripts/clean_disk.py --force
   ```

5. **Verify results:**
   ```bash
   python scripts/analyze_disk.py
   ```

### Workflow 2: Clean Secondary Drive

When user wants to clean D drive or external drives:

1. **Analyze the drive:**
   ```bash
   # Use forward slashes for cross-platform compatibility
   python scripts/analyze_disk.py --path "D:/"
   ```

2. **Clean specific folder on D drive:**
   ```bash
   python scripts/clean_disk.py --path "D:/Temp" --dry-run
   ```

3. **Clean system locations + D drive downloads:**
   ```bash
   python scripts/clean_disk.py --temp --cache --path "D:/Downloads" --dry-run
   ```

4. **Execute after review:**
   ```bash
   python scripts/clean_disk.py --temp --cache --path "D:/Downloads" --force
   ```

### Workflow 3: Large Drive Analysis (500GB+)

For analyzing very large drives that may exceed default limits:

1. **Check default limits would be insufficient:**
   - Default: 1,000,000 files, 300 seconds (5 minutes)
   - For 830GB drive with 1M+ files, increase limits

2. **Analyze with increased limits:**
   ```bash
   python scripts/analyze_disk.py --path "D:/" \
       --file-limit 2000000 \
       --time-limit 600 \
       --top 50
   ```

3. **For complete analysis without limits:**
   - Use Python API directly (set limits to None)
   - Or set very high values: `--file-limit 10000000 --time-limit 3600`

4. **Save report for comparison:**
   ```bash
   python scripts/analyze_disk.py --path "D:/" \
       --file-limit 2000000 \
       --output "D_drive_analysis_$(date +%Y%m%d).json"
   ```

### Workflow 4: Continuous Monitoring

For proactive disk management in production:

1. **Start monitor with custom thresholds:**
   ```bash
   python scripts/monitor_disk.py --watch --interval 300 --warning 70 --critical 85
   ```

2. **CI/CD integration (alert mode):**
   ```bash
   # In automation pipeline - non-zero exit triggers alert
   python scripts/monitor_disk.py --alerts-only --warning 80 --critical 90
   # Exit codes: 0=OK, 1=Warning, 2=Critical
   ```

3. **Log results for trending:**
   ```bash
   while true; do
       python scripts/monitor_disk.py --json >> disk_usage.log
       sleep 3600  # Check every hour
   done
   ```

### Workflow 5: Automated Cleanup Script

Create a safe automated cleanup routine:

```bash
#!/bin/bash
# automated_cleanup.sh

# 1. Analyze before
echo "=== Before Cleanup ==="
python scripts/analyze_disk.py --output before.json

# 2. Preview ALL cleaning operations
echo "=== Previewing Cleanup ==="
python scripts/clean_disk.py --dry-run --json > cleanup_preview.json

# 3. Execute (only if preview looks good)
echo "=== Executing Cleanup ==="
python scripts/clean_disk.py --force

# 4. Clean D drive temp folder
echo "=== Cleaning D:/Temp ==="
python scripts/clean_disk.py --path "D:/Temp" --force

# 5. Analyze after
echo "=== After Cleanup ==="
python scripts/analyze_disk.py --output after.json

# 6. Compare
echo "=== Space Freed ==="
# Use jq or similar to compare before.json and after.json
```

## Common Issues and Solutions

### Issue: "Scan stopped early" Warning

**Symptoms:**
```
⚠️  Scan stopped early: file_limit (1000000 files)
```

**Cause:** Scan reached the default file count or time limit.

**Solutions:**
1. **Increase limits for large drives:**
   ```bash
   python scripts/analyze_disk.py --path "D:/" \
       --file-limit 2000000 \
       --time-limit 600
   ```

2. **Use Python API for unlimited scanning:**
   ```python
   from diskcleaner.core import DirectoryScanner
   scanner = DirectoryScanner("D:/", max_files=None, max_seconds=None)
   files = scanner.scan()
   ```

### Issue: clean_disk.py Finds 0 Files

**Symptoms:**
```
TEMP FILES:
  ✅ C:\Users\...\AppData\Local\Temp
     Files: 0, Space: 0.00 MB
```

**Causes:**
1. Very clean system (actually no temp files)
2. Scan didn't reach the temp directories
3. Permissions preventing access

**Solutions:**
1. **Check if temp files exist:**
   ```bash
   # Windows
   dir "%TEMP%"

   # Linux/macOS
   ls -la /tmp
   ```

2. **Verify paths are accessible:**
   ```bash
   python scripts/clean_disk.py --dry-run --json
   ```

3. **Clean specific path directly:**
   ```bash
   python scripts/clean_disk.py --path "C:/Users/YourName/AppData/Local/Temp" --dry-run
   ```

### Issue: Path Not Found Errors

**Symptoms:**
```
❌ Error: Path does not exist: D:\Projects
```

**Cause:** Backslashes or invalid path format.

**Solution:**
```bash
# ❌ Wrong - backslashes may fail
python scripts/clean_disk.py --path "D:\Projects"

# ✅ Correct - forward slashes work everywhere
python scripts/clean_disk.py --path "D:/Projects"

# ✅ Also correct - use tilde for home directory
python scripts/clean_disk.py --path "~/Documents"
```

### Issue: Progress Bars Not Showing

**Symptoms:** No visual progress bars during operations.

**Cause:** Progress bars auto-disable in non-TTY environments:
- IDE terminals (PyCharm, VS Code)
- CI/CD environments
- Piped output (`|`, `>`)
- JSON mode

**Solutions:**
1. **Use real terminal:** Windows Terminal, PowerShell, CMD, Git Bash
2. **Check if running in TTY:**
   ```python
   import sys
   print(sys.stdout.isatty())  # Should be True
   ```

3. **Force enable (not recommended):** Modify code to set `enable=True`

## Output Formats

### Interactive Mode (Default)
Human-readable console output with:
- Visual progress bars
- Emoji indicators for status
- Formatted tables

### JSON Mode
Machine-readable output for:
- Automation pipelines
- Log aggregation
- Further processing

Use `--json` flag with any script.

### Report Files
Save detailed reports with `--output report.json` for:
- Historical tracking
- Comparison over time
- Audit trails

## Advanced Usage

### Python API

For integration with other tools:

```python
from diskcleaner.core import DirectoryScanner, SmartCleanupEngine

# Scan directory
scanner = DirectoryScanner("/path/to/scan")
files = scanner.scan()

# Analyze and get recommendations
engine = SmartCleanupEngine("/path/to/scan")
report = engine.analyze()

# Clean with safety checks
results = engine.clean(
    categories=["temp", "cache", "logs"],
    dry_run=True  # Set False to actually delete
)
```

### Performance Optimization

For maximum performance on large directories:

```python
from diskcleaner.optimization.scan import ConcurrentScanner, QuickProfiler

# Quick profiling first
profiler = QuickProfiler(sample_time=1.0)
profile = profiler.profile(large_path)

print(f"Estimated: {profile.file_count:,} files")
print(f"Estimated time: {profile.estimated_time:.1f}s")

# Full concurrent scan if needed
if profile.file_count < 100000:
    scanner = ConcurrentScanner()
    result = scanner.scan(large_path)
```

## Testing

Comprehensive test suite ensures reliability:

- **244 tests** covering all functionality
- **Cross-platform**: Windows, macOS, Linux
- **All Python versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Performance benchmarks**: Validate optimization improvements
- **Integration tests**: End-to-end workflows

Run tests:
```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/test_optimization.py
pytest tests/benchmarks/

# With coverage
pytest tests/ --cov=diskcleaner --cov-report=html
```

## Troubleshooting

### Permission Errors
The scanner handles permission errors gracefully. Protected directories are automatically skipped on each platform:
- **Windows**: C:\Windows, C:\Program Files
- **macOS**: /System, /Library, /private/var/vm
- **Linux**: /proc, /sys, /dev

### Performance Issues
If scanning seems slow:
1. Check if path is network drive (slower than local)
2. Verify anti-virus isn't scanning every file access
3. Use `--sample` flag for quick estimates on large directories

### Empty Results
If no files found:
1. Check path exists and is accessible
2. Verify files aren't all protected (system directories)
3. Run with higher verbosity to see what's being scanned

## Contributing

To modify or extend the toolkit:

1. **Optimization modules**: `diskcleaner/optimization/`
   - `scan.py`: ConcurrentScanner, QuickProfiler
   - `hash.py`: AdaptiveHasher, DuplicateFinder
   - `delete.py`: BatchDeleter, AsyncDeleter
   - `memory.py`: MemoryMonitor
   - `profiler.py`: PerformanceProfiler

2. **Core modules**: `diskcleaner/core/`
   - `scanner.py`: DirectoryScanner with os.scandir()
   - `smart_cleanup.py`: SmartCleanupEngine
   - Other core components

3. **Platform-specific**: `diskcleaner/platforms/`
   - Windows, macOS, Linux implementations

4. **Tests**: `tests/`
   - Unit tests for all components
   - Performance benchmarks
   - Cross-platform tests

5. **Scripts**: `scripts/`
   - User-facing CLI tools

Always run tests after changes:
```bash
pytest tests/ -v
pre-commit run --all-files
```

## License

MIT License - See LICENSE file for details.
