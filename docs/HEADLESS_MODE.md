# Dev-Bot Headless 模式完整指南

## 概述

Headless 模式提供全自动、无交互的执行方式，适合自动化场景。

## 核心特性

- **全自动运行**：无需用户交互，完全自动化
- **JSON 输出**：结果以 JSON 格式输出，便于程序解析
- **无进度显示**：不显示进度条或交互提示
- **适合集成**：适合 CI/CD、自动化脚本、API 集成

## 使用方法

### 基本用法

```bash
dev-bot run --headless "任务描述"
```

### 结合其他模式

```bash
# Headless + 规划模式
dev-bot run --headless --plan "分析代码"

# Headless + 执行模式
dev-bot run --headless -y "修复 bug"

# Headless + 思考模式
dev-bot run --headless --thinking "优化性能"
```

### 自定义 API 配置

```bash
dev-bot run --headless --api-host 0.0.0.0 --api-port 9000 "任务"
```

## 输出格式

### 成功响应

```json
{
  "success": true,
  "mode": "normal",
  "duration": 21.85,
  "output": "AI 的回复内容...",
  "error": ""
}
```

### 失败响应

```json
{
  "success": false,
  "mode": "plan",
  "duration": 5.32,
  "output": "",
  "error": "错误详情..."
}
```

## 字段说明

- `success`: 是否成功（boolean）
- `mode`: 执行模式（normal, plan, execute, thinking）
- `duration`: 执行耗时（秒）
- `output`: AI 的输出内容（字符串）
- `error`: 错误信息（成功时为空）

## 实际应用场景

### 1. CI/CD 管道

```yaml
# GitHub Actions 示例
name: Code Analysis

on: [push]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Analyze code with Dev-Bot
        run: |
          result=$(dev-bot run --headless --plan "分析代码质量")
          echo "$result" | jq .
```

### 2. 自动化脚本

```bash
#!/bin/bash

# 分析代码
echo "开始代码分析..."
result=$(dev-bot run --headless --plan "分析当前代码结构")

# 解析结果
success=$(echo "$result" | jq -r '.success')
output=$(echo "$result" | jq -r '.output')

if [ "$success" = "true" ]; then
    echo "分析成功："
    echo "$output"
else
    echo "分析失败"
    exit 1
fi
```

### 3. 定时任务

```bash
# 每天晚上 2 点运行代码检查
0 2 * * * cd /path/to/project && dev-bot run --headless "每日代码检查" > /dev/null 2>&1
```

### 4. API 集成

```python
import json
import subprocess

def run_dev_bot(prompt: str) -> dict:
    """通过 headless 模式调用 Dev-Bot"""
    cmd = ["dev-bot", "run", "--headless", prompt]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# 使用
result = run_dev_bot("生成 API 文档")
if result["success"]:
    print(result["output"])
```

### 5. 批量处理

```bash
#!/bin/bash

# 批量分析多个文件
for file in src/*.py; do
    echo "分析 $file..."
    dev-bot run --headless --plan "分析 $file" | jq .output
done
```

## 与交互模式的对比

| 特性 | 交互模式 | Headless 模式 |
|------|----------|--------------|
| 输出格式 | 人类可读文本 | JSON |
| 用户交互 | 需要交互 | 无需交互 |
| 进度显示 | 显示进度 | 不显示 |
| 适用场景 | 日常使用 | 自动化 |
| 程序解析 | 困难 | 容易 |

## 解析 JSON 输出

### Bash

```bash
# 获取 success 字段
success=$(echo "$result" | jq -r '.success')

# 获取 output 字段
output=$(echo "$result" | jq -r '.output')

# 获取 duration 字段
duration=$(echo "$result" | jq -r '.duration')
```

### Python

```python
import json

result = json.loads(output)
success = result['success']
output_text = result['output']
duration = result['duration']
```

### JavaScript/Node.js

```javascript
const result = JSON.parse(output);
const success = result.success;
const outputText = result.output;
const duration = result.duration;
```

## 最佳实践

### 1. 错误处理

```bash
result=$(dev-bot run --headless "任务")
success=$(echo "$result" | jq -r '.success')

if [ "$success" != "true" ]; then
    error=$(echo "$result" | jq -r '.error')
    echo "执行失败: $error"
    exit 1
fi
```

### 2. 超时控制

```bash
timeout 300 dev-bot run --headless "长时间任务"
```

### 3. 日志记录

```bash
dev-bot run --headless "任务" >> dev-bot.log 2>&1
```

### 4. 结果缓存

```bash
# 缓存结果到文件
result=$(dev-bot run --headless "任务")
echo "$result" > cache/result_$(date +%s).json
```

## 常见问题

### Q: Headless 模式会启动 API 服务吗？

A: 不会。Headless 模式直接调用核心功能，不启动 API 服务。`--api-host` 和 `--api-port` 参数是为将来扩展预留的。

### Q: 如何在 headless 模式下传递更复杂的参数？

A: 将参数编码到 prompt 中，例如：
```bash
dev-bot run --headless "分析文件: src/main.py, 关注: 性能优化"
```

### Q: Headless 模式支持异步调用吗？

A: 支持在异步脚本中调用，例如：
```python
import asyncio
import subprocess

async def run_headless(prompt):
    proc = await asyncio.create_subprocess_exec(
        "dev-bot", "run", "--headless", prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return json.loads(stdout.decode())
```

### Q: 如何处理超时？

A: 使用系统的 timeout 命令：
```bash
timeout 300 dev-bot run --headless "任务"
```

## 性能考虑

- Headless 模式比交互模式略快（无交互开销）
- 适合批量处理和自动化任务
- 建议为长时间任务设置合理的超时

## 安全建议

1. **验证输入**：验证 prompt 参数，避免注入攻击
2. **限制权限**：在受限环境中运行
3. **审计日志**：记录所有 headless 调用
4. **结果验证**：验证输出内容，防止意外行为

## 总结

Headless 模式是 Dev-Bot 自动化能力的核心特性，提供了：
- 全自动执行
- JSON 格式输出
- 易于集成
- 适合 CI/CD 和自动化场景

通过合理使用 headless 模式，可以实现完全自动化的 AI 驱动开发流程。