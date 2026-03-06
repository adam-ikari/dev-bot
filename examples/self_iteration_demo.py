"""极简自我迭代系统演示"""
import asyncio
from pathlib import Path
from dev_bot.self_iteration_simple import SimpleSelfIteration


async def main():
    """演示自我迭代"""
    project_root = Path("/home/zhaodi-chen/project/dev-bot")
    
    # 创建迭代系统
    iteration = SimpleSelfIteration(project_root)
    
    print("="*60)
    print("Dev-Bot 极简自我迭代演示")
    print("="*60)
    
    # 运行一次迭代
    print("\n开始运行迭代...")
    result = await iteration.run_iteration()
    
    print("\n" + "="*60)
    print("迭代结果")
    print("="*60)
    
    print(f"\n迭代 ID: {result['iteration_id']}")
    print(f"时间戳: {result['timestamp']}")
    
    print("\n上下文:")
    print(f"  测试结果: {result['context']['test_results']}")
    print(f"  代码覆盖率: {result['context']['coverage']:.2f}%")
    print(f"  错误数量: {result['context']['error_count']}")
    print(f"  Git 状态: {'有变更' if result['context']['git_dirty'] else '干净'}")
    
    print("\nAI 决策:")
    print(f"  分析: {result['decision'].get('analysis', 'N/A')}")
    print(f"  问题: {result['decision'].get('problem', 'N/A')}")
    print(f"  行动: {result['decision'].get('action', 'N/A')}")
    print(f"  步骤数: {len(result['decision'].get('steps', []))}")
    
    print("\n执行结果:")
    print(f"  成功: {result['execution']['success']}")
    print(f"  完成步骤: {len(result['execution']['steps_completed'])}")
    print(f"  失败步骤: {len(result['execution']['steps_failed'])}")
    print(f"  变更数: {len(result['execution']['changes'])}")
    
    print("\n验证结果:")
    print(f"  改进成功: {result['verification']['success']}")
    print(f"  覆盖率变化: {result['verification']['improvements']['delta_coverage']:+.2f}%")
    print(f"  错误变化: {result['verification']['improvements']['delta_errors']:+d}")
    
    print("\n" + "="*60)
    print("演示完成")
    print("="*60)
    
    # 显示日志位置
    print(f"\n迭代日志保存在: {project_root / '.dev-bot-evolution' / 'iteration_log.json'}")


if __name__ == "__main__":
    asyncio.run(main())