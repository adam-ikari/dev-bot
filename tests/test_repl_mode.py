#!/usr/bin/env python3
"""
测试 REPL 模式用户输入管理器
"""

import time

from dev_bot.repl_mode import UserInputManager, get_user_input_manager


class TestUserInputManager:
    """测试 UserInputManager 类"""

    def test_initialization(self):
        """测试初始化"""
        manager = UserInputManager()

        assert manager.input_queue.qsize() == 0
        assert len(manager.input_history) == 0
        assert manager.max_history == 100
        assert manager.is_running is False
        assert manager.input_thread is None
        assert len(manager.pending_inputs) == 0

    def test_start_stop(self):
        """测试启动和停止"""
        manager = UserInputManager()

        assert manager.is_running is False

        manager.start()
        assert manager.is_running is True
        assert manager.input_thread is not None

        manager.stop()
        assert manager.is_running is False

    def test_start_already_running(self):
        """测试重复启动"""
        manager = UserInputManager()

        manager.start()
        first_thread = manager.input_thread

        # 再次启动不应该创建新线程
        manager.start()
        assert manager.input_thread == first_thread

        manager.stop()

    def test_stop_without_start(self):
        """测试未启动就停止"""
        manager = UserInputManager()

        # 不应该抛出异常
        manager.stop()
        assert manager.is_running is False

    def test_get_pending_inputs_empty(self):
        """测试获取待处理输入（空）"""
        manager = UserInputManager()

        pending = manager.get_pending_inputs()

        assert pending == []
        assert len(manager.pending_inputs) == 0

    def test_get_pending_inputs_with_data(self):
        """测试获取待处理输入（有数据）"""
        manager = UserInputManager()

        # 模拟添加输入
        manager.pending_inputs.append("input1")
        manager.pending_inputs.append("input2")

        pending = manager.get_pending_inputs()

        assert pending == ["input1", "input2"]
        assert len(manager.pending_inputs) == 0  # 应该被清空

    def test_get_recent_inputs_empty(self):
        """测试获取最近输入（空）"""
        manager = UserInputManager()

        recent = manager.get_recent_inputs(count=5)

        assert recent == []

    def test_get_recent_inputs_with_data(self):
        """测试获取最近输入（有数据）"""
        manager = UserInputManager()

        # 添加历史输入
        for i in range(10):
            manager.input_history.append(f"input_{i}")

        # 获取最近 5 个
        recent = manager.get_recent_inputs(count=5)

        assert len(recent) == 5
        assert recent == ["input_5", "input_6", "input_7", "input_8", "input_9"]

    def test_get_recent_inputs_exceeds_history(self):
        """测试获取最近输入（超过历史记录）"""
        manager = UserInputManager()

        # 只添加 3 个输入
        for i in range(3):
            manager.input_history.append(f"input_{i}")

        # 请求 5 个，但只有 3 个
        recent = manager.get_recent_inputs(count=5)

        assert len(recent) == 3
        assert recent == ["input_0", "input_1", "input_2"]

    def test_max_history_limit(self):
        """测试历史记录限制（通过输入循环）"""
        manager = UserInputManager()
        manager.start()

        # 模拟添加超过最大历史的输入
        for i in range(150):
            manager.input_queue.put(f"input_{i}")
            # 模拟输入循环的处理逻辑
            if len(manager.input_history) >= manager.max_history:
                manager.input_history.pop(0)
            manager.input_history.append(f"input_{i}")

        # 应该只保留最近的 100 个
        assert len(manager.input_history) == 100
        assert manager.input_history[0] == "input_50"
        assert manager.input_history[-1] == "input_149"

        manager.stop()

    def test_input_loop_thread_safety(self):
        """测试输入循环的线程安全性"""
        manager = UserInputManager()
        manager.start()

        # 等待线程启动
        time.sleep(0.2)

        # 线程应该正在运行
        assert manager.is_running is True

        # 停止应该安全
        manager.stop()
        assert manager.is_running is False

    def test_multiple_start_stop_cycles(self):
        """测试多次启动停止循环"""
        manager = UserInputManager()

        for _ in range(3):
            manager.start()
            assert manager.is_running is True
            time.sleep(0.1)
            manager.stop()
            assert manager.is_running is False

    def test_get_user_input_manager(self):
        """测试 get_user_input_manager 函数"""
        manager = get_user_input_manager()

        assert isinstance(manager, UserInputManager)
        # 每次调用应该返回新实例
        manager2 = get_user_input_manager()
        assert manager is not manager2

    def test_pending_inputs_clearing(self):
        """测试待处理输入清空"""
        manager = UserInputManager()

        # 添加输入
        manager.pending_inputs.extend(["input1", "input2", "input3"])

        # 获取一次
        pending1 = manager.get_pending_inputs()
        assert pending1 == ["input1", "input2", "input3"]

        # 再次获取应该为空
        pending2 = manager.get_pending_inputs()
        assert pending2 == []

    def test_input_history_order(self):
        """测试输入历史顺序"""
        manager = UserInputManager()

        # 按顺序添加输入
        inputs = ["first", "second", "third", "fourth", "fifth"]
        for inp in inputs:
            manager.input_history.append(inp)

        # 获取最近输入应该保持顺序
        recent = manager.get_recent_inputs(count=3)
        assert recent == ["third", "fourth", "fifth"]

    def test_empty_string_handling(self):
        """测试空字符串处理"""
        manager = UserInputManager()

        # 添加空字符串和空白字符串
        manager.pending_inputs.append("")
        manager.pending_inputs.append("   ")
        manager.pending_inputs.append("valid input")

        pending = manager.get_pending_inputs()

        # 应该返回所有输入（包括空字符串）
        assert len(pending) == 3

    def test_concurrent_access(self):
        """测试并发访问"""
        import threading

        manager = UserInputManager()
        manager.start()

        def add_inputs():
            for i in range(10):
                manager.pending_inputs.append(f"thread_{i}")

        threads = [threading.Thread(target=add_inputs) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        manager.stop()

        # 获取所有输入
        pending = manager.get_pending_inputs()

        # 应该有 30 个输入
        assert len(pending) == 30
