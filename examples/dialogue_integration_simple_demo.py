"""对话整合简单演示

演示如何使用对话整合器的基本功能
"""
import asyncio
from dev_bot.dialogue_integrator import DialogueIntegrator


async def main():
    """主函数"""
    print("\n=== 对话整合简单演示 ===\n")
    
    # 创建对话整合器
    integrator = DialogueIntegrator()
    integrator._initialize()
    
    print("✓ 对话整合器已初始化")
    
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
    
    # 查看对话信息
    dialogue = await integrator.get_dialogue(dialogue_id)
    print(f"✓ 对话主题: {dialogue.topic}")
    print(f"✓ 对话参与者: {', '.join(dialogue.participants)}")
    print(f"✓ 消息数量: {len(dialogue.messages)}")
    
    # 列出所有对话
    all_dialogues = await integrator.list_dialogues()
    print(f"\n✓ 当前共有 {len(all_dialogues)} 个对话")
    
    # 获取状态
    status = await integrator.get_dialogue_status()
    print(f"✓ 当前对话 ID: {status['current_dialogue_id']}")
    
    print("\n=== 演示完成 ===\n")


if __name__ == "__main__":
    asyncio.run(main())