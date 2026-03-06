#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 自主进化系统

体现 AI 的决策能力，包含三个核心子系统：
1. 决策系统：分析当前状态，评估选项，做出决策
2. 学习系统：积累经验，识别模式，优化策略
3. 优化系统：自我改进，提示词优化，代码优化
"""

import asyncio
import json
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.multi_iflow_manager import get_multi_iflow_manager, MultiIFlowStrategy


class EvolutionPhase(Enum):
    """进化阶段"""
    ANALYSIS = "analysis"          # 分析阶段
    DECISION = "decision"          # 决策阶段
    EXECUTION = "execution"        # 执行阶段
    EVALUATION = "evaluation"      # 评估阶段
    LEARNING = "learning"          # 学习阶段
    OPTIMIZATION = "optimization"  # 优化阶段


class DecisionType(Enum):
    """决策类型"""
    DEVELOPMENT = "development"      # 开发决策
    DEBUGGING = "debugging"         # 调试决策
    OPTIMIZATION = "optimization"    # 优化决策
    REFACTORING = "refactoring"     # 重构决策
    FEATURE_ADDITION = "feature"     # 功能添加
    BUG_FIX = "bug_fix"            # 错误修复
    DOCUMENTATION = "documentation" # 文档改进
    TESTING = "testing"            # 测试改进


class AIDecisionSystem:
    """AI 决策系统
    
    负责分析当前状态，评估可选方案，做出最优决策
    """
    
    def __init__(self, project_root: Path, ai_command: str = "iflow"):
        self.project_root = project_root
        self.ai_command = ai_command
        self.decision_history: List[Dict] = []
        self.max_history = 50
        
        # 决策权重配置
        self.decision_weights = {
            DecisionType.DEVELOPMENT: 0.3,
            DecisionType.DEBUGGING: 0.2,
            DecisionType.OPTIMIZATION: 0.15,
            DecisionType.REFACTORING: 0.1,
            DecisionType.FEATURE_ADDITION: 0.1,
            DecisionType.BUG_FIX: 0.1,
            DecisionType.DOCUMENTATION: 0.05,
            DecisionType.TESTING: 0.0,
        }
    
    async def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """做出决策
        
        Args:
            context: 当前上下文信息
        
        Returns:
            决策结果，包含决策类型、理由、执行计划
        """
        print(f"[AI决策系统] 开始分析当前状态...")
        
        # 阶段 1: 分析
        analysis = await self._analyze_context(context)
        
        # 阶段 2: 评估
        options = await self._evaluate_options(analysis)
        
        # 阶段 3: 选择
        decision = await self._select_best_option(options)
        
        # 记录决策
        self._record_decision(decision)
        
        return decision
    
    async def _analyze_context(self, context: Dict) -> Dict:
        """分析当前上下文"""
        prompt = f"""你是 Dev-Bot 的 AI 决策系统，负责分析当前项目状态。

当前上下文：
{json.dumps(context, indent=2, ensure_ascii=False)}

请分析以下方面：
1. 项目当前状态（健康度、进度、问题）
2. 代码质量（测试覆盖率、代码复杂度、技术债务）
3. 运行时状态（错误率、性能瓶颈、资源使用）
4. 开发进度（已完成功能、待办事项、阻塞问题）
5. 潜在风险（安全漏洞、依赖问题、兼容性问题）

输出 JSON 格式：
{{
    "health_score": 0-100,
    "critical_issues": ["问题1", "问题2"],
    "opportunities": ["机会1", "机会2"],
    "priorities": ["优先级1", "优先级2"],
    "recommendations": ["建议1", "建议2"]
}}
"""
        
        result = await self._call_ai(prompt)
        return self._parse_json_response(result)
    
    async def _evaluate_options(self, analysis: Dict) -> List[Dict]:
        """评估可选方案"""
        prompt = f"""基于以下分析结果，评估可能的行动方案。

分析结果：
{json.dumps(analysis, indent=2, ensure_ascii=False)}

请评估以下行动方案：
1. 开发新功能
2. 修复现有错误
3. 优化性能
4. 重构代码
5. 改进测试
6. 更新文档

