# AI 守护与 AI 循环交互架构

## 概述

本文档描述了 Dev-Bot 的 AI 守护、AI 循环和用户交互层之间的交互架构。

## 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    用户交互层 (最顶层)                        │
│                                                              │
│  接收用户指令 → 解析命令 → 转发到 AI 守护 → 返回结果        │
│                                                              │
│  命令示例: start_ai, stop_ai, status, help                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI 守护 (中间层)                            │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  核心守护层 (不可变)                              │      │
│  │  • 进程监控                                       │      │
│  │  • 健康检查                                       │      │
│  │  • 自动恢复                                       │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  业务逻辑层 (可变)                                │      │
│  │  • 业务规则                                       │      │
│  │  • 策略配置                                       │      │
│  │  • 扩展接口                                       │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  职责: 监控 AI 循环，自动恢复，管理业务规则                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI 循环控制接口                             │
│                                                              │
│  • 启动/停止 AI 循环                                         │
│  • 暂停/恢复 AI 循环                                         │
│  • 获取状态和日志                                            │
│  • 发送消息到 AI 循环                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI 循环进程 (底层)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  两阶段 AI 循环                                   │      │
│  │                                                   │      │
│  │  阶段 1: AI 决策 (iflow --plan)                  │      │
│  │  阶段 2: AI 执行 (iflow -y)                      │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  • 接收用户指令                                              │
│  • 执行 AI 开发任务                                          │
│  • 保存长期记忆                                              │
│  • 与 iflow 交互                                             │
└─────────────────────────────────────────────────────────────┘
```

## 通信机制

### 1. 用户 → 用户交互层

**方式**: 直接函数调用或命令行输入

**示例**:
```python
# 方式 1: 直接调用
result = await user_layer.execute_command("start_ai")

# 方式 2: 交互式输入
[dev-bot] > start_ai
```

### 2. 用户交互层 → AI 循环控制器

**方式**: 直接方法调用

**示例**:
```python
# 启动 AI 循环
await ai_controller.start()

# 暂停 AI 循环
await ai_controller.pause()

# 发送消息
await ai_controller.send_message("Hello AI!")
```

### 3. AI 循环控制器 → AI 循环进程

**方式**: IPC (文件系统)

**命令文件**: `.ipc/ai_loop_command.json`
**响应文件**: `.ipc/ai_loop_response.json`

**命令格式**:
```json
{
  "command": "pause",
  "params": {},
  "timestamp": 1234567890.123
}
```

**响应格式**:
```json
{
  "success": true,
  "error": null,
  "result": "AI 循环已暂停"
}
```

### 4. AI 守护 → AI 循环

**方式**: IPC 状态监控

**状态文件**: `.ipc/ai-loop-status.json`

**监控机制**:
- 定期检查进程状态
- 检查最后响应时间
- 自动恢复异常进程

## 交互流程

### 场景 1: 启动 AI 循环

```
用户: start_ai
  ↓
用户交互层: 解析命令
  ↓
用户交互层: 调用 ai_controller.start()
  ↓
AI 循环控制器: 创建子进程
  ↓
AI 循环进程: 启动两阶段 AI 循环
  ↓
AI 守护: 监控进程状态
  ↓
用户交互层: 返回 "✓ AI 循环已启动"
```

### 场景 2: 暂停 AI 循环

```
用户: pause_ai
  ↓
用户交互层: 解析命令
  ↓
用户交互层: 调用 ai_controller.pause()
  ↓
AI 循环控制器: 写入 pause 命令到 IPC
  ↓
AI 循环进程: 读取命令，设置 is_paused = True
  ↓
AI 循环进程: 跳过当前会话
  ↓
AI 循环控制器: 等待响应
  ↓
用户交互层: 返回 "✓ AI 循环已暂停"
```

### 场景 3: 发送消息到 AI 循环

```
用户: send Please focus on bug fixes
  ↓
用户交互层: 解析命令
  ↓
用户交互层: 调用 ai_controller.send_message(msg)
  ↓
AI 循环控制器: 写入消息到 IPC
  ↓
AI 循环进程: 读取消息
  ↓
AI 循环进程: 记录消息到日志
  ↓
用户交互层: 返回 "✓ 消息已发送"
```

### 场景 4: AI 循环异常恢复

```
AI 循环进程: 异常退出
  ↓
AI 守护: 检测到进程不存在
  ↓
AI 守护: 评估进程状态（不健康）
  ↓
AI 守护: 执行恢复策略（重启）
  ↓
AI 循环控制器: 创建新进程
  ↓
AI 循环进程: 重新启动
  ↓
