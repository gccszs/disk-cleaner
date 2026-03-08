# 🚨 我没有 Python，怎么用这个技能？

## 不要担心！你有几个选择

---

## 选项 1: 安装 Python（推荐，5 分钟）

### 为什么推荐？
- ✅ 一次安装，永久使用
- ✅ 可以运行所有 Python 脚本
- ✅ 这个技能包会完全发挥作用
- ✅ Python 是很多开发工具的基础

### Windows 用户（最简单）

1. **下载 Python**
   - 访问：https://www.python.org/downloads/
   - 点击黄色的大按钮 "Download Python 3.x.x"

2. **安装 Python**
   - 运行下载的安装程序
   - ⚠️ **非常重要**: 勾选底部的 "Add Python to PATH"
   - 点击 "Install Now"

3. **验证安装**
   ```bash
   # 打开新的命令提示符（CMD）
   python --version
   ```
   如果看到 `Python 3.x.x`，说明安装成功！

4. **使用技能包**
   ```bash
   cd skills\disk-cleaner
   python scripts\check_skill.py
   ```

### macOS 用户

1. **使用 Homebrew（如果已安装）**
   ```bash
   brew install python@3.11
   ```

2. **或者从官网下载**
   - 访问：https://www.python.org/downloads/macos/
   - 下载并安装

3. **验证安装**
   ```bash
   python3 --version
   ```

4. **使用技能包**
   ```bash
   cd skills/disk-cleaner
   python3 scripts/check_skill.py
   ```

### Linux 用户

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3

# Fedora/RHEL
sudo dnf install python3

# 验证
python3 --version
```

---

## 选项 2: 使用在线 Python（无需安装）

### Google Colab（推荐）

1. 访问：https://colab.research.google.com/
2. 点击 "新建笔记本"
3. 上传技能包文件
4. 在单元格中运行：
   ```python
   !python scripts/check_skill.py
   ```

### Replit

1. 访问：https://replit.com/
2. 创建新的 Python Repl
3. 上传技能包文件
4. 在终端中运行脚本

---

## 选项 3: 让 Agent 帮你

### 如果你使用 Claude Code

直接告诉 Claude：
```
"我想分析我的磁盘空间，但我不确定是否安装了 Python"
"请帮我检查 Python 环境"
"请帮我安装 Python"
```

### Agent 会做什么？

1. **自动检查** Python 是否已安装
2. **如果没有**，引导你安装
3. **验证安装**是否成功
4. **帮你运行**技能包

### 示例对话

```
你: 我的 C 盘快满了，帮我分析一下

Claude: 我来帮你检查 Python 环境...
[检查中...]
✅ 发现 Python 3.9.0

✅ 找到技能包: C:\...\skills\disk-cleaner

🔍 开始分析磁盘空间...
[运行分析...]

分析完成！发现以下大文件夹：
...
```

```
你: 我有 Python 吗？

Claude: 让我检查一下...

❌ 未找到 Python

🪟 你使用的是 Windows，请按以下步骤安装：

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.11
3. 安装时勾选 "Add Python to PATH"
4. 完成后重启命令行

需要我提供更详细的指导吗？
```

---

## 选项 4: 使用系统自带工具（临时方案）

如果你暂时不想安装 Python，可以使用系统自带的工具：

### Windows

1. **磁盘清理**
   - 打开"此电脑"
   - 右键点击 C 盘，选择"属性"
   - 点击"磁盘清理"

2. **存储感知**
   - 设置 > 系统 > 存储
   - 开启"存储感知"

### macOS

1. **关于本机 > 存储空间**
   - 点击"管理"
   - 查看建议并清理

2. **使用终端命令**
   ```bash
   # 查看文件夹大小
   du -sh ~/Documents
   du -sh ~/Downloads
   ```

### Linux

```bash
# 查看磁盘使用
df -h

# 查看文件夹大小
du -sh ~/*
```

**注意**: 系统工具功能有限，不如这个技能包强大。

---

## 📊 选项对比

| 选项 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| 安装 Python | 功能完整，一次安装永久使用 | 需要 5 分钟安装 | ⭐⭐⭐⭐⭐ |
| 在线 Python | 无需安装 | 需要上传文件，速度较慢 | ⭐⭐⭐ |
| Agent 协助 | 最简单，有指导 | 需要交互 | ⭐⭐⭐⭐ |
| 系统工具 | 无需任何安装 | 功能有限 | ⭐⭐ |

---

## 🎯 推荐流程

1. **先问 Agent**: "帮我检查 Python 环境"
2. **如果已有**: 直接使用技能包
3. **如果没有**: Agent 会引导你安装
4. **安装后**: 享受完整的磁盘管理功能

---

## ❓ 常见问题

### Q: 安装 Python 会影响我的系统吗？

**A**: 不会。Python 是一个解释器，只是让你能运行 Python 脚本。不会修改系统设置。

### Q: 我可以卸载 Python 吗？

**A**: 可以。安装程序会提供卸载选项，或者在控制面板中卸载。

### Q: Python 安全吗？

**A**: 是的。Python 是世界上最流行的编程语言之一，被数百万人使用。

### Q: 安装需要多少空间？

**A**: Python 大约需要 200-300MB 空间。

### Q: 我有多个 Python 版本怎么办？

**A**: 没关系。技能包会自动找到可用的 Python 3.7+ 版本。

---

## 💡 最后建议

**如果你**:
- 🔧 经常需要管理磁盘 → **安装 Python**（一劳永逸）
- 📊 只是想看看磁盘情况 → **让 Agent 帮你**（最简单）
- 🚫 不想安装任何东西 → **使用系统工具**（临时方案）
- 🌐 只需偶尔使用 → **在线 Python**（无需安装）

---

## 📞 仍需要帮助？

告诉 Agent：
```
"我没有 Python，请详细指导我安装"
"我想使用 disk-cleaner 但不知道怎么开始"
"请帮我检查我的系统配置"
```

Agent 会根据你的情况提供个性化的指导！
