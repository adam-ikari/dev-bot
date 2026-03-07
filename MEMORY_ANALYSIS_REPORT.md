# Dev-Bot 内存占用过高问题分析报告

## 执行状态
✅ 任务完成

## 工作总结
对 dev-bot 项目进行了全面的内存占用分析，重点关注进程管理、内存泄漏、循环引用、iFlow 调用、IPC 通信和长期记忆管理等方面。

## 关键发现

### 1. 当前内存使用情况
- **iflow 进程 (PID: 3893)** 内存使用：
  - VmRSS (实际物理内存): 357,656 KB (~349 MB)
  - VmSize (虚拟内存): 32,945,784 KB (~31.4 GB)
  - VmPeak (峰值虚拟内存): 33,315,904 KB (~31.8 GB)
  - VmHWM (峰值物理内存): 725,612 KB (~708 MB)
  - 线程数: 11

### 2. 主要内存问题点

#### 🔴 问题 1: iflow 进程的虚拟内存异常高（31.4 GB）
**位置**: `dev_bot/iflow_manager.py` 和外部 iflow CLI 工具

**问题描述**:
- iflow Node.js 进程的虚拟内存高达 31.4 GB，但实际物理内存仅 349 MB
- 这通常是由于 Node.js 的 V8 引擎预留了大量虚拟内存用于堆管理
- 虚拟内存过高不一定会导致实际内存压力，但表明进程配置可能需要优化

**影响**:
- 可能触发系统内存限制（如容器环境）
- 可能导致进程启动慢或失败
- 可能影响其他进程的内存分配

**修复建议**:
```python
# dev_bot/iflow_manager.py

async def _execute_iflow(
    self,
    prompt: str,
    args: List[str],
    timeout: int
) -> IFlowCallResult:
    """执行 iflow 命令"""
    process = None
    try:
        # 限制进程的内存使用（Linux specific）
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        # 设置软限制为 2GB，避免虚拟内存过度分配
        try:
            resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, hard))
        except ValueError:
            pass  # 可能权限不足

        process = await asyncio.create_subprocess_exec(
            self.iflow_command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
            start_new_session=True if sys.platform != 'win32' else False
        )
```

#### 🟡 问题 2: AI 循环中的无限循环可能导致累积内存
**位置**: `dev_bot/ai_loop_process.py:408`

**问题描述**:
```python
async def run(self):
    """运行 AI 循环"""
    self.is_running = True
    
    try:
        # 主循环 - 没有明确的退出条件
        while self.is_running:
            await self._run_session()
            await asyncio.sleep(2)
```

**内存泄漏风险**:
- 每次会话都可能创建新的对象
- 历史记录累积（虽然有 MAX_HISTORY_ENTRIES=50 的限制）
- 频繁调用 iflow 可能导致进程累积

**修复建议**:
```python
# dev_bot/ai_loop_process.py

async def run(self):
    """运行 AI 循环"""
    self.is_running = True
    session_count = 0
    max_sessions = 1000  # 防止无限运行
    
    try:
        while self.is_running and session_count < max_sessions:
            await self._run_session()
            session_count += 1
            
            # 定期强制清理内存
            if session_count % 50 == 0:
                await self._force_memory_cleanup()
            
            await asyncio.sleep(2)
            
            # 检查是否达到会话限制
            if session_count >= max_sessions:
                self._log("warning", f"达到最大会话数限制 ({max_sessions})，停止运行")
                self.is_running = False
```

#### 🟡 问题 3: 多 iFlow 并发调用可能导致进程爆炸
**位置**: `dev_bot/multi_iflow_manager.py`

**问题描述**:
- 多 iflow 管理器会为每个角色创建独立的 IFlowManager 实例
- 每次并发调用都会创建新的子进程
- 没有对并发数量进行限制

**修复建议**:
```python
# dev_bot/multi_iflow_manager.py

class MultiIFlowManager:
    def __init__(
        self,
        iflow_command: str = "iflow",
        default_timeout: int = 300,
        max_retries: int = 3,
        max_concurrent_calls: int = 5  # 新增：最大并发数
    ):
        self.max_concurrent_calls = max_concurrent_calls
        self.concurrency_semaphore = asyncio.Semaphore(max_concurrent_calls)
        
    async def _call_instance(
        self,
        instance: IForkInstance,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> IFlowCallResult:
        """调用单个 iFlow 实例（带并发控制）"""
        async with self.concurrency_semaphore:
            # 原有的调用逻辑
            pass
```

