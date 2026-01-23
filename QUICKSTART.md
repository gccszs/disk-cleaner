# Disk Cleaner - 快速入门指南

## Windows 用户快速开始

### 方法1: 使用批处理脚本（最简单）

双击运行以下脚本：

1. **`scripts\analyze_disk.bat`** - 分析磁盘空间
2. **`scripts\clean_disk.bat`** - 清理磁盘（默认安全模式）
3. **`scripts\monitor_disk.bat`** - 监控磁盘使用

**示例**:
```batch
# 在命令提示符中
cd D:\other_pj\my-skills\disk-cleaner\.worktrees\feature-v2.0-enhancement

# 分析D盘
scripts\analyze_disk.bat D: 50

# 预览清理（安全）
scripts\clean_disk.bat

# 实际清理
scripts\clean_disk.bat force
```

### 方法2: 使用Python命令

**基本命令**:
```bash
# 分析C盘
python scripts/analyze_disk.py

# 分析D盘（推荐使用正斜杠）
python scripts/analyze_disk.py --path "D:/"

# 预览清理
python scripts/clean_disk.py --dry-run

# 实际清理
python scripts/clean_disk.py --force
```

**大磁盘扫描**:
```bash
# 830GB D盘示例
python scripts/analyze_disk.py --path "D:/" --file-limit 2000000 --time-limit 600 --top 50
```

### 方法3: 使用PowerShell

```powershell
# 分析D盘
python scripts/analyze_disk.py -path "D:/"

# 清理临时文件
python scripts/clean_disk.py -temp -dry-run

# 持续监控
python scripts/monitor_disk.py -watch -interval 60
```

## 常见问题

### Q: 为什么使用正斜杠 `/` 而不是反斜杠 `\`？

**A**: Windows支持两种斜杠，但正斜杠在所有平台和shell中都能正确工作：
```bash
# ✅ 推荐（所有平台通用）
python scripts/analyze_disk.py --path "D:/Projects"

# ⚠️ 可能有问题（某些shell解析错误）
python scripts\analyze_disk.py --path "D:\Projects"
```

### Q: 如何分析大磁盘（500GB+）？

**A**: 增加扫描限制：
```bash
python scripts/analyze_disk.py --path "D:/" --file-limit 2000000 --time-limit 600
```

### Q: 为什么看不到进度条？

**A**: 进度条在以下情况下自动禁用：
- IDE内置终端（PyCharm, VS Code）
- 使用 `--json` 参数
- 使用 `--no-progress` 参数

**解决**: 在Windows Terminal、PowerShell或CMD中运行

### Q: 如何安全地清理磁盘？

**A**: 始终先使用 `--dry-run`:
```bash
# 1. 预览（安全）
python scripts/clean_disk.py --dry-run

# 2. 检查报告后实际执行
python scripts/clean_disk.py --force
```

## 推荐工作流

### 场景1: C盘空间不足

```bash
# 步骤1: 分析C盘
python scripts/analyze_disk.py --path "C:/" --top 50

# 步骤2: 预览清理
python scripts/clean_disk.py --dry-run

# 步骤3: 实际清理
python scripts/clean_disk.py --force

# 步骤4: 验证结果
python scripts/analyze_disk.py --path "C:/"
```

### 场景2: 定期维护

```bash
# 监控磁盘使用（每分钟检查）
python scripts/monitor_disk.py --watch --interval 60 --warning 70
```

### 场景3: 自动化脚本

创建批处理文件 `my_cleanup.bat`:
```batch
@echo off
echo 开始清理...

REM 预览
python scripts/clean_disk.py --dry-run --json > before.json

REM 实际清理
python scripts/clean_disk.py --force

REM 验证
python scripts/clean_disk.py --dry-run --json > after.json

echo 完成！
pause
```

## 获取更多帮助

```bash
# 查看完整参数
python scripts/analyze_disk.py --help
python scripts/clean_disk.py --help
python scripts/monitor_disk.py --help

# 阅读使用指南
# 查看 USAGE_GUIDE.md 文件
```

## 下一步

- 📖 阅读 `USAGE_GUIDE.md` - 详细使用指南
- 📚 阅读 `SKILL.md` - 完整功能文档
- 🧪 查看 `tests/` - 更多使用示例
