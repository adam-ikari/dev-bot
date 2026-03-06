# Dev-Bot 命令行参考

## 统一命令入口

Dev-Bot 提供统一的命令行接口，支持多种功能：

```bash
python -m dev_bot [命令] [参数]
```

或使用安装后的命令：

```bash
dev-bot [命令] [参数]
```

## 命令概览

```
dev-bot
├── ui                    # 用户界面
├── run                   # 快速执行
├── iterate               # 迭代系统
└── dialogue              # 对话系统
```

## 1. UI 命令 - 用户界面

启动 Dev-Bot 的用户界面。

### 基本用法

```bash
# 启动 TUI 模式（默认）
dev-bot ui

# 启动 Web 模式
dev-bot ui --mode web

# 启动 API 模式
dev-bot ui --mode api
```

### 参数

- `--mode`: 交互模式
  - `tui`: 终端用户界面（默认）
  - `web`: 网页端
  - `api`: REST API
- `--host`: Web/API 监听地址（默认: 127.0.0.1）
- `--port`: Web/API 监听端口（默认: 8080）

### 示例

```bash
# TUI 模式
dev-bot ui

# Web 模式，监听所有接口
dev-bot ui --mode web --host 0.0.0.0 --port 9000

# API 模式
dev-bot ui --mode api
```

## 2. Run 命令 - 快速执行

快速执行一个 iflow 命令。

### 基本用法

```bash
# 普通模式
dev-bot run "分析这个文件"

# 规划模式
dev-bot run --plan "设计一个 REST API"

# 执行模式
dev-bot run -y "修复这个 bug"

# 思考模式
dev-bot run --thinking "优化这段代码"
```

### 参数

- `--plan`: 规划模式（只分析不执行）
- `-y`: 执行模式（直接执行无需授权）
- `--thinking`: 思考模式（更全面的分析）
- `prompt`: 提示词（必需）

### 示例

```bash
# 分析代码
dev-bot run --plan "分析 src/main.py 的代码结构"

# 执行重构
dev-bot run -y "重构 user 模块"

# 深度思考
dev-bot run --thinking "如何提高系统性能"
```

## 3. Iterate 命令 - 迭代系统

启动自我迭代系统，让 Dev-Bot 持续改进项目。

### 基本用法

```bash
# 运行一次自我迭代
dev-bot iterate

# 启动连续自我迭代
dev-bot iterate --continuous

# 迭代其他项目
dev-bot iterate --project /path/to/other/project
```

### 参数

- `--continuous`: 连续迭代模式
- `--interval`: 迭代间隔（秒，默认: 1800，即 30 分钟）
- `--project`: 项目路径（默认: 当前目录）
- `--once`: 只运行一次迭代（与不指定参数相同）

### 示例

```bash
# Dev-Bot 自我迭代
dev-bot iterate

# Dev-Bot 开发 Web 应用项目
dev-bot iterate --project /path/to/web-app

# 持续迭代，每 10 分钟一次
dev-bot iterate --continuous --interval 600
```

### 迭代流程

每次迭代包括：
1. **观察** - 收集测试结果、覆盖率、错误日志等
2. **AI 分析决策** - AI 分析当前状态，决定如何改进
3. **AI 执行** - AI 执行改进步骤
4. **验证** - 验证改进效果

迭代日志保存在 `.dev-bot-evolution/iteration_log.json`

## 4. Dialogue 命令 - 对话系统

管理 AI 对话系统。

### 子命令

#### 4.1 创建对话

```bash
dev-bot dialogue create "对话主题" [--participants 参与者...]
```

**参数**：
- `topic`: 对话主题（必需）
- `--participants`: 参与者列表（可选，默认: analyzer, developer, tester）

**示例**：
```bash
# 创建对话
dev-bot dialogue create "如何优化数据库查询"

# 指定参与者
dev-bot dialogue create "设计 API 接口" --participants architect developer reviewer
```

#### 4.2 列出对话

```bash
dev-bot dialogue list
```

**示例**：
```bash
dev-bot dialogue list
```

#### 4.3 查看对话信息

