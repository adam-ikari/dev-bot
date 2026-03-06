#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 团队演示脚本

展示多个 AI 循环与 AI 守护组成的协作团队
"""
import asyncio
import sys
from pathlib import Path

# 添加 dev_bot 到路径
dev_bot_path = Path(__file__).parent.parent
if str(dev_bot_path) not in sys.path:
    sys.path.insert(0, str(dev_bot_path))

from dev_bot.ai_team import AITeamManager, AIRole
from dev_bot.output_router import (
    get_output_router,
    reset_output_router,
    OutputSource,
    LogLevel
)


async def demo_team_init():
    """演示团队初始化"""
    print("=" * 60)
    print("团队初始化演示")
    print("=" * 60)

    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=2)

    print("\n[演示] 启动 AI 团队...")
    await manager.start()

    # 查看团队状态
    status = await manager.get_status()
    print(f"[演示] 团队名称: {status['team_name']}")
    print(f"[演示] 成员数量: {len(status['members'])}")

    print("\n[演示] 团队成员:")
    for member_id, member_data in status['members'].items():
        print(f"  - {member_id} ({member_data['role']}) - PID: {member_data['pid']}")

    # 停止团队
    print("\n[演示] 停止 AI 团队...")
    await manager.stop()

    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_task_management():
    """演示任务管理"""
    print("=" * 60)
    print("任务管理演示")
    print("=" * 60)

    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=1)

    print("\n[演示] 启动 AI 团队...")
    await manager.start()

    # 添加任务
    print("\n[演示] 添加任务...")
    task1_id = await manager.add_task("实现用户登录功能", AIRole.DEVELOPER)
    print(f"  任务 1: {task1_id}")

    task2_id = await manager.add_task("编写单元测试", AIRole.TESTER)
    print(f"  任务 2: {task2_id}")

    task3_id = await manager.add_task("代码审查", AIRole.REVIEWER)
    print(f"  任务 3: {task3_id}")

    # 等待任务分发
    print("\n[演示] 等待任务分发...")
    await asyncio.sleep(3)

    # 查看任务状态
    status = await manager.get_status()
    print(f"\n[演示] 任务统计:")
    print(f"  总计: {status['tasks']['total']}")
    print(f"  待处理: {status['tasks']['pending']}")
    print(f"  进行中: {status['tasks']['active']}")
    print(f"  已完成: {status['tasks']['completed']}")

    # 停止团队
    print("\n[演示] 停止 AI 团队...")
    await manager.stop()

    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_team_collaboration():
    """演示团队协作"""
    print("=" * 60)
    print("团队协作演示")
    print("=" * 60)

    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=1)

    print("\n[演示] 启动 AI 团队...")
    await manager.start()

    # 模拟完整的开发流程
    print("\n[演示] 模拟开发流程...")

    # 1. 需求分析
    print("  1. 需求分析")
    task1_id = await manager.add_task("分析用户需求", AIRole.ANALYZER)
    await asyncio.sleep(2)

    # 2. 代码开发
    print("  2. 代码开发")
    task2_id = await manager.add_task("编写功能代码", AIRole.DEVELOPER)
    await asyncio.sleep(2)

    # 3. 测试
    print("  3. 测试")
    task3_id = await manager.add_task("编写测试用例", AIRole.TESTER)
    await asyncio.sleep(2)

    # 4. 审查
    print("  4. 审查")
    task4_id = await manager.add_task("代码审查", AIRole.REVIEWER)
    await asyncio.sleep(2)

    # 查看团队状态
    status = await manager.get_status()
    print(f"\n[演示] 团队协作统计:")
    print(f"  总任务: {status['tasks']['total']}")
    print(f"  已完成: {status['tasks']['completed']}")
    print(f"  失败: {status['tasks']['failed']}")

    # 查看成员贡献
    print(f"\n[演示] 成员贡献:")
    for member_id, member_data in status['members'].items():
        print(f"  {member_id}: 完成 {member_data['tasks_completed']} 个任务")

    # 停止团队
    print("\n[演示] 停止 AI 团队...")
    await manager.stop()

    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_role_system():
    """演示角色系统"""
    print("=" * 60)
    print("角色系统演示")
    print("=" * 60)

    print("\n[演示] AI 团队角色:")

    roles = [
        (AIRole.DEVELOPER, "开发者：编写代码和实现功能"),
        (AIRole.TESTER, "测试者：编写测试用例和执行测试"),
        (AIRole.REVIEWER, "审查者：审查代码质量和安全性"),
        (AIRole.ANALYZER, "分析师：分析需求和设计方案"),
        (AIRole.OPTIMIZER, "优化者：优化性能和资源使用"),
        (AIRole.DOCUMENTER, "文档者：编写文档和说明")
    ]

    for role, description in roles:
        print(f"  - {role.value:12} : {description}")

    print("\n[演示] 角色协作流程:")
    print("  1. 分析师分析需求")
    print("  2. 开发者编写代码")
    print("  3. 测试者编写测试")
    print("  4. 审查者审查代码")
    print("  5. 优化者优化性能")
    print("  6. 文档者编写文档")

    print("[演示] 演示完成\n")


async def demo_team_monitoring():
    """演示团队监控"""
    print("=" * 60)
    print("团队监控演示")
    print("=" * 60)

    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=1)

    print("\n[演示] 启动 AI 团队...")
    await manager.start()

    # 添加任务
    await manager.add_task("监控测试任务", AIRole.TESTER)

    # 监控一段时间
    print("\n[演示] 监控团队 5 秒...")
    await asyncio.sleep(5)

    # 查看详细状态
    status = await manager.get_status()

    print(f"\n[演示] 团队状态:")
    print(f"  运行中: {status['is_running']}")

    print(f"\n[演示] 成员状态:")
    for member_id, member_data in status['members'].items():
        health = "✓" if member_data['is_healthy'] else "✗"
        print(f"  {health} {member_id}: PID={member_data['pid']}, "
              f"完成={member_data['tasks_completed']}, 失败={member_data['tasks_failed']}")

    print(f"\n[演示] 任务状态:")
    print(f"  待处理: {status['tasks']['pending']}")
    print(f"  进行中: {status['tasks']['active']}")
    print(f"  已完成: {status['tasks']['completed']}")
    print(f"  失败: {status['tasks']['failed']}")

    # 停止团队
    print("\n[演示] 停止 AI 团队...")
    await manager.stop()

    reset_output_router()
    print("[演示] 演示完成\n")


async def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "AI 团队演示" + " " * 31 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    # 运行所有演示
    await demo_team_init()
    await demo_role_system()
    await demo_task_management()
    await demo_team_collaboration()
    await demo_team_monitoring()

    print("=" * 60)
    print("所有演示完成！")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())