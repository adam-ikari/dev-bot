#!/usr/bin/env python3
"""
提示词生成器

为不同的守护场景生成结构化提示词
"""

from pathlib import Path
from typing import Dict, Any, List, Optional


class PromptGenerator:
    """提示词生成器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
    
    def generate_health_check_prompt(
        self,
        process_type: str,
        pid: Optional[int],
        process_stats: Dict[str, Any],
        resource_usage: Dict[str, Any]
    ) -> str:
        """生成健康检查提示词"""
        prompt = f"""评估 {process_type} 进程的健康状况。

进程信息：
- PID: {pid}
- 运行时间: {process_stats.get('uptime', 'unknown')}秒
- 状态: {process_stats.get('status', 'unknown')}
- 重启次数: {process_stats.get('restart_count', 0)}

资源使用：
- CPU: {resource_usage.get('cpu_percent', 0)}%
- 内存: {resource_usage.get('memory_percent', 0)}%
- 线程数: {resource_usage.get('num_threads', 0)}
- 文件描述符: {resource_usage.get('num_fds', 0)}

请以 JSON 格式返回健康评估结果：
{{
  "health_status": "healthy/warning/critical",
  "health_score": 0-100,
  "issues": ["问题1", "问题2"],
  "recommendations": ["建议1", "建议2"],
  "action_required": true/false
}}
"""
        return prompt
    
    def generate_anomaly_detection_prompt(
        self,
        process_type: str,
        current_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        anomalies: List[Dict[str, Any]]
    ) -> str:
        """生成异常检测提示词"""
        prompt = f"""分析 {process_type} 进程的异常模式。

当前指标：
{self._format_metrics(current_metrics)}

基准指标：
{self._format_metrics(baseline_metrics)}

检测到的异常：
{self._format_anomalies(anomalies)}

请以 JSON 格式返回异常分析结果：
{{
  "anomaly_type": "spike/drop/pattern_drift/unknown",
  "severity": "low/medium/high/critical",
  "root_cause": "根本原因分析",
  "potential_impact": "潜在影响",
  "immediate_actions": ["行动1", "行动2"],
  "preventive_measures": ["措施1", "措施2"],
  "needs_investigation": true/false
}}
"""
        return prompt
    
    def generate_performance_analysis_prompt(
        self,
        process_type: str,
        performance_data: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]]
    ) -> str:
        """生成性能分析提示词"""
        prompt = f"""分析 {process_type} 进程的性能瓶颈。

性能数据：
- 平均响应时间: {performance_data.get('avg_response_time', 'unknown')}ms
- 95th 响应时间: {performance_data.get('p95_response_time', 'unknown')}ms
- 99th 响应时间: {performance_data.get('p99_response_time', 'unknown')}ms
- 吞吐量: {performance_data.get('throughput', 'unknown')} req/s
- 错误率: {performance_data.get('error_rate', 0)}%

检测到的瓶颈：
{self._format_bottlenecks(bottlenecks)}

请以 JSON 格式返回性能分析结果：
{{
  "bottleneck_type": "cpu/memory/i_o/network/algorithm",
  "bottleneck_source": "瓶颈来源",
  "optimization_priority": "low/medium/high/critical",
  "optimization_suggestions": [
    {{"technique": "技术", "expected_improvement": "预期提升", "complexity": "low/medium/high"}},
    ...
  ],
  "code_optimizations": [{{"file": "file.py", "function": "func", "suggestion": "建议"}}],
  "config_tunings": [{{"parameter": "param", "current": "current", "recommended": "recommended"}}]
}}
"""
        return prompt
    
    def generate_predictive_analysis_prompt(
        self,
        process_type: str,
        historical_data: List[Dict[str, Any]],
        current_state: Dict[str, Any]
    ) -> str:
        """生成预测分析提示词"""
        prompt = f"""基于历史数据预测 {process_type} 进程的未来状态。

当前状态：
{self._format_metrics(current_state)}

历史数据摘要：
- 数据点数量: {len(historical_data)}
- 时间范围: {self._get_time_range(historical_data)}
- 平均正常运行时间: {self._calculate_avg_uptime(historical_data)}
- 平均重启间隔: {self._calculate_avg_restart_interval(historical_data)}

请以 JSON 格式返回预测分析结果：
{{
  "predicted_uptime_hours": 预测正常运行时间（小时）,
  "failure_probability": 0-1,
  "risk_level": "low/medium/high/critical",
  "predicted_failure_time": "预计失败时间",
  "proactive_actions": ["行动1", "行动2"],
  "monitoring_recommendations": ["建议1", "建议2"],
  "maintenance_windows": ["窗口1", "窗口2"]
}}
"""
        return prompt
    
    def generate_system_optimization_prompt(
        self,
        system_state: Dict[str, Any],
        all_processes: List[Dict[str, Any]]
    ) -> str:
        """生成系统优化提示词"""
        prompt = f"""分析整个系统的优化机会。

系统状态：
- 总进程数: {len(all_processes)}
- 总 CPU 使用: {system_state.get('total_cpu', 0)}%
- 总内存使用: {system_state.get('total_memory', 0)}%
- 总线程数: {system_state.get('total_threads', 0)}

