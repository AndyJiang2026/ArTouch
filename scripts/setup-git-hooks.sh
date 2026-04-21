<!--
AI-ASSISTED: Yes
AI-TOOL: Claude Code
PROMPT: Create a setup script to install git hooks for the ArtTouch project
DATE: 2026-04-19
ENGINEER: System
RISK-LEVEL: P2
-->

#!/bin/bash
# =============================================================================
# ArtTouch NFC - Git Hooks 安装脚本
# =============================================================================
# 首次克隆项目后运行此脚本，安装所有必需的 git hooks
# =============================================================================

set -e

echo "🔧 安装 ArtTouch NFC Git Hooks..."

# 确保在项目根目录
cd "$(dirname "$0")/.."

# 1. 安装 commit-msg hook
echo "📌 安装 commit-msg hook..."
cp .github/hooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
echo "   ✅ commit-msg hook 已安装"

# 2. 安装 pre-commit hooks
echo "📌 安装 pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo "   ✅ pre-commit hooks 已安装"
else
    echo "   ⚠️  pre-commit 未安装，跳过"
    echo "   💡 运行以下命令安装: pip install pre-commit"
fi

# 3. 安装 Python 依赖
echo "📌 检查 Python 依赖..."
if command -v python3 &> /dev/null; then
    pip install -q pre-commit ruff black mypy pytest pytest-cov
    echo "   ✅ 开发依赖已安装"
else
    echo "   ⚠️  Python3 未安装"
fi

echo ""
echo "✅ Git Hooks 安装完成！"
echo ""
echo "后续开发: 每次提交时，commit-msg hook 会自动验证 commit 格式"
echo "          pre-commit 会在提交前检查代码质量（需先运行 pip install pre-commit）"
