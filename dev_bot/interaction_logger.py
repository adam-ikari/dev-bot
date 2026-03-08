#!/usr/bin/env python3
"""AI 交互日志记录器 - 记录所有 AI 交互"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class InteractionLogger:
    """AI 交互日志记录器"""
    
    def __init__(self, log_file: str = "ai_interactions.log"):
        self.log_file = log_file
        self.entries: List[Dict] = []
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """确保日志文件存在"""
        Path(self.log_file).touch(exist_ok=True)
    
    def log_interaction(
        self,
        prompt: str,
        response: str,
        duration: float,
        prompt_updated: bool = False,
        code_modified: bool = False,
        status: str = "success"
    ):
        """记录一次 AI 交互
        
        Args:
            prompt: 提示词
            response: 响应
            duration: 持续时间（秒）
            prompt_updated: 提示词是否被更新
            code_modified: 代码是否被修改
            status: 状态
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "iteration": len(self.entries) + 1,
            "prompt": prompt,
            "response": response,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "duration": duration,
            "status": status,
            "prompt_updated": prompt_updated,
            "code_modified": code_modified
        }
        
        self.entries.append(entry)
        self._write_entry(entry)
        
        logger.info(f"📝 AI 交互 #{entry['iteration']}: "
                   f"prompt={entry['prompt_length']} chars, "
                   f"response={entry['response_length']} chars, "
                   f"duration={duration:.2f}s")
    
    def _write_entry(self, entry: Dict):
        """写入日志文件"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"写入 AI 日志失败: {e}")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.entries:
            return {}
        
        total_duration = sum(e["duration"] for e in self.entries)
        total_tokens = sum(e["prompt_length"] + e["response_length"] for e in self.entries)
        
        return {
            "total_interactions": len(self.entries),
            "total_duration": total_duration,
            "total_tokens": total_tokens,
            "avg_duration": total_duration / len(self.entries),
            "avg_tokens": total_tokens / len(self.entries),
            "prompt_updates": sum(1 for e in self.entries if e["prompt_updated"]),
            "code_modifications": sum(1 for e in self.entries if e["code_modified"]),
            "success_rate": sum(1 for e in self.entries if e["status"] == "success") / len(self.entries) * 100
        }
    
    def get_recent_entries(self, limit: int = 10) -> List[Dict]:
        """获取最近的日志条目"""
        return self.entries[-limit:]
    
    def clear(self):
        """清空日志"""
        self.entries = []
        Path(self.log_file).write_text("", encoding="utf-8")
        logger.info("🗑️ AI 交互日志已清空")


def view_interaction_logs(log_file: str = "ai_interactions.log", limit: int = 10):
    """查看最近的 AI 交互日志
    
    Args:
        log_file: 日志文件路径
        limit: 显示条数
    """
    entries = []
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    except FileNotFoundError:
        print(f"日志文件不存在: {log_file}")
        return
    
    # 显示最近的记录
    for entry in entries[-limit:]:
        print(f"\n{'='*60}")
        print(f"迭代 {entry['iteration']} ({entry['timestamp']})")
        print(f"{'='*60}")
        print(f"持续时间: {entry['duration']:.2f}s")
        print(f"提示词长度: {entry['prompt_length']} 字符")
        print(f"响应长度: {entry['response_length']} 字符")
        print(f"状态: {entry['status']}")
        print(f"提示词更新: {'是' if entry['prompt_updated'] else '否'}")
        print(f"代码修改: {'是' if entry['code_modified'] else '否'}")
        print(f"\n响应预览:")
        print(entry['response'][:200] + "..." if len(entry['response']) > 200 else entry['response'])


def analyze_interaction_logs(log_file: str = "ai_interactions.log"):
    """分析 AI 交互日志
    
    Args:
        log_file: 日志文件路径
    """
    entries = []
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    except FileNotFoundError:
        print(f"日志文件不存在: {log_file}")
        return
    
    if not entries:
        print("没有日志记录")
        return
    
    # 统计
    total = len(entries)
    prompt_updates = sum(1 for e in entries if e["prompt_updated"])
    code_modifications = sum(1 for e in entries if e["code_modified"])
    successful = sum(1 for e in entries if e["status"] == "success")
    
    total_duration = sum(e["duration"] for e in entries)
    total_tokens = sum(e["prompt_length"] + e["response_length"] for e in entries)
    
    print(f"\n{'='*60}")
    print("AI 交互日志分析")
    print(f"{'='*60}")
    print(f"总交互次数: {total}")
    print(f"提示词更新次数: {prompt_updates} ({prompt_updates/total*100:.1f}%)")
    print(f"代码修改次数: {code_modifications} ({code_modifications/total*100:.1f}%)")
    print(f"成功率: {successful/total*100:.1f}%")
    print(f"平均持续时间: {total_duration/total:.2f}s")
    print(f"总持续时间: {total_duration:.2f}s")
    print(f"平均 token 数: {total_tokens/total:.0f}")
    print(f"总 token 数: {total_tokens:.0f}")
    print(f"{'='*60}")