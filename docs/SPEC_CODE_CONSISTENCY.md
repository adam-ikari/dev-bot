# Spec 和代码一致性检查

## 功能概述

Dev-Bot 现在支持自动检查 Spec 和代码的一致性。当检测到不一致时，系统会通过 REPL 非阻塞地询问用户如何处理。

## 工作原理

### 1. 自动分析

系统会定期分析 Spec 文件和实际代码实现，检查以下方面：

- **缺少功能**: Spec 中定义了功能，但代码中未实现
- **错误实现**: 代码实现与 Spec 描述不符
- **过时 Spec**: 代码已实现新功能，但 Spec 未更新
- **接口不匹配**: Spec 定义的接口与代码不一致

### 2. AI 驱动

分析过程使用 AI 进行智能判断，包括：

1. **Spec 内容摘要**: 从 Spec 文件中提取关键信息
2. **代码实现摘要**: 分析代码结构和主要功能
3. **一致性评估**: AI 对比 Spec 和代码，识别不一致之处
4. **建议生成**: 提供清晰的修复建议

### 3. 非阻塞用户交互

当检测到不一致时：

1. **问题记录**: 将问题描述写入 `.dev-bot-cache/user_inputs.txt`
2. **提供选项**: 给出多个处理选择（更新 Spec、修改代码、两者都修改、忽略）
3. **继续执行**: 不阻塞主开发流程，用户可以在后续工作中回复

## 使用示例

### 示例 1: 缺少功能

**Spec 定义**:
```json
{
  "metadata": {
    "name": "user-authentication",
    "type": "feature"
  },
  "features": [
    "用户登录",
    "用户注册",
    "密码重置"
  ]
}
```

**代码实现**: 只有登录和注册功能

**REPL 询问**:
```
# Dev-Bot 问题 (2026-03-04T20:00:00)
Spec 中定义了"密码重置"功能，但在代码中未找到相关实现。
不一致类型: missing_feature
严重程度: high

# 请选择:
# 1. 更新 Spec（移除密码重置功能）
# 2. 修改代码（实现密码重置功能）
# 3. 两者都修改
# 4. 忽略（暂时）
# 输入你的选择:
```

### 示例 2: 接口不匹配

**Spec 定义**:
```json
{
  "metadata": {
    "name": "user-api",
    "type": "api"
  },
  "endpoints": [
    {
      "path": "/api/users",
      "method": "GET",
      "parameters": {
        "page": "integer",
        "limit": "integer",
        "sort": "string"
      }
    }
  ]
}
```

**代码实现**: 缺少 `sort` 参数

**REPL 询问**:
```
# Dev-Bot 问题 (2026-03-04T20:00:00)
Spec 中定义的 /api/users 端点缺少 sort 参数实现。
不一致类型: interface_mismatch
严重程度: medium

# 请选择:
# 1. 更新 Spec（移除 sort 参数）
# 2. 修改代码（添加 sort 参数）
# 3. 两者都修改
# 4. 忽略（暂时）
# 输入你的选择:
```

## 配置

### 自动检查频率

在 `config.json` 中配置检查频率：

```json
{
  "spec_consistency": {
    "enabled": true,
    "check_interval": 300,
    "severity_threshold": "medium"
  }
}
```

### 严重程度级别

- **high**: 必须处理的核心功能问题
- **medium**: 建议处理的功能不完整
- **low**: 可选的优化建议

## API 使用

### SpecManager

```python
from dev_bot.core import SpecManager, AIOrchestrator

spec_manager = SpecManager(project_root=Path("."))
ai_orchestrator = AIOrchestrator()

# 分析一致性
result = spec_manager.analyze_spec_code_consistency(
    code_summary="代码摘要",
    ai_orchestrator=ai_orchestrator,
    tech_stack="Python"
)

if not result['is_consistent']:
    print(f"发现问题: {result['issues']}")
    print(f"建议: {result['recommendation']}")
```

### 通过 REPL 询问用户

```python
from dev_bot.core import DevBotCore

core = DevBotCore()

# 通过 REPL 询问用户
core._ask_user_via_repl(
    "Spec 中定义了功能X，但代码中未实现。是否更新 Spec？"
)
```

## 注意事项

1. **非阻塞**: 询问不会停止开发流程，用户可以在后续工作中回复
2. **AI 建议**: AI 提供的建议仅供参考，用户需要根据实际情况决定
3. **定期检查**: 建议定期检查 Spec 和代码的一致性，确保文档和实现同步
4. **版本控制**: Spec 和代码都应该纳入版本控制，方便追踪变更历史

## 最佳实践

1. **保持同步**: 在实现新功能时，及时更新 Spec
2. **明确优先级**: 根据 business 价值决定是更新 Spec 还是修改代码
3. **团队协作**: 在团队中明确 Spec 和代码的维护责任
4. **自动化**: 将一致性检查集成到 CI/CD 流程中

## 相关文件

- `dev_bot/ai_prompts.py`: AI 提示词定义
- `dev_bot/core.py`: 核心实现（SpecManager、_analyze_and_decide）
- `PROMPT.md`: 主提示词文档
- `tests/test_spec_code_consistency.py`: 测试用例