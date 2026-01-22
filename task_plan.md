# Task Plan: disk-cleaner Skill 增强版实施

## Goal
基于设计文档 `docs/design-2025-01-22-enhancement.md`，将 disk-cleaner skill 从 v1.0 升级到 v2.0，实现智能清理、重复文件检测、增量扫描等核心增强功能。

## Phases Overview
- [x] Phase 0: 项目初始化与基础设施
- [ ] Phase 1: 核心功能模块（scanner, classifier, safety, cache）
- [ ] Phase 2: 智能清理引擎与重复文件检测
- [ ] Phase 3: 平台特定功能（Windows/Linux/macOS）
- [ ] Phase 4: 自动化工作流（scheduler, watcher, notifier）
- [ ] Phase 5: 测试与质量保证
- [ ] Phase 6: 文档与发布

---

## Planning Phase (✅ 已完成)

**日期**: 2025-01-22
**完成内容**:
- ✅ 创建 task_plan.md - 详细的 52 个任务分解
- ✅ 创建 notes.md - 技术决策和实施注意事项
- ✅ 创建 implementation-tracker.md - 进度追踪系统
- ✅ 完成头脑风暴和设计阶段

---

## Phase 0: 项目初始化与基础设施

**目标**: 搭建开发环境和项目结构

### 任务列表
- [ ] **0.1 创建模块目录结构**
  - 创建 `diskcleaner/` 主包
  - 创建子包: `core/`, `platforms/`, `config/`
  - 创建 `__init__.py` 文件
  - **验收**: 目录结构符合设计文档
  - **依赖**: 无
  - **优先级**: P0 (最高)

- [ ] **0.2 设置开发工具配置**
  - 创建 `Makefile`
  - 创建 `.pre-commit-config.yaml`
  - 创建 `mypy.ini`
  - 创建 `pytest.ini` / `pyproject.toml`
  - **验收**: `make help` 可用，`make lint` 通过
  - **依赖**: 0.1
  - **优先级**: P0

- [ ] **0.3 配置 CI/CD**
  - 创建 `.github/workflows/test.yml`
  - 创建 `.github/workflows/lint.yml`
  - 配置跨平台测试矩阵（Windows/Linux/macOS, Python 3.8-3.11）
  - **验收**: GitHub Actions 自动运行测试
  - **依赖**: 0.2
  - **优先级**: P1

- [ ] **0.4 设置测试框架**
  - 创建 `tests/` 目录结构
  - 创建 `tests/conftest.py` 和 fixtures
  - 配置 pytest 和 coverage
  - **验收**: `pytest tests/` 可运行
  - **依赖**: 0.2
  - **优先级**: P0

---

## Phase 1: 核心功能模块

**目标**: 实现基础扫描、分类、安全检查和缓存功能

### 任务列表
- [ ] **1.1 实现 core/cache.py - 缓存管理**
  - 实现 `CacheManager` 类
  - 实现缓存存储/加载（JSON格式）
  - 实现缓存过期检查（7天TTL）
  - 实现 `ScanSnapshot` 数据类
  - **验收**: 单元测试通过，缓存正确读写
  - **依赖**: 0.4
  - **优先级**: P0

- [ ] **1.2 实现 core/scanner.py - 目录扫描引擎**
  - 实现 `DirectoryScanner` 类
  - 实现基本扫描功能（递归遍历）
  - 实现增量扫描（使用 cache.py）
  - 实现文件变更检测（size, mtime, inode）
  - 实现并行扫描（可选）
  - **验收**: 扫描性能测试通过，增量扫描比全量快3倍+
  - **依赖**: 1.1
  - **优先级**: P0

- [ ] **1.3 实现 config/ 模块 - 配置管理**
  - 实现 `Config` 类
  - 实现 `loader.py` - 配置加载器（YAML解析）
  - 实现 `defaults.py` - 默认配置
  - 实现四级优先级合并（命令行 > 项目 > 用户 > 默认）
  - **验收**: 配置正确加载和合并
  - **依赖**: 0.2
  - **优先级**: P0

