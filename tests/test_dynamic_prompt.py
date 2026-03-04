#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试动态提示词功能
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dev_bot.core import DevBotCore, AIOrchestrator


@pytest.fixture
def test_project_root(tmp_path):
    """创建测试项目根目录"""
    return tmp_path


@pytest.fixture
def dev_bot_core(test_project_root):
    """创建 DevBotCore 实例"""
    # 创建日志目录
    log_dir = test_project_root / ".ai-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 DevBotCore
    core = DevBotCore(test_project_root)
    # 设置 AIOrchestrator 的日志目录
    core.ai.log_dir = log_dir
    
    return core


def test_dynamic_prompt_initialization(dev_bot_core):
    """测试动态提示词初始化"""
    assert dev_bot_core.prompt_modification is None
    assert dev_bot_core.prompt_modification_type is None
    assert dev_bot_core.prompt_modification_context is None


def test_build_prompt_with_dynamic_prompt(dev_bot_core):
    """测试使用动态提示词构建提示词"""
    # 设置动态提示词修改内容
    dev_bot_core.prompt_modification = "这是一个对提示词的修改"
    dev_bot_core.prompt_modification_type = "fix"
    dev_bot_core.prompt_modification_context = "修复登录功能的错误"
    
    prompt = dev_bot_core._build_prompt("", [])
    
    # 应该包含基础提示词和修改内容
    assert "你是 Dev-Bot 的 AI 开发助手" in prompt
    assert "## 修改或补充要求" in prompt
    assert "这是一个对提示词的修改" in prompt
    assert "修复登录功能的错误" in prompt


def test_build_prompt_without_dynamic_prompt(dev_bot_core):
    """测试不使用动态提示词构建提示词"""
    dev_bot_core.prompt_modification = None
    
    prompt = dev_bot_core._build_prompt("", [])
    
    # 应该只包含基础提示词
    assert "你是 Dev-Bot 的 AI 开发助手" in prompt
    assert "## 任务" in prompt
    # 不应该包含修改内容
    assert "## 修改或补充要求" not in prompt


def test_build_prompt_with_user_inputs(dev_bot_core):
    """测试包含用户输入的提示词构建"""
    dev_bot_core.prompt_modification = "动态修改内容"
    user_inputs = ["修复错误", "添加测试"]
    
    prompt = dev_bot_core._build_prompt("", user_inputs)
    
    # 应该包含基础提示词、用户输入和修改内容
    assert "你是 Dev-Bot 的 AI 开发助手" in prompt
    assert "- 修复错误" in prompt
    assert "- 添加测试" in prompt
    assert "## 修改或补充要求" in prompt
    assert "动态修改内容" in prompt


@patch('dev_bot.ai_prompts.get_decision_prompt')
def test_analyze_and_decide_updates_dynamic_prompt(
    mock_get_prompt, dev_bot_core
):
    """测试决策后更新动态提示词"""
    # Mock 决策提示词
    mock_get_prompt.return_value = "决策提示词"
    
    # Mock AI 决策响应
    mock_decision = json.dumps({
        'analysis': '测试分析',
        'is_reasonable': True,
        'action': 'none',
        'action_description': '继续',
        'should_stop': False,
        'should_rerun': False,
        'reason': '需要继续',
        'next_prompt': '修复登录功能的密码验证错误',
        'next_prompt_type': 'fix',
        'next_context': '密码验证逻辑存在问题'
    })
    
    with patch.object(dev_bot_core.ai, 'call_ai', return_value=mock_decision):
        decision = dev_bot_core._analyze_and_decide("AI 输出内容")
    
    # 验证动态提示词已更新
    assert dev_bot_core.prompt_modification == "修复登录功能的密码验证错误"
    assert dev_bot_core.prompt_modification_type == "fix"
    assert dev_bot_core.prompt_modification_context == "密码验证逻辑存在问题"
    
    # 验证决策返回
    assert decision['action'] == 'none'
    assert decision['next_prompt'] == "修复登录功能的密码验证错误"


@patch('dev_bot.ai_prompts.get_decision_prompt')
def test_analyze_and_decide_clears_dynamic_prompt(
    mock_get_prompt, dev_bot_core
):
    """测试决策后清空动态提示词"""
    # 设置初始修改内容
    dev_bot_core.prompt_modification = "之前的修改内容"
    dev_bot_core.prompt_modification_type = "fix"
    
    # Mock 决策提示词
    mock_get_prompt.return_value = "决策提示词"
    
    # Mock AI 决策响应（没有 next_prompt）
    mock_decision = json.dumps({
        'analysis': '测试分析',
        'is_reasonable': True,
        'action': 'stop',
        'action_description': '任务完成',
        'should_stop': True,
        'should_rerun': False,
        'reason': '任务已完成'
    })
    
    with patch.object(dev_bot_core.ai, 'call_ai', return_value=mock_decision):
        decision = dev_bot_core._analyze_and_decide("AI 输出内容")
    
    # 验证动态提示词已清空
    assert dev_bot_core.prompt_modification is None
    assert dev_bot_core.prompt_modification_type is None
    assert dev_bot_core.prompt_modification_context is None
    
    # 验证决策返回
    assert decision['action'] == 'stop'


def test_dynamic_prompt_types(dev_bot_core):
    """测试不同类型的动态提示词"""
    prompt_types = [
        ('continue', '继续当前任务'),
        ('fix', '修复错误'),
        ('implement', '实现新功能'),
        ('review', '代码审查'),
        ('test', '运行测试'),
        ('custom', '自定义任务')
    ]
    
    for prompt_type, prompt_text in prompt_types:
        dev_bot_core.prompt_modification = prompt_text
        dev_bot_core.prompt_modification_type = prompt_type
        
        prompt = dev_bot_core._build_prompt("", [])
        
        # 应该包含基础提示词和修改内容
        assert "你是 Dev-Bot 的 AI 开发助手" in prompt
        assert "## 修改或补充要求" in prompt
        assert prompt_text in prompt


def test_build_prompt_preserves_base_content(dev_bot_core):
    """测试构建提示词时保留基础内容"""
    dev_bot_core.prompt_modification = "添加新要求"
    spec_content = "Spec 内容示例"
    user_inputs = ["用户指令"]
    
    prompt = dev_bot_core._build_prompt(spec_content, user_inputs)
    
    # 验证所有内容都存在
    assert "你是 Dev-Bot 的 AI 开发助手" in prompt
    assert "Spec 内容示例" in prompt
    assert "- 用户指令" in prompt
    assert "## 修改或补充要求" in prompt
    assert "添加新要求" in prompt


if __name__ == '__main__':
    pytest.main([__file__, '-v'])