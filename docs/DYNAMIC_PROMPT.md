# 动态提示词功能文档

## 概述

Dev-Bot 支持在每轮 AI 调用结束时，通过 AI 决策动态生成对下一轮提示词的修改或补充。这使得 AI 能够根据当前进度和问题，智能地调整下一轮的工作方向，同时保留原有的上下文信息。

## 工作原理

### 1. AI 决策流程

在每轮 AI 调用结束后，系统会：

1. **分析 AI 输出**: 评估本轮 AI 调用的结果
2. **做出决策**: 决定下一步动作（继续、修复、停止等）
3. **生成提示词修改**: 如果需要继续，生成对提示词的修改或补充内容

### 2. 提示词修改生成

**重要**: AI 决策生成的是对原提示词的修改或补充，而不是完全替换。

AI 决策时会生成以下信息：

- **next_prompt**: 对原提示词的修改或补充内容
- **next_prompt_type**: 修改类型（continue/fix/implement/review/test/custom）
- **next_context**: 修改的上下文信息

### 3. 提示词构建方式

系统会按照以下顺序构建最终提示词：

1. **基础提示词**: 包含角色定义、Spec 内容、用户输入、任务要求等
2. **修改或补充要求**: AI 生成的修改内容追加到基础提示词末尾
3. **上下文信息**: 如果有，追加到修改内容之后

这种设计确保了：
- 保留原有的 Spec 和上下文信息
- 只在需要时追加新的要求
- 保持提示词的连续性和完整性

### 4. 修改类型

| 类型 | 描述 | 示例场景 |
|------|------|----------|
| `continue` | 继续当前任务 | 部分完成功能，需要继续下一步 |
| `fix` | 修复错误或问题 | 检测到错误需要修复 |
| `implement` | 实现新功能 | Spec 中定义了新功能 |
| `review` | 代码审查 | 需要审查代码质量 |
| `test` | 运行或编写测试 | 功能完成需要测试 |
| `custom` | 自定义任务 | 其他特殊情况 |

## 使用示例

### 示例 1: 修复错误

**第一轮 AI 输出**:
```
实现了用户登录功能，但在密码验证时出现错误。
```

**AI 决策**:
```json
{
  "analysis": "登录功能已实现，但密码验证有错误",
  "is_reasonable": true,
  "action": "fix_errors",
  "action_description": "修复密码验证错误",
  "should_stop": false,
  "should_rerun": false,
  "reason": "需要修复密码验证逻辑",
  "next_prompt": "修复用户登录功能中的密码验证错误。具体问题：\n1. 密码长度检查不正确（应该是 8-20 位）\n2. 特殊字符验证失败\n\n请修复这些问题并确保测试通过。",
  "next_prompt_type": "fix",
  "next_context": "密码验证逻辑存在问题，需要修复长度检查和特殊字符验证"
}
```

**第二轮 AI 调用**（基础提示词 + 修改内容）:
```
你是 Dev-Bot 的 AI 开发助手。

## Spec 内容
[原有 Spec 内容...]

## 用户输入
[用户输入...]

## 任务

根据 Spec 和用户输入，完成开发工作：

1. 理解 Spec 中的需求
2. 分析用户输入的指令
3. 编写/修改代码实现功能
4. 确保代码质量
5. 运行测试验证

## 修改或补充要求

修复用户登录功能中的密码验证错误。具体问题：
1. 密码长度检查不正确（应该是 8-20 位）
2. 特殊字符验证失败

请修复这些问题并确保测试通过。

## 上下文信息

密码验证逻辑存在问题，需要修复长度检查和特殊字符验证

## 输出格式

请直接输出你的工作内容，包括：
- 代码更改（使用代码块）
- 测试结果
- 遇到的问题
- 下一步建议

不需要使用特定的格式标记，自然输出即可。
```

### 示例 2: 实现新功能

**第一轮 AI 输出**:
```
已完成用户登录和登出功能。
```

**AI 决策**:
```json
{
  "analysis": "基本登录功能已完成",
  "is_reasonable": true,
  "action": "none",
  "action_description": "继续实现其他功能",
  "should_stop": false,
  "should_rerun": false,
  "reason": "根据 Spec，还需要实现密码重置功能",
  "next_prompt": "现在实现用户密码重置功能。\n\n要求：\n1. 用户可以通过邮箱请求密码重置\n2. 发送包含重置链接的邮件\n3. 用户点击链接后可以设置新密码\n4. 重置链接有效期为 1 小时\n\n请实现完整的密码重置流程，包括必要的测试。",
  "next_prompt_type": "implement",
  "next_context": "根据 Spec 需要实现密码重置功能"
}
```

