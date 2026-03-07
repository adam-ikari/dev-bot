#!/usr/bin/env python3
"""记忆系统 - AI 决策持久化"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class MemorySystem:
    """记忆系统 - 管理长期记忆和上下文"""
    
    def __init__(self, memory_dir: str = ".dev-bot-memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.context_file = self.memory_dir / "context.json"
        self.history_file = self.memory_dir / "history.json"
    
    def load_context(self) -> Dict[str, Any]:
        """加载上下文"""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告: 无法加载上下文: {e}")
                return self._default_context()
        return self._default_context()
    
    def save_context(self, context: Dict[str, Any]) -> None:
        """保存上下文"""
        try:
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(context, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"错误: 无法保存上下文: {e}")
    
    def load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告: 无法加载历史记录: {e}")
                return []
        return []
    
    def save_history(self, history: List[Dict[str, Any]]) -> None:
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"错误: 无法保存历史记录: {e}")
    
    def add_history_entry(self, entry_type: str, content: str, result: str = "") -> None:
        """添加历史记录"""
        history = self.load_history()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": entry_type,
            "content": content[:500],  # 限制长度
            "result": result[:500] if result else ""
        }
        history.append(entry)
        
        # 只保留最近 100 条记录
        if len(history) > 100:
            history = history[-100:]
        
        self.save_history(history)
    
    def update_context(self, key: str, value: Any) -> None:
        """更新上下文"""
        context = self.load_context()
        context[key] = value
        context["last_updated"] = datetime.now().isoformat()
        self.save_context(context)
    
    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        context = self.load_context()
        history = self.load_history()
        
        summary = []
        summary.append("## 项目上下文")
        
        if "project_info" in context:
            summary.append(f"- 项目信息: {context['project_info']}")
        
        if "tech_stack" in context:
            summary.append(f"- 技术栈: {context['tech_stack']}")
        
        if "learnings" in context and context["learnings"]:
            summary.append(f"\n## 学到的经验 ({len(context['learnings'])} 条)")
            for i, learning in enumerate(context["learnings"][-5:], 1):
                summary.append(f"{i}. {learning}")
        
        if history:
            summary.append(f"\n## 最近活动 ({len(history)} 条)")
            for entry in history[-3:]:
                summary.append(f"- [{entry['type']}] {entry['timestamp'][:19]}")
        
        return "\n".join(summary)
    
    def _default_context(self) -> Dict[str, Any]:
        """默认上下文"""
        return {
            "project_info": "",
            "tech_stack": [],
            "learnings": [],
            "decisions": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def clear_memory(self) -> None:
        """清空记忆"""
        if self.context_file.exists():
            self.context_file.unlink()
        if self.history_file.exists():
            self.history_file.unlink()


# 全局实例
_memory_system = None


def get_memory_system() -> MemorySystem:
    """获取记忆系统实例"""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
    return _memory_system


def load_memory() -> Dict[str, Any]:
    """加载记忆（便捷函数）"""
    return get_memory_system().load_context()


def save_memory(memory: Dict[str, Any]) -> None:
    """保存记忆（便捷函数）"""
    get_memory_system().save_context(memory)


def get_memory_summary() -> str:
    """获取记忆摘要（便捷函数）"""
    return get_memory_system().get_context_summary()
