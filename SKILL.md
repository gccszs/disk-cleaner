---
name: disk-cleaner
description: "Cross-platform disk space monitoring, analysis, and cleaning toolkit. Use when Claude needs to: (1) Analyze disk space usage and identify large files/directories consuming space, (2) Clean temporary files, caches, logs, and other junk files safely, (3) Monitor disk usage with configurable warning/critical thresholds, (4) Generate detailed reports on disk health and cleanup recommendations. Specializes in Windows C drive cleanup while maintaining full compatibility with Linux and macOS. Provides interactive CLI, automated scripts, and detailed reporting modes. All operations prioritize safety with built-in protection for system files."
---

# Disk Cleaner Skill

Cross-platform disk management toolkit for monitoring, analyzing, and cleaning disk space safely.

## Quick Start

### Analyze Disk Space

```bash
# Analyze current drive (C:\ on Windows, / on Unix)
python scripts/analyze_disk.py

# Analyze specific path
python scripts/analyze_disk.py --path "D:\Projects"

# Get top 50 largest items
python scripts/analyze_disk.py --top 50

# Output as JSON
python scripts/analyze_disk.py --json

# Save report
python scripts/analyze_disk.py --output disk_report.json
```

### Clean Junk Files

```bash
# Dry run (default - safe simulation)
python scripts/clean_disk.py --dry-run

# Actually clean files (use --force)
python scripts/clean_disk.py --force

# Clean specific category
python scripts/clean_disk.py --temp       # Clean temp files only
python scripts/clean_disk.py --cache      # Clean cache only
python scripts/clean_disk.py --logs       # Clean logs only
python scripts/clean_disk.py --recycle    # Clean recycle bin only
python scripts/clean_disk.py --downloads 90  # Clean downloads older than 90 days
```

### Monitor Disk Usage

```bash
# Check current status
python scripts/monitor_disk.py

# Continuous monitoring (every 60 seconds)
python scripts/monitor_disk.py --watch

# Custom thresholds
python scripts/monitor_disk.py --warning 70 --critical 85

# Alert mode (CI/CD friendly)
python scripts/monitor_disk.py --alerts-only

# Custom monitoring interval
python scripts/monitor_disk.py --watch --interval 300
```

## Script Reference

### analyze_disk.py

Main disk analysis tool that identifies space consumption patterns.

**Key capabilities:**
- Scan directories to find largest files and folders
- Analyze temporary file locations
- Calculate disk usage statistics
- Generate detailed reports

**Common use cases:**
```
"Analyze my C drive and show what's taking up space"
"What are the largest directories in my home folder?"
"Show me temp files taking up space"
```

### clean_disk.py

Safe junk file removal with multiple safety mechanisms.

**Safety features:**
- Protected paths (never deletes system directories)
- Protected extensions (never deletes executables)
- Dry-run mode by default
- Detailed logging of all operations

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

**Protected extensions:**
```
.exe, .dll, .sys, .drv, .bat, .cmd, .ps1, .sh, .bash, .zsh,
.app, .dmg, .pkg, .deb, .rpm, .msi, .iso, .vhd, .vhdx
```

## Typical Workflows

### Workflow 1: Investigate and Clean

When user says "My C drive is full":

1. Analyze current state: `python scripts/analyze_disk.py`
2. Preview cleanup: `python scripts/clean_disk.py --dry-run`
3. Review report, confirm with user
4. Execute cleanup: `python scripts/clean_disk.py --force`
5. Verify results: `python scripts/analyze_disk.py`

### Workflow 2: Continuous Monitoring

For proactive disk management:

1. Start monitor: `python scripts/monitor_disk.py --watch --interval 300`
2. Set appropriate thresholds: `--warning 70 --critical 85`
3. Monitor alerts and take action when needed

### Workflow 3: One-Time Deep Clean

For thorough cleanup:

```bash
# Preview all cleaning
python scripts/clean_disk.py --dry-run

# If satisfied, execute
python scripts/clean_disk.py --force

# Analyze results
python scripts/analyze_disk.py
```

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
