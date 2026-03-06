# AI 守护进程分层架构文档

## 概述

Dev-Bot 的 AI 守护进程采用分层架构设计，将核心守护功能与业务逻辑分离，提供更好的可维护性和扩展性。

## 架构设计

### 三层架构

```
┌─────────────────────────────────────────┐
│         AIGuardian (整合层)             │
│    整合核心守护层和业务逻辑层           │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│ 核心守护层      │    │ 业务逻辑层       │
│ (不可变)        │    │ (可变)          │
│                │    │                 │
│ • 进程监控      │    │ • 业务规则       │
│ • 健康检查      │    │ • 策略配置       │
│ • 自动恢复      │    │ • 扩展接口       │
└────────────────┘    └─────────────────┘
```

## 核心组件

### 1. 核心守护层 (CoreGuardian)

**职责**：
- 进程注册和管理
- 进程健康检查
- 自动恢复机制
- 基础状态管理

**特点**：
- 不可变：核心逻辑稳定，不随业务需求变化
- 可靠：提供基础的进程监控和恢复功能
- 独立：不依赖业务逻辑，可独立测试

**主要类**：
- `CoreGuardian`: 核心守护类
- `HealthChecker`: 健康检查器抽象基类
- `DefaultHealthChecker`: 默认健康检查实现
- `RecoveryStrategy`: 恢复策略抽象基类
- `DefaultRecoveryStrategy`: 默认恢复策略实现

### 2. 业务逻辑层 (BusinessLogicLayer)

**职责**：
- 业务规则管理
- 策略配置
- 业务相关决策
- 扩展接口

**特点**：
- 可变：根据业务需求灵活调整
- 扩展：支持自定义业务规则和策略
- 配置化：支持通过配置文件管理

**主要类**：
- `BusinessLogicLayer`: 业务逻辑层类
- `BusinessRule`: 业务规则抽象基类
- `MaxRestartRule`: 最大重启次数规则
- `IdleTimeRule`: 空闲时间规则

### 3. 整合层 (AIGuardian)

**职责**：
- 整合核心守护层和业务逻辑层
- 提供统一的守护接口
- 状态管理和历史记录

**特点**：
- 完整：提供完整的守护功能
- 简洁：对外提供简单的 API
- 监控：记录状态历史，便于调试

## 使用示例

### 基本使用

```python
import asyncio
from pathlib import Path
from dev_bot.guardian import AIGuardian

async def main():
    # 创建 AI 守护进程
    ai_guardian = AIGuardian(check_interval=30)
    
    # 注册要监控的进程
    ai_guardian.register_process(
        "ai_loop",
        None,  # 初始没有 PID
        ["python", "ai_loop_process.py"],
        max_restarts=10
    )
    
    # 启动守护
    await ai_guardian.start()
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await ai_guardian.stop()

asyncio.run(main())
```

### 自定义业务规则

```python
from dev_bot.guardian import AIGuardian, BusinessRule

class CustomRule(BusinessRule):
    """自定义业务规则"""
    
    def __init__(self, threshold=5):
        self.threshold = threshold
    
    async def evaluate(self, process_type, process_info):
        """评估是否需要特殊处理"""
        restart_count = process_info.get("restart_count", 0)
        return restart_count >= self.threshold
    
    async def execute(self, process_type, process_info):
        """执行特殊处理"""
        print(f"{process_type} 重启次数达到阈值 {self.threshold}")
        # 发送告警通知
        return True

# 使用自定义规则
ai_guardian = AIGuardian()
ai_guardian.add_business_rule(CustomRule(threshold=3))
```

### 自定义恢复策略

```python
from dev_bot.guardian import AIGuardian
from dev_bot.guardian.core import RecoveryStrategy

class CustomRecoveryStrategy(RecoveryStrategy):
    """自定义恢复策略"""
    
    async def recover(self, process_type, process_info):
        """执行自定义恢复操作"""
        print(f"执行自定义恢复: {process_type}")
        # 实现自定义恢复逻辑
        return True

# 使用自定义策略
ai_guardian = AIGuardian()
ai_guardian.set_custom_recovery_strategy("ai_loop", CustomRecoveryStrategy())
```

### 配置文件

创建 `guardian_config.json`:

```json
{
  "max_restart_threshold": 10,
  "max_idle_time": 600,
  "check_interval": 30
}
```

使用配置文件：

```python
from pathlib import Path
from dev_bot.guardian import AIGuardian

ai_guardian = AIGuardian(
    check_interval=30,
    config_file=Path("guardian_config.json")
)
```

## 测试

运行分层架构测试：

```bash
python3 tests/test_guardian_layered.py
```

测试覆盖：
- 核心守护层功能
- 业务逻辑层功能
- 整合层功能
- 自定义业务规则
- 配置文件加载

## 架构优势

### 1. 分离关注点
- 核心守护层专注于进程监控和恢复
- 业务逻辑层专注于业务规则和策略
- 职责清晰，易于维护

### 2. 可扩展性
- 通过继承 `BusinessRule` 添加自定义规则
- 通过实现 `RecoveryStrategy` 添加自定义恢复策略
- 支持配置化管理

### 3. 可测试性
- 每层可独立测试
- 提供完整的测试套件
- 支持模拟和桩测试

### 4. 稳定性
- 核心守护层不可变，确保基础功能稳定
- 业务逻辑层可变，支持灵活调整
- 降低变更风险

## 文件结构

```
dev_bot/
├── guardian/
│   ├── __init__.py           # 导出接口
│   ├── core.py               # 核心守护层
│   └── business.py           # 业务逻辑层
├── guardian_process.py       # 守护进程主程序（使用分层架构）
└── process_coordinator.py    # 进程协调器（集成守护）
```

## 向后兼容

新的分层架构保持了与原有 `GuardianProcess` 类的兼容性，但推荐使用新的 `AIGuardian` 类以获得更好的功能。

## 未来扩展

1. **更多业务规则**
   - 资源使用监控规则
   - 性能指标规则
   - 依赖关系规则

2. **更多恢复策略**
   - 滚动重启策略
   - 降级恢复策略
   - 通知告警策略

3. **监控集成**
   - Prometheus 指标导出
   - 日志聚合
   - 可视化仪表板

## 总结

分层架构的 AI 守护进程提供了：
- ✅ 清晰的职责分离
- ✅ 强大的扩展能力
- ✅ 完善的测试覆盖
- ✅ 向后兼容性
- ✅ 易于维护和扩展

通过核心守护层和业务逻辑层的分离，Dev-Bot 的 AI 守护进程变得更加稳定、灵活和可维护。