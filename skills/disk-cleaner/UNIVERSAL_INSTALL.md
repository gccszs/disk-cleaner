# Universal Installation Guide

## 🌐 Platform & IDE Independent Installation

This guide works for **ALL platforms** and **ALL AI IDEs**.

---

## 📋 What You Need

- **Python 3.7+** - The ONLY requirement
- **This skill package** - The .skill file or extracted directory

That's it! No other dependencies.

---

## 🚀 Quick Install (3 Steps)

### Step 1: Verify Python

```bash
# Windows
python --version

# macOS/Linux
python3 --version
```

If you see `Python 3.x.x`, you're ready!

If not, install from: https://www.python.org/downloads/

### Step 2: Extract Skill Package

Extract `disk-cleaner.skill` to ONE of these locations:

**Recommended (User-level):**
```bash
# Windows
%USERPROFILE%\skills\disk-cleaner\

# macOS/Linux
~/.skills/disk-cleaner/
```

**Alternative (Project-level):**
```bash
your-project/skills/disk-cleaner/
```

**Any location works!** The skill includes intelligent auto-detection.

### Step 3: Verify Installation

```bash
cd skills/disk-cleaner  # Or wherever you extracted it
python scripts/check_skill.py
```

Expected output:
```
✅ All checks passed! Skill package ready to use.
```

---

## 🎯 Installation Locations

The skill works at **ANY** of these levels:

### User Level (Recommended)

```
~/.skills/disk-cleaner/          # Unix-like (macOS, Linux)
~/agent-skills/disk-cleaner/     # Alternative
C:\Users\You\skills\disk-cleaner\  # Windows
```

**Benefits:**
- ✅ Available to all projects
- ✅ Single installation
- ✅ Easy to update

### Project Level

```
your-project/
├── skills/
│   └── disk-cleaner/  ← Extract here
├── src/
└── README.md
```

**Benefits:**
- ✅ Project-specific
- ✅ Version locked
- ✅ Portable with project

### Global/System Level

```
/usr/local/share/skills/disk-cleaner/  # Linux (system-wide)
C:\ProgramData\skills\disk-cleaner\   # Windows (system-wide)
```

**Benefits:**
- ✅ All users can access
- ✅ Centralized management

**Note:** May require admin privileges.

---

## 🤖 AI IDE Compatibility

This skill works with **ALL** AI IDEs:

### Cursor

```bash
# Extract to:
~/.cursor/skills/disk-cleaner/
# OR
your-project/.cursor/skills/disk-cleaner/
```

No configuration needed - Cursor auto-detects.

### Windsurf

```bash
# Extract to:
~/.windsurf/skills/disk-cleaner/
# OR
your-project/skills/disk-cleaner/
```

Works immediately.

### Continue

```bash
# Extract to:
~/.continue/skills/disk-cleaner/
# OR
your-project/skills/disk-cleaner/
```

Optionally add to config.json:
```json
{
  "skills": ["./skills/disk-cleaner"]
}
```

### Aider

```bash
# Extract anywhere, then use via:
!python skills/disk-cleaner/scripts/analyze_disk.py
```

### Claude Code

```bash
# Extract to:
~/.claude/skills/disk-cleaner/
# OR
your-project/skills/disk-cleaner/
```

Auto-detected by Claude Code.

### Other AI IDEs

The skill works via subprocess - just extract and use!

---

## 🔧 Environment Variables (Optional)

You can set these to override auto-detection:

```bash
# Specify skill location
export DISK_CLEANER_SKILL_PATH=/path/to/disk-cleaner

# Specify Python command
export DISK_CLEANER_PYTHON_CMD=python3

# Enable debug output
export DISK_CLEANER_DEBUG=true
```

**Windows:**
```cmd
set DISK_CLEANER_SKILL_PATH=C:\path\to\disk-cleaner
set DISK_CLEANER_PYTHON_CMD=python
set DISK_CLEANER_DEBUG=true
```

---

## 📁 Directory Structure (After Extraction)

