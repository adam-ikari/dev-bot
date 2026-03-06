"""Headless 模式演示

展示如何使用 --headless 选项进行自动化、无交互的执行
"""
import asyncio
import json
import subprocess
from pathlib import Path


async def demo_headless_mode():
    """演示 headless 模式"""
    print("="*70)
    print("Dev-Bot Headless 模式演示")
    print("="*70)
    print()
    
    print("Headless 模式特点：")
    print("  ✓ 全自动运行，无需交互")
    print("  ✓ 输出 JSON 格式，便于程序解析")
    print("  ✓ 适合 CI/CD 和自动化脚本")
    print("  ✓ 支持所有模式（plan, execute, thinking）")
    print()
    
    # 示例 1: 普通模式（headless）
    print("示例 1: 普通模式（headless）")
    print("-" * 70)
    
    result = await run_headless("分析当前代码结构")
    print(f"状态: {'成功' if result['success'] else '失败'}")
    print(f"耗时: {result['duration']:.2f}秒")
    print(f"输出长度: {len(result['output'])} 字符")
    print()
    
    # 示例 2: 规划模式（headless）
    print("示例 2: 规划模式（headless）")
    print("-" * 70)
    
    result = await run_headless_plan("设计一个 REST API")
    print(f"模式: {result['mode']}")
    print(f"状态: {'成功' if result['success'] else '失败'}")
    print(f"耗时: {result['duration']:.2f}秒")
    print()
    
    # 示例 3: 执行模式（headless）
    print("示例 3: 执行模式（headless）")
    print("-" * 70)
    
    result = await run_headless_execute("修复测试失败")
    print(f"模式: {result['mode']}")
    print(f"状态: {'成功' if result['success'] else '失败'}")
    print(f"耗时: {result['duration']:.2f}秒")
    if result['error']:
        print(f"错误: {result['error'][:100]}")
    print()
    
    # 示例 4: 思考模式（headless）
    print("示例 4: 思考模式（headless）")
    print("-" * 70)
    
    result = await run_headless_thinking("优化系统性能")
    print(f"模式: {result['mode']}")
    print(f"状态: {'成功' if result['success'] else '失败'}")
    print(f"耗时: {result['duration']:.2f}秒")
    print()
    
    # 示例 5: 解析 JSON 结果
    print("示例 5: 解析 JSON 结果")
    print("-" * 70)
    
    result = await run_headless("生成一个简单的 Python 函数")
    
    # 解析 JSON
    if result['success']:
        # 提取代码块（如果有）
        output = result['output']
        if '```python' in output:
            code_start = output.find('```python')
            code_end = output.find('```', code_start + 9)
            if code_end != -1:
                code = output[code_start + 9:code_end].strip()
                print(f"提取的代码（{len(code)} 字符）:")
                print(code[:200] + "...")
        else:
            print(f"纯文本输出（{len(output)} 字符）:")
            print(output[:200] + "...")
    print()
    
    print("="*70)
    print("演示完成")
    print("="*70)
    print()
    
    print("实际应用：")
    print("  1. CI/CD 管道")
    print("  2. 自动化脚本")
    print("  3. 定时任务")
    print("  4. API 集成")
    print()


async def run_headless(prompt: str) -> dict:
    """运行 headless 模式（普通）"""
    cmd = ["uv", "run", "python", "-m", "dev_bot", "run", "--headless", prompt]
    result = await run_command(cmd)
    return json.loads(result)


async def run_headless_plan(prompt: str) -> dict:
    """运行 headless 模式（规划）"""
    cmd = ["uv", "run", "python", "-m", "dev_bot", "run", "--headless", "--plan", prompt]
    result = await run_command(cmd)
    return json.loads(result)


async def run_headless_execute(prompt: str) -> dict:
    """运行 headless 模式（执行）"""
    cmd = ["uv", "run", "python", "-m", "dev_bot", "run", "--headless", "-y", prompt]
    result = await run_command(cmd)
    return json.loads(result)


async def run_headless_thinking(prompt: str) -> dict:
    """运行 headless 模式（思考）"""
    cmd = ["uv", "run", "python", "-m", "dev_bot", "run", "--headless", "--thinking", prompt]
    result = await run_command(cmd)
    return json.loads(result)


async def run_command(cmd: list) -> str:
    """运行命令并返回输出"""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path.cwd()
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {stderr.decode()}")
    
    # 只返回最后一行（JSON）
    output = stdout.decode().strip()
    lines = output.split('\n')
    
    # 找到 JSON 行（以 { 开头的行）
    for line in reversed(lines):
        if line.strip().startswith('{'):
            return line
    
    return output


if __name__ == "__main__":
    try:
        asyncio.run(demo_headless_mode())
    except KeyboardInterrupt:
        print("\n演示已取消")
    except Exception as e:
        print(f"\n❌ 演示出错: {str(e)}")
        import traceback
        traceback.print_exc()