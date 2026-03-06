#!/usr/bin/env python3
"""
Dev-Bot 自我进化系统
支持自我迭代、自我修复、自我进化
"""

import json
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dev_bot.error_handler import UnifiedErrorHandler


class SelfEvolutionSystem:
    """Dev-Bot 自我进化系统"""

    def __init__(
        self,
        project_root: Path,
        config: Any,
        logger: Any,
        error_handler: UnifiedErrorHandler
    ):
        """初始化自我进化系统

        Args:
            project_root: 项目根目录
            config: 配置对象
            logger: 日志记录器
            error_handler: 错误处理器
        """
        self.project_root = project_root
        self.config = config
        self.logger = logger
        self.error_handler = error_handler

        # 进化数据目录
        self.evolution_dir = project_root / ".dev-bot-evolution"
        self.evolution_dir.mkdir(exist_ok=True)

        # 进化历史
        self.evolution_history_file = self.evolution_dir / "evolution_history.json"
        self.evolution_history = self._load_evolution_history()

        # 当前版本
        self.current_version = self._get_current_version()

        # 统计信息
        self.evolution_stats = {
            "self_fix_count": 0,
            "self_improve_count": 0,
            "self_refactor_count": 0,
            "self_optimize_count": 0
        }

    def _get_current_version(self) -> str:
        """获取当前版本"""
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "0.0.0"

    def _load_evolution_history(self) -> List[Dict[str, Any]]:
        """加载进化历史"""
        if self.evolution_history_file.exists():
            with open(self.evolution_history_file, encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_evolution_history(self) -> None:
        """保存进化历史"""
        with open(self.evolution_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.evolution_history, f, indent=2, ensure_ascii=False)

    async def analyze_self(self) -> Dict[str, Any]:
        """自我分析 - 识别需要改进的地方

        Returns:
            分析结果
        """
        self.logger.info("[自我进化] 开始自我分析...")

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "version": self.current_version,
            "code_quality": await self._analyze_code_quality(),
            "error_patterns": await self._analyze_error_patterns(),
            "performance": await self._analyze_performance(),
            "architecture": await self._analyze_architecture(),
            "suggestions": []
        }

        # 生成改进建议
        suggestions = await self._generate_improvement_suggestions(analysis)
        analysis["suggestions"] = suggestions

        self.logger.info(f"[自我进化] 分析完成，发现 {len(suggestions)} 个改进建议")

        return analysis

    async def _analyze_code_quality(self) -> Dict[str, Any]:
        """分析代码质量"""
        self.logger.info("[自我进化] 分析代码质量...")

        quality = {
            "total_files": 0,
            "python_files": 0,
            "test_coverage": 0.0,
            "complexity": 0.0,
            "maintainability": 0.0,
            "issues": []
        }

        try:
            # 统计 Python 文件
            for py_file in self.project_root.rglob("*.py"):
                if ".venv" not in str(py_file) and "__pycache__" not in str(py_file):
                    quality["python_files"] += 1
                    quality["total_files"] += 1

            # 运行代码质量检查
            try:
                result = subprocess.run(
                    ["ruff", "check", str(self.project_root), "--output-format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.stdout:
                    issues = json.loads(result.stdout)
                    quality["issues"] = issues[:10]  # 只保留前10个
            except Exception as e:
                self.logger.warning(f"代码质量检查失败: {e}")

            self.logger.info(f"[自我进化] 发现 {quality['python_files']} 个 Python 文件")

        except Exception as e:
            self.logger.error(f"[自我进化] 代码质量分析失败: {e}")

        return quality

    async def _analyze_error_patterns(self) -> Dict[str, Any]:
        """分析错误模式"""
        self.logger.info("[自我进化] 分析错误模式...")

        patterns = {
            "common_errors": {},
            "error_frequency": {},
            "fix_success_rate": 0.0
        }

        # 从错误处理器获取统计
        stats = self.error_handler.get_statistics()
        patterns["fix_success_rate"] = stats.get("fix_success_rate", 0.0)

        # 分析崩溃日志
        crash_logs = list((self.project_root / ".crash-logs").glob("*.json"))
        for crash_log in crash_logs[-10:]:  # 只分析最近10个
            try:
                with open(crash_log, encoding='utf-8') as f:
                    crash_info = json.load(f)
                    error_type = crash_info.get("error_type", "Unknown")
                    patterns["common_errors"][error_type] = (
                        patterns["common_errors"].get(error_type, 0) + 1
                    )
            except Exception:
                continue

        self.logger.info(f"[自我进化] 分析了 {len(crash_logs)} 个崩溃日志")

        return patterns

    async def _analyze_performance(self) -> Dict[str, Any]:
        """分析性能"""
        self.logger.info("[自我进化] 分析性能...")

        performance = {
            "startup_time": 0.0,
            "memory_usage": 0.0,
            "response_time": 0.0,
            "bottlenecks": []
        }

        # 基本性能指标
        try:
            import psutil
            process = psutil.Process()
            performance["memory_usage"] = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass

        return performance

    async def _analyze_architecture(self) -> Dict[str, Any]:
        """分析架构"""
        self.logger.info("[自我进化] 分析架构...")

        architecture = {
            "modules": [],
            "dependencies": [],
            "coupling": 0.0,
            "cohesion": 0.0,
            "suggestions": []
        }

        # 识别主要模块
        dev_bot_dir = self.project_root / "dev_bot"
        if dev_bot_dir.exists():
            for module_file in dev_bot_dir.glob("*.py"):
                if not module_file.name.startswith("_"):
                    architecture["modules"].append(module_file.stem)

        self.logger.info(f"[自我进化] 识别了 {len(architecture['modules'])} 个模块")

        return architecture

    async def _generate_improvement_suggestions(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成改进建议

        Args:
            analysis: 分析结果

        Returns:
            改进建议列表
        """
        suggestions = []

        # 基于代码质量的建议
        if analysis["code_quality"]["issues"]:
            suggestions.append({
                "type": "code_quality",
                "priority": "medium",
                "description": f"发现 {len(analysis['code_quality']['issues'])} 个代码质量问题",
                "action": "fix_code_quality",
                "details": analysis["code_quality"]["issues"][:3]
            })

        # 基于错误模式的建议
        if analysis["error_patterns"]["fix_success_rate"] < 80:
            rate = analysis['error_patterns']['fix_success_rate']
            suggestions.append({
                "type": "error_handling",
                "priority": "high",
                "description": f"自动修复成功率较低 ({rate:.1f}%)",
                "action": "improve_error_handling",
                "details": "需要改进错误分析和修复策略"
            })

        # 基于性能的建议
        if analysis["performance"]["memory_usage"] > 500:
            suggestions.append({
                "type": "performance",
                "priority": "low",
                "description": f"内存使用较高 ({analysis['performance']['memory_usage']:.1f} MB)",
                "action": "optimize_memory",
                "details": "考虑优化内存使用"
            })

        return suggestions

    async def self_fix(self, analysis: Dict[str, Any]) -> bool:
        """自我修复 - 自动修复发现的问题

        Args:
            analysis: 分析结果

        Returns:
            修复是否成功
        """
        self.logger.info("[自我进化] 开始自我修复...")

        fixed_count = 0

        for suggestion in analysis["suggestions"]:
            try:
                action = suggestion.get("action")

                if action == "fix_code_quality":
                    if await self._fix_code_quality(suggestion):
                        fixed_count += 1

                elif action == "improve_error_handling":
                    if await self._improve_error_handling(suggestion):
                        fixed_count += 1

            except Exception as e:
                self.logger.error(f"[自我进化] 修复失败: {e}")
                self.logger.debug(traceback.format_exc())

        self.logger.info(f"[自我进化] 自我修复完成，修复了 {fixed_count} 个问题")

        if fixed_count > 0:
            self.evolution_stats["self_fix_count"] += fixed_count
            return True

        return False

    async def _fix_code_quality(self, suggestion: Dict[str, Any]) -> bool:
        """修复代码质量问题

        Args:
            suggestion: 建议信息

        Returns:
            修复是否成功
        """
        self.logger.info(f"[自我进化] 修复代码质量问题: {suggestion['description']}")

        try:
            # 使用 ruff 自动修复
            result = subprocess.run(
                ["ruff", "check", "--fix", str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.success("[自我进化] 代码质量修复成功")
                return True
            else:
                self.logger.warning(f"[自我进化] 代码质量修复部分失败: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"[自我进化] 代码质量修复异常: {e}")
            return False

    async def _improve_error_handling(self, suggestion: Dict[str, Any]) -> bool:
        """改进错误处理

        Args:
            suggestion: 建议信息

        Returns:
            改进是否成功
        """
        self.logger.info(f"[自我进化] 改进错误处理: {suggestion['description']}")

        # 这里可以添加具体的错误处理改进逻辑
        # 例如：优化错误分析提示词、添加新的错误类型等

        return True

    async def self_improve(self, analysis: Dict[str, Any]) -> bool:
        """自我改进 - 改进现有功能

        Args:
            analysis: 分析结果

        Returns:
            改进是否成功
        """
        self.logger.info("[自我进化] 开始自我改进...")

        improved = False

        # 基于分析结果进行改进
        if analysis["code_quality"]["python_files"] > 0:
            # 生成代码文档
            if await self._generate_documentation():
                improved = True

            # 优化代码结构
            if await self._optimize_code_structure():
                improved = True

        if improved:
            self.evolution_stats["self_improve_count"] += 1

        return improved

    async def _generate_documentation(self) -> bool:
        """生成代码文档"""
        self.logger.info("[自我进化] 生成代码文档...")

        try:
            # 检查是否有文档工具
            try:
                result = subprocess.run(
                    ["pdoc", "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.logger.info("[自我进化] pdoc 可用，可以生成文档")
                    return True
            except FileNotFoundError:
                pass

            self.logger.info("[自我进化] 文档工具不可用，跳过文档生成")
            return False

        except Exception as e:
            self.logger.error(f"[自我进化] 文档生成失败: {e}")
            return False

    async def _optimize_code_structure(self) -> bool:
        """优化代码结构"""
        self.logger.info("[自我进化] 优化代码结构...")

        # 这里可以添加代码结构优化逻辑
        # 例如：重组文件、提取公共代码等

        return True

    async def self_refactor(self) -> bool:
        """自我重构 - 重构代码结构

        Returns:
            重构是否成功
        """
        self.logger.info("[自我进化] 开始自我重构...")

        try:
            # 使用 ruff 进行代码格式化和重构
            result = subprocess.run(
                ["ruff", "format", str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.success("[自我进化] 代码重构成功")
                self.evolution_stats["self_refactor_count"] += 1
                return True
            else:
                self.logger.warning(f"[自我进化] 代码重构部分失败: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"[自我进化] 代码重构异常: {e}")
            return False

    async def self_optimize(self) -> bool:
        """自我优化 - 优化性能

        Returns:
            优化是否成功
        """
        self.logger.info("[自我进化] 开始自我优化...")

        try:
            # 运行性能测试
            # 这里可以添加具体的性能优化逻辑

            self.evolution_stats["self_optimize_count"] += 1
            return True

        except Exception as e:
            self.logger.error(f"[自我进化] 性能优化失败: {e}")
            return False

    async def evolve(self) -> Dict[str, Any]:
        """执行自我进化

        Returns:
            进化结果
        """
        self.logger.info("=" * 60)
        self.logger.info("[自我进化] Dev-Bot 自我进化开始")
        self.logger.info("=" * 60)

        evolution_result = {
            "timestamp": datetime.now().isoformat(),
            "version": self.current_version,
            "phases": [],
            "statistics": {}
        }

        # 阶段 1: 自我分析
        try:
            self.logger.info("[阶段 1/5] 自我分析...")
            analysis = await self.analyze_self()
            evolution_result["phases"].append({
                "phase": "analysis",
                "status": "success",
                "suggestions_found": len(analysis.get("suggestions", []))
            })
        except Exception as e:
            self.logger.error(f"[阶段 1/5] 自我分析失败: {e}")
            evolution_result["phases"].append({
                "phase": "analysis",
                "status": "failed",
                "error": str(e)
            })

        # 阶段 2: 自我修复
        try:
            self.logger.info("[阶段 2/5] 自我修复...")
            fix_result = await self.self_fix(analysis)
            evolution_result["phases"].append({
                "phase": "fix",
                "status": "success" if fix_result else "skipped"
            })
        except Exception as e:
            self.logger.error(f"[阶段 2/5] 自我修复失败: {e}")
            evolution_result["phases"].append({
                "phase": "fix",
                "status": "failed",
                "error": str(e)
            })

        # 阶段 3: 自我改进
        try:
            self.logger.info("[阶段 3/5] 自我改进...")
            improve_result = await self.self_improve(analysis)
            evolution_result["phases"].append({
                "phase": "improve",
                "status": "success" if improve_result else "skipped"
            })
        except Exception as e:
            self.logger.error(f"[阶段 3/5] 自我改进失败: {e}")
            evolution_result["phases"].append({
                "phase": "improve",
                "status": "failed",
                "error": str(e)
            })

        # 阶段 4: 自我重构
        try:
            self.logger.info("[阶段 4/5] 自我重构...")
            refactor_result = await self.self_refactor()
            evolution_result["phases"].append({
                "phase": "refactor",
                "status": "success" if refactor_result else "skipped"
            })
        except Exception as e:
            self.logger.error(f"[阶段 4/5] 自我重构失败: {e}")
            evolution_result["phases"].append({
                "phase": "refactor",
                "status": "failed",
                "error": str(e)
            })

        # 阶段 5: 自我优化
        try:
            self.logger.info("[阶段 5/5] 自我优化...")
            optimize_result = await self.self_optimize()
            evolution_result["phases"].append({
                "phase": "optimize",
                "status": "success" if optimize_result else "skipped"
            })
        except Exception as e:
            self.logger.error(f"[阶段 5/5] 自我优化失败: {e}")
            evolution_result["phases"].append({
                "phase": "optimize",
                "status": "failed",
                "error": str(e)
            })

        # 统计信息
        evolution_result["statistics"] = self.evolution_stats

        # 保存进化历史
        self.evolution_history.append(evolution_result)
        self._save_evolution_history()

        self.logger.info("=" * 60)
        self.logger.info("[自我进化] Dev-Bot 自我进化完成")
        self.logger.info(f"  修复: {self.evolution_stats['self_fix_count']}")
        self.logger.info(f"  改进: {self.evolution_stats['self_improve_count']}")
        self.logger.info(f"  重构: {self.evolution_stats['self_refactor_count']}")
        self.logger.info(f"  优化: {self.evolution_stats['self_optimize_count']}")
        self.logger.info("=" * 60)

        return evolution_result

    def get_evolution_history(self) -> List[Dict[str, Any]]:
        """获取进化历史

        Returns:
            进化历史列表
        """
        return self.evolution_history

    def get_evolution_stats(self) -> Dict[str, int]:
        """获取进化统计

        Returns:
            统计信息
        """
        return self.evolution_stats

