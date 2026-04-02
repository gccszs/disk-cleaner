# File Organization Feature

## Overview

The file organization feature provides intelligent file archival and organization capabilities with multiple strategies, dry-run preview, and safety checks.

## Features

- **Multiple Organization Strategies**: Desktop, Downloads, Project, and General
- **Dry-Run Mode**: Preview changes before executing
- **Safety Checks**: Protected paths, file locks, and permission verification
- **Conflict Detection**: Handles duplicate filenames and conflicting operations
- **Progress Tracking**: Real-time progress updates for large operations
- **Custom Rules**: Extensible rule engine for custom organization logic

## Installation

No additional dependencies required - uses Python standard library only.

## Usage

### Command Line Interface

#### List Available Strategies

```bash
python scripts/organize_files.py --list-strategies
```

Output:
```
Available Organization Strategies:
============================================================

DESKTOP
  Description: Organize desktop files by type
  Rules: 6

DOWNLOADS
  Description: Organize downloads by type and date
  Rules: 5

PROJECT
  Description: Organize files by project
  Rules: 4

GENERAL
  Description: General purpose organization
  Rules: 7

============================================================
```

#### Preview Organization (Dry-Run)

```bash
# Preview desktop organization
python scripts/organize_files.py ~/Desktop --strategy desktop --preview

# Preview downloads organization with date分层
python scripts/organize_files.py ~/Downloads --strategy downloads --preview

# Show more files in preview
python scripts/organize_files.py ~/Documents --strategy general --preview --max-files 100
```

#### Execute Organization

```bash
# Actually organize files (careful!)
python scripts/organize_files.py ~/Desktop --strategy desktop --execute

# Verbose mode with progress
python scripts/organize_files.py ~/Downloads --strategy downloads --execute --verbose
```

### Python API

#### Basic Usage

```python
from diskcleaner.core.organizer import FileOrganizer

# Create organizer
organizer = FileOrganizer(
    target_path="~/Desktop",
    strategy="desktop",
    dry_run=True,  # Preview mode
)

# Preview organization
preview = organizer.preview_organization(max_files=50)
print(preview)

# Execute organization (set dry_run=False to actually move files)
organized, skipped, errors = organizer.organize()

print(f"Organized: {organized}, Skipped: {skipped}, Errors: {errors}")
```

#### Custom Rules

```python
from diskcleaner.core.rules.archive_rules import (
    RuleEngine,
    ArchiveRule,
    RuleType,
)

# Create rule engine
engine = RuleEngine()

# Define custom rule
custom_rule = ArchiveRule(
    name="my_data_files",
    description="Organize my data files",
    rule_type=RuleType.EXTENSION,
    destination="MyData",
    priority=100,
    condition=lambda f: f.name.endswith(".dat"),
)

# Add to strategy
engine.add_custom_rule("desktop", custom_rule)

# Use in organizer
organizer = FileOrganizer(
    target_path="~/Desktop",
    strategy="desktop",
    dry_run=True,
)
```

#### Plan Generation and Execution

```python
from diskcleaner.core.organizer import FileOrganizer

organizer = FileOrganizer(
    target_path="~/Documents",
    strategy="general",
    dry_run=True,
)

# Generate plan
plan = organizer.generate_plan()

# Show summary
summary = plan.get_summary()
print(f"Total actions: {summary['total_actions']}")
print(f"Move actions: {summary['move_actions']}")
print(f"Skip actions: {summary['skip_actions']}")

# Show actions by destination
grouped = plan.get_actions_by_destination()
for dest, actions in grouped.items():
    print(f"{dest}: {len(actions)} files")

# Execute plan
organized, skipped, errors = organizer.execute_plan(plan)
```

## Organization Strategies

### Desktop Strategy

Organizes files by type into categories:
- **Images**: PNG, JPG, GIF, SVG, etc.
- **Documents**: PDF, DOC, TXT, etc.
- **Media**: MP4, MP3, AVI, etc.
- **Archives**: ZIP, TAR, RAR, etc.
- **Code**: PY, JS, TS, Java, etc.
- **Installers**: EXE, MSI, DMG, etc.

Example structure:
```
Desktop/
  Images/
    photo.png
    diagram.jpg
  Documents/
    report.pdf
    notes.txt
  Code/
    script.py
    main.js
```

### Downloads Strategy

Organizes files by type and date:
- Documents organized by month: `Documents/2026-04/`
- Images organized by month: `Images/2026-04/`
- Media organized by month: `Media/2026-04/`
- Archives organized by month: `Archives/2026-04/`

Example structure:
```
Downloads/
  Documents/
    2026-04/
      report.pdf
    2026-03/
      invoice.pdf
  Images/
    2026-04/
      screenshot.png
```

### Project Strategy

Organizes files by project and semantic grouping:
- **Source**: Code files detected by project path
- **Docs**: Documentation and README files
- **Assets**: Images, fonts, and media assets
- **Build**: Build artifacts and compiled files

Example structure:
```
Projects/
  my-app/
    Source/
      main.py
      utils.py
    Docs/
      README.md
      API.md
    Assets/
      logo.png
    Build/
      dist/
        app.exe
```

### General Strategy

Mixed strategy combining multiple criteria:
- **Large Files** (>100MB): `Large Files/`
- **Recent Files** (<7 days): `Recent/`
- **Old Files** (>90 days): `Archive/`
- **By Type**: Documents, Images, Media, Archives

## Safety Features

### Protected Paths

System paths are never modified:
- Windows: `C:\Windows`, `C:\Program Files`, etc.
- Linux: `/usr`, `/bin`, `/lib`, etc.
- macOS: `/System`, `/Library`, etc.

### Protected Extensions

Executable files are protected:
- `.exe`, `.dll`, `.sys` (Windows)
- `.sh`, `.bash` (Unix)
- `.app`, `.dmg` (macOS)

### Conflict Detection

- Detects duplicate filenames
- Handles same-file conflicts
- Adds timestamps to duplicate files

### Dry-Run Mode

Always preview first:
- See exactly what will happen
- Review destinations and actions
- No files are actually moved

## Testing

Run the test suite:

```bash
# Test all archive features
pytest tests/test_archive_rules.py tests/test_organizer.py tests/test_organize_cli.py -v

# Test specific module
pytest tests/test_archive_rules.py -v

# Test CLI integration
pytest tests/test_organize_cli.py -v
```

## Examples

See `examples/archive_demo.py` for detailed usage examples.

## Performance

- Efficient file scanning using `os.scandir()`
- Incremental scanning with cache support
- Progress callbacks for large operations
- Memory-efficient generator-based processing

## Limitations

- Only moves files (not directories)
- Requires write permissions for target path
- Does not handle symlinks in dry-run mode
- Large operations may take time

## Future Enhancements

- [ ] Undo/redo functionality
- [ ] Configuration file support
- [ ] Web UI preview
- [ ] Custom strategy definitions
- [ ] Parallel file operations
- [ ] Database tracking of moves
- [ ] Automatic organization scheduling

## License

Same as parent disk-cleaner project.
