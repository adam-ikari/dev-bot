# Dev-Bot

AI 驱动开发代理 - 可配置版本

## 功能

Dev-Bot 是一个可配置的 AI 开发代理工具，用于自动化执行 AI 驱动的开发任务。

## 配置

通过 `config.json` 文件配置：

```json
{
  "prompt_file": "PROMPT.md",
  "ai_command": "iflow",
  "ai_command_args": ["-y"],
  "timeout_seconds": 300,
  "wait_interval": 0.5,
  "log_dir": ".ai-logs",
  "stats_file": ".ai-logs/stats.json",
  "session_counter_file": ".ai-logs/session_counter.json",
  "auto_commit": true,
  "git_commit_template": "chore: record AI session #{session_num} ({status})"
}
```

### 配置项说明

- `prompt_file`: 提示词文件路径
- `ai_command`: AI 工具命令（如 iflow、claude 等）
- `ai_command_args`: AI 工具命令参数
- `timeout_seconds`: 超时时间（秒）
- `wait_interval`: 等待间隔（秒）
- `log_dir`: 日志目录
- `stats_file`: 统计文件路径
- `session_counter_file`: 会话计数器文件路径
- `auto_commit`: 是否自动提交到 Git
- `git_commit_template`: Git 提交消息模板

## 使用

### 直接运行

```bash
python main.py
```

### 打包为可执行文件

```bash
# 安装 PyInstaller
pip install pyinstaller

# 使用配置文件打包
pyinstaller dev-bot.spec

# 或直接打包
pyinstaller --onefile --name dev-bot main.py
```

打包后，可执行文件位于 `dist/` 目录。

### 使用打包后的文件

```bash
./dist/dev-bot
```

## 特性

- 可配置的 AI 工具和提示词
- 自动会话记录和统计
- 可选的 Git 自动提交
- 超时监控和自动恢复
- 优雅的 Ctrl+C 处理

## 注意

- 确保 AI 工具命令在系统 PATH 中可用
- 提示词文件必须存在
- Git 提交功能需要项目在 Git 仓库中