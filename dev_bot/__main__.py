#!/usr/bin/env python3
"""AI 自循环（命令行版本）"""

import asyncio
import os
import sys
import signal as signal_module
import logging
from pathlib import Path

from dev_bot import IflowCaller, IflowError, IflowTimeoutError, IflowProcessError, get_memory_system

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dev-bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化记忆系统
memory_system = get_memory_system()


def setup_signal_handlers(iflow_instance):
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"接收到信号 {signum}，正在停止...")
        iflow_instance.stop()
        sys.exit(0)
    
    signal_module.signal(signal_module.SIGTERM, signal_handler)
    signal_module.signal(signal_module.SIGINT, signal_handler)


async def main_async():
    """AI 自循环（异步版本）"""
    project_path = Path.cwd()
    
    # 加载记忆
    memory = memory_system.load_context()
    memory_summary = memory_system.get_context_summary()
    
    # 更新项目信息
    if not memory.get("project_info"):
        memory["project_info"] = str(project_path)
        memory_system.save_context(memory)
    
    iflow = IflowCaller()
    setup_signal_handlers(iflow)
    
    prompt = f"""你是 Dev-Bot，一个 AI 驱动的自主开发代理。

## 项目信息
- 项目路径: {project_path}
- 技术栈: Python 3.9+, asyncio
- 代码风格: PEP 8, 4空格缩进

## 你的使命
分析当前项目 → 做出决策 → 执行开发 → 验证结果 → 继续改进

## 工作原则
1. 先分析，后行动 - 每次修改前先阅读相关代码
2. 小步快跑，频繁验证 - 每次只修改一个功能点
3. 遇到错误立即停止 - 分析错误原因，不要盲目重试
4. 修改代码后必须测试 - 使用 pytest 运行相关测试
5. 代码审查 - 修改后检查是否引入新问题

## 输出格式
每次输出必须包含：
- [分析] 当前状态、问题分析、相关文件
- [决策] 计划做什么、为什么这样做
- [执行] 具体操作步骤、修改的文件和行号
- [验证] 测试方法、测试结果
- [结论] 成功/失败、影响范围、下一步计划

## 停止条件
当以下情况时停止：
- 所有功能已实现且测试通过
- 连续3次遇到相同错误无法解决
- 需要用户决策或输入
- 接收到停止信号

## 安全规则
- 不要删除重要文件（如 .git/、venv/ 等）
- 不要提交未经测试的代码
- 不要修改配置文件（除非明确需要且有备份）
- 不要运行危险的系统命令
- 修改代码前先备份或使用 git commit

## 错误处理
- 遇到错误时，先阅读错误信息，分析原因
- 检查相关代码和测试用例
- 如果错误持续出现，记录错误并暂停
- 不要无限重试相同的操作

现在开始分析当前项目！

{memory_summary}
"""
    
    try:
        loop_interval_str = os.getenv('DEVBOT_LOOP_INTERVAL', '1')
        loop_interval = int(loop_interval_str) if loop_interval_str.isdigit() else 1
        loop_interval = max(1, min(loop_interval, 300))  # 限制在 1-300 秒
    except Exception as e:
        logger.warning(f"解析循环间隔失败: {e}，使用默认值 1 秒")
        loop_interval = 1
    
    logger.info("Dev-Bot 启动（命令行模式）")
    logger.info(f"循环间隔: {loop_interval} 秒")
    logger.info("提示: 使用 'dev-bot tui' 启动图形界面以获得更好的交互体验")
    
    # 记录启动到历史
    memory_system.add_history_entry("system_start", "Dev-Bot 启动")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"=== 迭代 {iteration} ===")
            
            try:
                result = await iflow.call(prompt)
                print(result)
                logger.info(f"迭代 {iteration} 完成")
                
                # 记录迭代到历史
                memory_system.add_history_entry("ai_iteration", f"迭代 {iteration}", result[:200])
                
                # 定期保存记忆（每10次迭代）
                if iteration % 10 == 0:
                    memory_system.save_context(memory)
                    logger.info("记忆已保存")
                    
            except IflowTimeoutError as e:
                logger.error(f"超时错误: {e}")
                memory_system.add_history_entry("error", f"超时错误: {e}")
            except IflowProcessError as e:
                logger.error(f"进程错误: {e}")
                memory_system.add_history_entry("error", f"进程错误: {e}")
            except IflowError as e:
                logger.error(f"Iflow 错误: {e}")
                memory_system.add_history_entry("error", f"Iflow 错误: {e}")
            except Exception as e:
                logger.error(f"未知错误: {e}", exc_info=True)
                memory_system.add_history_entry("error", f"未知错误: {e}")
            
            await asyncio.sleep(loop_interval)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("接收到停止信号")
    finally:
        logger.info("Dev-Bot 停止")
        
        # 保存记忆和记录停止事件
        try:
            memory_system.save_context(memory)
            memory_system.add_history_entry("system_stop", "Dev-Bot 停止")
            logger.info("记忆已保存")
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")
        
        iflow.stop()


def main():
    """入口点函数（命令行模式）"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()