为每个方案评分（0-100），考虑：
- 重要性
- 紧急性
- 可行性
- 风险
- 预期收益

输出 JSON 格式：
{{
    "options": [
        {{
            "type": "development",
            "name": "方案名称",
            "score": 85,
            "reasoning": "评分理由",
            "estimated_effort": "low/medium/high",
            "expected_impact": "impact description"
        }}
    ]
}}
"""
        
        result = await self._call_ai(prompt)
        parsed = self._parse_json_response(result)
        return parsed.get("options", [])
    
    async def _select_best_option(self, options: List[Dict]) -> Dict:
        """选择最佳方案"""
        if not options:
            return {
                "type": "no_action",
                "name": "等待",
                "score": 0,
                "reasoning": "没有可执行的方案",
                "plan": []
            }
        
        # 按分数排序
        sorted_options = sorted(options, key=lambda x: x.get("score", 0), reverse=True)
        best_option = sorted_options[0]
        
        # 生成执行计划
        plan = await self._generate_execution_plan(best_option)
        
        return {
            "type": best_option.get("type", "unknown"),
            "name": best_option.get("name", ""),
            "score": best_option.get("score", 0),
            "reasoning": best_option.get("reasoning", ""),
            "estimated_effort": best_option.get("estimated_effort", ""),
            "expected_impact": best_option.get("expected_impact", ""),
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_execution_plan(self, option: Dict) -> List[Dict]:
        """生成执行计划"""
        prompt = f"""为以下行动方案生成详细的执行计划。

行动方案：
{json.dumps(option, indent=2, ensure_ascii=False)}

请生成具体的执行步骤，每个步骤包含：
- 步骤描述
- 预期输出
- 验证标准
- 依赖关系

输出 JSON 格式：
{{
    "steps": [
        {{
            "step": 1,
            "description": "步骤描述",
            "expected_output": "预期输出",
            "validation": "验证标准",
            "dependencies": []
        }}
    ]
}}
"""
        
        result = await self._call_ai(prompt)
        parsed = self._parse_json_response(result)
        return parsed.get("steps", [])
    
    async def _call_ai(self, prompt: str, timeout: int = 120) -> str:
        """调用 AI 工具"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.ai_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            output, error = await asyncio.wait_for(
                process.communicate(input=prompt.encode()),
                timeout=timeout
            )
            
            result = output.decode()
            if error:
                print(f"[AI决策系统] 警告: {error.decode()[:200]}")
            
            return result
            
        except asyncio.TimeoutError:
            print(f"[AI决策系统] AI 调用超时")
            return '{"error": "timeout"}'
        except Exception as e:
            print(f"[AI决策系统] AI 调用失败: {e}")
            return '{"error": str(e)}'
    
    def _parse_json_response(self, response: str) -> Dict:
        """解析 JSON 响应"""
        try:
            # 尝试提取 JSON 部分
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            print(f"[AI决策系统] JSON 解析失败: {e}")
            return {"error": str(e)}
    
    def _record_decision(self, decision: Dict):
        """记录决策历史"""
        self.decision_history.append(decision)
        if len(self.decision_history) > self.max_history:
            self.decision_history = self.decision_history[-self.max_history:]


