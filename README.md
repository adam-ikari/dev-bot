# Dev-Bot

Dev-Bot - AI 驱动开发工具集，包含 Spec Driven Development (SDD) 工具

## 功能特性

Dev-Bot 提供五大核心功能模块：

### 1. AI 驱动开发循环
- 自动循环调用 AI 工具完成开发任务
- 可配置的 AI 工具和提示词
- 自动会话记录和统计
- 可选的 Git 自动提交
- 超时监控和自动恢复
- **Spec 和代码一致性检查**: 自动检测 Spec 与代码实现的不一致，通过 REPL 非阻塞询问用户
- **动态提示词修改**: 每轮 AI 决策时自动生成对提示词的修改或补充，在保留原有上下文的基础上智能调整工作方向

### 2. Spec Driven Development (SDD)
- 创建和管理规格说明文档
- 使用 AI 自动生成 spec
- 验证 spec 格式
- 初始化 SDD 项目结构
- **一致性分析**: AI 驱动的 Spec 与代码对比分析

### 3. 核心功能（精简架构）
- **Spec 驱动开发**: 基于 Spec 文件进行开发
- **AI 循环**: 持续的 AI 决策和执行循环
- **REPL 模式**: 非阻塞用户交互
- **自动修复**: AI 驱动的错误修复
- **自动重启**: 智能崩溃恢复和重启策略

### 4. 统一日志系统 🆕
- **多级别日志**: 支持 DEBUG, INFO, WARNING, ERROR, CRITICAL
- **灵活输出**: 控制台和文件输出双模式
- **日志轮转**: 自动日志文件轮转，避免单个文件过大
- **格式自定义**: 支持自定义日志格式和日期格式
- **性能优化**: 高性能日志记录，支持高并发场景

### 5. 技术栈检测 🆕
- **自动识别**: 自动检测项目使用的编程语言、框架和工具
- **详细报告**: 生成完整的技术栈报告，包括：
  - 编程语言和版本
  - 主要框架和库
  - 数据库类型
  - 测试框架
  - 构建工具
  - 依赖管理工具
  - 代码规范工具
  - CI/CD 和其他工具
- **多语言支持**: 支持 Python、JavaScript、TypeScript、Java、Go、Rust 等

### 6. 配置验证增强 🆕
- **完整验证**: 使用 ConfigValidator 进行全面的配置验证
- **友好错误**: 提供清晰的错误消息和修复建议
- **类型检查**: 验证字段类型和值范围
- **自定义规则**: 支持自定义验证规则和 schema

## 安装

### 使用 uv 安装（推荐）

```bash
pip install uv
uv pip install dev-bot
# 或本地安装
uv pip install -e .
```

### 使用 pip 安装

```bash
pip install dev-bot
# 或本地安装
pip install -e .
```

## 使用

### AI 驱动开发循环

运行 AI 开发循环，自动调用 AI 工具：

```bash
# 命令行模式
dev-bot run

# TUI 模式（推荐）- 终端用户界面
dev-bot run --tui

# 指定配置文件
dev-bot run --config my-config.json
```

#### TUI 模式

TUI（Terminal User Interface）模式提供更好的用户体验：

**界面布局**：
- **上方区域**: AI 运行日志显示（根据屏幕高度自动调整）
  - 支持彩色输出
  - 可滚动查看历史日志
  - 不同类型日志使用不同颜色区分
- **下方区域**: REPL 输入区域（根据屏幕高度自动调整）
  - 实时用户输入
  - 非阻塞式交互
  - 自动适应屏幕大小变化

**自动调整规则**：
- 小屏幕（< 20 行）: 日志 70%，REPL 30%
- 中等屏幕（20-30 行）: 日志 75%，REPL 25%
- 大屏幕（> 30 行）: 日志 80%，REPL 20%
- 最小保护: REPL 至少保留 5 行

**快捷键**：
- `Ctrl+C` 或 `Ctrl+Q`: 退出
- `F1`: 全屏日志
- `F2`: 全屏 REPL
- `↑/↓`: 滚动日志（日志区域） / 滚动历史输入（REPL 输入框）
- `Enter`: 发送输入

**历史输入**：
- 在 REPL 输入框中按 `↑` 查看上一条历史输入
- 在 REPL 输入框中按 `↓` 查看下一条历史输入
- 可以编辑历史输入后重新发送

**日志类型**：
- [blue] 信息日志
- [green] 成功消息
- [yellow] 警告消息
- [red] 错误消息
- [cyan] AI 输出
- [dim] 调试信息

配置文件 `config.json`：

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

### Spec Driven Development

#### 初始化 SDD 项目

```bash
# 创建标准项目
dev-bot sdd init my-project

# 使用完整模板
dev-bot sdd init my-project --template full

# 快捷方式
dev-bot init my-project
```

项目结构：
```
my-project/
├── specs/           # spec 文件目录
├── src/             # 源代码目录
├── tests/           # 测试目录
├── docs/            # 文档目录
└── sdd-config.json  # SDD 配置文件
```