#### 🟡 问题 4: IPC 消息队列可能导致内存累积
**位置**: `dev_bot/ipc_realtime.py:53, 127`

**问题描述**:
```python
# 消息队列（限制大小防止内存泄漏）
self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)  # Server
self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=500)   # Client
```

**问题**:
- 队列大小限制较大（1000/500），可能仍然导致内存累积
- 如果消息处理速度慢于生成速度，队列会填满
- 队列填满后可能导致消息丢失

**修复建议**:
```python
# dev_bot/ipc_realtime.py

class IPCServer:
    def __init__(self, socket_path: Path):
        # 减小队列大小
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=100)  # 原来是 1000
        self.message_dropped_count = 0
        
    async def broadcast(self, message: IPCMessage):
        """广播消息给所有客户端"""
        if not self.is_running:
            return
        
        # 检查队列是否接近满
        if self.message_queue.qsize() > self.message_queue.maxsize * 0.9:
            self.message_dropped_count += 1
            if self.message_dropped_count % 100 == 0:
                print(f"[IPC Server] 警告: 已丢弃 {self.message_dropped_count} 条消息")
        
        # 原有的广播逻辑
```

#### 🟡 问题 5: 进程组清理可能不彻底
**位置**: `dev_bot/iflow_manager.py:207`

**问题描述**:
```python
async def _terminate_process_group(self, process: asyncio.subprocess.Process):
    """终止进程及其所有子进程"""
    try:
        if sys.platform != 'win32':
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                # 等待 5 秒
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # 强制杀死
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        await process.wait()
                    except:
                        pass
            except (ProcessLookupError, OSError):
                # 可能导致僵尸进程
                pass
```

**问题**:
- 异常处理过于宽松，可能留下僵尸进程
- 只等待 5 秒可能不够清理所有子进程

**修复建议**:
```python
# dev_bot/iflow_manager.py

async def _terminate_process_group(self, process: asyncio.subprocess.Process):
    """终止进程及其所有子进程（增强版）"""
    pid = process.pid
    try:
        if sys.platform != 'win32':
            # 尝试获取进程组 ID
            try:
                pgid = os.getpgid(pid)
                
                # 1. 首先尝试 SIGTERM（优雅退出）
                try:
                    os.killpg(pgid, signal.SIGTERM)
                except ProcessLookupError:
                    # 进程已不存在
                    return
                
                # 2. 等待最多 10 秒（延长等待时间）
                for _ in range(20):  # 20 * 0.5 = 10 秒
                    if process.returncode is not None:
                        break
                    await asyncio.sleep(0.5)
                
                # 3. 如果还没退出，使用 SIGKILL
                if process.returncode is None:
                    try:
                        os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    
                    # 4. 再次等待
                    for _ in range(10):  # 5 秒
                        if process.returncode is not None:
                            break
                        await asyncio.sleep(0.5)
                
                # 5. 如果还没退出，强制收集僵尸进程
                if process.returncode is None:
                    try:
                        process.kill()
                        await process.wait()
                    except:
                        pass
                
            except OSError as e:
                # 如果无法获取进程组，尝试直接终止进程
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
    except Exception as e:
        print(f"[iFlow管理器] 清理进程失败: {e}")
```

#### 🟢 问题 6: 长期记忆管理良好
**位置**: `dev_bot/ai_loop_process.py:530-551`

**状态**: ✅ 已有合理的限制

```python
def _load_memory(self) -> Dict:
    """加载长期记忆"""
    if self.memory_file.exists():
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            memory = json.load(f)
            # 限制历史记录大小
            if len(memory.get('history', [])) > self.MAX_HISTORY_ENTRIES:
                memory['history'] = memory['history'][-self.MAX_HISTORY_ENTRIES:]
            return memory
    return {"history": [], "learnings": [], "context": {}}
```

