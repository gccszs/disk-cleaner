# Disk Cleaner v2.0 - Intelligent Cross-Platform Disk Management

**[English](README.md)** | **[中文文档](README_zh.md)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/gccszs/disk-cleaner)
[![Skill](https://img.shields.io/badge/skill-add--skill-blue)](https://github.com/gccszs/disk-cleaner)

A comprehensive cross-platform disk space monitoring, analysis, and intelligent cleaning toolkit. Features advanced 3D file classification, duplicate detection, automated scheduling, and platform-specific optimization.

## ⚡ Quick Install

### Option 1: Install as Agent Skill (Recommended)

Install directly from CLI:

```bash
npx add-skill gccszs/disk-cleaner
```
OR
```bash
npx skills add gccszs/disk-cleaner
```

This will install the skill with all necessary files. The `.skill` package contains only the essential components:
- ✅ Core modules (`diskcleaner/`)
- ✅ Executable scripts (`scripts/`)
- ✅ Skill definition (`SKILL.md`)
- ✅ Reference documentation (`references/`)

**Note:** The skill package excludes tests, CI/CD configs, and development files for a clean, minimal installation.

### Option 2: Clone Repository

For development or standalone use:

```bash
git clone https://github.com/gccszs/disk-cleaner.git
cd disk-cleaner
```

See [Usage](#usage-examples) section for how to run the scripts.

---

## ✨ v2.0 New Features

- **🤖 Intelligent 3D Classification** - Files categorized by type, risk level, and age
- **🔍 Adaptive Duplicate Detection** - Fast/accurate strategies with automatic optimization
- **⚡ Incremental Scanning** - Cache-based performance optimization for repeated scans
- **🔒 Process-Aware Safety** - File lock detection and process termination
- **💻 Platform-Specific Optimization** - Windows Update, APT, Homebrew cache detection
- **⏰ Automated Scheduling** - Timer-based cleanup tasks
- **🎯 Interactive Cleanup UI** - 5 view modes with visual feedback
- **🛡️ Enhanced Safety** - Protected paths, 'YES' confirmation, backup & logging

## Features

### Core Capabilities
- **Disk Space Analysis**: Identify large files and directories consuming disk space
- **Smart Cleanup**: AI-powered suggestions based on file patterns and usage
- **Duplicate Detection**: Find and remove duplicate files to reclaim space
- **Safe Junk Cleaning**: Remove temporary files, caches, logs with built-in safety mechanisms
- **Disk Monitoring**: Real-time monitoring with configurable alert thresholds
- **Cross-Platform**: Full support for Windows, Linux, and macOS
- **Zero Dependencies**: Pure Python standard library implementation

### Advanced Features
- **3D File Classification**: Type × Risk × Age matrix for smart decisions
- **Incremental Scanning**: Only scan changed files for 10x faster subsequent scans
- **File Lock Detection**: Prevents deletion of locked files on all platforms
- **Platform-Specific Cleanup**: Windows Update, Linux package caches, macOS Xcode derived data
- **Automated Scheduling**: Set up recurring cleanup tasks with custom intervals
- **Interactive Selection**: Choose exactly what to clean with detailed previews

## Quick Start

### Prerequisites

Python 3.6 or higher (no external dependencies required - uses only standard library).

### Basic Usage

```bash
# Analyze disk space
python skills/disk-cleaner/scripts/analyze_disk.py

# Smart cleanup with duplicate detection (NEW v2.0)
python -c "from diskcleaner.core import SmartCleanupEngine; engine = SmartCleanupEngine('.'); print(engine.get_summary(engine.analyze()))"

# Preview cleanup (dry-run mode)
python skills/disk-cleaner/scripts/clean_disk.py --dry-run

# Monitor disk usage
python skills/disk-cleaner/scripts/monitor_disk.py

# Continuous monitoring
python skills/disk-cleaner/scripts/monitor_disk.py --watch
```

### v2.0 Advanced Usage

```bash
# Schedule automated cleanup (NEW v2.0)
python skills/disk-cleaner/scripts/scheduler.py add "Daily Cleanup" /tmp 24h --type smart
python skills/disk-cleaner/scripts/scheduler.py run  # Run due tasks

# Platform-specific cleanup suggestions
python -c "from diskcleaner.platforms import WindowsPlatform; import pprint; pprint.pprint(WindowsPlatform.get_system_maintenance_items())"
```

## Usage Examples

### Example 1: Smart Cleanup with Duplicate Detection

```python
from diskcleaner.core import SmartCleanupEngine

# Initialize engine
engine = SmartCleanupEngine("/path/to/clean", cache_enabled=True)

# Analyze directory
report = engine.analyze(
    include_duplicates=True,
    safety_check=True
)

# Get summary
print(engine.get_summary(report))

# Interactive cleanup (if you want)
from diskcleaner.core import InteractiveCleanupUI
ui = InteractiveCleanupUI(report)
ui.display_menu()  # Shows 5 view options
```

### Example 2: Automated Scheduling

```bash
# Add daily cleanup task
python skills/disk-cleaner/scripts/scheduler.py add "Daily Temp Cleanup" /tmp 24h --type temp

# List all scheduled tasks
python skills/disk-cleaner/scripts/scheduler.py list

# Run due tasks (dry-run by default)
python skills/disk-cleaner/scripts/scheduler.py run

# Run with actual deletion
python skills/disk-cleaner/scripts/scheduler.py run --force
```

### Example 3: Platform-Specific Cleanup

```python
from diskcleaner.platforms import WindowsPlatform, LinuxPlatform, MacOSPlatform
import platform

if platform.system() == "Windows":
    platform_impl = WindowsPlatform()
elif platform.system() == "Linux":
    platform_impl = LinuxPlatform()
else:
    platform_impl = MacOSPlatform()

# Get platform-specific cleanup suggestions
items = platform_impl.get_system_maintenance_items()
for key, item in items.items():
    print(f"{item['name']}: {item['description']}")
    print(f"  Risk: {item['risk']}, Size: {item['size_hint']}")
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
python skills/disk-cleaner/scripts/analyze_disk.py
```

## Usage Examples

### Disk Space Analysis

```bash
# Analyze current drive (C:\ on Windows, / on Unix)
python skills/disk-cleaner/scripts/analyze_disk.py

# Analyze specific path
python skills/disk-cleaner/scripts/analyze_disk.py --path "D:\Projects"

# Get top 50 largest items
python skills/disk-cleaner/scripts/analyze_disk.py --top 50

# Output as JSON for automation
python skills/disk-cleaner/scripts/analyze_disk.py --json

# Save report to file
python skills/disk-cleaner/scripts/analyze_disk.py --output disk_report.json
```

### Cleaning Junk Files

**IMPORTANT**: Always run with `--dry-run` first to preview changes!

```bash
# Preview cleanup (recommended first step)
python skills/disk-cleaner/scripts/clean_disk.py --dry-run

# Actually clean files
python skills/disk-cleaner/scripts/clean_disk.py --force

# Clean specific categories
python skills/disk-cleaner/scripts/clean_disk.py --temp       # Clean temp files only
python skills/disk-cleaner/scripts/clean_disk.py --cache      # Clean cache only
python skills/disk-cleaner/scripts/clean_disk.py --logs       # Clean logs only
python skills/disk-cleaner/scripts/clean_disk.py --recycle    # Clean recycle bin only
python skills/disk-cleaner/scripts/clean_disk.py --downloads 90  # Clean downloads older than 90 days
```

### Disk Monitoring

```bash
# Check current status
python skills/disk-cleaner/scripts/monitor_disk.py

# Continuous monitoring (every 60 seconds)
python skills/disk-cleaner/scripts/monitor_disk.py --watch

# Custom thresholds
python skills/disk-cleaner/scripts/monitor_disk.py --warning 70 --critical 85

# Alert mode (CI/CD friendly - exit codes based on status)
python skills/disk-cleaner/scripts/monitor_disk.py --alerts-only

# Custom monitoring interval (5 minutes)
python skills/disk-cleaner/scripts/monitor_disk.py --watch --interval 300
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
python skills/disk-cleaner/scripts/analyze_disk.py

# Preview cleanup
python skills/disk-cleaner/scripts/clean_disk.py --dry-run

# Execute cleanup
python skills/disk-cleaner/scripts/clean_disk.py --force
```

### 2. Automated Disk Monitoring
```bash
# Run in background with custom thresholds
python skills/disk-cleaner/scripts/monitor_disk.py --watch --warning 70 --critical 85 --interval 300
```

### 3. CI/CD Integration
```bash
# Check disk space in pipeline
python skills/disk-cleaner/scripts/monitor_disk.py --alerts-only --json

# Exit codes: 0=OK, 1=WARNING, 2=CRITICAL
if [ $? -ne 0 ]; then
  echo "Disk space issue detected!"
fi
```

## Development

### Project Structure
```
disk-cleaner/
├── skills/                   # Skills marketplace directory
│   └── disk-cleaner/
│       ├── SKILL.md          # Claude Code skill definition
│       ├── README.md         # Skill documentation
│       ├── scripts/          # Executable scripts
│       │   ├── analyze_disk.py
│       │   ├── clean_disk.py
│       │   ├── monitor_disk.py
│       │   └── scheduler.py
│       └── references/       # Reference documentation
│           └── temp_locations.md
├── diskcleaner/              # Core Python module
│   ├── core/                 # Core functionality
│   ├── optimization/         # Performance optimizations
│   └── platforms/            # Platform-specific code
├── tests/                    # Test suite (244 tests)
└── docs/                     # Additional documentation
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