- [ ] **1.4 实现 core/classifier.py - 文件分类器**
  - 实现 `FileClassifier` 类
  - 实现按类型分类（temp, logs, cache, media等）
  - 实现按风险分类（SAFE, CONFIRM_NEEDED, PROTECTED）
  - 实现按时间分类（7天/30天/90天分组）
  - **验收**: 测试文件正确分类到对应类别
  - **依赖**: 1.3
  - **优先级**: P0

- [ ] **1.5 实现 core/safety.py - 安全检查器**
  - 实现 `SafetyChecker` 类
  - 实现保护路径检查
  - 实现保护扩展名检查
  - 实现权限验证
  - 实现文件锁检测（跨平台）
  - **验收**: 安全测试通过，protected文件不被标记为可删除
  - **依赖**: 1.3
  - **优先级**: P0

---

## Phase 2: 智能清理引擎与重复文件检测

**目标**: 实现智能清理和重复文件检测核心功能

### 任务列表
- [ ] **2.1 实现 duplicate_finder.py - 重复文件检测**
  - 实现 `DuplicateFinder` 类
  - 实现自适应策略选择（<1000文件用精确，>1000用快速）
  - 实现快速策略（大小+时间预筛选）
  - 实现精确策略（SHA-256哈希）
  - 实现按可回收空间排序
  - **验收**: 重复文件100%准确识别，性能基准测试通过
  - **依赖**: 1.2
  - **优先级**: P0

- [ ] **2.2 实现 smart_cleanup.py - 智能清理引擎**
  - 实现 `SmartCleanupEngine` 类
  - 集成 scanner, classifier, duplicate_finder, safety
  - 实现 `analyze()` 方法生成清理报告
  - 实现 `CleanupReport` 数据结构
  - **验收**: 端到端测试通过
  - **依赖**: 1.2, 1.4, 1.5, 2.1
  - **优先级**: P0

- [ ] **2.3 实现交互式界面**
  - 实现视图选择菜单（类型/风险/时间/详细）
  - 实现分层展示（带日期范围和平均年龄）
  - 实现文件列表详情查看
  - 实现用户选择逻辑（y/n/v）
  - **验收**: 交互流程测试通过
  - **依赖**: 2.2
  - **优先级**: P0

- [ ] **2.4 实现最终确认机制**
  - 实现 'YES' 确认逻辑
  - 实现清理摘要展示（文件数、空间、用时）
  - 实现详细日志记录
  - **验收**: 未输入YES时不删除，日志正确记录
  - **依赖**: 2.3
  - **优先级**: P0

- [ ] **2.5 实现进程终止功能**
  - 实现 `_get_locking_process()` - 获取占用进程
  - 实现 `_terminate_process()` - 终止进程
  - 实现 `_show_process_details()` - 显示进程详情
  - 实现跨平台支持（Windows: handle.exe/taskkill, Unix: lsof/kill）
  - **验收**: 可以正确检测并终止锁定文件的进程
  - **依赖**: 1.5
  - **优先级**: P1

- [ ] **2.6 集成测试**
  - 编写端到端场景测试
  - 测试完整清理流程
  - 测试错误处理和边界情况
  - **验收**: 集成测试覆盖率>80%
  - **依赖**: 2.2, 2.3, 2.4, 2.5
  - **优先级**: P0

---

## Phase 3: 平台特定功能

**目标**: 实现Windows/Linux/macOS特定功能

### 任务列表
- [ ] **3.1 实现 platforms/windows.py**
  - 实现 Windows 临时位置检测
  - 实现 Windows Update 缓存检测
  - 实现 PowerShell 历史清理
  - 实现系统还原点检测
  - **验收**: Windows平台测试通过
  - **依赖**: 1.5
  - **优先级**: P1

- [ ] **3.2 实现 platforms/linux.py**
  - 实现 Linux 临时位置检测
  - 实现包管理器缓存检测（apt/dnf/pacman/snap）
  - 实现系统日志轮转建议
  - 实现 Docker 镜像/容器检测
  - 实现旧内核检测
  - **验收**: Linux平台测试通过
  - **依赖**: 1.5
  - **优先级**: P1

