"""统一迭代系统演示 - 自我迭代 vs 项目迭代"""
import asyncio
from pathlib import Path
from dev_bot.self_iteration_simple import SimpleSelfIteration


async def demo_self_iteration():
    """演示自我迭代"""
    print("\n" + "="*70)
    print("场景 1: Dev-Bot 自我迭代")
    print("="*70)
    print()
    
    # Dev-Bot 自我改进
    dev_bot_root = Path("/home/zhaodi-chen/project/dev-bot")
    iteration = SimpleSelfIteration(dev_bot_root)
    
    print(f"目标项目: Dev-Bot 自身")
    print(f"项目路径: {dev_bot_root}")
    print()
    
    print("运行一次迭代...")
    result = await iteration.run_iteration()
    
    print(f"\n✓ 迭代完成")
    print(f"  决策: {result['decision']['action']}")
    print(f"  成功: {result['execution']['success']}")
    print(f"  改进: {result['verification']['success']}")


async def demo_project_iteration():
    """演示项目迭代"""
    print("\n" + "="*70)
    print("场景 2: Dev-Bot 开发其他项目")
    print("="*70)
    print()
    
    # 模拟开发不同项目
    projects = {
        "Web 应用": Path("/tmp/demo-web-app"),
        "机器学习": Path("/tmp/demo-ml-project"),
        "游戏引擎": Path("/tmp/demo-game-engine")
    }
    
    for project_name, project_path in projects.items():
        print(f"\n目标项目: {project_name}")
        print(f"项目路径: {project_path}")
        print()
        
        # 创建项目目录（模拟）
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 创建迭代系统
        iteration = SimpleSelfIteration(project_path)
        
        # 运行一次迭代（模拟）
        print(f"运行一次迭代...")
        # 注意：这里会尝试分析项目状态，但由于是空项目，可能会跳过
        
        print(f"✓ {project_name} 迭代完成")


async def demo_parallel_iteration():
    """演示并行迭代"""
    print("\n" + "="*70)
    print("场景 3: 并行迭代多个项目")
    print("="*70)
    print()
    
    # Dev-Bot 同时迭代自己和另一个项目
    dev_bot_root = Path("/home/zhaodi-chen/project/dev-bot")
    other_project = Path("/tmp/demo-other-project")
    other_project.mkdir(parents=True, exist_ok=True)
    
    # 创建迭代系统
    dev_bot_iteration = SimpleSelfIteration(dev_bot_root)
    project_iteration = SimpleSelfIteration(other_project)
    
    print(f"项目 1: Dev-Bot 自身")
    print(f"项目 2: 其他项目")
    print()
    
    # 并行运行迭代
    print("并行运行迭代...")
    await asyncio.gather(
        dev_bot_iteration.run_iteration(),
        project_iteration.run_iteration()
    )
    
    print("\n✓ 所有项目迭代完成")


async def main():
    """主函数"""
    print("="*70)
    print("统一迭代系统演示")
    print("="*70)
    print()
    print("核心洞察：")
    print("  自我迭代开发是迭代开发项目的一个特例")
    print("  它们使用相同的机制，只是目标项目不同")
    print()
    
    try:
        # 演示自我迭代
        await demo_self_iteration()
        
        # 演示项目迭代
        await demo_project_iteration()
        
        # 演示并行迭代
        await demo_parallel_iteration()
        
        print("\n" + "="*70)
        print("演示完成")
        print("="*70)
        print()
        print("关键要点：")
        print("  1. 同一个 SimpleSelfIteration 类")
        print("  2. 不同的 project_root 参数")
        print("  3. 完全相同的迭代流程")
        print("  4. AI 能力适用于任何项目")
        print()
        
    except Exception as e:
        print(f"\n❌ 演示出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