class AILearningSystem:
    """AI 学习系统
    
    负责积累经验、识别模式、优化策略
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.experience_file = project_root / ".dev-bot-evolution" / "experience.json"
        self.experience_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.experiences: List[Dict] = []
        self.patterns: Dict[str, Any] = {}
        self.strategies: Dict[str, Any] = {}
        
        self._load_experiences()
    
    def _load_experiences(self):
        """加载经验数据"""
        if self.experience_file.exists():
            try:
                with open(self.experience_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.experiences = data.get("experiences", [])
                    self.patterns = data.get("patterns", {})
                    self.strategies = data.get("strategies", {})
            except Exception as e:
                print(f"[AI学习系统] 加载经验失败: {e}")
    
    def _save_experiences(self):
        """保存经验数据"""
        try:
            data = {
                "experiences": self.experiences,
                "patterns": self.patterns,
                "strategies": self.strategies,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.experience_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AI学习系统] 保存经验失败: {e}")
    
    async def learn_from_execution(self, execution: Dict):
        """从执行中学习"""
        print(f"[AI学习系统] 从执行中学习...")
        
        # 记录经验
        experience = {
            "timestamp": datetime.now().isoformat(),
            "decision_type": execution.get("decision_type"),
            "action": execution.get("action"),
            "result": execution.get("result"),
            "success": execution.get("success", False),
            "lessons_learned": execution.get("lessons", []),
            "metrics": execution.get("metrics", {})
        }
        
        self.experiences.append(experience)
        
        # 识别模式
        await self._identify_patterns()
        
        # 优化策略
        await self._optimize_strategies()
        
        # 保存
        self._save_experiences()
    
    async def _identify_patterns(self):
        """识别模式"""
        if len(self.experiences) < 5:
            return
        
        # 统计成功的决策类型
        success_by_type = {}
        for exp in self.experiences:
            if exp.get("success"):
                dtype = exp.get("decision_type", "unknown")
                success_by_type[dtype] = success_by_type.get(dtype, 0) + 1
        
        self.patterns["successful_types"] = success_by_type
        
        # 识别常见问题
        common_issues = {}
        for exp in self.experiences:
            if not exp.get("success"):
                lessons = exp.get("lessons_learned", [])
                for lesson in lessons:
                    common_issues[lesson] = common_issues.get(lesson, 0) + 1
        
        self.patterns["common_issues"] = common_issues
    
    async def _optimize_strategies(self):
        """优化策略"""
        if not self.patterns:
            return
        
        # 基于模式调整策略
        successful_types = self.patterns.get("successful_types", {})
        if successful_types:
            # 优先使用成功的决策类型
            self.strategies["preferred_types"] = sorted(
                successful_types.keys(),
                key=lambda x: successful_types[x],
                reverse=True
            )
        
        # 避免常见问题
        common_issues = self.patterns.get("common_issues", {})
        if common_issues:
            self.strategies["avoid"] = sorted(
                common_issues.keys(),
                key=lambda x: common_issues[x],
                reverse=True
            )[:5]
    
    def get_recommendations(self, context: Dict) -> List[str]:
        """获取基于经验的推荐"""
        recommendations = []
        
        # 基于策略的推荐
        preferred_types = self.strategies.get("preferred_types", [])
        if preferred_types:
            recommendations.append(f"优先考虑这些决策类型: {', '.join(preferred_types[:3])}")
        
        # 避免常见问题
        avoid = self.strategies.get("avoid", [])
        if avoid:
            recommendations.append(f"注意避免: {', '.join(avoid[:3])}")
        
        return recommendations


class AIOptimizationSystem:
    """AI 优化系统
    
    负责自我改进、提示词优化、代码优化
    """
    
    def __init__(self, project_root: Path, ai_command: str = "iflow"):
        self.project_root = project_root
        self.ai_command = ai_command
        self.prompt_file = project_root / "PROMPT.md"
        self.optimization_history: List[Dict] = []
    
    async def optimize_prompt(self, feedback: Dict) -> bool:
        """优化提示词"""
        print(f"[AI优化系统] 开始优化提示词...")
        
        if not self.prompt_file.exists():
            print(f"[AI优化系统] 提示词文件不存在")
            return False
        
        # 读取当前提示词
        with open(self.prompt_file, 'r', encoding='utf-8') as f:
            current_prompt = f.read()
        
        # 生成优化建议
        prompt = f"""你是 Dev-Bot 的提示词优化专家。

当前提示词：
{current_prompt}

反馈信息：
{json.dumps(feedback, indent=2, ensure_ascii=False)}

请优化提示词，考虑：
1. 清晰度：指令是否明确
2. 完整性：是否包含所有必要信息
3. 有效性：是否产生期望的结果
4. 简洁性：是否简洁明了
5. 适应性：是否适应不同场景