AI 守护: 记录恢复次数
```

## 核心组件

### 1. 用户交互层 (UserInteractionLayer)

**职责**:
- 接收和解析用户命令
- 转发命令到下层
- 显示系统状态
- 管理命令历史

**主要方法**:
- `execute_command(cmd)`: 执行用户命令
- `start()`: 启动交互层
- `stop()`: 停止交互层

### 2. AI 循环控制器 (AILoopController)

**职责**:
- 控制 AI 循环进程生命周期
- 发送命令到 AI 循环
- 获取 AI 循环状态和日志

**主要方法**:
- `start()`: 启动 AI 循环
- `stop()`: 停止 AI 循环
- `pause()`: 暂停 AI 循环
- `resume()`: 恢复 AI 循环
- `send_message(msg)`: 发送消息
- `get_status()`: 获取状态

### 3. AI 守护 (AIGuardian)

**职责**:
- 监控 AI 循环进程
- 自动恢复异常进程
- 执行业务规则

**主要方法**:
- `start()`: 启动守护
- `stop()`: 停止守护
- `register_process()`: 注册进程
- `add_business_rule()`: 添加业务规则

### 4. AI 循环进程 (AILoopProcess)

**职责**:
- 执行两阶段 AI 循环
- 接收和处理命令
- 保存长期记忆

**主要方法**:
- `run()`: 运行 AI 循环
- `_check_command()`: 检查命令
- `_handle_command()`: 处理命令

## 可用命令

### AI 循环控制
- `start_ai` - 启动 AI 循环
- `stop_ai` - 停止 AI 循环
- `pause_ai` - 暂停 AI 循环
- `resume_ai` - 恢复 AI 循环
- `restart_ai` - 重启 AI 循环

### 状态查询
- `status` - 查看系统状态
- `ai_status` - 查看 AI 循环状态
- `guardian_status` - 查看 AI 守护状态
- `logs [N]` - 查看最近 N 条日志

### 消息发送
- `send <msg>` - 发送消息到 AI 循环

### 其他
- `help` - 显示帮助信息
- `exit` / `quit` - 退出系统

## 使用示例

### 交互式模式

```bash
python3 -m dev_bot.user_interaction
```

```
[dev-bot] > start_ai
✓ AI 循环已启动

[dev-bot] > status
=== 系统状态 ===
AI 循环: running (PID: 12345)
AI 守护: 运行中
恢复次数: 0

[dev-bot] > send Please focus on testing
✓ 消息已发送: Please focus on testing...

[dev-bot] > pause_ai
✓ AI 循环已暂停

[dev-bot] > resume_ai
✓ AI 循环已恢复

[dev-bot] > stop_ai
✓ AI 循环已停止

[dev-bot] > exit
```

### 编程方式

```python
import asyncio
from pathlib import Path
from dev_bot.user_interaction import UserInteractionLayer

async def main():
    project_root = Path.cwd()
    user_layer = UserInteractionLayer(project_root)
    
    # 启动
    await user_layer.start()
    
    # 控制循环
    await user_layer.execute_command("start_ai")
    await asyncio.sleep(10)
    await user_layer.execute_command("pause_ai")
    await asyncio.sleep(5)
    await user_layer.execute_command("resume_ai")
    await asyncio.sleep(10)
    await user_layer.execute_command("stop_ai")
    
    # 停止
    await user_layer.stop()

asyncio.run(main())
```

## 扩展性

### 添加新命令

在 `UserInteractionLayer` 中添加新的命令处理方法：

```python
async def _cmd_custom(self) -> str:
    """自定义命令"""
    # 实现逻辑
    return "✓ 自定义命令执行成功"
```

然后在 `execute_command` 中添加命令匹配：

```python
elif cmd_str == "custom":
    return await self._cmd_custom()
```

### 添加新业务规则

创建自定义业务规则：

```python
from dev_bot.guardian import BusinessRule

class CustomRule(BusinessRule):
    async def evaluate(self, process_type, process_info):
        # 评估逻辑
        return True
    
    async def execute(self, process_type, process_info):
        # 执行逻辑
        return True

# 添加到 AI 守护
ai_guardian.add_business_rule(CustomRule())
```

## 总结

AI 守护与 AI 循环交互架构提供了：

- ✅ **清晰的层次结构**：用户层 → 守护层 → 控制层 → 执行层
- ✅ **灵活的通信机制**：支持同步和异步通信
- ✅ **强大的控制能力**：启动、停止、暂停、恢复、消息发送
- ✅ **自动恢复机制**：AI 守护自动监控和恢复异常进程
- ✅ **易于扩展**：支持添加新命令和业务规则
- ✅ **完整的状态管理**：实时监控各层状态

这个架构确保了 Dev-Bot 系统的稳定性、可扩展性和用户友好性。