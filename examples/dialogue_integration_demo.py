"""对话整合演示

演示如何使用 REPL、问题队列和 AI 对话系统进行交互
"""
import asyncio
from dev_bot.dialogue_integrator import DialogueIntegrator, get_dialogue_integrator
from dev_bot.queue_manager import QuestionQueue


async def demo_basic_dialogue():
    """演示基本对话流程"""
    print("\n=== 演示 1: 基本对话流程 ===\n")
    
    integrator = DialogueIntegrator()
    integrator._initialize()  # 初始化管理器
    
    # 创建任务
    task_id = await integrator.task_manager.enqueue(
        prompt="如何优化 Python 程序的性能？",
        mode="--plan",
        priority=0
    )
    print(f"✓ 任务已创建: {task_id}")
    
    # 从任务创建对话
    dialogue_id = await integrator.create_dialogue_from_queue(
        task_id=task_id,
        participants=["analyzer", "developer"]
    )
    print(f"✓ 对话已创建: {dialogue_id}")
    
    # 添加用户消息
    success = await integrator.add_user_message(
        content="我想了解具体的优化策略。",
        dialogue_id=dialogue_id
    )
    print(f"✓ 用户消息已发送: {success}")
    
    # 查看对话信息
    dialogue = await integrator.get_dialogue(dialogue_id)
    print(f"✓ 对话主题: {dialogue.topic}")
    print(f"✓ 对话参与者: {', '.join(dialogue.participants)}")
    print(f"✓ 消息数量: {len(dialogue.messages)}")


async def demo_multiple_dialogues():
    """演示多个对话管理"""
    print("\n=== 演示 2: 多个对话管理 ===\n")
    
    integrator = DialogueIntegrator()
    integrator._initialize()  # 初始化管理器
    
    # 创建多个对话
    dialogues = []
    topics = [
        "如何实现并发处理？",
        "数据库优化方案",
        "缓存策略设计"
    ]
    
    for topic in topics:
        task_id = await integrator.task_manager.enqueue(
            prompt=topic,
            mode="--plan",
            priority=0
        )
        dialogue_id = await integrator.create_dialogue_from_queue(
            task_id=task_id,
            participants=["analyzer", "developer", "tester"]
        )
        dialogues.append(dialogue_id)
        print(f"✓ 对话已创建: {dialogue_id} - {topic}")
    
    # 列出所有对话
    all_dialogues = await integrator.list_dialogues()
    print(f"\n✓ 当前共有 {len(all_dialogues)} 个对话")
    
    for dialogue in all_dialogues:
        print(f"  - {dialogue.dialogue_id}: {dialogue.topic}")


async def demo_user_interaction():
    """演示用户交互流程"""
    print("\n=== 演示 3: 用户交互流程 ===\n")
    
    integrator = DialogueIntegrator()
    integrator._initialize()  # 初始化管理器
    
    # 创建对话
    task_id = await integrator.task_manager.enqueue(
        prompt="设计一个 REST API",
        mode="--plan",
        priority=0
    )
    dialogue_id = await integrator.create_dialogue_from_queue(
        task_id=task_id,
        participants=["analyzer", "developer", "reviewer"]
    )
    
    print(f"✓ 对话已创建: {dialogue_id}")
    
    # 模拟用户交互
    user_messages = [
        "我需要支持用户认证。",
        "使用 JSON 格式返回数据。",
        "需要实现分页功能。"
    ]
    
    for i, message in enumerate(user_messages, 1):
        print(f"\n[用户] 发送消息 {i}: {message}")
        success = await integrator.add_user_message(
            content=message,
            dialogue_id=dialogue_id
        )
        print(f"✓ 消息发送: {success}")
        
        # 查看对话状态
        dialogue = await integrator.get_dialogue(dialogue_id)
        print(f"✓ 当前消息数: {len(dialogue.messages)}")
    
    print(f"\n✓ 用户交互完成，共发送 {len(user_messages)} 条消息")


async def demo_dialogue_status():
    """演示对话状态查询"""
    print("\n=== 演示 4: 对话状态查询 ===\n")
    
    integrator = DialogueIntegrator()
    integrator._initialize()  # 初始化管理器
    
    # 创建对话
    task_id = await integrator.task_manager.enqueue(
        prompt="代码重构建议",
        mode="--plan",
        priority=0
    )
    dialogue_id = await integrator.create_dialogue_from_queue(
        task_id=task_id,
        participants=["analyzer", "developer"]
    )
    
    # 添加一些消息
    await integrator.add_user_message(
        content="关注代码的可维护性。",
        dialogue_id=dialogue_id
    )
    
    # 获取对话状态
    status = await integrator.get_dialogue_status()
    
    print(f"✓ 当前对话 ID: {status['current_dialogue_id']}")
    print(f"✓ 对话管理器状态: {status['dialogue_manager_status']['total_dialogues']} 个对话")
    print(f"✓ 任务管理器状态: {status['task_manager_status']['total']} 个任务")


async def demo_tui_commands():
    """演示 TUI 命令"""
    print("\n=== 演示 5: TUI 命令 ===\n")
    
    print("在 TUI 中，用户可以使用以下命令：")
    print()
    print("1. 提交问题:")
    print("   dev-bot> 如何优化数据库查询？")
    print()
    print("2. 从任务创建对话:")
    print("   dev-bot> dialogue create q_1_1234567890 analyzer developer")
    print()
    print("3. 发送消息到对话:")
    print("   dev-bot> dialogue send dialogue_1234567890_0 我需要更详细的解释")
    print()
    print("4. 查看对话信息:")
    print("   dev-bot> dialogue info dialogue_1234567890_0")
    print()
    print("5. 列出所有对话:")
    print("   dev-bot> dialogue list")
    print()
    print("6. 运行对话:")
    print("   dev-bot> dialogue run dialogue_1234567890_0")
    print()
    print("✓ 所有命令都通过对话整合器实现用户参与")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("Dev-Bot 对话整合演示")
    print("="*60)
    
    try:
        await demo_basic_dialogue()
        await demo_multiple_dialogues()
        await demo_user_interaction()
        await demo_dialogue_status()
        await demo_tui_commands()
        
        print("\n" + "="*60)
        print("演示完成！")
        print("="*60)
        print()
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