**第二轮 AI 调用**（基础提示词 + 修改内容）:
```
你是 Dev-Bot 的 AI 开发助手。

## Spec 内容
[原有 Spec 内容...]

## 任务

根据 Spec 和用户输入，完成开发工作：

1. 理解 Spec 中的需求
2. 分析用户输入的指令
3. 编写/修改代码实现功能
4. 确保代码质量
5. 运行测试验证

## 修改或补充要求

现在实现用户密码重置功能。

要求：
1. 用户可以通过邮箱请求密码重置
2. 发送包含重置链接的邮件
3. 用户点击链接后可以设置新密码
4. 重置链接有效期为 1 小时

请实现完整的密码重置流程，包括必要的测试。

## 上下文信息

根据 Spec 需要实现密码重置功能

## 输出格式

[输出格式说明...]
```
4. 重置链接有效期为 1 小时

请实现完整的密码重置流程。
```

## 实现细节

### 决策提示词更新

在 `dev_bot/ai_prompts.py` 中，`DECISION_PROMPT` 已更新：

```python
{
  "analysis": "对 AI 输出和代码质量的简要分析",
  "is_reasonable": true/false,
  "action": "...",
  "action_description": "动作描述",
  "should_stop": true/false,
  "should_rerun": true/false,
  "reason": "决策原因",
  "user_question": "用户问题（如果需要）",
  "next_prompt": "下一轮 AI 调用的提示词（如果需要继续）",
  "next_prompt_type": "continue|fix|implement|review|test|custom",
  "next_context": "下一轮的上下文信息"
}
```

### 核心逻辑更新

在 `dev_bot/core.py` 中：

1. **存储动态提示词**:
```python
def __init__(self, project_root: Optional[Path] = None):
    # ...
    self.dynamic_prompt = None
    self.dynamic_prompt_type = None
    self.dynamic_prompt_context = None
```

2. **使用动态提示词**:
```python
def _build_prompt(self, spec_content: str, user_inputs: List[str]) -> str:
    # 如果有动态提示词，优先使用
    if self.dynamic_prompt:
        prompt = self.dynamic_prompt
        # 添加上下文和用户输入
        if self.dynamic_prompt_context:
            prompt += f"\n\n## 上下文信息\n{self.dynamic_prompt_context}\n"
        if user_inputs:
            prompt += f"\n\n## 用户输入\n{chr(10).join(f'- {inp}' for inp in user_inputs)}\n"
        return prompt
    
    # 否则使用默认提示词
    # ...
```

3. **更新动态提示词**:
```python
def _analyze_and_decide(self, ai_output: str) -> Optional[Dict[str, Any]]:
    # ...
    if output:
        decision = json.loads(output)
        
        # 更新动态提示词
        next_prompt = decision.get('next_prompt')
        if next_prompt:
            self.dynamic_prompt = next_prompt
            self.dynamic_prompt_type = decision.get('next_prompt_type', 'custom')
            self.dynamic_prompt_context = decision.get('next_context', '')
            print(f"[ℹ️] 已生成下一轮提示词 (类型: {self.dynamic_prompt_type})")
        else:
            # 清空动态提示词
            self.dynamic_prompt = None
            self.dynamic_prompt_type = None
            self.dynamic_prompt_context = None
```

## 最佳实践

### 1. 提示词设计

- **具体明确**: 提示词应该清晰、具体、可执行
- **上下文完整**: 包含足够的上下文信息
- **可量化**: 尽量使用可量化的要求
- **分步骤**: 复杂任务应该分解为多个步骤

### 2. 提示词类型选择

| 场景 | 推荐类型 | 原因 |
|------|----------|------|
| 部分完成的功能 | `continue` | 继续当前任务 |
| 检测到错误 | `fix` | 修复特定问题 |
| Spec 中有新功能 | `implement` | 实现新功能 |
| 代码审查 | `review` | 审查代码质量 |
| 功能完成 | `test` | 运行测试 |
| 特殊情况 | `custom` | 灵活处理 |

### 3. 上下文信息

在 `next_context` 中应该包含：

- 当前任务的状态
- 已完成的工作
- 遇到的问题
- 特殊的约束条件
- 相关的代码位置

## 测试

测试文件：`tests/test_dynamic_prompt.py`

包含以下测试用例：

1. 动态提示词初始化
2. 使用动态提示词构建提示词
3. 不使用动态提示词构建提示词
4. 包含用户输入的提示词构建
5. 决策后更新动态提示词
6. 决策后清空动态提示词
7. 不同类型的动态提示词

## 优势

1. **智能适应**: AI 可以根据实际情况调整工作方向
2. **精准指导**: 每轮提示词都针对具体问题
3. **上下文保持**: 保留任务的连续性和上下文
4. **灵活控制**: 支持多种任务类型和场景
5. **自动优化**: 无需手动编写每一轮的提示词

## 注意事项

1. **AI 质量**: 动态提示词的质量取决于 AI 的能力
2. **错误处理**: 如果 AI 决策失败，会降级到默认提示词
3. **提示词长度**: 避免生成过长的提示词
4. **类型匹配**: 确保 `next_prompt_type` 与实际任务匹配
5. **上下文准确性**: 提供准确的上下文信息

## 相关文件

- `dev_bot/ai_prompts.py`: AI 提示词定义
- `dev_bot/core.py`: 核心逻辑实现
- `tests/test_dynamic_prompt.py`: 测试用例

## 许可证

MIT