#### 创建 Spec 文件

```bash
# 手动创建
dev-bot sdd new-spec user-auth --type feature

# 使用 AI 创建
dev-bot sdd ai-spec user-auth --type feature --desc "用户认证功能"

# 验证 spec
dev-bot sdd validate specs/user-auth.json
```

#### Spec 类型

- **feature**: 功能规格（需求、用户故事、验收标准）
- **api**: API 规格（端点、模型、认证）
- **component**: 组件规格（属性、事件、方法）
- **service**: 服务规格（接口、依赖、配置）

## 命令参考

```bash
dev-bot --help                    # 查看帮助
dev-bot run                       # 运行 AI 开发循环
dev-bot sdd --help                # SDD 工具帮助
dev-bot sdd init <name>           # 初始化项目
dev-bot sdd new-spec <name>       # 创建 spec
dev-bot sdd ai-spec <name>        # AI 创建 spec
dev-bot sdd validate <file>       # 验证 spec
```

## 新功能使用指南

### 统一日志系统

在代码中使用日志系统：

```python
from dev_bot import setup_logging, get_logger, info, error

# 配置日志系统
setup_logging(
    log_level="INFO",
    log_dir="./logs",
    enable_file=True,
    enable_console=True
)

# 获取日志记录器
logger = get_logger(__name__)
logger.info("Application started")
logger.error("An error occurred")

# 使用便捷函数
info("Info message")
error("Error message")
```

日志级别：
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息消息
- **WARNING**: 警告消息
- **ERROR**: 错误消息
- **CRITICAL**: 严重错误消息

### 技术栈检测

在代码中检测项目技术栈：

```python
from dev_bot import detect_tech_stack, generate_tech_stack_report

# 检测技术栈
tech_stack = detect_tech_stack()

# 生成报告
report = generate_tech_stack_report()
print(report)
```

输出示例：
```
技术栈识别报告：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

编程语言: Python 3.13.3
主要框架: FastAPI, SQLAlchemy
数据库: PostgreSQL
测试框架: pytest
构建工具: Hatchling
依赖管理: uv (基于 pyproject.toml)
代码规范: ruff, pytest
其他工具: GitHub Actions, Docker

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 配置验证

在代码中验证配置：

```python
from dev_bot import ConfigValidator
from pathlib import Path

# 创建验证器
validator = ConfigValidator()

# 验证配置文件
result = validator.validate(Path("config.json"))

if result.is_valid:
    print("配置验证通过")
else:
    print("配置验证失败：")
    for error in result.errors:
        print(f"  - {validator.format_error(error)}")
```

## 工作流程

### Spec Driven Development 工作流

1. **初始化项目**: `dev-bot init my-project`
2. **创建 spec**: `dev-bot sdd ai-spec feature --desc "功能描述"`
3. **验证 spec**: `dev-bot sdd validate spec.json`
4. **生成代码**: 使用 AI 工具基于 spec 生成代码
5. **迭代优化**: 根据需求调整 spec 和代码

### AI 开发循环工作流

1. **配置 AI 工具**: 编辑 `config.json`
2. **准备提示词**: 编辑 `PROMPT.md`
3. **运行循环**: `dev-bot run`
4. **查看日志**: 检查 `.ai-logs/` 目录
5. **自动提交**: Git 自动记录会话

## 配置说明

### AI 开发循环配置项

- `prompt_file`: 提示词文件路径
- `ai_command`: AI 工具命令（iflow、claude 等）
- `ai_command_args`: AI 工具命令参数
- `timeout_seconds`: 超时时间（秒）
- `wait_interval`: 等待间隔（秒）
- `log_dir`: 日志目录
- `stats_file`: 统计文件路径
- `session_counter_file`: 会话计数器文件路径
- `auto_commit`: 是否自动提交到 Git
- `git_commit_template`: Git 提交消息模板

### SDD 项目配置

`sdd-config.json`：

```json
{
  "project": {
    "name": "my-project",
    "version": "0.1.0",
    "description": ""
  },
  "sdd": {
    "specs_dir": "specs",
    "src_dir": "src",
    "tests_dir": "tests",
    "default_spec_type": "feature"
  },
  "code_generation": {
    "framework": "auto",
    "style_guide": "pep8"
  }
}
```

## 注意事项

- 确保 AI 工具命令在系统 PATH 中可用
- 提示词文件必须存在
- Git 提交功能需要项目在 Git 仓库中
- Python 版本要求：3.8+

## 更多文档

- [SDD CLI 使用指南](SDD_CLI_README.md)
- [AI 创建 Spec 指南](SDD_AI_GUIDE.md)
- [Spec 和代码一致性检查](docs/SPEC_CODE_CONSISTENCY.md)
- [TUI 用户指南](docs/TUI_GUIDE.md)
- [动态提示词功能](docs/DYNAMIC_PROMPT.md)

## 许可证

MIT