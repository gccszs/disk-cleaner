# 磁盘清理工具 v2.0 - 智能跨平台磁盘管理

**[English](README.md)** | **[中文文档](README_zh.md)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/gccszs/disk-cleaner)
[![Skill](https://img.shields.io/badge/skill-add--skill-blue)](https://github.com/gccszs/disk-cleaner)

一个全面的跨平台磁盘空间监控、分析和智能清理工具包。具备先进的3D文件分类、重复文件检测、自动化调度和平台特定优化功能。

## ✨ v2.0 新特性

- **🤖 智能3D分类** - 按类型、风险等级和文件年龄对文件进行分类
- **🔍 自适应重复检测** - 快速/准确策略，自动优化性能
- **⚡ 增量扫描** - 基于缓存的性能优化，重复扫描速度提升10倍
- **🔒 进程感知安全** - 文件锁定检测和进程终止
- **💻 平台特定优化** - Windows更新、APT、Homebrew缓存检测
- **⏰ 自动化调度** - 基于定时器的清理任务
- **🎯 交互式清理UI** - 5种视图模式，带可视化反馈
- **🛡️ 增强安全性** - 受保护路径、'YES'确认机制、备份和日志记录

## 功能特性

### 核心能力
- **磁盘空间分析**：识别占用磁盘空间的大文件和目录
- **智能清理**：基于文件模式和使用情况的AI驱动建议
- **重复文件检测**：查找并删除重复文件以回收空间
- **安全垃圾清理**：内置安全机制，清理临时文件、缓存、日志
- **磁盘监控**：实时监控，可配置告警阈值
- **跨平台**：完全支持 Windows、Linux 和 macOS
- **零依赖**：纯Python标准库实现

### 高级特性
- **3D文件分类**：类型 × 风险 × 年龄矩阵，智能决策
- **增量扫描**：仅扫描变更的文件，后续扫描速度提升10倍
- **文件锁定检测**：防止在所有平台上删除锁定的文件
- **平台特定清理**：Windows更新、Linux包管理器缓存、macOS Xcode衍生数据
- **自动化调度**：设置自定义间隔的定期清理任务
- **交互式选择**：通过详细预览精确选择要清理的内容

## 快速开始

### 前置要求

Python 3.6 或更高版本（无需外部依赖 - 仅使用标准库）。

### 安装

#### 方式1：作为技能安装（推荐）

```bash
npx add-skill gccszs/disk-cleaner
```

#### 方式2：克隆仓库

```bash
git clone https://github.com/gccszs/disk-cleaner.git
cd disk-cleaner
```

### 基本使用

```bash
# 分析磁盘空间
python scripts/analyze_disk.py

# 智能清理及重复检测（v2.0新增）
python -c "from diskcleaner.core import SmartCleanupEngine; engine = SmartCleanupEngine('.'); print(engine.get_summary(engine.analyze()))"

# 预览清理（干运行模式）
python scripts/clean_disk.py --dry-run

# 监控磁盘使用
python scripts/monitor_disk.py

# 持续监控
python scripts/monitor_disk.py --watch
```

### v2.0 高级使用

```bash
# 调度自动清理（v2.0新增）
python scripts/scheduler.py add "每日清理" /tmp 24h --type smart
python scripts/scheduler.py run  # 执行到期任务

# 平台特定清理建议
python -c "from diskcleaner.platforms import WindowsPlatform; import pprint; pprint.pprint(WindowsPlatform.get_system_maintenance_items())"
```

## 使用示例

### 示例1：智能清理及重复检测

```python
from diskcleaner.core import SmartCleanupEngine

# 初始化引擎
engine = SmartCleanupEngine("/path/to/clean", cache_enabled=True)

# 分析目录
report = engine.analyze(
    include_duplicates=True,
    safety_check=True
)

# 获取摘要
print(engine.get_summary(report))

# 交互式清理（如果需要）
from diskcleaner.core import InteractiveCleanupUI
ui = InteractiveCleanupUI(report)
ui.display_menu()  # 显示5个视图选项
```

### 示例2：自动化调度

```bash
# 添加每日清理任务
python scripts/scheduler.py add "每日临时文件清理" /tmp 24h --type temp

# 列出所有计划任务
python scripts/scheduler.py list

# 运行到期任务（默认干运行）
python scripts/scheduler.py run

# 实际删除运行
python scripts/scheduler.py run --force
```

### 示例3：平台特定清理

```python
from diskcleaner.platforms import WindowsPlatform, LinuxPlatform, MacOSPlatform
import platform

if platform.system() == "Windows":
    platform_impl = WindowsPlatform()
elif platform.system() == "Linux":
    platform_impl = LinuxPlatform()
else:
    platform_impl = MacOSPlatform()

# 获取平台特定的清理建议
items = platform_impl.get_system_maintenance_items()
for key, item in items.items():
    print(f"{item['name']}: {item['description']}")
    print(f"  风险: {item['risk']}, 大小: {item['size_hint']}")
```

## 安装

### 快速安装（推荐）

使用 Vercel 的 add-skill CLI 直接从 GitHub 安装：

```bash
npx add-skill gccszs/disk-cleaner -g
```

将 `gccszs` 替换为你的实际 GitHub 用户名。

### 作为 Claude Code 技能（手动）

1. 从 [发布页面](https://github.com/gccszs/disk-cleaner/releases) 下载 `disk-cleaner.skill`
2. 通过 Claude Code 安装：
   ```
   /skill install path/to/disk-cleaner.skill
   ```

### 独立使用

```bash
# 克隆仓库
git clone https://github.com/gccszs/disk-cleaner.git
cd disk-cleaner

# 脚本可直接使用（无需依赖）
python scripts/analyze_disk.py
```

## 使用示例

### 磁盘空间分析

```bash
# 分析当前驱动器（Windows上为 C:\，Unix上为 /）
python scripts/analyze_disk.py

# 分析特定路径
python scripts/analyze_disk.py --path "D:\Projects"

# 获取前50个最大项目
python scripts/analyze_disk.py --top 50

# 输出为JSON格式以便自动化
python scripts/analyze_disk.py --json

# 保存报告到文件
python scripts/analyze_disk.py --output disk_report.json
```

### 清理垃圾文件

**重要提示**：始终先使用 `--dry-run` 预览变更！

```bash
# 预览清理（推荐的第一步）
python scripts/clean_disk.py --dry-run

# 实际清理文件
python scripts/clean_disk.py --force

# 清理特定类别
python scripts/clean_disk.py --temp       # 仅清理临时文件
python scripts/clean_disk.py --cache      # 仅清理缓存
python scripts/clean_disk.py --logs       # 仅清理日志
python scripts/clean_disk.py --recycle    # 仅清理回收站
python scripts/clean_disk.py --downloads 90  # 清理90天以上的下载文件
```

### 磁盘监控

```bash
# 检查当前状态
python scripts/monitor_disk.py

# 持续监控（每60秒）
python scripts/monitor_disk.py --watch

# 自定义阈值
python scripts/monitor_disk.py --warning 70 --critical 85

# 告警模式（CI/CD友好 - 基于状态的退出代码）
python scripts/monitor_disk.py --alerts-only

# 自定义监控间隔（5分钟）
python scripts/monitor_disk.py --watch --interval 300
```

## 脚本参考

### `analyze_disk.py`

磁盘空间分析工具，识别空间消耗模式。

**能力：**
- 扫描目录以查找最大的文件和文件夹
- 分析临时文件位置
- 计算磁盘使用统计
- 生成详细报告

### `clean_disk.py`

安全的垃圾文件删除，具有多重安全机制。

**安全特性：**
- 受保护的路径（从不删除系统目录）
- 受保护的扩展名（从不删除可执行文件）
- 默认干运行模式
- 所有操作的详细日志记录

**清理类别：**
- **temp**：临时文件（%TEMP%、/tmp等）
- **cache**：应用程序和浏览器缓存
- **logs**：日志文件（默认30天以上）
- **recycle**：回收站/废纸篓
- **downloads**：旧的下载文件（可配置年龄）

### `monitor_disk.py`

持续或一次性磁盘使用监控。

**特性：**
- 多驱动器监控（所有挂载点）
- 可配置的警告/严重阈值
- 带告警的持续监控模式
- 用于自动化的JSON输出
- CI/CD集成的非零退出代码

**退出代码：**
- `0`：所有驱动器正常
- `1`：超过警告阈值
- `2`：超过严重阈值

## 平台支持

| 功能 | Windows | Linux | macOS |
|---------|---------|-------|-------|
| 磁盘分析 | ✅ | ✅ | ✅ |
| 临时清理 | ✅ | ✅ | ✅ |
| 缓存清理 | ✅ | ✅ | ✅ |
| 日志清理 | ✅ | ✅ | ✅ |
| 回收站 | ✅ | ✅ | ✅ |
| 实时监控 | ✅ | ✅ | ✅ |

### Windows 特定位置
- `%TEMP%`、`%TMP%`、`%LOCALAPPDATA%\Temp`
- `C:\Windows\Temp`、`C:\Windows\Prefetch`
- `C:\Windows\SoftwareDistribution\Download`
- 浏览器缓存（Chrome、Edge、Firefox）
- 开发工具缓存（npm、pip、Gradle、Maven）

### Linux 特定位置
- `/tmp`、`/var/tmp`、`/var/cache`
- 包管理器缓存（apt、dnf、pacman）
- 浏览器缓存
- 开发工具缓存

### macOS 特定位置
- `/tmp`、`/private/tmp`、`/var/folders`
- `~/Library/Caches`、`~/Library/Logs`
- iOS设备备份
- Homebrew缓存

## 安全特性

### 受保护的路径
系统目录永远不会被触动：
- Windows：`C:\Windows`、`C:\Program Files`、`C:\ProgramData`
- Linux/macOS：`/usr`、`/bin`、`/sbin`、`/System`、`/Library`

### 受保护的扩展名
可执行文件和系统文件受保护：
```
.exe, .dll, .sys, .drv, .bat, .cmd, .ps1, .sh, .bash, .zsh,
.app, .dmg, .pkg, .deb, .rpm, .msi, .iso, .vhd, .vhdx
```

## 使用场景

### 1. 释放Windows上的C盘空间
```bash
# 分析占用空间的内容
python scripts/analyze_disk.py

# 预览清理
python scripts/clean_disk.py --dry-run

# 执行清理
python scripts/clean_disk.py --force
```

### 2. 自动化磁盘监控
```bash
# 使用自定义阈值在后台运行
python scripts/monitor_disk.py --watch --warning 70 --critical 85 --interval 300
```

### 3. CI/CD集成
```bash
# 在管道中检查磁盘空间
python scripts/monitor_disk.py --alerts-only --json

# 退出代码：0=正常，1=警告，2=严重
if [ $? -ne 0 ]; then
  echo "检测到磁盘空间问题！"
fi
```

## 开发

### 项目结构
```
disk-cleaner/
├── SKILL.md                 # Claude Code 技能定义
├── README.md                # 英文文档
├── README_zh.md             # 中文文档（本文件）
├── CHANGELOG.md             # 更新日志
├── scripts/
│   ├── analyze_disk.py      # 磁盘分析工具
│   ├── clean_disk.py        # 垃圾文件清理器
│   └── monitor_disk.py      # 磁盘使用监控
└── references/
    └── temp_locations.md    # 平台特定的临时文件位置
```

### 贡献
欢迎贡献！请随时提交 Pull Request。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 免责声明

本工具会修改系统上的文件。始终：
1. 在实际清理前查看干运行输出
2. 清理前备份重要数据
3. 使用风险自负

作者不对任何数据丢失或系统问题负责。

## 致谢

- 作为 [Claude Code 技能](https://claude.com/claude-code) 构建
- 可通过 [Vercel 的 add-skill CLI](https://github.com/vercel/vercel/tree/main/packages/add-skill) 安装
- 跨平台兼容性已在 Windows 10/11、Ubuntu 20.04+、macOS 12+ 上测试
