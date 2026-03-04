# Dev-Bot

AI 驱动开发代理 - 可配置版本

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## 简介

Dev-Bot 是一个高度可配置的 AI 驱动开发代理工具，可以自动化执行 AI 辅助的开发任务。通过配置文件，您可以轻松切换不同的 AI 工具和提示词，适应各种开发场景。

## 功能特性

- ✅ **完全可配置** - 支持自定义 AI 工具、提示词、超时等
- ✅ **多 AI 工具支持** - 兼容 iflow、claude 等多种 AI 工具
- ✅ **自动会话管理** - 自动记录每次 AI 调用的日志和统计
- ✅ **Git 集成** - 可选的自动提交功能
- ✅ **超时监控** - 智能超时检测和自动恢复
- ✅ **优雅退出** - 支持 Ctrl+C 优雅停止
- ✅ **跨平台** - 支持 Linux、macOS、Windows

## 快速开始

### 方式一：下载预编译版本

```bash
# 下载最新版本
wget https://github.com/yourusername/dev-bot/releases/latest/download/dev-bot-linux-amd64.tar.gz

# 解压
tar -xzf dev-bot-linux-amd64.tar.gz

# 运行
cd linux-amd64
./dev-bot
```

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/yourusername/dev-bot.git
cd dev-bot

# 运行
python main.py
```

## 配置

通过修改 `config.json` 文件来配置 Dev-Bot：

```json
{
  "ai_command": "iflow",
  "prompt_file": "PROMPT.md",
  "timeout": 300
}
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `ai_command` | string | "iflow" | AI 工具命令（必需） |
| `prompt_file` | string | "PROMPT.md" | 提示词文件路径 |
| `timeout` | integer | 300 | 超时时间（秒） |

## 许可证

MIT License