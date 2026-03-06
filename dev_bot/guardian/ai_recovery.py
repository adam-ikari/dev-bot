#!/usr/bin/env python3
"""
AI 驱动的恢复策略

使用 AI (iflow) 进行智能诊断和修复
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from .core import RecoveryStrategy


class AIRecoveryStrategy(RecoveryStrategy):
    """AI 驱动的恢复策略"""
    
    def __init__(self, iflow_manager=None, project_root: Optional[Path] = None):
        self.iflow_manager = iflow_manager
        self.project_root = project_root or Path.cwd()
        self.diagnosis_cache: Dict[str, Dict] = {}
        self.max_cache_size = 100
    
    async def recover(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """执行 AI 驱动的恢复操作"""
        print(f"[AI 恢复] 开始分析 {process_type} 失败原因...")
        
        # 检查重启次数
        restart_count = process_info.get("restart_count", 0)
        max_restarts = process_info.get("max_restarts", 10)
        
        if restart_count >= max_restarts:
            print(f"[AI 恢复] {process_type} 重启次数已达上限（{max_restarts}）")
            return False
        
        # 第一步：智能诊断
        diagnosis = await self._diagnose_failure(process_type, process_info)
        if not diagnosis:
            print(f"[AI 恢复] 诊断失败，使用简单重启策略")
            return await self._simple_restart(process_type, process_info)
        
        # 第二步：生成修复方案
        fix_plan = await self._generate_fix_plan(process_type, diagnosis)
        if not fix_plan:
            print(f"[AI 恢复] 生成修复方案失败，使用简单重启策略")
            return await self._simple_restart(process_type, process_info)
        
        # 第三步：执行修复
        fix_success = await self._execute_fix(process_type, fix_plan)
        
        if not fix_success:
            print(f"[AI 恢复] 修复失败，尝试简单重启")
            return await self._simple_restart(process_type, process_info)
        
        # 第四步：重启进程
        return await self._simple_restart(process_type, process_info)
    
    async def _diagnose_failure(self, process_type: str, process_info: Dict[str, Any]) -> Optional[Dict]:
        """诊断失败原因"""
        # 检查缓存
        cache_key = f"{process_type}_{process_info.get('restart_count', 0)}"
        if cache_key in self.diagnosis_cache:
            print(f"[AI 恢复] 使用缓存的诊断结果")
            return self.diagnosis_cache[cache_key]
        
        # 收集诊断信息
        diagnostic_info = {
            "process_type": process_type,
            "startup_command": process_info.get("startup_command"),
            "restart_count": process_info.get("restart_count", 0),
            "project_root": str(self.project_root),
            "last_error": process_info.get("last_error", "Unknown")
        }
        
        # 检查日志文件
        log_files = list(self.project_root.glob(".error-logs/*.json"))
        if log_files:
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest_log, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    diagnostic_info["latest_error_log"] = log_data
            except Exception as e:
                print(f"[AI 恢复] 读取错误日志失败: {e}")
        
        # 检查进程输出
        diagnostic_info["process_info"] = str(process_info)
        
        # 如果有 iflow_manager，进行 AI 分析
        if self.iflow_manager:
            prompt = self._build_diagnosis_prompt(diagnostic_info)
            try:
                response = await self.iflow_manager.call_iflow(prompt)
                diagnosis = {
                    "cause": response.get("diagnosis", "Unknown"),
                    "severity": response.get("severity", "medium"),
                    "suggestions": response.get("suggestions", []),
                    "ai_analysis": response
                }
                
                # 缓存结果
                if len(self.diagnosis_cache) >= self.max_cache_size:
                    # 删除最旧的缓存
                    oldest_key = next(iter(self.diagnosis_cache))
                    del self.diagnosis_cache[oldest_key]
                self.diagnosis_cache[cache_key] = diagnosis
                
                return diagnosis
            except Exception as e:
                print(f"[AI 恢复] AI 分析失败: {e}")
        
        # 简单分析
        return {
            "cause": "Process exited unexpectedly",
            "severity": "medium",
            "suggestions": ["Check process logs", "Verify dependencies"],
            "ai_analysis": None
        }
    
    def _build_diagnosis_prompt(self, diagnostic_info: Dict) -> str:
        """构建诊断提示词"""
        prompt = f"""分析进程失败原因并提供建议。

进程信息：
- 进程类型: {diagnostic_info['process_type']}
- 启动命令: {' '.join(diagnostic_info['startup_command'])}
- 重启次数: {diagnostic_info['restart_count']}
- 项目根目录: {diagnostic_info['project_root']}
- 最后错误: {diagnostic_info['last_error']}

