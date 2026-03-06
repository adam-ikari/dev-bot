#!/usr/bin/env python3
"""
测试非阻塞 Spec 询问器
"""

import json
import tempfile
import time
from pathlib import Path

from dev_bot.nonblocking_inquirer import (
    NonBlockingSpecInquirer,
    SpecQuestion,
    create_spec_inquirer,
)


class TestSpecQuestion:
    """测试 SpecQuestion 类"""

    def test_question_creation(self):
        """测试问题创建"""
        question = SpecQuestion(
            question_id="test_1",
            question="测试问题",
            context="测试上下文",
            priority=3
        )

        assert question.question_id == "test_1"
        assert question.question == "测试问题"
        assert question.context == "测试上下文"
        assert question.priority == 3
        assert question.answer is None
        assert question.resolved is False
        assert question.acknowledged is False

    def test_question_timestamp(self):
        """测试问题时间戳"""
        before_time = time.time()
        question = SpecQuestion("test_1", "测试", "上下文")
        after_time = time.time()

        assert before_time <= question.timestamp <= after_time


class TestNonBlockingSpecInquirer:
    """测试 NonBlockingSpecInquirer 类"""

    def test_initialization_without_spec(self):
        """测试无 spec 文件初始化"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")
        assert inquirer.spec is None
        assert inquirer.is_running is False
        assert inquirer.question_queue.qsize() == 0
        assert len(inquirer.answered_questions) == 0

    def test_initialization_with_nonexistent_spec(self):
        """测试使用不存在的 spec 文件初始化"""
        inquirer = NonBlockingSpecInquirer(
            spec_file=Path("/nonexistent/spec.json"),
            ai_tool="test"
        )
        assert inquirer.spec is None

    def test_load_spec(self):
        """测试加载 spec 文件"""
        spec_data = {
            "metadata": {"type": "feature"},
            "requirements": [
                {"id": "req_1", "description": "需求1"}
            ],
            "user_stories": [
                {"requirement_id": "req_1", "story": "用户故事1"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec_data, f)
            spec_file = Path(f.name)

        try:
            inquirer = NonBlockingSpecInquirer(spec_file=spec_file, ai_tool="test")
            assert inquirer.spec is not None
            assert inquirer.spec["metadata"]["type"] == "feature"
            assert len(inquirer.spec["requirements"]) == 1
        finally:
            spec_file.unlink()

    def test_check_missing_parts_feature(self):
        """测试检查缺失部分 - feature 类型"""
        spec_data = {
            "metadata": {"type": "feature"},
            "requirements": [{"id": "req_1"}],
            # 缺少 user_stories 和 acceptance_criteria
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec_data, f)
            spec_file = Path(f.name)

        try:
            inquirer = NonBlockingSpecInquirer(spec_file=spec_file, ai_tool="test")
            missing = inquirer._check_missing_parts()

            assert "user_stories" in missing
            assert "acceptance_criteria" in missing
            assert "requirements" not in missing
        finally:
            spec_file.unlink()

    def test_check_missing_parts_api(self):
        """测试检查缺失部分 - API 类型"""
        spec_data = {
            "metadata": {"type": "api"},
            # 缺少 endpoints 和 models
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec_data, f)
            spec_file = Path(f.name)

        try:
            inquirer = NonBlockingSpecInquirer(spec_file=spec_file, ai_tool="test")
            missing = inquirer._check_missing_parts()

            assert "endpoints" in missing
            assert "models" in missing
        finally:
            spec_file.unlink()

    def test_check_incomplete_requirements(self):
        """测试检查不完整的需求"""
        spec_data = {
            "metadata": {"type": "feature"},
            "requirements": [
                {"id": "req_1", "description": "This is a complete requirement description that is long enough"},  # 完整
                {"id": "req_2", "description": "short"},  # 不完整
                {"id": "req_3", "description": ""},  # 空描述
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec_data, f)
            spec_file = Path(f.name)

        try:
            inquirer = NonBlockingSpecInquirer(spec_file=spec_file, ai_tool="test")
            incomplete = inquirer._check_incomplete_requirements()

            assert len(incomplete) == 2
            assert incomplete[0]["id"] == "req_2"
            assert incomplete[1]["id"] == "req_3"
        finally:
            spec_file.unlink()

    def test_check_requirements_without_stories(self):
        """测试检查缺少用户故事的需求"""
        spec_data = {
            "metadata": {"type": "feature"},
            "requirements": [
                {"id": "req_1"},
                {"id": "req_2"},
                {"id": "req_3"},
            ],
            "user_stories": [
                {"requirement_id": "req_1", "story": "故事1"},
                {"requirement_id": "req_2", "story": "故事2"},
                # req_3 缺少用户故事
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(spec_data, f)
            spec_file = Path(f.name)

        try:
            inquirer = NonBlockingSpecInquirer(spec_file=spec_file, ai_tool="test")
            missing = inquirer._check_requirements_without_stories()

            assert len(missing) == 1
            assert "req_3" in missing
        finally:
            spec_file.unlink()

    def test_add_question(self):
        """测试添加问题"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        inquirer._add_question(
            question_id="test_1",
            question="测试问题",
            context="上下文",
            priority=3
        )

        assert inquirer.question_queue.qsize() == 1

    def test_add_duplicate_question(self):
        """测试添加重复问题"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        # 添加相同问题两次
        inquirer._add_question("test_1", "问题1", "上下文", priority=3)
        inquirer._add_question("test_1", "问题1", "上下文", priority=3)

        # 应该只有一个问题
        assert inquirer.question_queue.qsize() == 1

    def test_get_pending_questions(self):
        """测试获取待处理问题"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        # 添加多个问题
        inquirer._add_question("test_1", "问题1", "上下文", priority=5)
        inquirer._add_question("test_2", "问题2", "上下文", priority=3)
        inquirer._add_question("test_3", "问题3", "上下文", priority=1)

        questions = inquirer.get_pending_questions(max_count=5)

        # 应该按优先级排序
        assert len(questions) == 3
        assert questions[0].priority == 5
        assert questions[1].priority == 3
        assert questions[2].priority == 1

    def test_get_pending_questions_with_limit(self):
        """测试获取待处理问题（带限制）"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        # 添加多个问题
        for i in range(5):
            inquirer._add_question(f"test_{i}", f"问题{i}", "上下文", priority=i)

        # 只获取前 3 个
        questions = inquirer.get_pending_questions(max_count=3)

        assert len(questions) == 3

    def test_acknowledge_question(self):
        """测试确认问题"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        inquirer._add_question("test_1", "问题1", "上下文", priority=3)
        inquirer.acknowledge_question("test_1")

        # 问题应该从队列移到已回答列表
        assert inquirer.question_queue.qsize() == 0
        assert len(inquirer.answered_questions) == 1
        assert inquirer.answered_questions[0].acknowledged is True

    def test_dismiss_question(self):
        """测试忽略问题"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        inquirer._add_question("test_1", "问题1", "上下文", priority=3)
        inquirer.dismiss_question("test_1")

        # 问题应该从队列移除，不在已回答列表中
        assert inquirer.question_queue.qsize() == 0
        assert len(inquirer.answered_questions) == 0

    def test_get_stats(self):
        """测试获取统计信息"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        inquirer._add_question("test_1", "问题1", "上下文", priority=3)
        inquirer.acknowledge_question("test_1")
        inquirer._add_question("test_2", "问题2", "上下文", priority=2)

        stats = inquirer.get_stats()

        assert stats["pending_questions"] == 1
        assert stats["answered_questions"] == 1
        assert stats["acknowledged_questions"] == 1
        assert stats["is_running"] is False

    def test_start_stop_analysis(self):
        """测试启动和停止分析"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        assert inquirer.is_running is False

        inquirer.start_analysis()
        assert inquirer.is_running is True

        inquirer.stop_analysis()
        assert inquirer.is_running is False

    def test_print_pending_questions_empty(self):
        """测试打印待处理问题（空）"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        # 不应该抛出异常
        inquirer.print_pending_questions()

    def test_print_pending_questions_with_questions(self):
        """测试打印待处理问题（有内容）"""
        inquirer = NonBlockingSpecInquirer(spec_file=None, ai_tool="test")

        inquirer._add_question("test_1", "高优先级问题", "上下文", priority=5)
        inquirer._add_question("test_2", "低优先级问题", "上下文", priority=1)

        # 不应该抛出异常
        inquirer.print_pending_questions()


class TestCreateSpecInquirer:
    """测试 create_spec_inquirer 函数"""

    def test_create_inquirer(self):
        """测试创建询问器"""
        inquirer = create_spec_inquirer(
            spec_file=Path("test.json"),
            ai_tool="test"
        )

        assert isinstance(inquirer, NonBlockingSpecInquirer)
        assert inquirer.ai_tool == "test"
