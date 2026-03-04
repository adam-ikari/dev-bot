#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 Spec 和代码一致性分析功能
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dev_bot.core import AIOrchestrator, REPLManager, SpecManager


@pytest.fixture
def test_project_root(tmp_path):
    """创建测试项目根目录"""
    return tmp_path


@pytest.fixture
def spec_manager(test_project_root):
    """创建 SpecManager 实例"""
    return SpecManager(test_project_root)


@pytest.fixture
def ai_orchestrator(tmp_path):
    """创建 AIOrchestrator 实例"""
    # 创建临时日志目录
    log_dir = tmp_path / ".ai-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 AIOrchestrator 并指定日志目录
    return AIOrchestrator(log_dir=log_dir)


@pytest.fixture
def sample_spec(test_project_root):
    """创建示例 Spec 文件"""
    spec_data = {
        "spec_version": "1.0",
        "metadata": {
            "name": "test-feature",
            "type": "feature",
            "description": "测试功能"
        },
        "requirements": [
            "用户可以登录",
            "用户可以登出"
        ],
        "features": [
            "登录功能",
            "登出功能"
        ]
    }
    
    spec_file = test_project_root / "specs" / "test-feature.json"
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        json.dump(spec_data, f, ensure_ascii=False, indent=2)
    
    return spec_file


def test_spec_manager_load_specs(spec_manager, sample_spec):
    """测试加载 Spec"""
    specs = spec_manager.load_specs()
    assert len(specs) == 1
    assert specs[0]['metadata']['name'] == 'test-feature'


def test_spec_manager_validate_specs(spec_manager, sample_spec):
    """测试验证 Spec"""
    result = spec_manager.validate_specs()
    assert result['total'] == 1
    assert result['valid'] == 1
    assert len(result['issues']) == 0


def test_spec_manager_get_spec_content_summary(spec_manager, sample_spec):
    """测试获取 Spec 内容摘要"""
    summary = spec_manager.get_spec_content_summary()
    assert 'test-feature' in summary
    assert 'feature' in summary
    assert '测试功能' in summary


def test_spec_manager_analyze_spec_code_consistency_no_specs(spec_manager, ai_orchestrator):
    """测试分析 Spec 和代码一致性 - 无 Spec"""
    result = spec_manager.analyze_spec_code_consistency(
        code_summary="代码摘要",
        ai_orchestrator=ai_orchestrator,
        tech_stack="Python"
    )
    assert result['is_consistent'] == True
    assert '没有 Spec 文件' in result['summary']


@patch('dev_bot.ai_prompts.get_spec_code_consistency_prompt')
def test_spec_manager_analyze_spec_code_consistency_with_ai(
    mock_get_prompt, spec_manager, ai_orchestrator, sample_spec
):
    """测试分析 Spec 和代码一致性 - 使用 AI"""
    # Mock AI 响应
    mock_ai_response = json.dumps({
        'is_consistent': False,
        'consistency_score': 0.7,
        'issues': [
            {
                'type': 'missing_feature',
                'severity': 'high',
                'spec_section': '登录功能',
                'code_location': '未找到',
                'description': 'Spec 中定义了登录功能，但代码中未实现',
                'suggested_action': 'modify_code'
            }
        ],
        'summary': '发现不一致',
        'recommendation': '实现登录功能'
    })
    
    with patch.object(ai_orchestrator, 'call_ai', return_value=mock_ai_response):
        result = spec_manager.analyze_spec_code_consistency(
            code_summary="代码摘要",
            ai_orchestrator=ai_orchestrator,
            tech_stack="Python"
        )
    
    assert result['is_consistent'] == False
    assert result['consistency_score'] == 0.7
    assert len(result['issues']) == 1
    assert result['issues'][0]['type'] == 'missing_feature'


def test_spec_manager_analyze_spec_code_consistency_ai_error(
    spec_manager, ai_orchestrator, sample_spec
):
    """测试分析 Spec 和代码一致性 - AI 调用失败"""
    with patch.object(ai_orchestrator, 'call_ai', return_value=None):
        result = spec_manager.analyze_spec_code_consistency(
            code_summary="代码摘要",
            ai_orchestrator=ai_orchestrator,
            tech_stack="Python"
        )
    
    assert result['is_consistent'] == True
    assert 'AI 调用失败' in result['summary']


def test_spec_manager_analyze_spec_code_consistency_json_error(
    spec_manager, ai_orchestrator, sample_spec
):
    """测试分析 Spec 和代码一致性 - JSON 解析失败"""
    with patch.object(ai_orchestrator, 'call_ai', return_value='invalid json'):
        result = spec_manager.analyze_spec_code_consistency(
            code_summary="代码摘要",
            ai_orchestrator=ai_orchestrator,
            tech_stack="Python"
        )
    
    assert result['is_consistent'] == True
    assert '无法解析分析结果' in result['summary']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])