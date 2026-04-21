# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Update Makefile with Docker deployment commands
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P3

.PHONY: help install dev lint format test clean
.PHONY: docker-build docker-up docker-down docker-logs docker-restart
.PHONY: db-migrate db-reset

help:
	@echo "ArtTouch NFC - 可用命令:"
	@echo ""
	@echo "  开发环境:"
	@echo "    make install    - 安装后端依赖"
	@echo "    make dev        - 开发模式安装"
	@echo "    make lint       - 运行代码检查 (ruff)"
	@echo "    make format     - 格式化代码 (black + ruff)"
	@echo "    make test       - 运行测试 (pytest)"
	@echo "    make clean      - 清理缓存文件"
	@echo ""
	@echo "  Docker 部署:"
	@echo "    make docker-build   - 构建 Docker 镜像"
	@echo "    make docker-up      - 启动所有服务 (生产)"
	@echo "    make docker-down    - 停止所有服务"
	@echo "    make docker-logs    - 查看日志"
	@echo "    make docker-restart - 重启所有服务"
	@echo ""
	@echo "  数据库:"
	@echo "    make db-migrate - 运行数据库迁移"
	@echo "    make db-reset   - 重置数据库 (慎用!)"

# =============================================================================
# Development
# =============================================================================

install:
	pip install -r backend/requirements.txt
	pip install ruff black mypy pytest pytest-cov

dev:
	pip install -e backend/
	pip install ruff black mypy pytest pytest-cov

lint:
	ruff check .

format:
	black .
	ruff check --fix .

test:
	SECRET_KEY=test DATABASE_URL=sqlite:///./test.db pytest -v --tb=short

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov

# =============================================================================
# Docker Deployment
# =============================================================================

docker-build:
	docker compose build --no-cache

docker-build-light:
	docker compose build

docker-up:
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@docker compose ps

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-logs-backend:
	docker compose logs -f backend

docker-restart:
	docker compose restart

docker-shell:
	docker compose exec backend /bin/bash

# =============================================================================
# Database
# =============================================================================

db-migrate:
	@echo "Run: docker compose exec backend python -m app.database"
	@echo "Or use Alembic for production migrations"

# =============================================================================
# Production helpers
# =============================================================================

secret-key:
	@python -c "import secrets; print(secrets.token_hex(32))"

env-check:
	@if [ ! -f .env ]; then echo ".env file not found!"; exit 1; fi
	@echo ".env file exists"
