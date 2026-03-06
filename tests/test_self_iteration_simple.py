"""测试极简自我迭代系统"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from dev_bot.self_iteration_simple import SimpleSelfIteration, IterationContext


@pytest.fixture
def iteration(tmp_path):
    """创建迭代系统实例"""
    return SimpleSelfIteration(tmp_path)


@pytest.mark.asyncio
async def test_collect_context(iteration):
    """测试收集上下文"""
    # Mock 子进程执行
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_exec.return_value = mock_process
        
        context = await iteration._collect_context()
        
        assert context is not None
        assert context.iteration_id.startswith("iter_")
        assert context.timestamp > 0


@pytest.mark.asyncio
async def test_ai_analyze_and_decide(iteration):
    """测试 AI 分析和决策"""
    context = IterationContext(
        iteration_id="test_1",
        timestamp=1234567890.0,
        test_results={"returncode": 0},
        code_coverage=50.0,
        error_count=5,
        recent_changes=[],
        git_status={"dirty": False},
        system_metrics={}
    )
    
    # Mock core.call_iflow
    with patch.object(iteration.core, 'call_iflow') as mock_call:
        mock_call.return_value = {
            "success": True,
            "output": '''{
                "analysis": "测试通过但覆盖率低",
                "problem": "代码覆盖率不足",
                "action": "add_tests",
                "steps": ["为关键模块添加测试", "运行测试验证"],
                "expected_outcome": "覆盖率提升"
            }'''
        }
        
        decision = await iteration.ai_analyze_and_decide(context)
        
        assert decision["analysis"] == "测试通过但覆盖率低"
        assert decision["problem"] == "代码覆盖率不足"
        assert decision["action"] == "add_tests"
        assert len(decision["steps"]) == 2


@pytest.mark.asyncio
async def test_ai_execute_skip(iteration):
    """测试执行跳过"""
    decision = {
        "analysis": "无需改进",
        "action": "skip",
        "steps": []
    }
    
    result = await iteration.ai_execute(decision)
    
    assert result["success"] is True
    assert len(result["steps_completed"]) == 0


@pytest.mark.asyncio
async def test_ai_execute_with_steps(iteration):
    """测试执行步骤"""
    decision = {
        "analysis": "需要修复测试",
        "action": "fix_tests",
        "steps": ["修复失败的测试用例"]
    }
    
    # Mock core.call_iflow
    with patch.object(iteration.core, 'call_iflow') as mock_call:
        mock_call.return_value = {
            "success": True,
            "output": "测试已修复"
        }
        
        result = await iteration.ai_execute(decision)
        
        assert result["success"] is True
        assert len(result["steps_completed"]) == 1
        assert len(result["changes"]) == 1


@pytest.mark.asyncio
async def test_verify(iteration):
    """测试验证"""
    context = IterationContext(
        iteration_id="test_1",
        timestamp=1234567890.0,
        test_results={"returncode": 1},
        code_coverage=40.0,
        error_count=10,
        recent_changes=[],
        git_status={"dirty": False},
        system_metrics={}
    )
    
    # Mock 子进程执行
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"TOTAL 100 0 45%\n", b""))
        mock_exec.return_value = mock_process
        
        result = await iteration.verify(context)
        
        assert result["success"] is True
        assert result["new_coverage"] == 45.0
        assert result["improvements"]["coverage_improved"] is True


@pytest.mark.asyncio
async def test_run_iteration(iteration):
    """测试完整迭代"""
    context = IterationContext(
        iteration_id="test_1",
        timestamp=1234567890.0,
        test_results={"returncode": 1},
        code_coverage=40.0,
        error_count=10,
        recent_changes=[],
        git_status={"dirty": False},
        system_metrics={}
    )
    
    # Mock 所有方法
    with patch.object(iteration, '_collect_context', return_value=context):
        with patch.object(iteration, 'ai_analyze_and_decide') as mock_analyze:
            mock_analyze.return_value = {
                "analysis": "测试失败",
                "action": "fix_tests",
                "steps": ["修复测试"]
            }
            
            with patch.object(iteration, 'ai_execute') as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "steps_completed": ["修复测试"],
                    "steps_failed": [],
                    "changes": [],
                    "errors": []
                }
                
                with patch.object(iteration, 'verify') as mock_verify:
                    mock_verify.return_value = {
                        "success": True,
                        "improvements": {"coverage_improved": True}
                    }
                    
                    result = await iteration.run_iteration()
                    
                    assert result["iteration_id"] == "test_1"
                    assert result["decision"]["action"] == "fix_tests"
                    assert result["execution"]["success"] is True
                    assert result["verification"]["success"] is True


def test_stop(iteration):
    """测试停止"""
    assert iteration.is_running is False
    
    iteration.is_running = True
    iteration.stop()
    
    assert iteration.is_running is False