- [ ] **3.3 实现 platforms/macos.py**
  - 实现 macOS 临时位置检测
  - 实现 iOS 设备备份检测
  - 实现 Homebrew 缓存检测
  - 实现 Xcode 派生数据检测
  - 实现 .DS_Store 文件清理
  - **验收**: macOS平台测试通过
  - **依赖**: 1.5
  - **优先级**: P1

- [ ] **3.4 跨平台集成测试**
  - 在Windows/Linux/macOS上运行完整测试套件
  - 验证平台特定功能正确工作
  - 修复跨平台兼容性问题
  - **验收**: 三大平台CI全部通过
  - **依赖**: 3.1, 3.2, 3.3
  - **优先级**: P0

---

## Phase 4: 自动化工作流

**目标**: 实现定时任务、目录监控、通知功能

### 任务列表
- [ ] **4.1 实现 scheduler.py - 定时任务管理**
  - 实现 `TaskScheduler` 类
  - 实现 Windows 任务计划程序集成
  - 实现 Linux cron 集成
  - 实现 macOS launchd 集成
  - 实现任务列表查看和删除
  - **验收**: 可以成功创建和管理定时任务
  - **依赖**: 无
  - **优先级**: P1

- [ ] **4.2 实现目录监控**
  - 实现 `DirectoryWatcher` 类
  - 实现目录大小监控
  - 实现阈值检测和告警
  - 实现基线重置逻辑
  - 支持Ctrl+C优雅退出
  - **验收**: 监控测试通过，正确触发告警
  - **依赖**: 1.2
  - **优先级**: P2

- [ ] **4.3 实现通知集成**
  - 实现 `Notifier` 类
  - 实现Windows原生通知
  - 实现Linux notify-send
  - 实现macOS osascript通知
  - 实现webhook通知（Slack/Discord/企业微信）
  - **验收**: 通知测试通过，各平台通知正确发送
  - **依赖**: 无
  - **优先级**: P2

- [ ] **4.4 创建实用脚本**
  - 创建 `examples/scripts/weekly_cleanup.sh`
  - 创建 `examples/scripts/docker_monitor.sh`
  - 创建 `examples/scripts/scheduled_cleanup.bat`
  - 编写脚本使用说明
  - **验收**: 脚本可独立运行
  - **依赖**: 4.1, 4.2, 4.3
  - **优先级**: P2

---

## Phase 5: 测试与质量保证

**目标**: 完善测试覆盖率、性能优化、代码质量

### 任务列表
- [ ] **5.1 完善单元测试**
  - 为所有核心模块编写测试
  - 测试覆盖率 >80%
  - 添加边界条件测试
  - 添加异常处理测试
  - **验收**: `pytest --cov` 显示覆盖率>80%
  - **依赖**: 所有开发任务
  - **优先级**: P0

- [ ] **5.2 性能基准测试**
  - 创建 `tests/benchmarks/test_scan_performance.py`
  - 创建 `tests/benchmarks/test_hash_performance.py`
  - 创建 `tests/benchmarks/test_memory_usage.py`
  - 建立性能基线
  - **验收**: 性能基准测试通过，扫描<1秒/1000文件
  - **依赖**: 1.2, 2.1
  - **优先级**: P1

- [ ] **5.3 类型注解检查**
  - 为所有公共API添加类型注解
  - 通过 mypy 严格检查
  - 修复所有类型错误
  - **验收**: `mypy diskcleaner/` 无错误
  - **依赖**: 所有开发任务
  - **优先级**: P1

- [ ] **5.4 代码质量优化**
  - 通过 black 格式化所有代码
  - 通过 flake8 检查
  - 修复所有 linting 错误
  - 优化代码结构
  - **验收**: `make lint` 全部通过
  - **依赖**: 5.3
  - **优先级**: P1

- [ ] **5.5 安全审计**
  - 审查文件删除逻辑
  - 审查权限检查
  - 审查进程终止逻辑
  - 审查配置加载安全性
  - **验收**: 安全审计清单完成，无高风险问题
  - **依赖**: 所有开发任务
  - **优先级**: P0

---

## Phase 6: 文档与发布

**目标**: 完善文档、打包发布

