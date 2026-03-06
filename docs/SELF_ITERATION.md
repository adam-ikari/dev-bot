# Dev-Bot 极简自我迭代系统

## 核心设计原则

1. **极简设计** - 只依赖 AI 能力，不使用复杂的决策系统、学习系统、优化系统
2. **AI 自主** - AI 自主决定做什么、怎么做
3. **单次迭代** - 每次迭代独立，AI 根据当前状态决策

## 迭代循环

```
观察 → AI 分析决策 → AI 执行 → 验证
```

### 1. 观察阶段
收集当前系统状态：
- 测试结果
- 代码覆盖率
- 错误数量
- Git 状态
- 系统指标（CPU、内存）

### 2. AI 分析决策阶段
AI 分析当前状态并决定改进方向：
- 分析当前问题
- 识别最需要改进的地方
- 制定改进计划
- 确定实施步骤

### 3. AI 执行阶段
AI 执行改进步骤：
- 使用 iflow 执行每个步骤
- 支持代码修改、命令执行、任务分析
- 记录执行结果

### 4. 验证阶段
验证改进效果：
- 重新运行测试
- 比较覆盖率变化
- 比较错误数量变化
- 判断改进是否成功

## 使用方式

### 单次迭代

```python
from pathlib import Path
from dev_bot.self_iteration_simple import SimpleSelfIteration

# 创建迭代系统
iteration = SimpleSelfIteration(Path("/path/to/project"))

# 运行一次迭代
result = await iteration.run_iteration()

# 查看结果
print(f"迭代 ID: {result['iteration_id']}")
print(f"AI 决策: {result['decision']['action']}")
print(f"执行成功: {result['execution']['success']}")
print(f"改进成功: {result['verification']['success']}")
```

### 连续迭代

```python
from pathlib import Path
from dev_bot.self_iteration_simple import SimpleSelfIteration

# 创建迭代系统
iteration = SimpleSelfIteration(Path("/path/to/project"))

# 启动连续迭代（每 30 分钟）
await iteration.start_continuous_iteration(interval=1800)

# 停止迭代
iteration.stop()
```

## 迭代日志

每次迭代的结果会保存在 `.dev-bot-evolution/iteration_log.json` 中：

```json
[
  {
    "iteration_id": "iter_1_1234567890",
    "timestamp": 1234567890.0,
    "context": {
      "test_results": 0,
      "coverage": 45.5,
      "error_count": 3,
      "git_dirty": false
    },
    "decision": {
      "analysis": "测试通过但覆盖率低",
      "problem": "代码覆盖率不足",
      "action": "add_tests",
      "steps": ["为关键模块添加测试"]
    },
    "execution": {
      "success": true,
      "steps_completed": ["为关键模块添加测试"],
      "changes": [...]
    },
    "verification": {
      "success": true,
      "improvements": {
        "coverage_improved": true,
        "delta_coverage": 5.5
      }
    }
  }
]
```

## AI 决策示例

AI 可以做出以下类型的决策：

1. **修复测试** - 当测试失败时
2. **添加测试** - 当覆盖率低时
3. **优化代码** - 当性能有问题时
4. **重构代码** - 当代码质量差时
5. **添加功能** - 当需要新功能时
6. **修复错误** - 当有错误日志时
7. **更新文档** - 当文档不完整时
8. **跳过** - 当无需改进时

## 优势

1. **完全自主** - AI 自主分析、决策、执行，无需人工干预
2. **极简实现** - 代码简洁，易于理解和维护
3. **灵活可配置** - 可以调整迭代间隔、AI 超时等参数
4. **可追溯** - 完整的迭代日志，便于回顾和学习
5. **渐进式改进** - 每次迭代改进一点点，持续优化

## 注意事项

1. **AI 质量** - 依赖 iflow 的质量，确保 AI 提供正确的分析和决策
2. **执行安全** - AI 执行的命令和代码修改需要谨慎，建议在测试环境先验证
3. **迭代间隔** - 合理设置迭代间隔，避免频繁迭代影响性能
4. **手动干预** - 必要时可以手动停止迭代，审查和修改 AI 的决策

## 未来改进

1. **增量学习** - 记录成功的改进模式，加速后续迭代
2. **多策略并行** - 同时尝试多种改进策略，选择最佳方案
3. **回滚机制** - 改进失败时自动回滚到之前的状态
4. **用户反馈** - 支持用户反馈，改进 AI 的决策质量