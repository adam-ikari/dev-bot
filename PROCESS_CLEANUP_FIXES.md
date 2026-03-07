# Node 进程清理修复总结

## 问题描述

系统运行时启动了过多的 Node 进程，导致资源浪费和潜在的进程泄漏。

## 根本原因分析

1. **iflow 进程没有被正确清理**
   - 每次调用 iflow 都会创建新的子进程
   - 超时后只是简单调用 `kill()`，没有确保进程完全清理
   - 可能产生僵尸进程或孤儿进程

2. **缺少进程组管理**
   - iflow 进程可能产生子进程（如实际的 Node.js 运行时）
   - 这些子进程没有被正确追踪和清理

3. **没有进程泄漏检测机制**
   - 系统没有定期检查和清理泄漏的进程
   - 无法及时发现和修复进程泄漏问题

## 修复方案

### 1. 修复 iflow 进程清理逻辑 (iflow_manager.py)

**修改位置**: `dev_bot/iflow_manager.py:229`

**主要改进**:
- 使用进程组管理 (`start_new_session=True`)
- 实现 `_terminate_process_group()` 方法
- 发送 SIGTERM 到整个进程组，而不是单个进程
- 等待进程组结束（最多 5 秒）
- 如果进程组没有结束，强制发送 SIGKILL
- Windows 和 Unix 系统分别处理

**关键代码**:
```python
async def _terminate_process_group(self, process: asyncio.subprocess.Process):
    """终止进程及其所有子进程"""
    if sys.platform != 'win32':
        # Unix 系统：终止整个进程组
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            await process.wait()
```

### 2. 添加进程泄漏检测和清理 (guardian_process.py)

**修改位置**: `dev_bot/guardian_process.py:run()` 和新增 `_cleanup_leaked_processes()`

**主要改进**:
- 在守护进程主循环中定期执行进程清理（每 60 秒）
- 获取所有运行中的 Node 进程
- 与已知进程列表比较，识别泄漏进程
- 自动清理泄漏的进程
- 记录清理操作

**关键代码**:
```python
async def _cleanup_leaked_processes(self):
    """检查并清理泄漏的 Node 进程"""
    # 每 60 秒执行一次
    # 获取所有 Node 进程
    # 比较已知进程列表
    # 清理泄漏的进程
```

## 验证结果

### 测试 1: 基本功能测试

```
============================================================
测试 iflow 进程清理功能
============================================================

[测试 1] 正常调用（预期成功）
成功: True
输出: Hello! 👋 I'm ready to help...

[测试 2] 超时调用（预期超时并清理进程）
成功: True

[测试 3] 检查进程泄漏
当前 Node 进程数量: 2
预期数量: 2 (守护进程 + AI 循环实例)
✓ 进程清理测试通过

调用统计:
  总调用次数: 3
  成功次数: 2
  失败次数: 1
  成功率: 66.7%
```

### 当前进程状态

```
PID 1571: node /home/zhaodi-chen/.npm-global/bin/iflow
PID 1585: /home/zhaodi-chen/.nvm/versions/node/v20.19.1/bin/node /home/zhaodi-chen/.npm-global/lib/node_modules/@iflow-ai/iflow-cli/bundle/iflow.js
```

进程数量: 2（符合预期）

## 预期效果

1. **进程数量正确**: 始终保持 2 个 Node 进程（1 个守护进程 + 1 个 AI 循环实例）
2. **无进程泄漏**: 超时或异常退出的进程会被正确清理
3. **自动监控**: 守护进程定期检查并清理泄漏进程
4. **资源优化**: 避免资源浪费和系统性能下降

## 后续建议

1. **监控日志**: 定期检查守护进程日志，确认进程清理正常工作
2. **性能测试**: 在高负载场景下测试进程管理的稳定性
3. **告警机制**: 考虑添加进程数量告警，当异常时及时通知
4. **配置优化**: 根据实际使用情况调整清理间隔和超时时间

## 修改的文件

1. `dev_bot/iflow_manager.py` - 修复进程清理逻辑
2. `dev_bot/guardian_process.py` - 添加进程泄漏检测和清理

## 测试文件

1. `test_process_cleanup.py` - 基本功能测试
2. `test_timeout_cleanup.py` - 超时场景压力测试