# Dev-Bot 统一命令行接口

## 快速开始

Dev-Bot 提供统一的命令行接口，支持多种功能：

```bash
# 查看帮助
dev-bot --help

# 启动 TUI 模式（默认）
dev-bot

# 快速执行任务
dev-bot run "分析这个文件"

# 自我迭代（一次）
dev-bot iterate

# 持续自我迭代
dev-bot iterate --continuous

# 创建对话
dev-bot dialogue create "讨论主题"
```

**默认行为**：
- 直接运行 `dev-bot`（不带任何参数）会启动 **TUI 模式**
- TUI 模式提供交互式命令行界面
- 可以在 TUI 中提交问题、查看队列、管理对话等

## 命令列表

### 1. UI - 用户界面

```bash
dev-bot ui                    # TUI 模式
dev-bot ui --mode web         # Web 模式
dev-bot ui --mode api         # API 模式
```

### 2. Run - 快速执行

```bash
dev-bot run "任务描述"                     # 普通模式（交互式）
dev-bot run --headless "任务描述"          # 无头模式（全自动，输出 JSON）
dev-bot run --plan "任务描述"              # 规划模式
dev-bot run -y "任务描述"                  # 执行模式
dev-bot run --thinking "任务描述"          # 思考模式
```

#### Headless 模式

`--headless` 选项提供全自动、无交互的执行方式：

- **JSON 输出**：结果以 JSON 格式输出，便于程序解析
- **无交互**：完全自动化，无需用户输入
- **适合集成**：适合 CI/CD、自动化脚本、API 集成

**输出格式**：
```json
{
  "success": true,
  "mode": "normal",
  "duration": 21.85,
  "output": "AI 的回复内容...",
  "error": ""
}
```

**使用场景**：
```bash
# CI/CD 管道
dev-bot run --headless --plan "分析代码" | jq .

# 自动化脚本
result=$(dev-bot run --headless "生成代码")
echo $result | jq .output

# 定时任务
0 2 * * * dev-bot run --headless "每日代码检查"
```

### 3. Iterate - 迭代系统

```bash
dev-bot iterate                              # 运行一次迭代
dev-bot iterate --once                       # 运行一次迭代
dev-bot iterate --continuous                 # 连续迭代模式
dev-bot iterate --project /path/to/project   # 迭代其他项目
```

### 4. Dialogue - 对话系统

```bash
dev-bot dialogue create "主题"                           # 创建对话
dev-bot dialogue list                                   # 列出对话
dev-bot dialogue info <对话ID>                           # 查看对话
dev-bot dialogue run <对话ID>                            # 运行对话
```

## 典型使用场景

### 场景 1: Dev-Bot 自我迭代

```bash
# 让 Dev-Bot 持续自我改进
dev-bot iterate --continuous
```

### 场景 2: Dev-Bot 开发其他项目

```bash
# Dev-Bot 开发 Web 应用
dev-bot iterate --project /path/to/web-app --continuous

# Dev-Bot 开发机器学习项目
dev-bot iterate --project /path/to/ml-project --continuous
```

### 场景 3: AI 团队协作

```bash
# 创建 AI 团队对话
dev-bot dialogue create "设计新功能"

# 运行对话
dev-bot dialogue run dialogue_xxx

# 查看结果
dev-bot dialogue info dialogue_xxx
```

### 场景 4: 快速任务执行

```bash
# 分析代码
dev-bot run --plan "分析 src/main.py"

# 执行重构
dev-bot run -y "重构 user 模块"
```

## 详细文档

完整的命令行参考请查看：[CLI_REFERENCE.md](docs/CLI_REFERENCE.md)

## 核心特性

- **统一接口**：所有功能通过统一的命令行接口访问
- **灵活切换**：轻松在不同项目和模式间切换
- **完全自主**：AI 自主分析、决策、执行
- **持续改进**：支持持续迭代，自动优化项目