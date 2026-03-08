# 提示词持久化功能

## 功能概述

实现了提示词的持久化存储，确保提示词的版本控制和历史记录可追溯。

## 实现细节

### 1. 存储位置

提示词持久化到 `.dev-bot-evolution/current_prompt.json` 文件。

### 2. 存储内容

```json
{
  "version": 1,
  "prompt": "当前提示词内容",
  "base_template": "基础提示词模板",
  "history": [
    {
      "version": 1,
      "prompt": "版本1提示词",
      "reason": "修改原因",
      "timestamp": "2026-03-08T19:00:00"
    }
  ],
  "last_updated": "2026-03-08T19:00:00"
}
```

### 3. 关键方法

- `_save_prompt_to_file()`: 保存提示词到文件
- `update_prompt()`: 更新提示词并持久化

### 4. 自动触发

每次调用 `update_prompt()` 时自动持久化。

## 使用场景

1. **提示词优化**: AI 动态优化提示词后自动保存
2. **版本回退**: 可查看历史版本并回退
3. **状态恢复**: 重启后可恢复之前的提示词状态

## 相关文件

- `dev_bot/guardian.py`: 提示词持久化实现
- `.dev-bot-evolution/current_prompt.json`: 持久化存储文件