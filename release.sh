#!/bin/bash

################################################################################
# Dev-Bot 发布脚本
################################################################################

set -e

VERSION=${1:-$(date +%Y.%m.%d)}
RELEASE_DIR="release"

echo "========================================"
echo "Dev-Bot 发布脚本"
echo "版本: $VERSION"
echo "========================================"

# 清理旧的发布文件
rm -rf "$RELEASE_DIR" "dist" "build" "*.egg-info"
mkdir -p "$RELEASE_DIR"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "错误: uv 未安装，请先安装 uv"
    echo "安装命令: pip install uv"
    exit 1
fi

# 构建 Python 包
echo "构建 Python 包..."
uv build

# 复制构建产物到发布目录
echo "复制构建产物..."
cp dist/*.whl "$RELEASE_DIR/"
cp dist/*.tar.gz "$RELEASE_DIR/"

# 复制配置文件
echo "复制配置文件..."
cp config.json "$RELEASE_DIR/"

# 创建发布说明
echo "创建发布说明..."
cat > "$RELEASE_DIR/README.md" << 'EOF'
# Dev-Bot

AI 驱动开发代理 - 可配置版本

## 安装

### 使用 uv 安装（推荐）

```bash
uv pip install dev_bot-*.whl
```

### 使用 pip 安装

```bash
pip install dev_bot-*.whl
```

## 配置

1. 复制配置文件：
   ```bash
   cp config.json ~/.config/dev-bot/config.json
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

## 使用

安装后可以直接运行：

```bash
dev-bot
```

## 配置说明

详细配置说明请参考 [README.md](../README.md)

## 系统要求

- Python 3.8+
- AI 工具（如 iflow、claude 等）需要在系统 PATH 中
EOF

# 创建压缩包
echo "创建发布包..."
cd "$RELEASE_DIR"
tar -czf "dev-bot-${VERSION}.tar.gz" *.whl *.tar.gz README.md config.json
cd ..

echo "========================================"
echo "发布完成！"
echo "========================================"
echo "发布文件: $RELEASE_DIR/dev-bot-${VERSION}.tar.gz"
echo "Wheel 文件: $RELEASE_DIR/dev_bot-*.whl"
echo "源码包: $RELEASE_DIR/dev_bot-*.tar.gz"
echo "========================================"