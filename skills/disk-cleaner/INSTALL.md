# Disk Cleaner 技能包 - 安装和使用指南

## 📦 技能包信息

- **名称**: disk-cleaner
- **版本**: 2.0.0
- **类型**: Claude Code 技能包
- **平台**: Windows / macOS / Linux (跨平台)
- **Python 要求**: 3.7+

## 🎯 主要功能

1. **高性能磁盘扫描** - 使用 os.scandir() 优化，速度提升 3-5 倍
2. **智能清理** - 安全清理临时文件、缓存、日志等
3. **磁盘监控** - 实时监控磁盘使用情况，设置警告阈值
4. **跨平台支持** - 完全支持 Windows、macOS、Linux
5. **独立运行** - 无需预先安装任何依赖

## 📥 安装方法

### 方法 1: 直接解压（推荐）

1. 下载 `disk-cleaner.skill` 文件
2. 重命名为 `disk-cleaner.zip`
3. 解压到你的技能目录：
   - **Windows**: `%USERPROFILE%\.claude\skills\disk-cleaner\`
   - **macOS/Linux**: `~/.claude/skills/disk-cleaner/`

### 方法 2: Claude Code 安装

在 Claude Code 中使用：
```
/install-skill path/to/disk-cleaner.skill
```

### 方法 3: 手动安装

```bash
# 创建技能目录
mkdir -p ~/.claude/skills/disk-cleaner

