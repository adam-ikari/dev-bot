# Dev-Bot 架构 V2 - iflow 驱动系统

## 核心哲学

**Dev-Bot 的核心哲学是监督 iflow 工作，通过循环迭代，调用 iflow 完成自主迭代、自主修复、自主开发、自主进化。**

## 架构概览

```
Dev-Bot (轻量级驱动器和长期记忆)
│
├── 长期记忆系统
│   ├── 项目历史记录
│   ├── 提示词优化历史
│   ├── 开发经验总结
│   └── 学习成果保存 (.dev-bot-memory/context.json)
│
├── 驱动循环（两阶段 AI 循环）
│   ├── 阶段 1: AI 决策 (iflow --plan)
│   │   ├── 读取长期记忆
│   │   ├── 读取 spec 文件
│   │   ├── 分析当前项目状态
│   │   └── 决定下一步做什么
│   │
│   └── 阶段 2: AI 执行 (iflow -y)
│       ├── 根据决策执行任务
│       ├── 编写代码
│       ├── 修复错误
│       └── 完成功能
│
├── 监督界面 (TUI)
│   └── 显示 iflow 工作状态
│
└── 兜底机制 (AI 终端读取系统)
    ├── 检测 iflow 无限错误迭代
    ├── 自主修复（开发自身的时候）
    └── 自主重启 AI 循环
```

## 核心职责

### Dev-Bot 的职责
1. **提供长期记忆** - 保存 iflow 的历史、上下文、学习成果
2. **提供驱动循环** - 持续调用 iflow，让它不断迭代
3. **提供监督界面** - TUI 显示 iflow 工作状态和进度
4. **提供兜底机制** - AI 终端读取系统在最底层保障程序运行
5. **Spec 驱动** - 通过 spec 引导 iflow 进行有目的的开发

### iflow 的职责
1. **自主决策** - 分析项目，决定下一步做什么
2. **自主执行** - 根据决策执行任务
3. **自主修复** - 发现问题，自动修复
4. **自主开发** - 实现功能，添加代码
5. **自主进化** - 优化架构，提升能力

## 两阶段 AI 循环

### 阶段 1: AI 决策
```bash
iflow --plan "分析当前项目状态，决定下一步要做什么"
```

- 使用 `--plan` 参数
- 只允许 iflow 做决策和规划
- 不执行任何修改操作
- 输出决策结果和实现策略

### 阶段 2: AI 执行
```bash
iflow -y "根据决策执行任务，编写代码，修复错误"
```

- 使用 `-y` 参数（yolo 模式）
- 授权 iflow 执行操作无需用户授权
- iflow 可以直接修改代码
- iflow 可以直接执行命令

## iflow 参数说明

| 参数 | 说明 | 互斥 | 使用场景 |
|------|------|------|----------|
| `--plan` | 只做计划，不执行 | 与 `-y` 互斥 | AI 决策阶段 |
| `-y` | yolo 模式，无需授权 | 与 `--plan` 互斥 | AI 执行阶段 |
| `--thinking` | 思考模式，更全面 | 无 | 复杂任务分析 |

## 完全自主运行

整个过程**人工干预不是必须的**：

```
启动 Dev-Bot
    ↓
Dev-Bot 提供长期记忆和驱动循环
    ↓
iflow 开始自主工作
    ├── 分析项目
    ├── 规划任务
    ├── 执行开发
    ├── 修复错误
    └── 优化提示词
    ↓
持续迭代（无限循环）
    ↓
如果出现问题
    ├── 兜底机制检测问题
    ├── iflow 自主修复
    ├── iflow 自主重启
    └── 继续工作
    ↓
（无需人工干预）
```

## 自主进化的含义

### 1. 自我迭代开发（针对自身项目）
- Dev-Bot 自己修改自己的工程代码
- 自己添加新功能
- 自己修复 bug
- 自己优化架构
- 自己提升能力

### 2. 优化提示词（针对其他项目）
- 为其他项目生成和优化提示词
- 根据项目特点调整 iflow 的工作方式
- 迭代改进开发流程
- 提升其他项目的开发效率

## 兜底机制

### 三大作用

1. **发现 iflow 无限错误迭代**
   - 监控 iflow 的工作状态
   - 检测到 iflow 陷入错误循环
   - 防止无限重复相同的错误操作
   - 及时中断并恢复

2. **自主修复**（开发自身的时候）
   - 当 Dev-Bot 运行时发生错误
   - AI 终端读取系统检测到错误
   - iflow 自主修复自己的代码
   - 恢复正常运行

3. **自主重启 AI 循环**
   - 当 AI 循环意外终止
   - AI 终端读取系统检测到终止
   - 自动重启 AI 循环
   - 确保持续工作

## 实现细节

### 长期记忆系统

```python
# 记忆文件路径
memory_file = project_root / ".dev-bot-memory" / "context.json"

# 记忆结构
{
  "history": [
    {
      "session": 1,
      "phase": "decision",
      "timestamp": "2026-03-05T10:00:00",
      "content": "决策内容..."
    },
    {
      "session": 1,
      "phase": "execution",
      "timestamp": "2026-03-05T10:01:00",
      "content": "执行结果..."
    }
  ],
  "learnings": [],
  "context": {}
}
```

### AI 循环流程

```python
async def ai_loop():
    while not shutdown_requested:
        # 加载长期记忆
        memory = load_memory()
        
        # 读取 spec
        spec_content = read_spec()
        
        # ========== 阶段 1: AI 决策 ==========
        decision_prompt = f"""
当前上下文：{memory['context']}
Spec 内容：{spec_content}
分析当前项目状态，决定下一步要做什么。
"""
        
        decision = await call_iflow(
            prompt=decision_prompt,
            args=["--plan"]  # 只做计划
        )
        
        # ========== 阶段 2: AI 执行 ==========
        execution_prompt = f"""
决策结果：{decision}
根据决策执行任务，编写代码，修复错误。
"""
        
        result = await call_iflow(
            prompt=execution_prompt,
            args=["-y"]  # yolo 模式
        )
        
        # 保存结果到长期记忆
        memory['history'].append({
            "session": session_num,
            "phase": "decision",
            "content": decision
        })
        memory['history'].append({
            "session": session_num,
            "phase": "execution",
            "content": result
        })
        
        save_memory(memory)
```

## 核心优势

1. **清晰的分离** - 决策和执行分开，职责明确
2. **灵活的决策** - iflow 可以根据情况做出不同的决策
3. **高效的执行** - 有了明确的决策，执行更加专注
4. **持续迭代** - 每轮循环都基于前一轮的结果
5. **完全自主** - 无需人工干预
6. **Spec 驱动** - 所有工作都基于 spec
7. **长期记忆** - 持续积累知识和经验

## 总结

Dev-Bot 现在是一个轻量级的 iflow 驱动器和长期记忆系统：

- **Dev-Bot 不做决策** - 所有决策由 iflow 做出
- **Dev-Bot 不执行代码** - 所有代码修改由 iflow 完成
- **Dev-Bot 只驱动** - 提供循环和上下文
- **iflow 是主角** - Dev-Bot 只是 iflow 的助手

这样的架构更清晰、更简单，充分发挥 iflow 作为 AI Agent 的能力！