```bash
dev-bot dialogue info <对话ID>
```

**参数**：
- `dialogue_id`: 对话 ID（必需）

**示例**：
```bash
dev-bot dialogue info dialogue_1234567890_0
```

#### 4.4 运行对话

```bash
dev-bot dialogue run <对话ID> [--duration 最大持续时间]
```

**参数**：
- `dialogue_id`: 对话 ID（必需）
- `--duration`: 最大持续时间（秒，默认: 300）

**示例**：
```bash
# 运行对话
dev-bot dialogue run dialogue_1234567890_0

# 运行对话，最长 10 分钟
dev-bot dialogue run dialogue_1234567890_0 --duration 600
```

## 快速参考

### 常用命令

```bash
# 启动 Dev-Bot
dev-bot ui

# 快速执行
dev-bot run "任务描述"

# 自我迭代（一次）
dev-bot iterate

# 持续自我迭代
dev-bot iterate --continuous

# 创建对话
dev-bot dialogue create "主题"
```

### 查看帮助

```bash
# 主帮助
dev-bot --help

# 子命令帮助
dev-bot ui --help
dev-bot run --help
dev-bot iterate --help
dev-bot dialogue --help
```

## 实际应用场景

### 场景 1: 日常开发

```bash
# 启动 Dev-Bot TUI
dev-bot ui

# 在 TUI 中提交任务
dev-bot> 分析这个模块
dev-bot> --plan 设计重构方案
dev-bot> -y 执行重构
```

### 场景 2: Dev-Bot 自我改进

```bash
# 让 Dev-Bot 持续自我改进
dev-bot iterate --continuous

# Dev-Bot 会自动：
# 1. 分析自身测试结果
# 2. 识别问题
# 3. 制定改进方案
# 4. 执行改进
# 5. 验证效果
```

### 场景 3: Dev-Bot 开发其他项目

```bash
# Dev-Bot 开发 Web 应用
dev-bot iterate --project /path/to/web-app --continuous

# Dev-Bot 开发机器学习项目
dev-bot iterate --project /path/to/ml-project --continuous
```

### 场景 4: AI 团队协作

```bash
# 创建 AI 团队对话
dev-bot dialogue create "设计新功能"

# 运行对话，让 AI 团队协作
dev-bot dialogue run dialogue_xxx

# 查看对话结果
dev-bot dialogue info dialogue_xxx
```

## 注意事项

1. **执行模式**：使用 `-y` 参数时会直接执行，无需确认，请谨慎使用
2. **连续迭代**：连续迭代会持续运行，建议先测试单次迭代效果
3. **项目路径**：迭代其他项目时，确保项目有测试和覆盖率配置
4. **AI 依赖**：所有功能都依赖 iflow，确保 iflow 正确配置

## 进阶用法

### 组合使用

```bash
# 先分析，再执行
dev-bot run --plan "分析问题"
dev-bot run -y "解决问题"

# 迭代前后对比
dev-bot iterate --once
# ... 等待迭代完成
dev-bot iterate --once
```

### 脚本集成

```bash
#!/bin/bash
# 自动化脚本

# 运行测试
uv run pytest

# 让 Dev-Bot 分析并修复
dev-bot iterate --once

# 再次运行测试验证
uv run pytest
```

### 定时任务

```bash
# 每天晚上自动迭代
0 2 * * * cd /path/to/project && dev-bot iterate --once
```

## 故障排除

### 命令未找到

如果 `dev-bot` 命令未找到，使用 Python 模块方式：

```bash
python -m dev_bot [命令] [参数]
```

### 迭代失败

检查：
1. 项目是否有测试配置
2. iflow 是否正确安装和配置
3. 查看迭代日志：`.dev-bot-evolution/iteration_log.json`

### 对话系统问题

检查：
1. 对话 ID 是否正确
2. 参与者是否已定义
3. 查看对话日志

## 更多信息

- [迭代系统文档](SELF_ITERATION.md)
- [统一迭代文档](UNIFIED_ITERATION.md)
- [对话系统文档](AI_INTERACTION_ARCHITECTURE.md)