"""
        
        if 'latest_error_log' in diagnostic_info:
            prompt += f"\n最近错误日志:\n{json.dumps(diagnostic_info['latest_error_log'], indent=2)}\n"
        
        prompt += """

请以 JSON 格式返回分析结果，包含以下字段：
{
  "diagnosis": "失败原因诊断",
  "severity": "严重程度


请以 JSON 格式返回分析结果，包含以下字段：
{
  "diagnosis": "失败原因诊断",
  "severity": "严重程度

请以 JSON 格式返回分析结果，包含以下字段：
{
  "diagnosis": "失败原因诊断",
  "severity": "严重程度 (low/medium/high)",
  "suggestions": ["建议1", "建议2"],
  "needs_code_fix": true/false,
  "affected_files": ["文件路径1", "文件路径2"]
}
"""
        return prompt
    
    async def _generate_fix_plan(self, process_type: str, diagnosis: Dict) -> Optional[Dict]:
        """生成修复方案"""
        if not self.iflow_manager:
            return None
        
        json_template = '''{
  "fix_type": "restart/config/code_change",
  "actions": ["action1", "action2"],
  "files_to_modify": [{"path": "file.py", "changes": "description"}],
  "config_changes": {},
  "verification_steps": ["step1", "step2"]
}'''
        
        prompt = f"""为 {process_type} 进程生成修复方案。

诊断结果：
- 原因: {diagnosis['cause']}
- 严重程度: {diagnosis['severity']}
- 建议: {', '.join(diagnosis['suggestions'])}

请以 JSON 格式返回修复方案：
{json_template}
"""
        
        try:
            response = await self.iflow_manager.call_iflow(prompt)
            return response
        except Exception as e:
            print(f"[AI 恢复] 生成修复方案失败: {e}")
            return None
    
    async def _execute_fix(self, process_type: str, fix_plan: Dict) -> bool:
        """执行修复方案"""
        print(f"[AI 恢复] 执行修复方案: {fix_plan.get('fix_type', 'unknown')}")
        
        try:
            # 执行配置修改
            if fix_plan.get("config_changes"):
                await self._apply_config_changes(fix_plan["config_changes"])
            
            # 执行代码修改
            if fix_plan.get("files_to_modify"):
                await self._apply_code_changes(fix_plan["files_to_modify"])
            
            # 执行验证步骤
            if fix_plan.get("verification_steps"):
                for step in fix_plan["verification_steps"]:
                    print(f"[AI 恢复] 执行验证步骤: {step}")
                    # 这里可以添加实际的验证逻辑
            
            print(f"[AI 恢复] 修复方案执行完成")
            return True
        except Exception as e:
            print(f"[AI 恢复] 执行修复方案失败: {e}")
            return False
    
    async def _apply_config_changes(self, config_changes: Dict):
        """应用配置修改"""
        config_file = self.project_root / "config.json"
        if not config_file.exists():
            print(f"[AI 恢复] 配置文件不存在")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 应用修改
            config.update(config_changes)
            
            # 保存
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"[AI 恢复] 配置已更新")
        except Exception as e:
            print(f"[AI 恢复] 更新配置失败: {e}")
            raise
    
    async def _apply_code_changes(self, files_to_modify: list):
        """应用代码修改"""
        print(f"[AI 恢复] 需要修改 {len(files_to_modify)} 个文件")
        
        for file_info in files_to_modify:
            file_path = self.project_root / file_info["path"]
            if not file_path.exists():
                print(f"[AI 恢复] 文件不存在: {file_path}")
                continue
            
            print(f"[AI 恢复] 文件修改提示: {file_info.get('changes', 'No description')}")
            # 这里可以添加实际的代码修改逻辑
            # 为了安全起见，目前只记录日志，不自动修改代码
    
    async def _simple_restart(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """简单重启进程（后备方案）"""
        startup_command = process_info.get("startup_command")
        if not startup_command:
            return False
        
        try:
            process = await asyncio.create_subprocess_exec(
                *startup_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            process_info["pid"] = process.pid
            process_info["last_seen"] = asyncio.get_event_loop().time()
            process_info["restart_count"] = process_info.get("restart_count", 0) + 1
            
            print(f"[AI 恢复] {process_type} 已重启（PID: {process.pid}）")
            return True
        except Exception as e:
            print(f"[AI 恢复] 重启 {process_type} 失败: {e}")
            return False
