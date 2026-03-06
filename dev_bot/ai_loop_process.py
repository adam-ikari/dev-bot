#!/usr/bin/env python3
"""
AI 循环进程 - 独立进程运行

负责执行 AI 循环，通过 IPC 与其他进程通信
"""

import asyncio
import json
import os
import signal
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ipc import IPCManager
from dev_bot.main import Config
from dev_bot.ai_evolution_system import AIEvolutionSystem
from dev_bot.iflow_manager import get_iflow_manager, IFlowMode
from dev_bot.business_logic_layer import get_business_logic_layer


class AILoopProcess:
    """AI 循环进程"""
    
    def __init__(self, project_root: Path, config_file: str):
        self.project_root = project_root
        self.config_file = config_file
        self.config = Config(config_file)
        self.ipc = IPCManager(project_root)
        
        self.is_running = False
        self.is_paused = False
        self.session_num = 1
        self.memory_file = project_root / ".dev-bot-memory" / "context.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 命令和响应文件
        self.command_file = project_root / ".ipc" / "ai_loop_command.json"
        self.response_file = project_root / ".ipc" / "ai_loop_response.json"
        
        # 长期记忆配置
        self.MAX_HISTORY_ENTRIES = 100
        
        # AI 进化系统
        self.evolution_system = AIEvolutionSystem(
            project_root,
            self.config.get_ai_command()
        )
        
        # iFlow 管理器
        self.iflow_manager = get_iflow_manager(
            iflow_command=self.config.get_ai_command(),
            default_timeout=self.config.get_timeout(),
            max_retries=3
        )
        
        # 业务逻辑层
        self.business_logic = get_business_logic_layer()
        self.enable_business_logic = True  # 是否启用业务逻辑层
        
        # 进化模式配置
        self.enable_evolution = True
        self.evolution_interval = 5  # 每5次循环执行一次进化
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    async def run(self):
        """运行 AI 循环"""
        self.is_running = True
        
        print(f"[AI 循环] 启动 AI 循环进程（PID: {os.getpid()}）")
        
        # 更新状态
        self._update_status({"status": "running", "session": 0})
        
        try:
            # 主循环
            while self.is_running:
                await self._run_session()
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"[AI 循环] AI 循环出错: {e}")
            self._update_status({"status": "error", "error": str(e)})
        finally:
            print(f"[AI 循环] AI 循环进程退出")
            self._update_status({"status": "stopped"})
    
    async def _run_session(self):
        """运行一次会话"""
        # 检查暂停状态
        if self.is_paused:
            await asyncio.sleep(2)
            return
        
        # 检查命令
        command = await self._check_command()
        if command:
            await self._handle_command(command)
        
        self._log("info", f">>> AI 循环 #{self.session_num} <<<")
        
        # 判断是否执行进化循环
        is_evolution_session = self.enable_evolution and (self.session_num % self.evolution_interval == 0)
        
        if is_evolution_session:
            self._log("info", f"[AI 进化] 执行自主进化循环...")
            
            # 构建进化上下文
            evolution_context = {
                "session_num": self.session_num,
                "memory": self._load_memory(),
                "evolution_system_status": self.evolution_system.get_status()
            }
            
            # 执行进化
            evolution_result = await self.evolution_system.evolve(evolution_context)
            
            self._log("success", f"[AI 进化] 进化完成，进化次数: {self.evolution_system.evolution_count}")
            
            # 保存进化结果到记忆
            memory = self._load_memory()
            memory['history'].append({
                "session": self.session_num,
                "phase": "evolution",
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "content": "自主进化完成",
                "evolution_result": evolution_result
            })
            self._save_memory(memory)
        else:
            # 普通的 AI 循环
            # 加载长期记忆
            memory = self._load_memory()
            self._log("info", f"长期记忆: {len(memory.get('history', []))} 条历史记录")
            
            # 获取学习推荐
            recommendations = self.evolution_system.learning_system.get_recommendations(memory)
            if recommendations:
                self._log("info", f"[学习推荐] {recommendations[0]}")
            
            # 阶段 1: AI 决策
            self._log("info", "[阶段 1: AI 决策] 调用 iflow 分析...")
            decision_output = await self._ai_decision(memory)
            
            if decision_output:
                # 解析决策
                try:
                    import json
                    decision = json.loads(decision_output)
                except:
                    decision = {"type": "general", "plan": [], "output": decision_output}
                
                # 应用业务逻辑层验证决策
                if self.enable_business_logic:
                    self._log("info", "[业务逻辑层] 验证决策...")
                    validation_result = await self.business_logic.validate_decision_with_rules(
                        decision,
                        {"session": self.session_num, "memory": memory}
                    )
                    
                    if not validation_result["valid"]:
                        self._log("warning", f"[业务逻辑层] 决策验证失败: {len(validation_result['violations'])} 个违规")
                        for violation in validation_result["violations"]:
                            self._log("warning", f"  - {violation['rule_name']}: {violation['message']}")
                    else:
                        self._log("success", f"[业务逻辑层] 决策验证通过 (通过率: {validation_result['pass_rate']:.1%})")
                    
                    # 应用业务策略
                    decision = self.business_logic.apply_business_strategy(decision)
                    self._log("info", "[业务逻辑层] 已应用业务策略")
                
                # 阶段 2: AI 执行
                self._log("info", "[阶段 2: AI 执行] 调用 iflow 开始工作...")
                execution_result = await self._ai_execution(decision_output)
                
                # 检查执行约束
                if self.enable_business_logic and execution_result:
                    self._log("info", "[业务逻辑层] 检查执行约束...")
                    constraint_result = await self.business_logic.check_execution_constraints(
                        {"output": execution_result},
                        {"session": self.session_num, "decision": decision}
                    )
                    
                    if not constraint_result["passed"]:
                        self._log("warning", f"[业务逻辑层] 约束检查失败: {len(constraint_result['violations'])} 个违规")
                    else:
                        self._log("success", "[业务逻辑层] 约束检查通过")
                
                # 更新业务状态
                if self.enable_business_logic:
                    self.business_logic.update_business_state({
                        "decision_count": self.business_logic.get_business_state().get("decision_count", 0) + 1,
                        "session_count": self.session_num
                    })
                
                # 保存记忆
                memory['history'].append({
                    "session": self.session_num,
                    "phase": "complete",
                    "timestamp": __import__('datetime').datetime.now().isoformat(),
                    "content": "会话完成",
                    "decision": decision,
                    "business_validation": validation_result if self.enable_business_logic else None
                })
                self._save_memory(memory)
                
                self._log("success", f"AI 循环 #{self.session_num} 完成")
            else:
                self._log("warning", f"AI 循环 #{self.session_num} 跳过（无决策）")
        
        # 更新状态
        status_data = {
            "status": "running",
            "session": self.session_num,
            "last_activity": __import__('datetime').datetime.now().isoformat()
        }
        
        # 添加进化系统状态
        status_data["evolution"] = self.evolution_system.get_status()
        
        self._update_status(status_data)
        
        self.session_num += 1
    
    async def _ai_decision(self, memory: Dict) -> str:
        """AI 决策 - 使用 iflow --plan"""
        try:
            # 读取 spec
            spec_files = list((self.project_root / "specs").glob("*.json"))
            spec_content = ""
            if spec_files:
                with open(spec_files[0], 'r', encoding='utf-8') as f:
                    spec_content = json.dumps(json.load(f), indent=2, ensure_ascii=False)
            
            # 构建提示词
            prompt = f"""你是 Dev-Bot 的 AI 决策系统。

当前上下文：
{json.dumps(memory.get('context', {}), indent=2, ensure_ascii=False)}

历史记录（最近 5 条）：
{json.dumps(memory.get('history', [])[-5:], indent=2, ensure_ascii=False)}

Spec 内容：
{spec_content if spec_content else '无 Spec'}

请输出你的决策（下一步做什么，如何做）。"""
            
            # 构建上下文
            context = {
                "memory": memory,
                "spec": spec_content,
                "session": self.session_num
            }
            
            # 使用 iflow 管理器调用
            self._log("info", "[阶段 1: AI 决策] 调用 iflow --plan...")
            result = await self.iflow_manager.call_plan(
                prompt=prompt,
                context=context,
                timeout=300
            )
            
            if result.success:
                self._log("success", f"[阶段 1: AI 决策] 决策完成（耗时: {result.duration:.2f}秒）")
                self._log("ai_output", result.output[:500])
                
                # 记录调用统计
                stats = self.iflow_manager.get_statistics()
                self._log("info", f"[iFlow统计] 成功率: {stats['success_rate']:.1%}")
                
                return result.output
            else:
                self._log("error", f"[阶段 1: AI 决策] 调用失败: {result.error}")
                return ""
            
        except Exception as e:
            self._log("error", f"[阶段 1: AI 决策] 出错: {e}")
            return ""
    
    async def _ai_execution(self, decision: str):
        """AI 执行 - 使用 iflow -y"""
        try:
            prompt = f"""你是 Dev-Bot 的 AI 执行系统。

决策结果：
{decision}

请开始执行。"""
            
            # 构建上下文
            context = {
                "decision": decision,
                "session": self.session_num
            }
            
            # 使用 iflow 管理器调用
            self._log("info", "[阶段 2: AI 执行] 调用 iflow -y...")
            result = await self.iflow_manager.call_yolo(
                prompt=prompt,
                context=context,
                timeout=600
            )
            
            if result.success:
                self._log("success", f"[阶段 2: AI 执行] 执行完成（耗时: {result.duration:.2f}秒）")
                self._log("ai_output", result.output[:500])
                
                # 记录调用统计
                stats = self.iflow_manager.get_statistics()
                self._log("info", f"[iFlow统计] 成功率: {stats['success_rate']:.1%}")
                
                return result.output
            else:
                self._log("error", f"[阶段 2: AI 执行] 调用失败: {result.error}")
                return ""
            
        except Exception as e:
            self._log("error", f"[阶段 2: AI 执行] 出错: {e}")
            return ""

        output = output.decode()
            if error:
                self._log("warning", f"[阶段 2: AI 执行] stderr: {error.decode()[:200]}")
            
            self._log("ai_output", output[:500])
            
        except asyncio.TimeoutError:
            self._log("error", "[阶段 2: AI 执行] 超时")
        except Exception as e:
            self._log("error", f"[阶段 2: AI 执行] 出错: {e}")
    
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
    
    def _save_memory(self, memory: Dict):
        """保存长期记忆"""
        # 保存前再次限制
        if len(memory.get('history', [])) > self.MAX_HISTORY_ENTRIES:
            memory['history'] = memory['history'][-self.MAX_HISTORY_ENTRIES:]
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    
    def _log(self, level: str, message: str):
        """写入日志"""
        print(f"[AI 循环] [{level.upper()}] {message}")
        self.ipc.write_log("ai_loop", level, message)
    
    def _update_status(self, status: Dict):
        """更新状态"""
        status["pid"] = os.getpid()
        self.ipc.write_status("ai_loop", status)
    
    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        print(f"[AI 循环] 收到 SIGTERM 信号，准备退出...")
        self.is_running = False
    
    async def _check_command(self) -> Optional[Dict]:
        """检查是否有新命令"""
        try:
            if self.command_file.exists():
                with open(self.command_file, 'r', encoding='utf-8') as f:
                    command = json.load(f)
                
                # 删除命令文件
                self.command_file.unlink()
                
                return command
        except Exception as e:
            print(f"[AI 循环] 读取命令失败: {e}")
        
        return None
    
    async def _handle_command(self, command: Dict):
        """处理命令"""
        cmd_type = command.get("command")
        params = command.get("params", {})
        
        response = {
            "success": False,
            "error": None,
            "result": None
        }
        
        try:
            if cmd_type == "pause":
                self.is_paused = True
                response["success"] = True
                response["result"] = "AI 循环已暂停"
                self._log("info", "AI 循环已暂停")
                
            elif cmd_type == "resume":
                self.is_paused = False
                response["success"] = True
                response["result"] = "AI 循环已恢复"
                self._log("info", "AI 循环已恢复")
                
            elif cmd_type == "send_message":
                message = params.get("message", "")
                self._log("info", f"收到消息: {message[:50]}...")
                response["success"] = True
                response["result"] = "消息已接收"
                
            else:
                response["error"] = f"未知命令: {cmd_type}"
                
        except Exception as e:
            response["error"] = str(e)
        
        # 发送响应
        try:
            with open(self.response_file, 'w', encoding='utf-8') as f:
                json.dump(response, f)
        except Exception as e:
            print(f"[AI 循环] 发送响应失败: {e}")
    
    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        print(f"[AI 循环] 收到 SIGINT 信号，准备退出...")
        self.is_running = False


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python ai_loop_process.py <项目根目录> [配置文件]")
        sys.exit(1)
    
    project_root = Path(sys.argv[1])
    config_file = sys.argv[2] if len(sys.argv) > 2 else "config.json"
    
    ai_loop = AILoopProcess(project_root, config_file)
    await ai_loop.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[AI 循环] AI 循环进程已停止")
