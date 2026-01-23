# Disk Cleaner 使用指南

## 快速开始

### 1. 基本用法

```bash
# 分析当前磁盘（Windows上是C:\，Unix上是/）
python scripts/analyze_disk.py

# 清理临时文件（默认是模拟运行，安全）
python scripts/clean_disk.py --dry-run

# 监控磁盘使用情况
python scripts/monitor_disk.py
```

## 2. 路径处理最佳实践

### Windows 路径兼容性

**问题**: 在Git Bash或某些终端中，反斜杠路径可能导致解析错误。

**解决方案 1: 使用正斜杠**
```bash
# ✅ 推荐：使用正斜杠（所有平台都支持）
python scripts/analyze_disk.py --path "D:/Projects"
python scripts/analyze_disk.py --path "C:/Users/YourName/AppData/Local/Temp"

# ⚠️ 避免：反斜杠可能在某些shell中有问题
python scripts/analyze_disk.py --path "D:\Projects"
```

**解决方案 2: 先cd到skill目录**
```bash
# 进入disk-cleaner目录
cd D:/other_pj/my-skills/disk-cleaner/.worktrees/feature-v2.0-enhancement

# 使用相对路径
python scripts/analyze_disk.py --path ../../../
```

**解决方案 3: 使用引号包裹路径**
```bash
# PowerShell / CMD
python scripts\analyze_disk.py --path "D:\Projects"

# Git Bash
python scripts/analyze_disk.py --path "D:/Projects"
```

### 路径处理技巧

```bash
# 当前用户目录
python scripts/analyze_disk.py --path ~

# 当前目录
python scripts/analyze_disk.py --path .

# 上级目录
python scripts/analyze_disk.py --path ..
```

## 3. 扫描限制配置

### 针对不同磁盘大小的建议

**小磁盘 (< 100GB)**
```bash
# 使用默认设置即可
python scripts/analyze_disk.py --path "C:/"
```

**中等磁盘 (100GB - 500GB)**
```bash
# 稍微增加限制
python scripts/analyze_disk.py --path "D:/" --file-limit 1500000 --time-limit 400
```

**大磁盘 (500GB+)**
```bash
# 830GB D盘示例
python scripts/analyze_disk.py --path "D:/" \
    --file-limit 2000000 \
    --time-limit 600 \
    --top 50
```

**完整扫描（无限制）**
```python
# 在Python中使用API，设置为None或超大值
from diskcleaner.core import DirectoryScanner

scanner = DirectoryScanner(
    "D:/",
    max_files=None,  # 无文件数量限制
    max_seconds=None  # 无时间限制
)
files = scanner.scan()
```

## 4. 进度条说明

### 为什么有时看不到进度条？

进度条会自动在以下情况下**禁用**：

1. **非TTY环境**
   - IDE内置终端（PyCharm, VS Code）
   - CI/CD环境（GitHub Actions）
   - 管道输出（`|` 或 `>` 重定向）

2. **JSON输出模式**
   ```bash
   # JSON模式自动禁用进度条
   python scripts/analyze_disk.py --json
   ```

3. **明确禁用**
   ```bash
   # 使用 --no-progress 标志
   python scripts/analyze_disk.py --no-progress
   ```

### 如何看到进度条？

**方法 1: 在真实终端中运行**
```bash
# Windows Terminal, PowerShell, CMD, Git Bash
python scripts/analyze_disk.py --path "D:/"
```

**方法 2: 强制启用（不推荐用于生产）**
需要修改代码，设置 `enable=True`:
```python
from diskcleaner.core.progress import ProgressBar

progress = ProgressBar(total=100, enable=True)  # 强制启用
```

### 终端兼容性

| 终端 | 进度条支持 | 备注 |
|------|----------|------|
| Windows Terminal | ✅ | 推荐 |
| PowerShell | ✅ | 推荐 |
| CMD | ✅ | 支持 |
| Git Bash | ✅ | 支持 |
| PyCharm终端 | ⚠️ | 可能需要配置 |
| VS Code终端 | ⚠️ | 可能需要配置 |
| CI/CD | ❌ | 自动禁用 |

## 5. 常见使用场景

### 场景1: C盘空间不足

```bash
# 1. 分析C盘
python scripts/analyze_disk.py --path "C:/" --top 50

# 2. 预览清理（安全模式）
python scripts/clean_disk.py --dry-run

# 3. 确认后执行清理
python scripts/clean_disk.py --force

# 4. 验证结果
python scripts/analyze_disk.py --path "C:/"
```

### 场景2: 分析大文件占用

```bash
# 查找最大的文件和目录
python scripts/analyze_disk.py --path "D:/" --top 100 --json > report.json

# 使用jq分析JSON（如果安装了）
cat report.json | jq '.scan_results.files | .[0:10]'
```

### 场景3: 定期监控