输出优化后的提示词（保持 Markdown 格式）。
"""
        
        try:
            result = await self._call_ai(prompt)
            
            # 验证优化结果
            if len(result) > len(current_prompt) * 0.5:  # 至少保留50%内容
                # 备份原提示词
                backup_file = self.prompt_file.with_suffix('.md.backup')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(current_prompt)
                
                # 保存优化后的提示词
                with open(self.prompt_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                # 记录优化历史
                self.optimization_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "prompt_optimization",
                    "original_length": len(current_prompt),
                    "optimized_length": len(result),
                    "feedback": feedback
                })
                
                print(f"[AI优化系统] 提示词优化完成")
                return True
            else:
                print(f"[AI优化系统] 优化结果无效")
                return False
                
        except Exception as e:
            print(f"[AI优化系统] 提示词优化失败: {e}")
            return False
    
    async def optimize_code(self, file_path: Path) -> bool:
        """优化代码"""
        print(f"[AI优化系统] 优化代码: {file_path}")
        
        if not file_path.exists():
            return False
        
        # 读取代码
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 生成优化建议
        prompt = f"""你是代码优化专家。请优化以下代码：

文件：{file_path}

代码：
{code}

优化目标：
1. 提高可读性
2. 改善性能
3. 增强可维护性
4. 遵循最佳实践

请输出优化后的代码（仅代码，不需要解释）。"""
        
        try:
            result = await self._call_ai(prompt)
            
            if result and result != code:
                # 备份原代码
                backup_file = file_path.with_suffix('.py.backup')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                # 保存优化后的代码
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                print(f"[AI优化系统] 代码优化完成")
                return True
            
        except Exception as e:
            print(f"[AI优化系统] 代码优化失败: {e}")
        
        return False
    
    async def _call_ai(self, prompt: str, timeout: int = 120) -> str:
        """调用 AI 工具"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.ai_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            output, error = await asyncio.wait_for(
                process.communicate(input=prompt.encode()),
                timeout=timeout
            )
            
            result = output.decode()
            return result
            
        except asyncio.TimeoutError:
            print(f"[AI优化系统] AI 调用超时")
            return ""
        except Exception as e:
            print(f"[AI优化系统] AI 调用失败: {e}")
            return ""