# 复制文件
cp -r disk-cleaner/* ~/.claude/skills/disk-cleaner/
```

## ✅ 验证安装

运行诊断工具检查安装：

```bash
cd ~/.claude/skills/disk-cleaner
python scripts/check_skill.py
```

预期输出：
```
============================================================
 诊断总结
============================================================

通过: 6/6
[OK] Python 版本
[OK] 操作系统
[OK] 文件结构
[OK] 模块导入
[OK] 文件权限
[OK] 脚本测试

🎉 所有检查通过！技能包可以正常使用。
```

## 🚀 使用方法

### 1. 分析磁盘空间

```bash
# 分析当前驱动器
python scripts/analyze_disk.py

# 分析特定路径
python scripts/analyze_disk.py --path "D:\Projects"

# 显示前 50 个最大项目
python scripts/analyze_disk.py --top 50

# 输出 JSON 格式
python scripts/analyze_disk.py --json --output report.json

# 分析大目录（自定义限制）
python scripts/analyze_disk.py --path "D:/" --file-limit 2000000 --time-limit 600
```

### 2. 清理垃圾文件

**⚠️ 重要**: 首次使用请务必使用 `--dry-run` 预览！

```bash
# 预览清理（安全模式）
python scripts/clean_disk.py --dry-run

# 实际清理
python scripts/clean_disk.py --force

# 清理特定类别
python scripts/clean_disk.py --temp --cache --dry-run
python scripts/clean_disk.py --logs --dry-run
python scripts/clean_disk.py --recycle --dry-run

# 清理旧下载文件（90 天以上）
python scripts/clean_disk.py --downloads 90 --dry-run

# 清理自定义路径
python scripts/clean_disk.py --path "D:\Temp" --dry-run
```

### 3. 监控磁盘使用

```bash
# 检查当前状态
python scripts/monitor_disk.py

# 持续监控（每 60 秒）
python scripts/monitor_disk.py --watch

# 自定义阈值
python scripts/monitor_disk.py --warning 70 --critical 85

# 自定义监控间隔（5 分钟）
python scripts/monitor_disk.py --watch --interval 300

# 仅显示警报（CI/CD 友好）
python scripts/monitor_disk.py --alerts-only
```

## 🧪 高级功能

### 智能扫描优化

技能包内置高性能扫描算法：

- **os.scandir() 优化**: 3-5 倍速度提升
- **并发扫描**: 多线程 I/O 操作
- **智能采样**: 大目录快速估算
- **内存自适应**: 自动监控内存使用
- **早期停止**: 文件数/时间限制

```bash
# 使用智能采样快速分析
python scripts/analyze_disk.py --sample

# 设置文件数限制
python scripts/analyze_disk.py --file-limit 1000000

# 设置时间限制
python scripts/analyze_disk.py --time-limit 300
```

### 错误诊断

如果遇到问题：

```bash
# 运行完整诊断
python scripts/check_skill.py

# 测试模块导入
python scripts/skill_bootstrap.py --test-import

# 启用调试模式
DISK_CLEANER_DEBUG=true python scripts/analyze_disk.py
```

## 🛡️ 安全特性

### 保护路径

技能包永远不会删除以下路径：
- **Windows**: `C:\Windows`, `C:\Program Files`, `C:\ProgramData`
- **macOS**: `/System`, `/Library`, `/Applications`
- **Linux**: `/usr`, `/bin`, `/sbin`, `/lib`, `/etc`

### 保护扩展

以下文件扩展名永远不会被删除：
```
.exe, .dll, .sys, .drv, .bat, .cmd, .ps1, .vbs
.sh, .bash, .zsh, .fish
.app, .dmg, .pkg
.deb, .rpm, .msi, .iso
.vhd, .vhdx, .vmdk
```

### 安全模式

默认情况下，所有清理操作都是 `--dry-run`（预览）模式，必须使用 `--force` 才会实际删除文件。

## 📊 性能指标

根据测试数据：

| 操作 | 性能 |
|------|------|
| 扫描 100K 文件 | ~2-3 秒 |
| 扫描 500K 文件 | ~10-15 秒 |
| 清理 10K 文件 | ~5-10 秒 |
| 内存使用 | <50MB |

## 🐛 故障排除

### 问题：模块导入失败

**症状**:
```
ImportError: No module named 'diskcleaner'
```

**解决方案**:
1. 确保从技能目录运行脚本
2. 运行诊断：`python scripts/check_skill.py`
3. 检查文件结构是否完整

### 问题：编码错误（Windows）

**症状**:
```
UnicodeEncodeError: 'gbk' codec can't encode character
```

**解决方案**:
技能包已内置编码处理，如果仍有问题：
```bash
chcp 65001  # 设置控制台为 UTF-8
python scripts/analyze_disk.py
```

### 问题：权限错误

**症状**:
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**:
- 技能包会自动跳过无权限的文件/目录
- 以管理员身份运行（如果需要）
- 检查文件/目录权限设置

## 📝 技能包结构

```
disk-cleaner/
├── SKILL.md              # 技能说明文档
├── README.txt            # 快速开始指南
├── skill.json            # 技能包元数据
├── scripts/              # 可执行脚本
│   ├── analyze_disk.py   # 磁盘分析工具
│   ├── clean_disk.py     # 清理工具
│   ├── monitor_disk.py   # 监控工具
│   ├── check_skill.py    # 诊断工具
│   ├── skill_bootstrap.py # 引导模块
│   ├── package_skill.py  # 打包工具
│   └── scheduler.py      # 调度器
├── diskcleaner/          # 核心模块
│   ├── __init__.py
│   ├── config/           # 配置管理
│   ├── core/             # 核心功能
│   ├── optimization/     # 性能优化
│   └── platforms/        # 平台适配
└── references/           # 参考文档
    └── temp_locations.md # 临时文件位置
```

## 🔄 更新技能包

当有新版本时：

1. 备份当前版本：
   ```bash
   mv ~/.claude/skills/disk-cleaner ~/.claude/skills/disk-cleaner.backup
   ```

2. 安装新版本（参考安装方法）

3. 验证：
   ```bash
   python scripts/check_skill.py
   ```

4. 如果满意，删除备份：
   ```bash
   rm -rf ~/.claude/skills/disk-cleaner.backup
   ```

## 📞 获取帮助

- 运行 `--help` 查看详细选项
- 运行诊断工具获取详细信息
- 查看 SKILL.md 了解更多细节
- 查看 references/temp_locations.md 了解平台特定信息

## ⚖️ 许可证

MIT License - 详见项目文件

---

**享受干净的磁盘！** 🎉