```bash
# 持续监控（每60秒检查一次）
python scripts/monitor_disk.py --watch --interval 60

# 设置警告阈值
python scripts/monitor_disk.py --warning 70 --critical 85 --watch
```

### 场景4: 自动化脚本

```bash
#!/bin/bash
# disk-cleanup.sh

# 分析（无进度条，JSON输出）
python scripts/analyze_disk.py --json --output report.json

# 清理（无进度条，实际删除）
python scripts/clean_disk.py --force --no-progress

# 再次分析
python scripts/analyze_disk.py --json --output report_after.json

# 对比
echo "清理前:"
jq '.summary.total_space_freed_gb' report.json
echo "清理后:"
jq '.summary.total_space_freed_gb' report_after.json
```

## 6. 参数参考

### analyze_disk.py

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| --path | -p | 当前盘 | 要分析的路径 |
| --top | -n | 20 | 显示最大的N项 |
| --file-limit | - | 1000000 | 最大文件数 |
| --time-limit | - | 300 | 最大扫描时间（秒） |
| --json | - | False | JSON格式输出 |
| --output | -o | - | 保存到文件 |
| --no-progress | - | False | 禁用进度条 |

### clean_disk.py

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --dry-run | True | 模拟运行（安全） |
| --force | False | 实际删除 |
| --temp | False | 只清理临时文件 |
| --cache | False | 只清理缓存 |
| --logs | False | 只清理日志 |
| --recycle | False | 只清理回收站 |
| --downloads | 90 | 清理N天前的下载 |
| --json | False | JSON格式输出 |
| --output | - | 保存到文件 |
| --no-progress | False | 禁用进度条 |

### monitor_disk.py

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --watch | False | 持续监控模式 |
| --interval | 60 | 检查间隔（秒） |
| --warning | 80 | 警告阈值（%） |
| --critical | 90 | 严重阈值（%） |
| --alerts-only | False | 只显示警告 |
| --json | False | JSON格式输出 |

## 7. 故障排除

### 问题1: "Scan stopped early"

**原因**: 达到文件数量或时间限制

**解决**:
```bash
# 增加限制
python scripts/analyze_disk.py --path "D:/" \
    --file-limit 2000000 \
    --time-limit 600
```

### 问题2: "Path is excluded from scanning"

**原因**: 尝试扫描系统保护目录

**解决**:
```bash
# 避免扫描这些目录
# Windows: C:\Windows, C:\Program Files
# macOS: /System, /Library
# Linux: /proc, /sys, /dev

# 改扫描用户目录
python scripts/analyze_disk.py --path ~
```

### 问题3: 进度条不显示

**检查**:
```bash
# 1. 确认在真实终端运行（不是IDE）
# 2. 确认没有使用 --no-progress
# 3. 确认没有使用 --json

# 测试进度条
python scripts/analyze_disk.py --path "C:/Users/YourName/AppData/Local/Temp"
```

### 问题4: PermissionError

**原因**: 权限不足或文件被占用

**解决**:
- 以管理员身份运行
- 关闭占用文件的应用程序
- 脚本会自动跳过无权限的文件，不会中断

## 8. 性能优化建议

### 快速扫描（采样）
```bash
# 使用QuickProfiler（未来功能）
# python scripts/analyze_disk.py --sample
```

### 并发扫描
```python
# 使用并发扫描器API
from diskcleaner.optimization.scan import ConcurrentScanner

scanner = ConcurrentScanner()
results = scanner.scan("D:/")
```

### 缓存优化
```python
# 启用增量扫描
scanner = DirectoryScanner("D:/", cache_enabled=True)
files, new, changed = scanner.scan_incremental()
```

## 9. 最佳实践

1. **先用 --dry-run 测试**
   ```bash
   python scripts/clean_disk.py --dry-run
   ```

2. **定期监控而非一次性清理**
   ```bash
   python scripts/monitor_disk.py --watch --interval 300
   ```

3. **保存报告以跟踪趋势**
   ```bash
   python scripts/analyze_disk.py --output report_$(date +%Y%m%d).json
   ```

4. **使用适当的限制**
   - 小磁盘: 默认设置
   - 大磁盘: 增加 --file-limit 和 --time-limit
   - 生产环境: 使用 --no-progress 和 --json

5. **安全性**
   - 永远先运行 --dry-run
   - 检查报告后再使用 --force
   - 避免扫描系统目录

## 10. 获取帮助

```bash
# 查看帮助
python scripts/analyze_disk.py --help
python scripts/clean_disk.py --help
python scripts/monitor_disk.py --help

# 查看版本和文档
python -m diskcleaner --help
```

## 相关文档

- `SKILL.md` - 完整功能文档
- `README.md` - 项目介绍
- `docs/PLANS.md` - 开发计划
- `tests/` - 测试用例（更多使用示例）
