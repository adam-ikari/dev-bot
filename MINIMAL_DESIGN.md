# Dev-Bot 极简核心设计

## 设计哲学

**极简 + AI 决策 + AI 执行**

## 核心功能（3个）

1. **AI 调用器** - 调用 iflow，让 AI 做决策
2. **进程管理** - 启动/停止 iflow 进程
3. **简单日志** - 记录输出

## 删除的非核心功能

❌ 复杂的 IPC 系统（ipc_realtime.py, ipc_zmq.py）
❌ 守护进程系统（guardian/, guardian_process.py）
❌ 进程监控器（anomaly_detector.py, auto_restart.py）
❌ AI 团队（ai_team.py, multi_iflow_manager.py）
❌ 复杂配置系统（config_validator.py, config_models.py）
❌ TUI 系统（tui.py）
❌ 文件监控（config_file_watcher.py）
❌ 状态持久化（ipc.py）
❌ 复杂的队列系统（queue_manager.py, command_scheduler.py）
❌ 进程协调器（process_coordinator.py）
❌ 进程追踪器（task_tracker.py）
❌ 全局清理（global_cleanup.py）
❌ AI 健康检查（ai_health_checker.py, ai_recovery.py）
❌ 进程统计（project_scanner.py）
❌ 事件循环控制（ai_loop_control.py, ai_loop_scheduler.py）
❌ AI 对话（ai_dialogue.py）
❌ 规范生成器（spec_generator.py）
❌ 业务逻辑层（business_logic_layer.py）

## 极简架构

```
Dev-Bot Core (200-300 lines)
├── main.py          (50 lines)  - 入口，循环调用 AI
├── iflow.py         (100 lines) - 调用 iflow，管理进程
└── logger.py        (30 lines)  - 简单日志
```

## 实现思路

```python
# iflow.py - 100 行
class IflowCaller:
    def __init__(self):
        self.process = None
    
    async def call(self, prompt):
        """调用 iflow"""
        # 1. 启动进程
        # 2. 发送 prompt
        # 3. 等待结果
        # 4. 返回输出
    
    async def stop(self):
        """停止进程"""
        # kill process

# main.py - 50 行
async def main():
    iflow = IflowCaller()
    
    while True:
        # AI 决策 + 执行
        prompt = "分析当前项目并决定下一步做什么"
        result = await iflow.call(prompt)
        print(result)
        
        await asyncio.sleep(1)

# logger.py - 30 lines
def log(message):
    print(f"[{datetime.now()}] {message}")
```

## 预期结果

- 文件数：67 → 3
- 代码量：2.9MB → <100KB
- 行数：~15,000 → ~200
- 功能：100% AI 能力

## 关键原则

1. **不做任何 AI 能做的事**
2. **不持久化状态**
3. **不监控**
4. **不恢复**
5. **不协调**
6. **只调用 iflow**

## 移除理由

| 功能 | 移除理由 |
|------|---------|
| IPC | 本地调用不需要 IPC |
| 守护进程 | iflow 自己管理进程 |
| 进程监控 | 用户手动监控 |
| 配置系统 | 硬编码默认值即可 |
| TUI | 终端输出即可 |
| 队列系统 | 串行调用更简单 |
| 健康检查 | 不需要，失败就失败 |
| 业务逻辑层 | AI 自己决定 |

## 使用方式

```bash
# 直接运行
python main.py

# AI 会：
# 1. 分析项目
# 2. 决定做什么
# 3. 自动执行
# 4. 循环直到完成
```

这就是极简！