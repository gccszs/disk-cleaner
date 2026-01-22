# Notes: disk-cleaner 实施注意事项

## 实施策略

### 开发原则
1. **零依赖**: 仅使用 Python 标准库
2. **类型注解**: 从一开始就添加，避免后期返工
3. **测试先行**: TDD 方法，先写测试再写实现
4. **渐进式**: 按 Phase 顺序，每个 Phase 都有可验收的输出

### 关键技术决策

#### 1. 文件锁检测方案
**Windows 选项:**
- 选项 A: 使用 `handle.exe` (Sysinternals) - 需要外部工具
- 选项 B: 尝试以独占模式打开文件 - 纯 Python
- 选项 C: 使用 `psutil` - 引入依赖（不符合零依赖原则）

**决策**: 优先使用选项 B（纯Python），handle.exe 作为可选项增强

**实现要点:**
```python
def _is_locked_windows_pure(path: str) -> bool:
    """纯 Python 实现，无外部依赖"""
    try:
        # 尝试以独占写入模式打开
        fd = os.open(path, os.O_EXCL | os.O_RDWR)
        os.close(fd)
        return False
    except OSError:
        return True
```

#### 2. 哈希计算性能优化
**挑战**: 大文件哈希计算慢

**优化策略:**
- 小文件（<10MB）: 完整哈希
- 大文件（≥10MB）: 只哈希前1MB + 后1MB + 中间1MB
- 缓存哈希结果到 `~/.disk-cleaner/cache/`

**实现要点:**
```python
def _compute_hash_fast(file: Path) -> str:
    """快速哈希计算"""
    size = file.stat().st_size
    if size < 10 * 1024 * 1024:  # 10MB
        return self._hash_full(file)
    else:
        return self._hash_sampled(file, chunk_size=1*1024*1024)
```

#### 3. 并行扫描考虑
**是否需要并行?**
- 优点: 大目录扫描更快
- 缺点: 增加复杂度，可能受GIL限制

**决策**: Phase 1 不实现，作为 Phase 5 性能优化项
**预期收益**: 2-4倍提速（取决于I/Ovs CPU占比）

#### 4. 配置文件格式
**YAML vs JSON vs TOML**

**决策**: YAML
- 优点: 人类可读性好，支持注释
- 缺点: 需要额外库（pyyaml）

**零依赖解决方案**:
- Phase 1: 使用简化的自定义格式（类 INI）
- Phase 6: 考虑添加 pyyaml 作为可选依赖

**替代方案**:
```python
# 使用 JSON + 注释行（#开头的行）
# protected paths
{
  "protected": {
    "paths": ["important-project/"],
    "patterns": ["*.database"]
  }
}
```

## 平台特定注意事项

### Windows
1. **路径分隔器**: 使用 `os.path` 和 `pathlib.Path` 处理
2. **权限**: 可能需要管理员权限清理系统目录
3. **长路径**: Windows 有 260 字符路径限制（可注册表禁用）
4. **符号链接**: 需要管理员权限创建，检测时注意

### Linux
1. **权限检查**: `os.access(path, os.W_OK)`
2. **inode**: 可用于检测文件是否变化
3. **/proc 文件系统**: 进程信息在 `/proc/PID/`
4. **lsof**: 不是所有发行版都预装，需要检测

### macOS
1. **资源分支**: macOS 的扩展属性，特殊处理
2. **不可移动文件**: SIP (System Integrity Protection) 保护
3. **APFS 文件系统**: 支持克隆，大小可能不准确

## 测试策略

### 单元测试结构
```python
# tests/test_scanner.py
class TestDirectoryScanner:
    def test_scan_empty_directory(self, temp_dir):
        """测试空目录扫描"""
        scanner = DirectoryScanner(temp_dir)
        result = scanner.scan()
        assert len(result) == 0

    def test_scan_with_files(self, temp_dir):
        """测试有文件的目录"""
        (temp_dir / "test.txt").write_text("hello")
        scanner = DirectoryScanner(temp_dir)
        result = scanner.scan()
        assert len(result) == 1
```

### Fixtures 复用
```python
# conftest.py
@pytest.fixture
def sample_project(temp_dir):
    """创建示例项目结构"""
    (temp_dir / "node_modules").mkdir()
    (temp_dir / "node_modules" / "package.json").write_text("{}")
    (temp_dir / "__pycache__").mkdir()
    (temp_dir / "app.log").write_text("x" * 1000)
    return temp_dir
```

### 性能基准
```python
# benchmarks/test_scan_performance.py
def test_scan_1000_files(benchmark):
    """扫描1000个文件应在1秒内完成"""
    # Setup
    temp_dir = create_temp_dir_with_n_files(1000)

    # Benchmark
    result = benchmark(scan_directory, temp_dir)

    # Assert
    assert len(result) == 1000
```

