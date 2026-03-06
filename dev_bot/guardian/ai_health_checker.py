#!/usr/bin/env python3
"""
AI 增强的健康检查器

使用 AI 进行智能健康评估
"""

import time
import psutil
from typing import Dict, Any, Optional
from .core import HealthChecker
from .prompt_generator import PromptGenerator


class AIHealthChecker(HealthChecker):
    """AI 增强的健康检查器"""
    
    def __init__(self, iflow_manager=None, project_root=None):
        super().__init__()
        self.iflow_manager = iflow_manager
        self.prompt_generator = PromptGenerator(project_root)
        self.health_cache: Dict[str, Dict] = {}
        self.cache_ttl = 60  # 缓存60秒
    
    async def check_health(self, process_type: str, pid: int) -> bool:
        """检查进程健康状态（使用 AI）"""
        # 首先进行基本检查
        basic_healthy = await super().check_health(process_type, pid)
        if not basic_healthy:
            return False
        
        # 如果有 iflow_manager，进行 AI 分析
        if self.iflow_manager:
            try:
                # 检查缓存
                cache_key = f"{process_type}_{pid}"
                if cache_key in self.health_cache:
                    cached = self.health_cache[cache_key]
                    if time.time() - cached['timestamp'] < self.cache_ttl:
                        return cached['result']
                
                # 收集进程信息
                process_stats = self._collect_process_stats(pid)
                resource_usage = self._collect_resource_usage(pid)
                
                # 生成提示词
                prompt = self.prompt_generator.generate_health_check_prompt(
                    process_type, pid, process_stats, resource_usage
                )
                
                # 调用 AI 分析
                response = await self.iflow_manager.call_iflow(prompt)
                
                # 解析结果
                health_status = response.get('health_status', 'healthy')
                is_healthy = health_status in ['healthy', 'warning']
                
                # 缓存结果
                self.health_cache[cache_key] = {
                    'result': is_healthy,
                    'timestamp': time.time(),
                    'analysis': response
                }
                
                # 打印建议
                if response.get('recommendations'):
                    print(f"[AI 健康检查] {process_type} 建议: {', '.join(response['recommendations'][:2])}")
                
                return is_healthy
            except Exception as e:
                print(f"[AI 健康检查] 分析失败: {e}")
                return True  # AI 失败时回退到基本检查结果
        
        return basic_healthy
    
    def _collect_process_stats(self, pid: int) -> Dict[str, Any]:
        """收集进程统计信息"""
        try:
            process = psutil.Process(pid)
            create_time = process.create_time()
            uptime = time.time() - create_time
            
            return {
                'pid': pid,
                'uptime': uptime,
                'status': process.status(),
                'num_threads': process.num_threads(),
                'num_fds': len(process.connections()) if hasattr(process, 'connections') else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _collect_resource_usage(self, pid: int) -> Dict[str, Any]:
        """收集资源使用情况"""
        try:
            process = psutil.Process(pid)
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': process.memory_percent(),
                'memory_mb': memory_info.rss / (1024 * 1024),
                'num_threads': process.num_threads(),
                'num_fds': len(process.connections()) if hasattr(process, 'connections') else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def analyze_anomalies(
        self,
        process_type: str,
        pid: int,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        anomalies: list
    ) -> Optional[Dict[str, Any]]:
        """分析异常（使用 AI）"""
        if not self.iflow_manager:
            return None
        
        try:
            prompt = self.prompt_generator.generate_anomaly_detection_prompt(
                process_type, current_metrics, baseline_metrics, anomalies
            )
            
            response = await self.iflow_manager.call_iflow(prompt)
            return response
        except Exception as e:
            print(f"[AI 异常分析] 分析失败: {e}")
            return None
    
    async def analyze_performance(
        self,
        process_type: str,
        performance_data: Dict[str, Any],
        bottlenecks: list
    ) -> Optional[Dict[str, Any]]:
        """分析性能（使用 AI）"""
        if not self.iflow_manager:
            return None
        
        try:
            prompt = self.prompt_generator.generate_performance_analysis_prompt(
                process_type, performance_data, bottlenecks
            )
            
            response = await self.iflow_manager.call_iflow(prompt)
            return response
        except Exception as e:
            print(f"[AI 性能分析] 分析失败: {e}")
            return None
    
    async def predict_failure(
        self,
        process_type: str,
        historical_data: list,
        current_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """预测失败（使用 AI）"""
        if not self.iflow_manager:
            return None
        
        try:
            prompt = self.prompt_generator.generate_predictive_analysis_prompt(
                process_type, historical_data, current_state
            )
            
            response = await self.iflow_manager.call_iflow(prompt)
            return response
        except Exception as e:
            print(f"[AI 失败预测] 预测失败: {e}")
            return None
    
    async def optimize_system(
        self,
        system_state: Dict[str, Any],
        all_processes: list
    ) -> Optional[Dict[str, Any]]:
        """优化系统（使用 AI）"""
        if not self.iflow_manager:
            return None
        
        try:
            prompt = self.prompt_generator.generate_system_optimization_prompt(
                system_state, all_processes
            )
            
            response = await self.iflow_manager.call_iflow(prompt)
            return response
        except Exception as e:
            print(f"[AI 系统优化] 优化失败: {e}")
            return None
    
    async def analyze_errors(
        self,
        process_type: str,
        error_logs: list,
        error_patterns: list
    ) -> Optional[Dict[str, Any]]:
        """分析错误（使用 AI）"""
        if not self.iflow_manager:
            return None
        
        try:
            prompt = self.prompt_generator.generate_error_analysis_prompt(
                process_type, error_logs, error_patterns
            )
            
            response = await self.iflow_manager.call_iflow(prompt)
            return response
        except Exception as e:
            print(f"[AI 错误分析] 分析失败: {e}")
            return None
    
    def clear_cache(self):
        """清空缓存"""
        self.health_cache.clear()
