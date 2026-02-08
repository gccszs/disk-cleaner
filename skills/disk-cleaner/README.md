# Disk Cleaner Skill

A high-performance cross-platform disk space monitoring, analysis, and cleaning toolkit for Claude Code.

## Quick Start

### As Claude Code Skill

Install directly from GitHub:

```bash
npx add-skill gccszs/disk-cleaner
```

### Manual Installation

1. Download `disk-cleaner.skill` from the [Releases](https://github.com/gccszs/disk-cleaner/releases) page
2. Install via Claude Code: `/skill install path/to/disk-cleaner.skill`

## Features

- **Disk Space Analysis**: Identify large files and directories consuming space
- **Smart Cleanup**: Safe removal of temporary files, caches, logs
- **Duplicate Detection**: Find and remove duplicate files
- **Disk Monitoring**: Real-time monitoring with alert thresholds
- **Cross-Platform**: Windows, Linux, macOS support
- **3-5x Faster**: Optimized scanning with os.scandir()

## Usage

### Analyze Disk Space

```bash
python scripts/analyze_disk.py --top 50
```

### Clean Junk Files (Preview)

```bash
python scripts/clean_disk.py --dry-run
```

### Monitor Disk Usage

```bash
python scripts/monitor_disk.py --watch
```

## Skill Structure

```
disk-cleaner/
├── SKILL.md           # Skill definition
├── README.md          # This file
├── diskcleaner/       # Core Python module
├── scripts/           # Executable scripts
└── references/        # Reference documentation
```

## Documentation

- [Full Skill Documentation](SKILL.md)
- [Project Repository](https://github.com/gccszs/disk-cleaner)

## License

MIT License