```
disk-cleaner/
├── SKILL.md              # Universal agent guide
├── AGENT_QUICK_REF.txt   # Quick reference
├── NO_PYTHON_GUIDE.md    # Help without Python
├── INSTALL.md            # This file
├── scripts/
│   ├── analyze_disk.py
│   ├── clean_disk.py
│   ├── monitor_disk.py
│   ├── check_skill.py    # Diagnostic tool
│   └── skill_bootstrap.py # Auto-detection module
└── diskcleaner/          # Self-contained modules
```

**No additional installation needed!**

---

## ✅ Verification

### Quick Check

```bash
python scripts/check_skill.py
```

### Detailed Check

```bash
# With debug output
DISK_CLEANER_DEBUG=true python scripts/check_skill.py
```

### Test Python Import

```bash
python scripts/skill_bootstrap.py --test-import
```

---

## 🚨 Troubleshooting

### Problem: Python not found

**Solution:** Install Python 3.7+

**Windows:**
1. Download from https://www.python.org/downloads/
2. ✅ Check "Add Python to PATH"
3. Install

**macOS:**
```bash
brew install python@3.11
```

**Linux:**
```bash
sudo apt install python3  # Debian/Ubuntu
sudo dnf install python3  # Fedora
```

### Problem: Skill not found

**Solution:** The skill searches many locations. If not found:

1. **Set environment variable:**
   ```bash
   export DISK_CLEANER_SKILL_PATH=/path/to/disk-cleaner
   ```

2. **Extract to recommended location:**
   ```bash
   mkdir -p ~/.skills
   cp -r disk-cleaner ~/.skills/
   ```

3. **Run from extracted location:**
   ```bash
   cd /path/to/disk-cleaner
   python scripts/check_skill.py
   ```

### Problem: Permission denied

**Unix-like (macOS/Linux):**
```bash
chmod +x scripts/*.py
```

**Windows:** Run as Administrator if needed

### Problem: Works in terminal but not in IDE

**Solution:** Check IDE can access Python

**Most IDEs:** Just add Python to system PATH

**Specific IDEs:**
- **Cursor:** Settings → Path → Python executable
- **Windsurf:** Settings → Languages → Python
- **Continue:** config.json → pythonPath

---

## 🎓 Usage Examples

### From Terminal

```bash
# Analyze current directory
python scripts/analyze_disk.py

# Preview cleanup
python scripts/clean_disk.py --dry-run

# Monitor disk
python scripts/monitor_disk.py
```

### From Python Script

```python
import subprocess
from pathlib import Path

skill_path = Path("~/skills/disk-cleaner").expanduser()

# Analyze
subprocess.run(
    ['python', 'scripts/analyze_disk.py'],
    cwd=str(skill_path)
)

# Clean preview
subprocess.run(
    ['python', 'scripts/clean_disk.py', '--dry-run'],
    cwd=str(skill_path)
)
```

### From Any AI IDE

The skill is detected automatically in most IDEs.

If not, use subprocess:
```python
!python skills/disk-cleaner/scripts/analyze_disk.py
```

---

## 🔄 Updates

To update the skill:

1. Download new version
2. Extract to same location
3. Overwrite existing files
4. Run `python scripts/check_skill.py` to verify

---

## 📞 Support

If you encounter issues:

1. Run diagnostic: `python scripts/check_skill.py`
2. Enable debug: `DISK_CLEANER_DEBUG=true`
3. Check SKILL.md for troubleshooting
4. See NO_PYTHON_GUIDE.md if you don't have Python

---

## ✨ Features

- ✅ **Platform Independent** - Works everywhere
- ✅ **IDE Agnostic** - Compatible with all AI IDEs
- ✅ **Self-Contained** - No pip install needed
- ✅ **Auto-Detection** - Finds itself automatically
- ✅ **Safe by Default** --dry-run for all operations
- ✅ **Cross-Platform** - Windows, macOS, Linux

---

**That's it! Extract and use - no complex setup required!**

The skill package works everywhere, with every AI IDE, at any installation level.
