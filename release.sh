#!/bin/bash

################################################################################
# Dev-Bot 发布脚本
################################################################################

set -e

VERSION=${1:-$(date +%Y.%m.%d)}
RELEASE_DIR="release"
BINARY_NAME="dev-bot"

echo "========================================"
echo "Dev-Bot 发布脚本"
echo "版本: $VERSION"
echo "========================================"

# 清理旧的发布文件
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 安装 PyInstaller
echo "安装 PyInstaller..."
python3 -m pip install pyinstaller --quiet

# 构建 Linux 二进制文件
echo "构建 Linux x86_64..."
pyinstaller --onefile --name "$BINARY_NAME" main.py --distpath "$RELEASE_DIR/linux-amd64"

# 构建示例配置文件
echo "复制配置文件..."
cp config.json "$RELEASE_DIR/config.json"

# 创建发布说明
echo "创建发布说明..."
cat > "$RELEASE_DIR/README.md" << 'EOF'
# Dev-Bot

AI 驱动开发代理 - 可配置版本

## 快速开始

1. 复制配置文件：
   ```bash
   cp config.json config.local.json
   ```

2. 根据需要修改配置：
   ```json
   {
     "prompt_file": "PROMPT.md",
     "ai_command": "iflow",
     "ai_command_args": ["-y"],
     "timeout_seconds": 300
   }
   ```

3. 运行：
   ```bash
   ./dev-bot
   ```

## 配置说明

详细配置说明请参考 [README.md](../README.md)

## 系统要求

- Linux x86_64
- AI 工具（如 iflow、claude 等）需要在系统 PATH 中
EOF

# 创建压缩包
echo "创建发布包..."
cd "$RELEASE_DIR"
tar -czf "dev-bot-${VERSION}-linux-amd64.tar.gz" linux-amd64/ README.md config.json
cd ..

echo "========================================"
echo "发布完成！"
echo "========================================"
echo "发布文件: $RELEASE_DIR/dev-bot-${VERSION}-linux-amd64.tar.gz"
echo "二进制文件: $RELEASE_DIR/linux-amd64/$BINARY_NAME"
echo "========================================"