进程列表：
{self._format_processes(all_processes)}

请以 JSON 格式返回系统优化建议：
{{
  "optimization_category": "resource_allocation/process_prioritization/caching/architecture",
  "priority_actions": [
    {{"action": "行动", "expected_gain": "预期收益", "effort": "low/medium/high"}}
  ],
  "resource_rebalancing": {{"process": "process", "current_allocation": "current", "optimal_allocation": "optimal"}},
  "process_prioritization": {{"high_priority": ["进程1", "进程2"], "low_priority": ["进程3", "进程4"]}},
  "system_wide_improvements": ["改进1", "改进2"]
}}
"""
        return prompt
    
    def generate_error_analysis_prompt(
        self,
        process_type: str,
        error_logs: List[Dict[str, Any]],
        error_patterns: List[str]
    ) -> str:
        """生成错误分析提示词"""
        prompt = f"""分析 {process_type} 进程的错误模式。

错误日志摘要：
- 总错误数: {len(error_logs)}
- 错误类型数量: {len(set(log.get('error_type') for log in error_logs))}

最近的错误：
{self._format_error_logs(error_logs[:5])}

检测到的错误模式：
{self._format_patterns(error_patterns)}

请以 JSON 格式返回错误分析结果：
{{
  "error_category": "code_logic/resource_dependency/configuration/external",
  "root_cause_analysis": "根本原因",
  "affected_components": ["组件1", "组件2"],
  "fix_strategies": [
    {{"strategy": "策略", "effectiveness": "有效性", "side_effects": "副作用"}}
  ],
  "prevention_measures": ["措施1", "措施2"],
  "code_changes_required": true/false,
  "test_recommendations": ["测试1", "测试2"]
}}
"""
        return prompt
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """格式化指标"""
        lines = []
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")
        return '\n'.join(lines)
    
    def _format_anomalies(self, anomalies: List[Dict[str, Any]]) -> str:
        """格式化异常"""
        if not anomalies:
            return "无异常"
        lines = []
        for i, anomaly in enumerate(anomalies[:5], 1):
            lines.append(f"{i}. {anomaly.get('metric', 'unknown')}: {anomaly.get('description', 'unknown')}")
        return '\n'.join(lines)
    
    def _format_bottlenecks(self, bottlenecks: List[Dict[str, Any]]) -> str:
        """格式化瓶颈"""
        if not bottlenecks:
            return "无瓶颈"
        lines = []
        for i, bottleneck in enumerate(bottlenecks[:5], 1):
            lines.append(f"{i}. {bottleneck.get('component', 'unknown')}: {bottleneck.get('issue', 'unknown')}")
        return '\n'.join(lines)
    
    def _format_processes(self, processes: List[Dict[str, Any]]) -> str:
        """格式化进程列表"""
        lines = []
        for i, proc in enumerate(processes[:10], 1):
            lines.append(f"{i}. {proc.get('process_type', 'unknown')} (PID: {proc.get('pid', 'unknown')}, CPU: {proc.get('cpu', 0)}%)")
        return '\n'.join(lines)
    
    def _format_error_logs(self, error_logs: List[Dict[str, Any]]) -> str:
        """格式化错误日志"""
        lines = []
        for log in error_logs:
            lines.append(f"- [{log.get('timestamp', 'unknown')}] {log.get('error_type', 'unknown')}: {log.get('message', 'unknown')[:100]}")
        return '\n'.join(lines)
    
    def _format_patterns(self, patterns: List[str]) -> str:
        """格式化模式"""
        if not patterns:
            return "无模式"
        lines = []
        for i, pattern in enumerate(patterns[:5], 1):
            lines.append(f"{i}. {pattern}")
        return '\n'.join(lines)
    
    def _get_time_range(self, data: List[Dict[str, Any]]) -> str:
        """获取时间范围"""
        if not data:
            return "无数据"
        timestamps = [d.get('timestamp', 0) for d in data if 'timestamp' in d]
        if not timestamps:
            return "无时间戳"
        return f"{min(timestamps)} - {max(timestamps)}"
    
    def _calculate_avg_uptime(self, data: List[Dict[str, Any]]) -> str:
        """计算平均正常运行时间"""
        if not data:
            return "无数据"
        uptimes = [d.get('uptime', 0) for d in data if 'uptime' in d]
        if not uptimes:
            return "无正常运行时间数据"
        return f"{sum(uptimes) / len(uptimes):.2f}秒"
    
    def _calculate_avg_restart_interval(self, data: List[Dict[str, Any]]) -> str:
        """计算平均重启间隔"""
        if not data:
            return "无数据"
        intervals = [d.get('restart_interval', 0) for d in data if 'restart_interval' in d]
        if not intervals:
            return "无重启间隔数据"
        return f"{sum(intervals) / len(intervals):.2f}秒"
    
    def generate_custom_prompt(
        self,
        task_description: str,
        context: Dict[str, Any],
        expected_output_format: str
    ) -> str:
        """生成自定义提示词"""
        prompt = f"""{task_description}

上下文信息：
{self._format_metrics(context)}

请以以下格式返回结果：
{expected_output_format}
"""
        return prompt