class AIEvolutionSystem:
    """AI 自主进化系统
    
    整合决策、学习、优化三个子系统，实现完整的自主进化
    """
    
    def __init__(self, project_root: Path, ai_command: str = "iflow"):
        self.project_root = project_root
        self.ai_command = ai_command
        
        # 子系统
        self.decision_system = AIDecisionSystem(project_root, ai_command)
        self.learning_system = AILearningSystem(project_root)
        self.optimization_system = AIOptimizationSystem(project_root, ai_command)
        
        # 多 iflow 管理器
        self.multi_iflow_manager = get_multi_iflow_manager(
            iflow_command=ai_command,
            default_timeout=300,
            max_retries=3
        )
        
        # 进化状态
        self.evolution_count = 0
        self.current_phase = EvolutionPhase.ANALYSIS
        
        # 是否启用多 iflow 并发
        self.enable_multi_iflow = True
        
        print(f"[AI进化系统] 初始化完成")
        print(f"[AI进化系统] 多 iflow 并发: {'启用' if self.enable_multi_iflow else '禁用'}")
    
    async def evolve(self, context: Dict) -> Dict:
        """执行一次完整的进化循环"""
        print(f"\n{'='*60}")
        print(f"[AI进化系统] 开始进化循环 #{self.evolution_count + 1}")
        print(f"{'='*60}\n")
        
        result = {
            "evolution_number": self.evolution_count + 1,
            "phases": [],
            "decision": None,
            "execution": None,
            "evaluation": None,
            "learning": None,
            "optimization": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 阶段 1: 分析
            self.current_phase = EvolutionPhase.ANALYSIS
            print(f"[阶段 1/6] 分析当前状态...")
            result["phases"].append({"phase": "analysis", "status": "started"})
            
            # 阶段 2: 决策
            self.current_phase = EvolutionPhase.DECISION
            print(f"[阶段 2/6] AI 决策...")
            result["phases"].append({"phase": "analysis", "status": "completed"})
            result["phases"].append({"phase": "decision", "status": "started"})
            
            decision = await self.decision_system.make_decision(context)
            result["decision"] = decision
            result["phases"].append({"phase": "decision", "status": "completed"})
            
            print(f"  决策类型: {decision.get('type')}")
            print(f"  决策名称: {decision.get('name')}")
            print(f"  决策分数: {decision.get('score')}")
            print(f"  决策理由: {decision.get('reasoning')}")
            print(f"  执行步骤数: {len(decision.get('plan', []))}")
            
            # 阶段 3: 执行
            self.current_phase = EvolutionPhase.EXECUTION
            print(f"\n[阶段 3/6] 执行决策...")
            result["phases"].append({"phase": "execution", "status": "started"})
            
            execution = await self._execute_decision(decision)
            result["execution"] = execution
            result["phases"].append({"phase": "execution", "status": "completed"})
            
            print(f"  执行结果: {execution.get('result')}")
            print(f"  执行成功: {execution.get('success')}")
            
            # 阶段 4: 评估
            self.current_phase = EvolutionPhase.EVALUATION
            print(f"\n[阶段 4/6] 评估执行结果...")
            result["phases"].append({"phase": "evaluation", "status": "started"})
            
            evaluation = await self._evaluate_execution(execution)
            result["evaluation"] = evaluation
            result["phases"].append({"phase": "evaluation", "status": "completed"})
            
            print(f"  评估分数: {evaluation.get('score')}")
            print(f"  评估反馈: {evaluation.get('feedback')}")
            
            # 阶段 5: 学习
            self.current_phase = EvolutionPhase.LEARNING
            print(f"\n[阶段 5/6] 从执行中学习...")
            result["phases"].append({"phase": "learning", "status": "started"})
            
            await self.learning_system.learn_from_execution(execution)
            result["learning"] = {
                "status": "completed",
                "experiences_count": len(self.learning_system.experiences)
            }
            result["phases"].append({"phase": "learning", "status": "completed"})
            
            # 阶段 6: 优化
            self.current_phase = EvolutionPhase.OPTIMIZATION
            print(f"\n[阶段 6/6] 优化系统...")
            result["phases"].append({"phase": "optimization", "status": "started"})
            
            optimization = await self._optimize_system(evaluation)
            result["optimization"] = optimization
            result["phases"].append({"phase": "optimization", "status": "completed"})
            
            if optimization.get("prompt_optimized"):
                print(f"  ✓ 提示词已优化")
            
            # 更新进化计数
            self.evolution_count += 1
            
            print(f"\n{'='*60}")
            print(f"[AI进化系统] 进化循环 #{self.evolution_count} 完成")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"[AI进化系统] 进化过程出错: {e}")
            import traceback
            traceback.print_exc()
            result["error"] = str(e)
        
        return result
    
    async def _execute_decision(self, decision: Dict) -> Dict:
        """执行决策"""
        try:
            prompt = f"""你是 Dev-Bot 的 AI 执行系统。

决策结果：
{json.dumps(decision, indent=2, ensure_ascii=False)}

请执行这个决策，完成所有计划步骤。

只执行必要的代码修改，不要做其他事情。"""
            
            # 调用 AI 执行
            process = await asyncio.create_subprocess_exec(
                self.ai_command, "-y",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            output, error = await asyncio.wait_for(
                process.communicate(input=prompt.encode()),
                timeout=600
            )
            
            return {
                "result": "executed",
                "success": process.returncode == 0,
                "output": output.decode()[:500],
                "error": error.decode()[:200] if error else None,
                "decision_type": decision.get("type")
            }
            
        except asyncio.TimeoutError:
            return {
                "result": "timeout",
                "success": False,
                "decision_type": decision.get("type")
            }
        except Exception as e:
            return {
                "result": "error",
                "success": False,
                "error": str(e),
                "decision_type": decision.get("type")
            }
    
    async def _evaluate_execution(self, execution: Dict) -> Dict:
        """评估执行结果（使用多 iflow 并发）"""
        if self.enable_multi_iflow:
            # 使用多 iflow 并发评估
            return await self._multi_iflow_evaluation(execution)
        else:
            # 单 iflow 评估
            return await self._single_iflow_evaluation(execution)
    
    async def _multi_iflow_evaluation(self, execution: Dict) -> Dict:
        """使用多 iflow 并发评估"""
        from dev_bot.multi_iflow_manager import IForkInstance
        
        # 获取预定义角色
        roles = self.multi_iflow_manager.get_predefined_roles()
        
        # 选择关键角色进行评估
        eval_instances = [
            roles["reviewer"],  # 审查者
            roles["tester"],    # 测试者
            roles["optimizer"]  # 优化者
        ]
        
        # 构建评估提示
        eval_prompt = f"""请评估以下执行结果：

执行结果：
{json.dumps(execution, indent=2, ensure_ascii=False)}

请从你的角度评估这个执行结果，给出评分（1-10）和建议。
"""
        
        # 并发调用评估
        result = await self.multi_iflow_manager.call_evaluation(
            prompt="执行结果评估",
            decision=json.dumps(execution, indent=2, ensure_ascii=False),
            instances=eval_instances,
            context={"execution": execution}
        )
        
        # 提取综合评分
        score = result.confidence * 100  # 转换为 0-100
        
        return {
            "score": int(score),
            "feedback": result.aggregated_result,
            "metrics": {
                "success": execution.get("success", False),
                "confidence": result.confidence,
                "consensus": result.consensus_score,
                "recommendations": result.recommendations
            },
            "multi_iflow_used": True
        }
    
    async def _single_iflow_evaluation(self, execution: Dict) -> Dict:
        """单 iflow 评估"""
        # 简单评估逻辑
        success = execution.get("success", False)
        score = 80 if success else 40
        
        feedback = []
        if success:
            feedback.append("执行成功")
        else:
            feedback.append(f"执行失败: {execution.get('error', '未知错误')}")
        
        return {
            "score": score,
            "feedback": "; ".join(feedback),
            "metrics": {
                "success": success
            },
            "multi_iflow_used": False
        }
    
    async def reflect_on_execution(
        self,
        prompt: str,
        execution_result: Dict
    ) -> Dict:
        """反思执行过程（使用多 iflow 并发）"""
        if not self.enable_multi_iflow:
            return {"reflections": [], "recommendations": []}
        
        from dev_bot.multi_iflow_manager import IForkInstance
        
        # 获取预定义角色
        roles = self.multi_iflow_manager.get_predefined_roles()
        
        # 选择关键角色进行反思
        reflect_instances = [
            roles["reviewer"],  # 审查者
            roles["architect"], # 架构师
            roles["optimizer"]  # 优化者
        ]
        
        # 并发调用反思
        result = await self.multi_iflow_manager.call_reflection(
            prompt=prompt,
            execution_result=json.dumps(execution_result, indent=2, ensure_ascii=False),
            instances=reflect_instances,
            context={"prompt": prompt}
        )
        
        return {
            "reflections": result.aggregated_result,
            "recommendations": result.recommendations,
            "duration": result.duration,
            "multi_iflow_used": True
        }
    
    async def _optimize_system(self, evaluation: Dict) -> Dict:
        """优化系统"""
        result = {
            "prompt_optimized": False,
            "code_optimized": False
        }
        
        # 根据评估结果决定是否优化
        if evaluation.get("score", 0) < 70:
            # 低分，尝试优化提示词
            feedback = {
                "score": evaluation.get("score"),
                "feedback": evaluation.get("feedback")
            }
            result["prompt_optimized"] = await self.optimization_system.optimize_prompt(feedback)
        
        return result
    
    def get_status(self) -> Dict:
        """获取进化系统状态"""
        return {
            "evolution_count": self.evolution_count,
            "current_phase": self.current_phase.value,
            "decision_history_count": len(self.decision_system.decision_history),
            "experience_count": len(self.learning_system.experiences),
            "pattern_count": len(self.learning_system.patterns),
            "optimization_count": len(self.optimization_system.optimization_history)
        }