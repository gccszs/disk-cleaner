# Disk Cleaner - Cross-Platform Disk Management Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/gccszs/disk-cleaner)
[![Skill](https://img.shields.io/badge/skill-add--skill-blue)](https://github.com/gccszs/disk-cleaner)

A comprehensive cross-platform disk space monitoring, analysis, and cleaning toolkit. Specializes in Windows C drive cleanup while maintaining full compatibility with Linux and macOS.

## Features

- **Disk Space Analysis**: Identify large files and directories consuming disk space
- **Safe Junk Cleaning**: Remove temporary files, caches, logs with built-in safety mechanisms
- **Disk Monitoring**: Real-time monitoring with configurable alert thresholds
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Multiple Modes**: Interactive CLI, automated scripts, and detailed reporting
- **Safety First**: Protected paths and extensions, dry-run mode by default

## Quick Start

### Prerequisites

Python 3.6 or higher (no external dependencies required - uses only standard library).

### Basic Usage

```bash
# Analyze disk space
python scripts/analyze_disk.py

# Preview cleanup (dry-run mode)
python scripts/clean_disk.py --dry-run

# Monitor disk usage
python scripts/monitor_disk.py

# Continuous monitoring
python scripts/monitor_disk.py --watch
```

## Installation

### Quick Install (Recommended)

Install directly from GitHub using Vercel's add-skill CLI:

```bash
npx add-skill gccszs/disk-cleaner -g
```

Replace `gccszs` with your actual GitHub username.

### As a Claude Code Skill (Manual)

1. Download `disk-cleaner.skill` from the [Releases](https://github.com/gccszs/disk-cleaner/releases) page
2. Install via Claude Code:
   ```
   /skill install path/to/disk-cleaner.skill
   ```

### Standalone Usage

```bash
# Clone the repository
git clone https://github.com/gccszs/disk-cleaner.git
cd disk-cleaner

# Scripts are ready to use (no dependencies needed)
python scripts/analyze_disk.py
```

## Usage Examples

### Disk Space Analysis

```bash
# Analyze current drive (C:\ on Windows, / on Unix)
python scripts/analyze_disk.py

# Analyze specific path
python scripts/analyze_disk.py --path "D:\Projects"

# Get top 50 largest items
python scripts/analyze_disk.py --top 50

# Output as JSON for automation
python scripts/analyze_disk.py --json

# Save report to file
python scripts/analyze_disk.py --output disk_report.json
```

### Cleaning Junk Files

**IMPORTANT**: Always run with `--dry-run` first to preview changes!

```bash
# Preview cleanup (recommended first step)
python scripts/clean_disk.py --dry-run

# Actually clean files
python scripts/clean_disk.py --force

# Clean specific categories
python scripts/clean_disk.py --temp       # Clean temp files only
python scripts/clean_disk.py --cache      # Clean cache only
python scripts/clean_disk.py --logs       # Clean logs only
python scripts/clean_disk.py --recycle    # Clean recycle bin only
python scripts/clean_disk.py --downloads 90  # Clean downloads older than 90 days
```

### Disk Monitoring

```bash
# Check current status
python scripts/monitor_disk.py

# Continuous monitoring (every 60 seconds)
python scripts/monitor_disk.py --watch

# Custom thresholds
python scripts/monitor_disk.py --warning 70 --critical 85

# Alert mode (CI/CD friendly - exit codes based on status)
python scripts/monitor_disk.py --alerts-only

# Custom monitoring interval (5 minutes)
python scripts/monitor_disk.py --watch --interval 300
```

## Scripts Reference

### `analyze_disk.py`

Disk space analysis tool that identifies space consumption patterns.

**Capabilities:**
- Scan directories to find largest files and folders
- Analyze temporary file locations
- Calculate disk usage statistics
- Generate detailed reports

### `clean_disk.py`

Safe junk file removal with multiple safety mechanisms.

**Safety Features:**
- Protected paths (never deletes system directories)
- Protected extensions (never deletes executables)
- Dry-run mode by default
- Detailed logging of all operations

**Categories Cleaned:**
- **temp**: Temporary files (%TEMP%, /tmp, etc.)
- **cache**: Application and browser caches
- **logs**: Log files (older than 30 days default)
- **recycle**: Recycle bin / trash
- **downloads**: Old download files (configurable age)

### `monitor_disk.py`

Continuous or one-shot disk usage monitoring.

**Features:**
- Multi-drive monitoring (all mount points)
- Configurable warning/critical thresholds
- Continuous monitoring mode with alerts
- JSON output for automation
- Non-zero exit codes for CI/CD integration

**Exit Codes:**
- `0`: All drives OK
- `1`: Warning threshold exceeded
- `2`: Critical threshold exceeded

## Platform Support

| Feature | Windows | Linux | macOS |
|---------|---------|-------|-------|
| Disk Analysis | ✅ | ✅ | ✅ |
| Temp Cleaning | ✅ | ✅ | ✅ |
| Cache Cleaning | ✅ | ✅ | ✅ |
| Log Cleaning | ✅ | ✅ | ✅ |
| Recycle Bin | ✅ | ✅ | ✅ |
| Real-time Monitoring | ✅ | ✅ | ✅ |

### Windows-Specific Locations
- `%TEMP%`, `%TMP%`, `%LOCALAPPDATA%\Temp`
- `C:\Windows\Temp`, `C:\Windows\Prefetch`
- `C:\Windows\SoftwareDistribution\Download`
- Browser caches (Chrome, Edge, Firefox)
- Development tool caches (npm, pip, Gradle, Maven)

### Linux-Specific Locations
- `/tmp`, `/var/tmp`, `/var/cache`
- Package manager caches (apt, dnf, pacman)
- Browser caches
- Development tool caches

### macOS-Specific Locations
- `/tmp`, `/private/tmp`, `/var/folders`
- `~/Library/Caches`, `~/Library/Logs`
- iOS device backups
- Homebrew cache

## Safety Features

### Protected Paths
System directories are never touched:
- Windows: `C:\Windows`, `C:\Program Files`, `C:\ProgramData`
- Linux/macOS: `/usr`, `/bin`, `/sbin`, `/System`, `/Library`

### Protected Extensions
Executables and system files are protected:
```
.exe, .dll, .sys, .drv, .bat, .cmd, .ps1, .sh, .bash, .zsh,
.app, .dmg, .pkg, .deb, .rpm, .msi, .iso, .vhd, .vhdx
```

## Use Cases

### 1. Free Up C Drive Space on Windows
```bash
# Analyze what's taking space
python scripts/analyze_disk.py

# Preview cleanup
python scripts/clean_disk.py --dry-run

# Execute cleanup
python scripts/clean_disk.py --force
```

### 2. Automated Disk Monitoring
```bash
# Run in background with custom thresholds
python scripts/monitor_disk.py --watch --warning 70 --critical 85 --interval 300
```

### 3. CI/CD Integration
```bash
# Check disk space in pipeline
python scripts/monitor_disk.py --alerts-only --json

# Exit codes: 0=OK, 1=WARNING, 2=CRITICAL
if [ $? -ne 0 ]; then
  echo "Disk space issue detected!"
fi
```

## Development

### Project Structure
```
disk-cleaner/
├── SKILL.md                 # Claude Code skill definition
├── README.md                # This file
├── scripts/
│   ├── analyze_disk.py      # Disk analysis tool
│   ├── clean_disk.py        # Junk file cleaner
│   └── monitor_disk.py      # Disk usage monitor
└── references/
    └── temp_locations.md    # Platform-specific temp file locations
```

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool modifies files on your system. Always:
1. Review the dry-run output before actual cleaning
2. Backup important data before cleanup
3. Use at your own risk

The authors are not responsible for any data loss or system issues.

## Acknowledgments

- Built as a [Claude Code Skill](https://claude.com/claude-code)
- Installable via [Vercel's add-skill CLI](https://github.com/vercel/vercel/tree/main/packages/add-skill)
- Cross-platform compatibility tested on Windows 10/11, Ubuntu 20.04+, macOS 12+
