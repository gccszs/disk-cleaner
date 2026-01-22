# disk-cleaner Skill 增强设计方案

**日期:** 2025-01-22
**版本:** v2.0
**状态:** 设计阶段

## 目录

1. [设计概述](#设计概述)
2. [架构设计](#架构设计)
3. [核心功能模块](#核心功能模块)
4. [交互设计](#交互设计)
5. [配置系统](#配置系统)
6. [安全增强](#安全增强)
7. [自动化工作流](#自动化工作流)
8. [测试与质量保证](#测试与质量保证)
9. [开发者体验](#开发者体验)
10. [实施计划](#实施计划)

---

## 设计概述

### 设计目标

在现有 disk-cleaner skill 基础上，增强以下能力：

1. **智能清理** - 基于文件类型、风险等级、时间特征三维分类，提供个性化清理建议
2. **重复文件检测** - 自适应策略，快速识别重复文件，优先展示可释放空间最大的项
3. **增量扫描** - 缓存机制，显著提升重复扫描性能
4. **跨平台增强** - 自动检测并提示平台特定清理项目（Windows Update、Docker、Homebrew 等）
5. **全面安全** - 文件锁检测、进程终止、权限验证、备份机制
6. **自动化能力** - 定时任务、事件驱动、通知集成
7. **开发友好** - 完整测试、类型注解、开发文档

### 核心原则

- **安全第一** - 必须得到用户明确确认才能删除
- **跨平台兼容** - Windows、Linux、macOS 同等支持
- **性能优化** - 增量扫描、自适应策略
- **用户友好** - 清晰的展示、灵活的配置

---

## 架构设计

### 目录结构

```
disk-cleaner/
├── SKILL.md                       # Skill 定义
├── README.md                      # 用户文档
├── LICENSE                        # MIT 许可证
│
├── scripts/                       # 可执行脚本
│   ├── analyze_disk.py            # 磁盘分析（增强）
│   ├── clean_disk.py              # 垃圾清理（增强）
│   ├── monitor_disk.py            # 磁盘监控（增强）
│   ├── smart_cleanup.py           # 新增：智能清理
│   ├── duplicate_finder.py        # 新增：重复文件检测
│   └── scheduler.py               # 新增：定时任务
│
├── diskcleaner/                   # 核心模块
│   ├── __init__.py
│   │
│   ├── core/                      # 核心功能
│   │   ├── scanner.py             # 目录扫描引擎
│   │   ├── classifier.py          # 文件分类器
│   │   ├── safety.py              # 安全检查器
│   │   └── cache.py               # 增量扫描缓存
│   │
│   ├── platforms/                 # 平台特定
│   │   ├── __init__.py
│   │   ├── windows.py             # Windows 特定
│   │   ├── linux.py               # Linux 特定
│   │   └── macos.py               # macOS 特定
│   │
│   └── config/                    # 配置管理
│       ├── __init__.py
│       ├── loader.py              # 配置加载器
│       └── defaults.py            # 默认配置
│
├── tests/                         # 测试套件
│   ├── conftest.py                # pytest 配置
│   ├── test_*.py                  # 单元测试
│   ├── benchmarks/               # 性能测试
│   └── fixtures/                 # 测试数据
│
├── examples/                      # 使用示例
│   ├── basic_usage.py
│   ├── advanced_cleanup.py
│   └── scripts/                   # 实用脚本
│
├── docs/                          # 文档
│   ├── CONTRIBUTING.md
│   ├── DEVELOPMENT.md
│   ├── ARCHITECTURE.md
│   ├── TESTING.md
│   └── API.md
│
└── references/                    # 参考资料
    └── temp_locations.md
```

### 核心工作流程

```
用户输入
   ↓
加载配置（命令行 > 项目 > 用户 > 默认）
   ↓
目录扫描（增量模式）
   ↓
三维分类（类型、风险、时间）
   ↓
重复文件检测（自适应策略）
   ↓
平台特定项目检测
   ↓
安全检查（文件锁、权限等）
   ↓
交互式展示（用户选择视图）
   ↓
用户选择清理项
   ↓
最终确认（输入 YES）
   ↓
执行删除（备份、日志）
   ↓
生成报告
```

---

## 核心功能模块

### 1. 智能清理引擎

**smart_cleanup.py** - 核心清理逻辑

```python
class SmartCleanupEngine:
    def __init__(self, target_path: str, config: Config):
        self.scanner = DirectoryScanner(target_path, cache_enabled=True)
        self.classifier = FileClassifier(config)
        self.duplicate_finder = DuplicateFinder(strategy='adaptive')
        self.safety = SafetyChecker(config)

    def analyze(self) -> CleanupReport:
        """扫描并生成清理建议"""
        # 1. 增量扫描
        files = self.scanner.scan_incremental()

        # 2. 三维分类
        categories = self.classifier.classify(files)

        # 3. 重复文件检测
        duplicates = self.duplicate_finder.find_duplicates(files)

        # 4. 平台特定项目
        platform_items = detect_platform_specific()

        # 5. 安全检查
        safe_items = self.safety.verify_all(
            categories + duplicates + platform_items
        )

        return CleanupReport(
            by_type=group_by_type(safe_items),
            by_risk=group_by_risk(safe_items),
            by_age=group_by_age(safe_items),
            total_reclaimable=sum_size(safe_items)
        )

    def interactive_cleanup(self, report: CleanupReport):
        """交互式清理流程"""
        # 1. 选择视图
        view_mode = self._select_view_mode()

        # 2. 展示报告
        self._display_report(report, view_mode)

        # 3. 用户选择
        selected = self._select_items(report)

        # 4. 最终确认
        if self._confirm_cleanup(selected):
            # 5. 执行删除
            self._execute_cleanup(selected)
```

### 2. 重复文件检测

**duplicate_finder.py** - 自适应策略

```python
class DuplicateFinder:
    def __init__(self, strategy: str = 'adaptive'):
        self.strategy = strategy
        self.cache = CacheManager()

    def find_duplicates(self, files: List[FileInfo]) -> List[DuplicateGroup]:
        """查找重复文件"""
        # 策略选择
        if self.strategy == 'adaptive':
            use_accurate = len(files) < 1000
        else:
            use_accurate = self.strategy == 'accurate'

        # 查找重复
        if use_accurate:
            duplicates = self._find_by_hash(files)
        else:
            duplicates = self._find_by_fast_strategy(files)

        # 排序：按可回收空间
        duplicates.sort(
            key=lambda d: d['size'] * (d['count'] - 1),
            reverse=True
        )

        return duplicates

    def _find_by_fast_strategy(self, files):
        """快速策略：先筛选，再哈希"""
        # 1. 按大小分组
        by_size = group_by_size(files)

        # 2. 只对疑似重复的文件计算哈希
        candidates = [g for g in by_size.values() if len(g) > 1]

        # 3. 精确验证
        duplicates = []
        for group in candidates:
            hashes = {}
            for file in group:
                hash = self._compute_hash(file)
                if hash in hashes:
                    hashes[hash].append(file)
                else:
                    hashes[hash] = [file]

            # 添加重复项
            duplicates.extend([
                {'files': files, 'size': files[0].size, 'count': len(files)}
                for files in hashes.values() if len(files) > 1
            ])

        return duplicates
```

### 3. 增量扫描

**cache.py** - 扫描缓存管理

```python
class CacheManager:
    def __init__(self, cache_dir: str = "~/.disk-cleaner/cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_scan_cache(self, path: str) -> Optional[ScanSnapshot]:
        """获取扫描缓存"""
        cache_file = self.cache_dir / f"{hashlib.md5(path.encode()).hexdigest()}.json"

        if not cache_file.exists():
            return None

        # 检查是否过期（7天）
        if time.time() - cache_file.stat().st_mtime > 7 * 24 * 3600:
            return None

        with open(cache_file) as f:
            return ScanSnapshot.from_dict(json.load(f))

    def save_scan_cache(self, path: str, snapshot: ScanSnapshot):
        """保存扫描缓存"""
        cache_file = self.cache_dir / f"{hashlib.md5(path.encode()).hexdigest()}.json"
        with open(cache_file, 'w') as f:
            json.dump(snapshot.to_dict(), f)

    def is_changed(self, file: FileInfo, cached: FileInfo) -> bool:
        """检查文件是否变化"""
        return (
            file.size != cached.size or
            file.mtime != cached.mtime or
            file.inode != cached.inode
        )
```

### 4. 文件分类器

**classifier.py** - 三维分类

```python
class FileClassifier:
    def classify(self, files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """按类型、风险、时间三维分类"""
        result = {
            'by_type': defaultdict(list),
            'by_risk': defaultdict(list),
            'by_age': defaultdict(list)
        }

        for file in files:
            # 类型分类
            file_type = self._classify_type(file)
            result['by_type'][file_type].append(file)

            # 风险分类
            risk = self._classify_risk(file)
            file.risk = risk
            result['by_risk'][risk].append(file)

            # 时间分类
            age_group = self._classify_age(file)
            result['by_age'][age_group].append(file)

        return result

    def _classify_type(self, file: FileInfo) -> str:
        """按文件类型分类"""
        type_rules = {
            '临时/构建产物': ['*.tmp', '*.pyc', '__pycache__', 'node_modules'],
            '日志文件': ['*.log'],
            '重复文件': None,  # 由 duplicate_finder 处理
            '缓存文件': ['*.cache', '.cache'],
            '下载文件': ['~/Downloads/*'],
            '媒体文件': ['*.mp4', '*.mkv', '*.jpg', '*.png'],
            '文档文件': ['*.pdf', '*.docx', '*.xlsx'],
        }

        for type_name, patterns in type_rules.items():
            if patterns and self._matches_patterns(file, patterns):
                return type_name

        return '其他文件'

    def _classify_risk(self, file: FileInfo) -> RiskLevel:
        """按风险等级分类"""
        if self._is_protected(file):
            return RiskLevel.PROTECTED
        elif self._is_temp(file):
            return RiskLevel.SAFE
        else:
            return RiskLevel.CONFIRM_NEEDED

    def _classify_age(self, file: FileInfo) -> str:
        """按时间特征分类"""
        age_days = (datetime.now() - file.mtime).days

        if age_days < 7:
            return '最近创建 (7天内)'
        elif age_days < 30:
            return '近期文件 (30天内)'
        elif age_days < 90:
            return '陈旧文件 (90天内)'
        else:
            return '很旧 (90天以上)'
```

---

## 交互设计

### 视图选择

```
🔍 分析完成！请选择查看方式：
  [1] 按文件类型（推荐）
  [2] 按风险等级
  [3] 按时间特征
  [4] 详细（所有维度）

选择 (1-4): 1
```

### 分层展示格式（按类型视图）

```
📦 临时/构建产物 (2.3GB)
   ✅ 安全 | 📅 2024-12-10 ~ 2025-01-19 | 平均: 25天前
   ├── node_modules/ (1.8GB)
   │   └── 📅 2024-12-15 ~ 2025-01-15 | 平均: 30天
   │      └── [查看文件] [删除]
   ├── __pycache__/ (450MB)
   │   └── 📅 2024-12-10 ~ 2025-01-19 | 平均: 15天
   │      └── [查看文件] [删除]
   └── *.pyc files (50MB)
      └── 📅 2024-12-10 ~ 2025-01-18 | 平均: 18天

📄 重复文件 (4.2GB)
   ⚠️ 需确认 | 📅 2024-08-15 ~ 2024-12-20 | 平均: 102天前
   ├── large_video.mp4 (3次重复, 4GB)
   │   └── 📅 创建: 2024-08-15 (129天前) | 📍 3个位置
   │      └── [查看位置] [删除重复]
   └── project_backup.zip (2次重复, 200MB)
      └── 📅 创建: 2024-10-01 (89天前) | 📍 2个位置

📜 旧日志 (890MB)
   ✅ 安全 | 📅 2024-08-01 ~ 2024-11-30 | 平均: 85天前
   └── *.log files (2,345个文件)
```

### 交互选择流程

```
📦 临时/构建产物 (2.3GB)
   ...
删除 node_modules/? [y/N/v]iew: y
   ✓ 已选择

删除 __pycache__/? [y/N/v]iew: v
   📁 __pycache__/
   ├── project1/__pycache__/ (200MB)
   ├── project2/__pycache__/ (150MB)
   └── project3/__pycache__/ (100MB)

删除 __pycache__/? [y/N]: y
   ✓ 已选择

⚠️  即将删除 2 个项目，释放 2.3GB
确认删除? 输入 'YES' 确认: YES

✓ 清理完成！
  - 删除文件: 12,450 个
  - 释放空间: 2.3 GB
  - 用时: 3.2 秒
  - 详细日志: ~/.disk-cleaner/logs/cleanup-2025-01-22.log
```

---

## 配置系统

### 配置文件示例

```yaml
# ~/.disk-cleaner/config.yaml 或项目目录 .disk-cleaner.yaml

# 受保护的路径和文件
protected:
  paths:
    - "important-project/"
    - "database/"
  patterns:
    - "*.database"
    - "*.db"
    - "config.*"

# 清理规则
rules:
  - name: "旧日志"
    pattern: "*.log"
    category: "日志"
    risk: "安全"
    age_threshold: 60  # 天

  - name: "构建产物"
    pattern: "node_modules/"
    category: "临时/构建产物"
    risk: "安全"
    age_threshold: 0

# 忽略规则
ignore:
  - "node_modules/@types"
  - ".git/*"
  - "*.lock"

# 安全设置
safety:
  check_file_locks: true
  verify_permissions: true
  backup_before_delete: false
  protected_extensions:
    - ".exe" ".dll" ".sys" ".drv"
    - ".bat" ".cmd" ".ps1"
    - ".sh" ".bash" ".zsh"
    - ".app" ".dmg" ".pkg"
    - ".deb" ".rpm" ".msi"
    - ".iso" ".vhd" ".vhdx"

# 扫描设置
scan:
  use_incremental: true
  cache_dir: "~/.disk-cleaner/cache"
  cache_ttl: 7  # 天
  parallel_jobs: 4

# 平台特定功能
platform_features:
  enabled: true
  auto_include: false

# 通知设置
notifications:
  enabled: false
  webhook_url: ""
  on_completion: true
  on_error: true
```

### 配置加载优先级

1. 命令行参数（最高）
2. 项目目录 `.disk-cleaner.yaml`
3. 用户配置 `~/.disk-cleaner/config.yaml`
4. 默认配置（最低）

---

## 安全增强

### 文件锁检测 + 进程终止

```python
class SafetyChecker:
    def handle_locked_files(self, items: List[CleanableItem]):
        """处理被锁定的文件"""
        locked_items = [i for i in items if i.status == FileStatus.LOCKED]

        if not locked_items:
            return

        print(f"\n⚠️  发现 {len(locked_items)} 个文件正在使用中:\n")

        for item in locked_items:
            process = self._get_locking_process(item.path)
            print(f"📄 {item.path}")
            print(f"   ├─ 大小: {format_size(item.size)}")
            print(f"   ├─ 进程: {process['name']} (PID: {process['pid']})")

            choice = input(f"   └─ 终止进程并删除? [y/N/v]iew: ").lower()

            if choice == 'y':
                if self._terminate_process(process['pid']):
                    item.status = FileStatus.SAFE
                    print(f"      ✓ 进程已终止")
            elif choice == 'v':
                self._show_process_details(process)

    def _get_locking_process(self, path: str) -> dict:
        """获取锁定文件的进程"""
        platform = platform.system()

        if platform == "Windows":
            # 使用 handle.exe
            result = subprocess.run(['handle', path], capture_output=True)
            # 解析输出
            return {'name': 'python.exe', 'pid': 12345}
        else:
            # 使用 lsof
            result = subprocess.run(['lsof', '-t', path], capture_output=True)
            return {'name': 'python', 'pid': 12345}

    def _terminate_process(self, pid: int) -> bool:
        """终止进程"""
        try:
            if platform.system() == "Windows":
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True)
            else:
                subprocess.run(['kill', '-9', str(pid)], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
```

### 权限验证

```
🔍 权限检查：
   ✓ C:\Temp - 可写
   ✓ C:\Users\user\Downloads - 可写
   ✗ C:\Windows\Temp - 需要管理员权限
   ℹ️  提示: 使用管理员权限运行以清理系统临时文件
```

### 备份机制

```python
def create_backup(file_path: str) -> str:
    """创建备份"""
    backup_dir = Path.home() / '.disk-cleaner' / 'backup' / datetime.now().strftime('%Y-%m-%d')
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / Path(file_path).name
    shutil.copy2(file_path, backup_path)

    # 记录元数据
    log_backup(file_path, backup_path)

    return str(backup_path)
```

---

## 自动化工作流

### 定时任务

**Windows:**
```python
def schedule_windows(command: str, schedule: str):
    """创建任务计划程序任务"""
    subprocess.run([
        'schtasks', '/Create',
        '/TN', 'DiskCleaner',
        '/TR', command,
        '/SC', 'WEEKLY',
        '/D', 'SUN',
        '/ST', '02:00'
    ])
```

**Linux/macOS:**
```python
def schedule_cron(command: str, schedule: str):
    """创建 cron 任务"""
    cron_job = f"0 2 * * 0 {command} >> ~/.disk-cleaner/logs/scheduled.log 2>&1"
    # 添加到 crontab
    ...
```

### 事件驱动清理

```python
class DirectoryWatcher:
    def watch(self, path: str, threshold: str, interval: int = 300):
        """监控目录增长"""
        baseline = self._get_dir_size(path)
        threshold_bytes = self._parse_size(threshold)

        while True:
            time.sleep(interval)
            current = self._get_dir_size(path)

            if current - baseline > threshold_bytes:
                self._notify_growth(path, current - baseline)
                baseline = current  # 重置
```

### 通知集成

```python
class Notifier:
    def send(self, message: str, webhook_url: str):
        """发送通知"""
        # 1. 系统通知
        if platform == "Windows":
            subprocess.run([
                'powershell', '-Command',
                f'[System.Windows.Forms.MessageBox]::Show("{message}")'
            ])
        elif platform == "Linux":
            subprocess.run(['notify-send', 'Disk Cleaner', message])

        # 2. Webhook
        if webhook_url:
            requests.post(webhook_url, json={'text': message})
```

---

## 测试与质量保证

### 测试结构

```
tests/
├── conftest.py                    # pytest 配置
├── test_analyzer.py               # 单元测试
├── test_cleaner.py
├── test_smart_cleanup.py
├── test_duplicate_finder.py
├── test_safety_checker.py
├── benchmarks/
│   ├── test_scan_performance.py   # 性能测试
│   └── test_memory_usage.py
└── fixtures/
    ├── test_files/                # 测试数据
    └── configs/                   # 测试配置
```

### pytest 配置

```python
# conftest.py
@pytest.fixture
def temp_dir():
    """临时目录"""
    temp = Path(tempfile.mkdtemp())
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def sample_files(temp_dir):
    """创建测试文件"""
    (temp_dir / "test.log").write_text("x" * 1000)
    (temp_dir / "dup1.txt").write_text("duplicate")
    (temp_dir / "dup2.txt").write_text("duplicate")
    return temp_dir
```

### 性能基准

```python
def test_scan_performance(sample_files):
    """扫描性能测试"""
    scanner = DirectoryScanner(sample_files)
    start = time.time()
    result = scanner.scan()
    elapsed = time.time() - start

    assert elapsed < 1.0
    assert len(result) > 0
```

### 类型检查

```ini
# mypy.ini
[mypy]
python_version = 3.8
warn_return_any = True
disallow_untyped_defs = True
```

---

## 开发者体验

### Makefile

```makefile
help:           ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort

install:        ## 安装开发依赖
	pip install -e ".[dev]"
	pre-commit install

test:           ## 运行测试
	pytest tests/ -v --cov=diskcleaner

lint:           ## 代码检查
	black --check .
	flake8 diskcleaner/
	mypy diskcleaner/

format:         ## 格式化代码
	black .
	isort .

build:          ## 构建
	python -m build
```

### pre-commit 配置

```yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

### CI/CD

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --cov
```

---

## 实施计划

### 阶段 1: 核心功能（2-3周）

- [ ] 创建 `diskcleaner/` 模块结构
- [ ] 实现 `scanner.py` - 增量扫描
- [ ] 实现 `classifier.py` - 三维分类
- [ ] 实现 `safety.py` - 安全检查
- [ ] 实现 `cache.py` - 缓存管理
- [ ] 编写单元测试

### 阶段 2: 智能清理（2-3周）

- [ ] 实现 `smart_cleanup.py`
- [ ] 实现 `duplicate_finder.py`
- [ ] 交互式界面
- [ ] 进程终止功能
- [ ] 集成测试

### 阶段 3: 平台特定功能（1-2周）

- [ ] 实现 `platforms/windows.py`
- [ ] 实现 `platforms/linux.py`
- [ ] 实现 `platforms/macos.py`
- [ ] 跨平台测试

### 阶段 4: 自动化（1-2周）

- [ ] 实现 `scheduler.py`
- [ ] 目录监控
- [ ] 通知集成
- [ ] 文档和示例

### 阶段 5: 质量保证（1周）

- [ ] 性能优化
- [ ] 完善测试覆盖率
- [ ] 代码审查
- [ ] 文档完善

### 阶段 6: 发布（1周）

- [ ] 更新 SKILL.md
- [ ] 更新 README.md
- [ ] 创建 GitHub Release
- [ ] 打包 .skill 文件

---

## 总结

这个增强设计在保持 disk-cleaner skill 原有优势（零依赖、跨平台、安全第一）的基础上，大幅提升了智能化水平和用户体验。通过三维分类、重复文件检测、增量扫描、进程终止等核心功能，以及完善的自动化能力、测试体系和开发工具，使其成为一个功能完整、生产就绪的磁盘管理工具。

**关键特性：**
- ✅ 智能清理建议（类型、风险、时间）
- ✅ 重复文件检测（自适应策略）
- ✅ 增量扫描（性能优化）
- ✅ 进程终止（安全删除）
- ✅ 平台特定功能（Windows/Linux/macOS）
- ✅ 定时任务和监控
- ✅ 全面测试（>80% 覆盖率）
- ✅ 类型注解和文档