## 常见陷阱

### 1. 递归符号链接
**问题**: 无限递归
**解决**: 跟踪已访问的 inode（Unix）或设备ID+索引（Windows）

### 2. 文件删除失败
**原因**: 权限、文件锁定、路径不存在
**处理**: 捕获异常，记录日志，继续处理其他文件

### 3. 内存占用
**问题**: 扫描大目录时内存暴涨
**解决**: 使用生成器而非列表，流式处理

### 4. 时间精度
**问题**: 不同文件系统时间精度不同（FAT vs NTFS vs ext4）
**解决**: 使用秒级精度，不依赖毫秒

### 5. 编码问题
**问题**: Windows 可能使用非 UTF-8 编码的文件名
**解决**: 使用 `os.fsencode()` / `os.fsdecode()`

## 依赖关系可视化

```
Phase 0 (初始化)
   ↓
Phase 1 (核心模块)
   ├── cache.py (无依赖)
   ├── scanner.py (依赖 cache.py)
   ├── config/ (无依赖)
   ├── classifier.py (依赖 config/)
   └── safety.py (依赖 config/)
   ↓
Phase 2 (智能清理)
   ├── duplicate_finder.py (依赖 scanner.py)
   ├── smart_cleanup.py (依赖 scanner, classifier, duplicate_finder, safety)
   ├── 交互式界面 (依赖 smart_cleanup.py)
   └── 进程终止 (依赖 safety.py)
   ↓
Phase 3 (平台特定) (依赖 safety.py)
   ├── windows.py
   ├── linux.py
   └── macos.py
   ↓
Phase 4 (自动化) (可并行)
   ├── scheduler.py (无依赖)
   ├── watcher.py (依赖 scanner.py)
   └── notifier.py (无依赖)
   ↓
Phase 5 (质量保证)
Phase 6 (发布)
```

## 实施检查清单

### Phase 0 完成标准
- [ ] `diskcleaner/` 目录结构创建
- [ ] `make help` 显示可用命令
- [ ] `make test` 运行成功（即使没有测试）
- [ ] GitHub Actions workflow 创建并触发

### Phase 1 完成标准
- [ ] `pytest tests/test_core.py` 全部通过
- [ ] 增量扫描比首次扫描快 3 倍以上
- [ ] 配置正确加载和合并
- [ ] 文件正确分类（类型/风险/时间）
- [ ] protected 文件不被标记为可删除

### Phase 2 完成标准
- [ ] 重复文件检测 100% 准确
- [ ] 可以完成一次端到端清理流程
- [ ] 交互界面显示正确的日期信息
- [ ] 必须输入 'YES' 才能删除
- [ ] 可以终止占用文件的进程

### Phase 3 完成标准
- [ ] Windows 测试全部通过
- [ ] Linux 测试全部通过
- [ ] macOS 测试全部通过
- [ ] 平台特定功能正确检测

### Phase 4 完成标准
- [ ] 可以创建定时任务
- [ ] 目录监控正确触发告警
- [ ] 通知在三大平台正确发送

### Phase 5 完成标准
- [ ] 测试覆盖率 > 80%
- [ ] `make lint` 无错误
- [ ] `mypy diskcleaner/` 无错误
- [ ] 性能基准测试通过

### Phase 6 完成标准
- [ ] 文档完整且易懂
- [ ] 示例可运行
- [ ] README 可指导新用户安装使用
- [ ] GitHub Release 发布
- [ ] .skill 文件打包

## 回滚计划

如果某个 Phase 失败或遇到不可解决的问题：

1. **Phase 1/2 核心功能失败**: 回退到 v1.0，保留改进的部分
2. **Phase 3 平台功能失败**: 标记为实验性功能，继续其他平台
3. **Phase 4 自动化失败**: 降级为手动触发，文档说明
4. **Phase 5 测试不达标**: 标记为 Beta 版本，继续改进

## 性能目标

| 指标 | 目标 | 测量方法 |
|------|------|----------|
| 扫描速度 | <1秒/1000文件 | benchmark |
| 重复检测 | <5秒/10000文件 | benchmark |
| 内存占用 | <100MB (10000文件) | memory profiler |
| 启动时间 | <0.5秒 | time command |
| 缓存命中率 | >80% (重复扫描) | cache stats |

## 安全检查清单

每次代码审查时检查：

- [ ] 文件删除前有确认机制
- [ ] protected 路径检查
- [ ] protected 扩展名检查
- [ ] 权限验证
- [ ] 文件锁检测
- [ ] 备份机制（可选）
- [ ] 详细日志记录
- [ ] 异常处理不崩溃
- [ ] 用户数据不泄露（日志中无敏感信息）