### 任务列表
- [ ] **6.1 编写开发文档**
  - 创建 `docs/ARCHITECTURE.md` - 架构设计
  - 创建 `docs/API.md` - API文档
  - 创建 `docs/DEVELOPMENT.md` - 开发指南
  - 创建 `docs/TESTING.md` - 测试指南
  - 创建 `docs/CONTRIBUTING.md` - 贡献指南
  - **验收**: 文档完整，新开发者可按文档搭建环境
  - **依赖**: Phase 5完成
  - **优先级**: P0

- [ ] **6.2 创建使用示例**
  - 创建 `examples/basic_usage.py`
  - 创建 `examples/advanced_cleanup.py`
  - 创建 `examples/custom_rules.yaml`
  - 为每个示例添加详细注释
  - **验收**: 示例可独立运行
  - **依赖**: Phase 4完成
  - **优先级**: P0

- [ ] **6.3 更新用户文档**
  - 更新 `SKILL.md` - 添加新功能说明
  - 更新 `README.md` - 新增功能、安装命令、使用示例
  - 更新 `references/temp_locations.md` - 补充新发现的位置
  - **验收**: 用户可以按README成功安装和使用
  - **依赖**: 6.1
  - **优先级**: P0

- [ ] **6.4 创建 GitHub Release**
  - 生成 CHANGELOG.md
  - 创建 git tag（v2.0.0）
  - 在GitHub创建 Release
  - 上传 `disk-cleaner.skill` 文件
  - **验收**: Release发布成功，用户可下载
  - **依赖**: 6.3
  - **优先级**: P0

- [ ] **6.5 创建 Issue 和 PR 模板**
  - 创建 `.github/ISSUE_TEMPLATE/bug_report.md`
  - 创建 `.github/ISSUE_TEMPLATE/feature_request.md`
  - 创建 `.github/PULL_REQUEST_TEMPLATE.md`
  - **验收**: 模板在GitHub上正确显示
  - **依赖**: 6.3
  - **优先级**: P2

---

## Key Questions
1. 是否需要使用外部库（如 psutil）来简化跨平台实现？
   - 决策：暂时保持零依赖，使用纯 Python 标准库
   - 理由：设计要求零依赖，确保最大兼容性

2. 是否需要在 Phase 1 就开始类型注解？
   - 决策：是的，从一开始就添加类型注解
   - 理由：后期添加成本更高，边开发边添加更高效

3. 文件锁检测是否必须依赖 handle.exe（Windows）？
   - 决策：尝试备用方案（psutil 或纯Python），handle.exe作为可选项
   - 理由：提升可移植性，不强制依赖外部工具

## Decisions Made
- **零依赖原则**: 仅使用 Python 标准库，不引入外部依赖
- **测试先行**: 每个模块先写测试，再写实现
- **渐进式开发**: Phase 0-2 为核心，Phase 3-6 可并行或延后
- **优先级分级**: P0（必须）> P1（重要）> P2（可选）

## Errors Encountered
- *（待更新）*

## Status
**Currently in Phase 0** - 计划阶段已完成，准备开始实施

### 已完成的准备工作
- ✅ 设计文档 (docs/design-2025-01-22-enhancement.md)
- ✅ 任务计划 (task_plan.md) - 52 个任务详细分解
- ✅ 实施笔记 (notes.md) - 技术决策和注意事项
- ✅ 进度追踪 (implementation-tracker.md)

### 下一步行动
1. 创建目录结构：`diskcleaner/{core,platforms,config}`
2. 创建 `__init__.py` 文件
3. 配置开发工具（Makefile, pre-commit, mypy等）

### 检查点
- **Checkpoint 1** (Phase 0完成): 开发环境就绪，测试框架可用
- **Checkpoint 2** (Phase 1完成): 核心模块实现，基础功能可测试
- **Checkpoint 3** (Phase 2完成): 智能清理和重复检测可用
- **Checkpoint 4** (Phase 3完成): 跨平台功能全部测试通过
- **Checkpoint 5** (Phase 5完成): 测试覆盖率>80%，代码质量达标
- **Checkpoint 6** (Phase 6完成): 文档完整，成功发布 v2.0.0
