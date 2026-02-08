.PHONY: help install test test-bench lint format clean build skill-package

help:           ## 显示帮助信息
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:        ## 安装开发依赖
	pip install -e ".[dev]"

test:           ## 运行所有测试
	pytest tests/ -v --cov=diskcleaner --cov-report=html --cov-report=term

test-bench:     ## 运行性能基准测试
	pytest tests/benchmarks/ -v

test-fast:      ## 快速测试（跳过慢速测试）
	pytest tests/ -v -m "not slow"

lint:           ## 代码检查
	@echo "Running black..."
	black --check diskcleaner/ tests/ examples/
	@echo "Running isort..."
	isort --check-only diskcleaner/ tests/ examples/
	@echo "Running flake8..."
	flake8 diskcleaner/ tests/ examples/ --max-line-length=100
	@echo "Running mypy..."
	mypy diskcleaner/

format:         ## 自动格式化代码
	black diskcleaner/ tests/ examples/
	isort diskcleaner/ tests/ examples/

clean:          ## 清理临时文件
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/
	rm -rf htmlcov/ .coverage
	find diskcleaner/ -type d -name __pycache__ -exec rm -rf {} +
	find diskcleaner/ -type f -name "*.pyc" -delete
	find tests/ -type d -name __pycache__ -exec rm -rf {} +
	find tests/ -type f -name "*.pyc" -delete

build:          ## 构建分发包
	python -m build

skill-package:  ## 打包技能文件 (.skill)
	python skills/disk-cleaner/scripts/package_skill.py

dev:            ## 设置开发环境
	pip install -e ".[dev]"
	pre-commit install

check: lint test ## 运行所有检查（lint + test）

all: format lint test ## 完整工作流（format + lint + test）