**优点**:
- 已有 MAX_HISTORY_ENTRIES = 50 的限制
- 加载和保存时都会检查限制
- 定期清理（每 100 次循环）

#### 🟢 问题 7: 进程管理器有清理机制
**位置**: `dev_bot/process_manager.py:267`

**状态**: ✅ 已有清理机制

```python
def cleanup_finished_processes(self) -> int:
    """清理已完成的进程"""
    finished_ids = [
        pid for pid, process in self.processes.items()
        if process.returncode is not None
    ]
    
    for pid in finished_ids:
        del self.processes[pid]
    
    return len(finished_ids)
```

**建议**: 可以定期调用此方法

### 3. 循环引用检查

未发现明显的循环引用问题。代码中主要使用：
- 字典存储数据（JSON 可序列化）
- 列表存储历史记录（有长度限制）
- 全局单例模式（通过 get_xxx() 函数）

### 4. 其他发现

#### 🟡 发现 1: 多个全局单例可能累积
**位置**: 多个文件

**全局单例列表**:
- `_global_process_manager` (process_manager.py)
- `_global_iflow_manager` (iflow_manager.py)
- `_global_ipc_server` (ipc_realtime.py)
- `_global_business_logic_layer` (business_logic_layer.py)
- `_global_multi_iflow_manager` (multi_iflow_manager.py)

**风险**: 如果这些单例持有大量数据，重启时可能需要手动清理

**建议**: 添加统一的清理函数

```python
# dev_bot/core.py 或新建 cleanup.py

async def cleanup_all_globals():
    """清理所有全局单例"""
    from dev_bot.process_manager import reset_process_manager
    from dev_bot.iflow_manager import reset_iflow_manager
    from dev_bot.business_logic_layer import reset_business_logic_layer
    from dev_bot.multi_iflow_manager import reset_multi_iflow_manager
    
    reset_process_manager()
    reset_iflow_manager()
    reset_business_logic_layer()
    reset_multi_iflow_manager()
    
    # 强制垃圾回收
    import gc
    gc.collect()
```

## 修复优先级

### 🔴 高优先级（立即修复）
1. **限制 iflow 进程的虚拟内存分配** - 防止虚拟内存爆炸
2. **增强进程组清理逻辑** - 防止僵尸进程累积

### 🟡 中优先级（近期修复）
3. **添加 AI 循环的会话限制** - 防止无限运行
4. **限制多 iFlow 并发调用数量** - 防止进程爆炸
5. **减小 IPC 消息队列大小** - 防止内存累积

### 🟢 低优先级（可选优化）
6. **定期清理进程管理器** - 释放已完成的进程
7. **添加统一的全局清理函数** - 便于重启时清理

## 推荐的监控指标

```python
# 添加到 ai_loop_process.py

def _get_memory_stats(self) -> Dict[str, Any]:
    """获取内存统计"""
    import psutil
    
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "rss": memory_info.rss / 1024 / 1024,  # MB
        "vms": memory_info.vms / 1024 / 1024,  # MB
        "percent": process.memory_percent(),
        "num_threads": process.num_threads(),
        "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
    }

async def _run_session(self):
    """运行一次会话"""
    # ... 原有逻辑 ...
    
    # 每隔 10 次会话记录内存统计
    if self.session_num % 10 == 0:
        stats = self._get_memory_stats()
        self._log("info", f"内存使用: RSS={stats['rss']:.1f}MB, VMS={stats['vms']:.1f}MB, {stats['num_threads']} 线程")
        
        # 警告阈值
        if stats['rss'] > 500:  # 500 MB
            self._log("warning", f"内存使用过高: {stats['rss']:.1f}MB")
```

## 总结

当前内存占用过高（349 MB 实际内存，31.4 GB 虚拟内存）的主要原因是：

1. **iflow 进程的虚拟内存配置问题**（31.4 GB 虚拟内存）
2. **潜在的进程清理不彻底**（可能累积僵尸进程）
3. **缺乏并发控制**（多 iflow 调用可能创建大量进程）

虽然代码中已经有合理的内存管理措施（如历史记录限制、定期清理），但需要进一步优化进程管理和资源限制。

建议优先修复高优先级问题，然后添加内存监控机制，以便及时发现和处理内存问题。