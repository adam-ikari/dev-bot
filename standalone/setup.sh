#!/bin/bash

################################################################################
# Dev-Bot 独立发布设置脚本
# 将 dev-bot 从当前项目中提取为独立仓库
################################################################################

set -e

echo "========================================"
echo "Dev-Bot 独立发布设置"
echo "========================================"

REPO_URL="https://github.com/yourusername/dev-bot.git"
VERSION="0.1.0"

# 检查是否在正确的目录
if [ ! -f "../main.py" ]; then
    echo "错误: 请在 dev-bot 目录中运行此脚本"
    exit 1
fi

echo ""
echo "此脚本将帮助您将 dev-bot 发布为独立仓库"
echo ""
echo "步骤:"
echo "1. 创建新的 GitHub 仓库"
echo "2. 复制必要的文件"
echo "3. 初始化 Git 仓库"
echo "4. 推送到 GitHub"
echo ""
read -p "是否继续? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 创建临时目录
TEMP_DIR=$(mktemp -d)
echo ""
echo "创建临时目录: $TEMP_DIR"

# 复制文件
echo "复制文件..."
cp ../main.py "$TEMP_DIR/"
cp ../config.json "$TEMP_DIR/"
cp ../dev-bot.spec "$TEMP_DIR/"
cp ../release.sh "$TEMP_DIR/"
cp standalone/README.md "$TEMP_DIR/README.md"

# 创建示例提示词文件
cat > "$TEMP_DIR/PROMPT.md" << 'EOF'
# Dev-Bot 开发提示词

这是一个示例提示词文件，用于指导 AI 工具执行任务。

## 任务目标
请帮助完成以下开发任务：

1. 分析当前项目结构
2. 根据需求实现功能
3. 编写测试用例
4. 优化代码质量

## 注意事项
- 遵循项目的代码规范
- 添加必要的注释
- 确保代码可维护性
- 考虑性能和安全性
EOF

# 创建 LICENSE 文件
cat > "$TEMP_DIR/LICENSE" << 'EOF'
MIT License

Copyright (c) 2026 Dev-Bot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# 创建 .gitignore
cat > "$TEMP_DIR/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Logs
.ai-logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Dev-Bot specific
stats.json
session_counter.json
release/
EOF

# 初始化 Git 仓库
echo "初始化 Git 仓库..."
cd "$TEMP_DIR"
git init
git add .
git commit -m "Initial commit: Dev-Bot v$VERSION"

echo ""
echo "========================================"
echo "准备完成！"
echo "========================================"
echo ""
echo "下一步操作:"
echo ""
echo "1. 创建 GitHub 仓库:"
echo "   访问: https://github.com/new"
echo "   仓库名: dev-bot"
echo "   描述: AI-driven development agent"
echo ""
echo "2. 推送到 GitHub:"
echo "   cd $TEMP_DIR"
echo "   git remote add origin $REPO_URL"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. 创建 GitHub Release:"
echo "   gh release create v$VERSION --title \"Dev-Bot v$VERSION\" --notes \"First stable release\""
echo ""
echo "临时目录位置: $TEMP_DIR"
echo "========================================"

# 询问是否立即推送
read -p "是否立即推送到 GitHub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "请输入 GitHub 仓库 URL: " REPO_URL_INPUT
    if [ -n "$REPO_URL_INPUT" ]; then
        git remote add origin "$REPO_URL_INPUT"
        git branch -M main
        git push -u origin main
        echo ""
        echo "✓ 推送成功！"
        echo ""
        echo "现在可以创建 GitHub Release:"
        echo "gh release create v$VERSION --title \"Dev-Bot v$VERSION\" --notes \"First stable release\""
    fi
fi
