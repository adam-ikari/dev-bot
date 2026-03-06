#!/usr/bin/env python3
"""
AI 守护进程 - 业务逻辑层（可变）

提供业务相关的规则、策略和扩展接口
这一层可以根据业务需求灵活调整
"""

import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from .core import CoreGuardian, RecoveryStrategy


class BusinessRule(ABC):
    """业务规则抽象基类"""
    
    @abstractmethod
    async def evaluate(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """评估是否需要特殊处理"""
        pass
    
    @abstractmethod
    async def execute(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """执行特殊处理"""
        pass


class MaxRestartRule(BusinessRule):
    """最大重启次数规则"""
    
    def __init__(self, threshold: int = 5):
        self.threshold = threshold
    
    async def evaluate(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """评估重启次数是否超过阈值"""
        restart_count = process_info.get("restart_count", 0)
        return restart_count >= self.threshold
    
    async def execute(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """执行：降低重启优先级或发送告警"""
        print(f"[业务层] {process_type} 重启次数达到阈值 {self.threshold}，发送告警")
        # 这里可以集成告警系统
        return True


class IdleTimeRule(BusinessRule):
    """空闲时间规则"""
    
    def __init__(self, max_idle_time: int = 300):
        self.max_idle_time = max_idle_time  # 最大空闲时间（秒）
    
    async def evaluate(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """评估进程是否空闲时间过长"""
        last_seen = process_info.get("last_seen")
        if not last_seen:
            return False
        
        import time
        idle_time = time.time() - last_seen
        return idle_time > self.max_idle_time
    
    async def execute(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """执行：记录空闲状态或触发检查"""
        import time
        idle_time = int(time.time() - process_info.get("last_seen", 0))
        print(f"[业务层] {process_type} 空闲时间过长（{idle_time}秒），记录状态")
        return True


class BusinessLogicLayer:
    """业务逻辑层（可变）
    
    提供业务相关的规则、策略和扩展接口
    """
    
    def __init__(self, core_guardian: CoreGuardian, config_file: Optional[Path] = None):
        self.core_guardian = core_guardian
        self.config_file = config_file
        self.config = {}
        
        # 业务规则列表
        self.business_rules: List[BusinessRule] = []
        
        # 自定义恢复策略
        self.custom_recovery_strategies: Dict[str, RecoveryStrategy] = {}
        
        # 加载配置
        if config_file and config_file.exists():
            self._load_config()
        
        # 初始化默认业务规则
        self._init_default_rules()
    
    def _load_config(self):
        """加载业务配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"[业务层] 已加载业务配置: {self.config_file}")
        except Exception as e:
            print(f"[业务层] 加载配置失败: {e}")
    
    def _init_default_rules(self):
        """初始化默认业务规则"""
        # 最大重启次数规则
        max_restart_threshold = self.config.get("max_restart_threshold", 5)
        self.add_rule(MaxRestartRule(max_restart_threshold))
        
        # 空闲时间规则
        max_idle_time = self.config.get("max_idle_time", 300)
        self.add_rule(IdleTimeRule(max_idle_time))
    
    def add_rule(self, rule: BusinessRule):
        """添加业务规则"""
        self.business_rules.append(rule)
        print(f"[业务层] 已添加业务规则: {rule.__class__.__name__}")
    
    def remove_rule(self, rule_class: type):
        """移除业务规则"""
        self.business_rules = [r for r in self.business_rules if not isinstance(r, rule_class)]
        print(f"[业务层] 已移除业务规则: {rule_class.__name__}")
    
    def set_custom_recovery_strategy(self, process_type: str, strategy: RecoveryStrategy):
        """设置自定义恢复策略"""
        self.custom_recovery_strategies[process_type] = strategy
        print(f"[业务层] 已为 {process_type} 设置自定义恢复策略")
    
    async def evaluate_and_execute_rules(self, process_type: str, process_info: Dict[str, Any]):
        """评估并执行业务规则"""
        for rule in self.business_rules:
            try:
                # 评估规则
                if await rule.evaluate(process_type, process_info):
                    # 执行规则
                    await rule.execute(process_type, process_info)
            except Exception as e:
                print(f"[业务层] 执行规则 {rule.__class__.__name__} 失败: {e}")
    
    async def get_recovery_strategy(self, process_type: str) -> Optional[RecoveryStrategy]:
        """获取恢复策略"""
        # 优先使用自定义策略
        if process_type in self.custom_recovery_strategies:
            return self.custom_recovery_strategies[process_type]
        
        # 使用默认策略
        return self.core_guardian.recovery_strategy
    
    def get_status(self) -> Dict[str, Any]:
        """获取业务层状态"""
        return {
            "rules": [rule.__class__.__name__ for rule in self.business_rules],
            "custom_strategies": list(self.custom_recovery_strategies.keys()),
            "config": self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新业务配置"""
        self.config.update(new_config)
        print(f"[业务层] 业务配置已更新")
        
        # 重新初始化规则
        self.business_rules.clear()
        self._init_default_rules()


class AIGuardian:
    """AI 守护进程（整合层）
    
    整合核心守护层和业务逻辑层，提供完整的守护功能
    """
    
    def __init__(
        self,
        check_interval: int = 30,
        config_file: Optional[Path] = None
    ):
        # 创建核心守护层
        self.core_guardian = CoreGuardian(
            check_interval=check_interval,
            on_status_update=self._on_status_update
        )
        
        # 创建业务逻辑层
        self.business_layer = BusinessLogicLayer(
            self.core_guardian,
            config_file
        )
        
        self.status_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
    
    def _on_status_update(self, status: Dict[str, Any]):
        """状态更新回调"""
        # 保存历史记录
        self.status_history.append({
            "timestamp": status.get("last_check_time"),
            "recovery_count": status.get("recovery_count"),
            "monitored_processes": len(status.get("monitored_processes", {}))
        })
        
        # 限制历史记录大小
        if len(self.status_history) > self.max_history_size:
            self.status_history = self.status_history[-self.max_history_size:]
    
    async def start(self):
        """启动 AI 守护进程"""
        print("[AI 守护] 启动 AI 守护进程...")
        
        # 启动核心守护层
        await self.core_guardian.start()
        
        print("[AI 守护] AI 守护进程已启动")
    
    async def stop(self):
        """停止 AI 守护进程"""
        print("[AI 守护] 停止 AI 守护进程...")
        
        # 停止核心守护层
        await self.core_guardian.stop()
        
        print("[AI 守护] AI 守护进程已停止")
    
    def register_process(
        self,
        process_type: str,
        pid: Optional[int],
        startup_command: List[str],
        max_restarts: int = 10
    ):
        """注册要监控的进程"""
        self.core_guardian.register_process(
            process_type,
            pid,
            startup_command,
            max_restarts
        )
    
    def update_process_status(self, process_type: str, pid: int):
        """更新进程状态"""
        self.core_guardian.update_process_status(process_type, pid)
    
    def add_business_rule(self, rule):
        """添加业务规则"""
        self.business_layer.add_rule(rule)
    
    def set_custom_recovery_strategy(self, process_type: str, strategy):
        """设置自定义恢复策略"""
        self.business_layer.set_custom_recovery_strategy(process_type, strategy)
    
    def get_status(self) -> Dict[str, Any]:
        """获取完整状态"""
        return {
            "core_guardian": self.core_guardian.get_status(),
            "business_layer": self.business_layer.get_status(),
            "status_history_count": len(self.status_history)
        }
    
    def get_process_status(self, process_type: str) -> Optional[Dict[str, Any]]:
        """获取特定进程的状态"""
        return self.core_guardian.get_process_status(process_type)