"""测试队列系统

测试问题队列、输入队列和 REPL 核心
"""
import pytest
import asyncio
from dev_bot.queue_manager import QuestionQueue, InputQueue, QuestionStatus, InputStatus


@pytest.mark.asyncio
async def test_question_queue_enqueue():
    """测试问题队列入队"""
    queue = QuestionQueue()

    question_id = await queue.enqueue("测试问题1", mode="--plan", priority=0)
    assert question_id.startswith("q_")

    question_id2 = await queue.enqueue("测试问题2", mode="-y", priority=1)
    assert question_id2.startswith("q_")
    assert question_id != question_id2

    status = await queue.get_status()
    assert status["total"] == 2
    assert status["pending"] == 2


@pytest.mark.asyncio
async def test_question_queue_dequeue():
    """测试问题队列出队"""
    queue = QuestionQueue()

    # 添加问题
    q1_id = await queue.enqueue("优先级0", priority=0)
    q2_id = await queue.enqueue("优先级1", priority=1)
    q3_id = await queue.enqueue("优先级0-2", priority=0)

    # 按优先级出队
    q1 = await queue.dequeue()
    assert q1.id == q1_id
    assert q1.status == QuestionStatus.PROCESSING

    q3 = await queue.dequeue()
    assert q3.id == q3_id  # 优先级相同，先入先出

    q2 = await queue.dequeue()
    assert q2.id == q2_id

    # 队列为空
    q_empty = await queue.dequeue()
    assert q_empty is None


@pytest.mark.asyncio
async def test_question_queue_update_result():
    """测试更新问题结果"""
    queue = QuestionQueue()

    question_id = await queue.enqueue("测试问题")
    await queue.dequeue()

    result = {"success": True, "output": "测试输出"}
    success = await queue.update_result(question_id, result, success=True)

    assert success is True

    status = await queue.get_status()
    assert status["completed"] == 1

    question_status = await queue.get_question_status(question_id)
    assert question_status is not None
    assert question_status["result"] == result


@pytest.mark.asyncio
async def test_question_queue_clear_completed():
    """测试清理已完成问题"""
    queue = QuestionQueue()

    q1_id = await queue.enqueue("问题1")
    q2_id = await queue.enqueue("问题2")
    q3_id = await queue.enqueue("问题3")

    await queue.dequeue()  # q1
    await queue.dequeue()  # q2

    await queue.update_result(q1_id, {"success": True})
    await queue.update_result(q2_id, {"success": False}, success=False, error="错误")

    cleared = await queue.clear_completed()
    assert cleared == 2

    status = await queue.get_status()
    assert status["total"] == 1  # 只剩 q3


@pytest.mark.asyncio
async def test_input_queue_request_and_provide():
    """测试输入队列请求和提供"""
    queue = InputQueue()

    input_id = await queue.request_input("q_1", "请输入密码")
    assert input_id.startswith("i_")

    # 提供输入
    success = await queue.provide_input(input_id, "123456")
    assert success is True

    status = await queue.get_status()
    assert status["total"] == 1
    assert status["provided"] == 1


@pytest.mark.asyncio
async def test_input_queue_consume():
    """测试输入队列消费"""
    queue = InputQueue()

    input_id = await queue.request_input("q_1", "请输入值")

    # 提供输入
    await queue.provide_input(input_id, "test_value")

    # 消费输入
    value = await queue.consume_input(input_id)
    assert value == "test_value"

    status = await queue.get_status()
    assert status["consumed"] == 1


@pytest.mark.asyncio
async def test_input_queue_wait_for_input():
    """测试等待输入"""
    queue = InputQueue()

    input_id = await queue.request_input("q_1", "请输入值")

    # 在另一个任务中提供输入
    async def provide_after_delay():
        await asyncio.sleep(0.1)
        await queue.provide_input(input_id, "delayed_value")

    asyncio.create_task(provide_after_delay())

    # 等待输入
    value = await queue.wait_for_input(input_id, timeout=1.0)
    assert value == "delayed_value"


@pytest.mark.asyncio
async def test_input_queue_wait_timeout():
    """测试等待输入超时"""
    queue = InputQueue()

    input_id = await queue.request_input("q_1", "请输入值")

    # 不提供输入，等待超时
    value = await queue.wait_for_input(input_id, timeout=0.1)
    assert value is None


@pytest.mark.asyncio
async def test_input_queue_clear_consumed():
    """测试清理已消费输入"""
    queue = InputQueue()

    i1_id = await queue.request_input("q_1", "输入1")
    i2_id = await queue.request_input("q_2", "输入2")

    await queue.provide_input(i1_id, "value1")
    await queue.provide_input(i2_id, "value2")

    await queue.consume_input(i1_id)
    await queue.consume_input(i2_id)

    cleared = await queue.clear_consumed()
    assert cleared == 2

    status = await queue.get_status()
    assert status["total"] == 0


@pytest.mark.asyncio
async def test_repl_core_submit_and_process():
    """测试 REPL 核心提交和处理问题"""
    from dev_bot.repl_core import REPLCore

    repl = REPLCore()
    await repl.start()

    # 提交问题（模拟）
    question_id = await repl.submit_question("测试提示词", mode="--plan")

    # 检查队列状态
    status = await repl.get_queue_status()
    assert status["question_queue"]["pending"] >= 1

    # 获取问题状态
    question_status = await repl.get_question_status(question_id)
    assert question_status is not None
    assert question_status["prompt"] == "测试提示词"

    await repl.stop()


@pytest.mark.asyncio
async def test_repl_core_input_management():
    """测试 REPL 核心输入管理"""
    from dev_bot.repl_core import REPLCore

    repl = REPLCore()
    await repl.start()

    # 请求输入
    input_id = await repl.request_input("q_1", "请输入值")

    # 提供输入
    success = await repl.provide_input(input_id, "test_value")
    assert success is True

    # 等待输入
    value = await repl.wait_for_input(input_id, timeout=1.0)
    assert value == "test_value"

    await repl.stop()


@pytest.mark.asyncio
async def test_repl_core_clear_completed():
    """测试 REPL 核心清理已完成任务"""
    from dev_bot.repl_core import REPLCore

    repl = REPLCore()
    await repl.start()

    # 提交问题
    q1_id = await repl.submit_question("问题1")
    q2_id = await repl.submit_question("问题2")

    # 模拟处理完成
    await repl.question_queue.dequeue()
    await repl.question_queue.update_result(q1_id, {"success": True})

    await repl.question_queue.dequeue()
    await repl.question_queue.update_result(q2_id, {"success": True})

    # 清理
    cleared = await repl.clear_completed()
    assert cleared["questions"] == 2

    await repl.stop()


def test_question_dataclass():
    """测试 Question 数据类"""
    from dev_bot.queue_manager import Question

    question = Question(
        id="q_1",
        prompt="测试",
        mode="--plan",
        priority=0
    )

    assert question.id == "q_1"
    assert question.status == QuestionStatus.PENDING

    data = question.to_dict()
    assert data["id"] == "q_1"
    assert data["status"] == "pending"


def test_input_item_dataclass():
    """测试 InputItem 数据类"""
    from dev_bot.queue_manager import InputItem

    input_item = InputItem(
        id="i_1",
        question_id="q_1",
        prompt="请输入"
    )

    assert input_item.id == "i_1"
    assert input_item.status == InputStatus.PENDING

    data = input_item.to_dict()
    assert data["id"] == "i_1"
    assert data["status"] == "pending"