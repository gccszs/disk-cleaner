# Platform-Specific Temporary File Locations

This document provides comprehensive information about temporary file locations across different operating systems.

## Windows

### Environment Variables
- `%TEMP%` - User temporary files
- `%TMP%` - User temporary files (alias)
- `%LOCALAPPDATA%\Temp` - Local application temp

### System Locations
- `C:\Windows\Temp` - System temporary files
- `C:\Windows\Prefetch` - Application prefetch data
- `C:\Windows\SoftwareDistribution\Download` - Windows Update cache
- `C:\Windows\Logs` - Windows logs
- `C:\Windows\Debug` - Debug logs
- `C:\Windows\Minidump` - Crash dumps

### User Profile Locations
- `%LOCALAPPDATA%\Microsoft\Windows\INetCache` - Internet Explorer cache
- `%LOCALAPPDATA%\Microsoft\Windows\History` - Browser history
- `%LOCALAPPDATA%\Microsoft\Windows\WebCache` - Web cache
- `%LOCALAPPDATA%\Temp` - Local temp files
- `%APPDATA%\Microsoft\Windows\Recent` - Recent files shortcuts
- `%USERPROFILE%\AppData\LocalLow\Microsoft\CryptnetUrlCache\Content` - Crypto cache
- `%USERPROFILE%\AppData\LocalLow\Microsoft\CryptnetUrlCache\MetaData` - Crypto metadata

### Browser Caches
- Chrome: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache`
- Chrome: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache`
- Edge: `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache`
- Firefox: `%APPDATA%\Mozilla\Firefox\Profiles\*.default-release\cache2`
- Firefox: `%LOCALAPPDATA%\Mozilla\Firefox\Profiles\*.default-release\startupCache`

### Application Caches
- VS Code: `%USERPROFILE%\.vscode\logs`
- npm: `%LOCALAPPDATA%\npm-cache`
- pip: `%LOCALAPPDATA%\pip\cache`
- yarn: `%LOCALAPPDATA%\Yarn\Cache`
- Gradle: `%USERPROFILE%\.gradle\caches`
- Maven: `%USERPROFILE%\.m2\repository`

### Recycle Bin
- `C:\$Recycle.Bin\` - All users' recycle bins

## macOS

### System Locations
- `/tmp` - System temporary files
- `/private/tmp` - Private temporary files
- `/private/var/tmp` - Variable temporary files
- `/private/var/folders` - Per-session temporary files
- `/Library/Caches` - System-wide caches
- `/Library/Logs` - System logs

### User Locations
- `~/Library/Caches` - User application caches
- `~/Library/Logs` - User application logs
- `~/Library/Application Support/CrashReporter` - Crash reports
- `~/.Trash` - User's trash
- `~/Downloads` - Downloaded files

### Browser Caches
- Safari: `~/Library/Caches/com.apple.Safari`
- Chrome: `~/Library/Caches/Google/Chrome/Default/Cache`
- Firefox: `~/Library/Caches/Firefox/Profiles/*.default-release`

### Development Tools
- npm: `~/.npm`
- pip: `~/Library/Caches/pip`
- Homebrew: `/Library/Caches/Homebrew`
- Docker: `~/Library/Containers/com.docker.docker/Data`

### iOS Backups
- `~/Library/Application Support/MobileSync/Backup`

## Linux

### System Locations
- `/tmp` - Temporary files (cleared on reboot)
- `/var/tmp` - Persistent temporary files
- `/var/cache` - Application cache
- `/var/log` - System logs
- `/var/crash` - Crash dumps

### Package Manager Caches
- apt (Debian/Ubuntu): `/var/cache/apt/archives`
- dnf/yum (Fedora/RHEL): `/var/cache/dnf`
- pacman (Arch): `/var/cache/pacman/pkg`
- snap: `/var/lib/snapd/snaps`

### User Locations
- `~/.cache` - User cache (XDG standard)
- `~/.local/share/Trash` - User's trash
- `~/.thumbnails` - Thumbnail cache
- `~/.local/share/Trash/files` - Trash files
- `~/.local/share/Trash/info` - Trash metadata

### Browser Caches
- Chrome: `~/.cache/google-chrome`
- Firefox: `~/.cache/mozilla/firefox`
- Chromium: `~/.cache/chromium`

### Development Tools
- npm: `~/.npm`
- yarn: `~/.yarn/cache`
- pip: `~/.cache/pip`
- conda: `~/.conda/pkgs`
- Docker: `/var/lib/docker`

## Safety Guidelines

### Never Delete
- System directories (`/System`, `/Windows`, `/Program Files`, `/usr`, `/bin`, `/sbin`, `/lib`)
- User executables (`.exe`, `.dll`, `.sys`, `.app`, `.deb`, `.rpm`)
- Critical system files (boot loaders, kernel files)
- Active database files
- Virtual machine disk images (unless verified unused)

### Always Verify Before Deleting
- Large files in user directories
- Application data directories
- Custom configuration files
- Files with unknown purposes

### Safe to Delete (Generally)
- `*.tmp` files
- `*.log` files (older than 30 days)
- `*.cache` directories
- `*.bak` files
- `~$*` temporary office files
- `.DS_Store` (macOS)
- `Thumbs.db` (Windows)
- Browser cache
- Old download files (with user verification)
