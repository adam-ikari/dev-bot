#!/usr/bin/env python3
# -*- coding: utf-8 -*-

################################################################################
# Dev-Bot - AI 驱动开发代理（可配置版本）
# 自动循环调用 AI 工具完成项目集成
# 版本: 2.0.0
################################################################################

import os
import sys
import json
import subprocess
import time
import signal
import threading
import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List

################################################################################
# 配置管理
################################################################################

class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            print(f"错误: 配置文件不存在: {self.config_path}")
            sys.exit(1)
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件格式错误: {e}")
            sys.exit(1)
    
    def _validate_config(self) -> None:
        """验证配置"""
        if 'ai_command' not in self.config:
            print(f"错误: 缺少必需的配置项: ai_command")
            sys.exit(1)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def get_prompt_file(self) -> Path:
        """获取提示词文件路径"""
        return Path(self.get('prompt_file', 'PROMPT.md'))
    
    def get_ai_command(self) -> str:
        """获取 AI 工具命令"""
        return self.get('ai_command', 'iflow')
    
    def get_ai_command_args(self) -> List[str]:
        """获取 AI 工具命令参数"""
        return self.get('ai_command_args', ['-y'])
    
    def get_timeout(self) -> int:
        """获取超时时间"""
        return self.get('timeout_seconds', 300)
    
    def get_wait_interval(self) -> float:
        """获取等待间隔"""
        return 0.5
    
    def get_log_dir(self) -> Path:
        """获取日志目录"""
        return Path('.ai-logs')
    
    def get_stats_file(self) -> Path:
        """获取统计文件"""
        log_dir = self.get_log_dir()
        return log_dir / 'stats.json'
    
    def get_session_counter_file(self) -> Path:
        """获取会话计数器文件"""
        log_dir = self.get_log_dir()
        return log_dir / 'session_counter.json'
    
    def get_auto_commit(self) -> bool:
        """是否自动提交"""
        return True
    
    def get_git_commit_template(self) -> str:
        """获取 Git 提交模板"""
        return 'chore: record AI session #{session_num} ({status})'


################################################################################
# 工具函数
################################################################################

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def ensure_log_dir(log_dir: Path) -> None:
    """创建日志目录"""
    log_dir.mkdir(parents=True, exist_ok=True)

def print_border() -> None:
    """打印边框"""
    print(f"{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════╗{Colors.NC}")

def print_separator() -> None:
    """打印分隔线"""
    print(f"{Colors.CYAN}────────────────────────────────────────────────────────────────────────────────{Colors.NC}")

def print_status(level: str, message: str) -> None:
    """打印状态消息"""
    level_map = {
        "success": f"{Colors.GREEN}[✓]{Colors.NC}",
        "error": f"{Colors.RED}[✗]{Colors.NC}",
        "warning": f"{Colors.YELLOW}[!]{Colors.NC}",
        "info": f"{Colors.BLUE}[i]{Colors.NC}",
        "system": f"{Colors.CYAN}[SYS]{Colors.NC}",
    }
    
    prefix = level_map.get(level, f"[{level}]")
    print(f"{prefix} {message}")

def print_banner(config: Config) -> None:
    """打印启动Banner"""
    banner = f"""
{Colors.CYAN}
███████╗██╗  ██╗███████╗███████╗███████╗██╗  ██╗███████╗
██╔════╝██║  ██║██╔════╝██╔════╝██╔════╝╚██╗██╔╝██╔════╝
███████╗███████║█████╗  ███████╗█████╗  ╚███╔╝ ███████╗
╚════██║██╔══██║██╔══╝  ╚════██║██╔══╝   ██╔██╗ ╚════██║
███████║██║  ██║███████╗███████║███████╗██╔╝ ██╗███████║
╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝
{Colors.NC}
"""
    print(banner, end='')
    print_border()
    print(f"{Colors.CYAN}║{Colors.NC} {Colors.CYAN}Dev-Bot{Colors.NC} - AI 驱动开发代理系统 v2.0{Colors.NC}                                          {Colors.CYAN}║{Colors.NC}")
    print_border()

def print_session_header(session_num: int) -> None:
    """打印会话头部"""
    print("")
    print_separator()
    print(f"{Colors.MAGENTA}>>> 会话 #{session_num} 启动 <<<{Colors.NC}")
    print_separator()
    print(f"时间戳: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"会话ID: {int(time.time())}")
    print("")


################################################################################
# 数据管理函数
################################################################################

def get_session_num(config: Config) -> int:
    """获取当前会话编号"""
    counter_file = config.get_session_counter_file()
    if counter_file.exists():
        try:
            with open(counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('current_session', 0)
        except (json.JSONDecodeError, IOError):
            return 0
    return 0

def update_session_num(config: Config, session_num: int) -> None:
    """更新会话编号（原子性）"""
    counter_file = config.get_session_counter_file()
    temp_file = counter_file.with_suffix('.tmp')
    start_time = datetime.datetime.now().isoformat()
    
    data = {
        "current_session": session_num,
        "last_updated": start_time,
        "total_sessions": session_num
    }
    
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(counter_file)
    except IOError:
        pass

def init_stats(config: Config) -> None:
    """初始化统计文件"""
    stats_file = config.get_stats_file()
    if not stats_file.exists():
        data = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_duration_seconds": 0,
            "start_time": None,
            "last_session_time": None,
            "sessions": []
        }
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

def read_stat(config: Config, key: str, default: str = "0") -> str:
    """读取统计值（带默认值）"""
    stats_file = config.get_stats_file()
    if stats_file.exists():
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return str(data.get(key, default))
        except (json.JSONDecodeError, IOError):
            return default
    return default


################################################################################
# 分析和记录函数
################################################################################

def analyze_with_ai_tool(config: Config, log_file: Path, session_num: int) -> str:
    """使用 AI 工具分析日志"""
    ai_command = config.get_ai_command()
    ai_args = config.get_ai_command_args()
    
    print_status("system", f"正在分析会话 #{session_num} 的 AI 输出...")
    
    # 读取日志内容
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
        except IOError:
            log_content = f"日志文件读取失败：{log_file}"
    else:
        log_content = f"日志文件不存在：{log_file}"
    
    # 构建分析提示
    prompt = f"""请分析以下 AI 会话日志，提取关键信息并按照以下格式输出：

## 工作内容
列出本次会话完成的主要工作（5项以内）

## 重要决策
列出本次会话做出的重要技术决策（3项以内）

## 遇到的问题
列出本次会话遇到的问题和错误（3项以内）

## 解决方案
列出问题的解决方案（3项以内）

## 关键成果
列出生成或修改的文件（5项以内）

请简洁明了，不要添加额外内容。

---
日志内容：
{log_content}
---
"""
    
    # 调用 AI 工具分析
    try:
        result = subprocess.run(
            [ai_command] + ai_args,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print_status("success", "AI 分析完成")
            return result.stdout
        else:
            raise subprocess.CalledProcessError(result.returncode, ai_command)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        print_status("warning", "AI 分析失败，使用默认摘要")
        return """## 工作内容
分析失败，无法提取工作内容

## 重要决策
无

## 遇到的问题
AI 工具分析失败

## 解决方案
检查 AI 工具配置

## 关键成果
无"""

def create_session_record(config: Config, session_num: int, status: str, 
                         duration: int, log_file: Path) -> Path:
    """创建会话记录文件"""
    log_dir = config.get_log_dir()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    record_filename = f"session_{session_num}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    record_file = log_dir / record_filename
    
    # 获取 AI 分析结果
    ai_analysis = analyze_with_ai_tool(config, log_file, session_num)
    
    # 创建记录文件内容
    content = f"""# 会话 #{session_num}

## 基本信息

- **时间：** {timestamp}
- **状态：** {status}
- **耗时：** {duration}s
- **日志文件：** `{log_file.name}`

{ai_analysis}

---

*生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    try:
        with open(record_file, 'w', encoding='utf-8') as f:
            f.write(content)
    except IOError:
        pass
    
    return record_file

def commit_to_git(config: Config, session_num: int, record_file: Path, 
                 status: str) -> bool:
    """提交到 Git"""
    if not config.get_auto_commit():
        return True
    
    stats_file = config.get_stats_file()
    counter_file = config.get_session_counter_file()
    
    # 检查 Git 仓库
    try:
        subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return True
    
    print_status("system", "提交会话记录到 Git...")
    
    # 添加文件到暂存区
    try:
        subprocess.run(
            ['git', 'add', str(record_file), str(stats_file), str(counter_file)],
            capture_output=True,
            check=False
        )
    except FileNotFoundError:
        pass
    
    # 检查是否有更改
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            capture_output=True
        )
        if result.returncode == 0:
            print_status("info", "没有新的更改需要提交")
            return True
    except FileNotFoundError:
        pass
    
    # 提交（带重试）
    commit_template = config.get_git_commit_template()
    commit_msg = commit_template.format(session_num=session_num, status=status)
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                capture_output=True,
                check=True
            )
            print_status("success", "Git 提交成功")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            if retry < max_retries - 1:
                time.sleep(1)
    
    print_status("warning", f"Git 提交失败（已重试 {max_retries} 次）")
    return False

def update_stats(config: Config, session_num: int, status: str, 
                duration: int, record_file: Path) -> None:
    """更新统计信息"""
    stats_file = config.get_stats_file()
    
    # 读取当前统计
    try:
        with open(stats_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        data = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_duration_seconds": 0,
            "start_time": None,
            "last_session_time": None,
            "sessions": []
        }
    
    # 更新计数
    data["total_sessions"] = data.get("total_sessions", 0) + 1
    if status == "success":
        data["successful_sessions"] = data.get("successful_sessions", 0) + 1
    else:
        data["failed_sessions"] = data.get("failed_sessions", 0) + 1
    data["total_duration_seconds"] = data.get("total_duration_seconds", 0) + duration
    
    # 构建新会话条目
    timestamp = datetime.datetime.now().isoformat()
    new_session = {
        "session_number": session_num,
        "status": status,
        "duration_seconds": duration,
        "timestamp": timestamp,
        "record_file": str(record_file)
    }
    
    # 更新数据
    if data.get("start_time") is None:
        data["start_time"] = timestamp
    data["last_session_time"] = timestamp
    data.setdefault("sessions", []).append(new_session)
    
    # 保存到文件
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError:
        pass
    
    # 提交到 Git
    commit_to_git(config, session_num, record_file, status)


################################################################################
# 超时监控函数
################################################################################

class TimeoutMonitor(threading.Thread):
    """超时监控线程"""
    
    def __init__(self, log_file: Path, main_pid: int, session_num: int, 
                 timeout_seconds: int):
        super().__init__(daemon=True)
        self.log_file = log_file
        self.main_pid = main_pid
        self.session_num = session_num
        self.timeout_seconds = timeout_seconds
        self.last_output_time = time.time()
        self.last_size = 0
        self.should_stop = threading.Event()
    
    def run(self) -> None:
        """监控主线程的输出"""
        while not self.should_stop.is_set():
            self.should_stop.wait(1)
            
            # 检查主进程
            try:
                os.kill(self.main_pid, 0)
            except ProcessLookupError:
                return
            
            # 检查输出
            if self.log_file.exists():
                try:
                    current_size = self.log_file.stat().st_size
                    if current_size != self.last_size:
                        self.last_output_time = time.time()
                        self.last_size = current_size
                except OSError:
                    pass
            
            # 检查超时
            current_time = time.time()
            elapsed = current_time - self.last_output_time
            
            if elapsed >= self.timeout_seconds:
                warning_msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 警告：连续 {self.timeout_seconds} 秒无输出，终止进程 PID={self.main_pid}"
                print(warning_msg, file=sys.stderr)
                
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write("\n")
                        f.write(warning_msg + "\n")
                        f.write("\n")
                        f.write("本次会话因超时被终止，将进入下一轮循环\n")
                except IOError:
                    pass
                
                # 终止主进程
                try:
                    os.kill(self.main_pid, signal.SIGTERM)
                    time.sleep(2)
                    os.kill(self.main_pid, 0)
                    os.kill(self.main_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                
                return
    
    def stop(self) -> None:
        """停止监控"""
        self.should_stop.set()

def interruptible_sleep(seconds: float) -> None:
    """可中断的等待（支持 Ctrl+C）"""
    iterations = int(seconds / 0.5)
    for _ in range(iterations):
        time.sleep(0.5)


################################################################################
# 全局变量
################################################################################

shutdown_requested = False
last_signal_time = 0


################################################################################
# 退出处理
################################################################################

def signal_handler(signum: int, frame) -> None:
    """信号处理函数"""
    global shutdown_requested, last_signal_time
    
    current_time = time.time()
    
    if current_time - last_signal_time < 1.0:
        print()
        print_separator()
        print_status("error", "收到连续中断信号，立即强制退出！")
        print_separator()
        print()
        sys.exit(130)
    
    last_signal_time = current_time
    shutdown_requested = True
    
    print()
    print_separator()
    print_status("warning", "收到中断信号 (Ctrl+C)")
    print_status("info", "当前AI调用循环完成后将退出dev-bot")
    print_status("info", "再次按Ctrl+C可立即强制退出")
    print_separator()
    print()

def ignore_signal_handler(signum: int, frame) -> None:
    """忽略信号处理函数"""
    print()
    print_status("warning", "收到信号，忽略并继续...")


################################################################################
# 主程序
################################################################################

def main() -> None:
    """主程序"""
    global shutdown_requested
    
    # 加载配置
    config = Config()
    
    # 初始化
    log_dir = config.get_log_dir()
    ensure_log_dir(log_dir)
    init_stats(config)
    session_num = get_session_num(config)
    
    # 显示启动信息
    print_banner(config)
    print_status("info", f"项目路径: {os.getcwd()}")
    print_status("info", f"日志目录: {log_dir}")
    print_status("info", f"AI工具: {config.get_ai_command()} {' '.join(config.get_ai_command_args())}")
    print_status("info", f"提示词文件: {config.get_prompt_file()}")
    print_separator()
    print()
    
    # 环境检查
    prompt_file = config.get_prompt_file()
    if not prompt_file.exists():
        print_status("error", f"提示词文件不存在: {prompt_file}")
        sys.exit(1)
    
    ai_command = config.get_ai_command()
    try:
        subprocess.run(['which', ai_command], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_status("error", f"AI 工具命令不可用: {ai_command}")
        sys.exit(1)
    
    print_status("success", "环境检查通过")
    print_status("info", "启动 AI 驱动开发循环...")
    print_status("warning", "提示：使用 Ctrl+C 停止循环")
    print_status("warning", f"超时设置：任意连续 {config.get_timeout()} 秒无输出将自动结束本轮")
    print_separator()
    print()
    
    # 主循环
    while not shutdown_requested:
        session_num += 1
        session_start_time = time.time()
        session_output = log_dir / f"session_{session_num}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # 更新会话编号
        update_session_num(config, session_num)
        
        # 显示会话信息
        print_session_header(session_num)
        
        # 启动超时监控
        main_pid = os.getpid()
        monitor = TimeoutMonitor(session_output, main_pid, session_num, 
                                config.get_timeout())
        monitor.start()
        
        # 执行 AI 工具
        print_status("info", f"正在调用 {ai_command} AI 助手...")
        print()
        sys.stdout.flush()
        
        exit_code = 0
        try:
            # 读取提示词文件并传递给 AI 工具
            with open(prompt_file, 'r', encoding='utf-8') as prompt_file_handle:
                prompt_content = prompt_file_handle.read()
            
            # 使用 tee 同时输出到终端和日志文件
            with open(session_output, 'w', encoding='utf-8') as log_file:
                # 写入会话头部
                log_file.write(f"{'='*80}\n")
                log_file.write(f"会话 #{session_num}\n")
                log_file.write(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"{'='*80}\n\n")
                
                # 执行 AI 工具并记录输出
                process = subprocess.Popen(
                    [ai_command] + config.get_ai_command_args(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=os.environ.copy()
                )
                
                # 实时输出并记录
                for line in process.stdout:
                    print(line, end='')
                    sys.stdout.flush()
                    log_file.write(line)
                    log_file.flush()
                
                # 等待进程结束
                process.wait()
                exit_code = process.returncode
                
                # 写入会话尾部
                log_file.write(f"\n{'='*80}\n")
                log_file.write(f"结束时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"退出码: {exit_code}\n")
                log_file.write(f"{'='*80}\n")
                
        except FileNotFoundError:
            print_status("error", f"AI 工具命令未找到: {ai_command}")
            exit_code = 127
            with open(session_output, 'w', encoding='utf-8') as log_file:
                log_file.write(f"错误: AI 工具命令未找到: {ai_command}\n")
        except Exception as e:
            print_status("error", f"执行 AI 工具时出错: {e}")
            exit_code = 1
            with open(session_output, 'w', encoding='utf-8') as log_file:
                log_file.write(f"错误: {e}\n")
        
        # 停止监控
        monitor.stop()
        monitor.join(timeout=2)
        
        # 处理结果
        status = "success" if exit_code == 0 else "failed"
        
        if status == "success":
            print()
            print_status("success", f"会话 #{session_num} 执行完成")
        else:
            print()
            print_status("warning", f"会话 #{session_num} 非正常退出 (退出码: {exit_code})")
            print_status("info", f"详细日志: {session_output}")
            print_status("info", "将进入下一轮循环...")
        
        # 计算耗时
        session_end_time = time.time()
        session_duration = int(session_end_time - session_start_time)
        print()
        print_status("info", f"会话耗时: {session_duration}s")
        print_separator()
        print()
        
        # 创建会话记录
        print_status("system", "正在生成会话记录...")
        record_file = create_session_record(config, session_num, status, 
                                           session_duration, session_output)
        print_status("success", f"记录文件: {record_file}")
        print()
        
        # 更新统计
        print_status("system", "更新统计数据...")
        update_stats(config, session_num, status, session_duration, record_file)
        print_status("success", "统计更新完成")
        print_separator()
        print()
        
        # 检查是否收到退出信号
        if shutdown_requested:
            print_separator()
            print_status("warning", "收到退出信号，当前AI调用循环已完成")
            print_status("info", "正在保存状态...")
            print_status("info", "Dev-Bot 已停止")
            print_status("info", "使用 python main.py 重新启动")
            print_separator()
            print()
            sys.exit(0)
        
        # 等待下一轮
        print_status("info", "等待 2 秒后开始下一轮...")
        print_status("info", f"会话 #{session_num + 1} 准备中...")
        interruptible_sleep(2)
        print()
    
    if shutdown_requested:
        print_separator()
        print_status("warning", "Dev-Bot 已停止")
        print_status("info", "使用 python main.py 重新启动")
        print_separator()
        print()
        sys.exit(0)

if __name__ == "__main__":
    # 信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, ignore_signal_handler)
    signal.signal(signal.SIGQUIT, ignore_signal_handler)
    signal.signal(signal.SIGUSR1, ignore_signal_handler)
    signal.signal(signal.SIGUSR2, ignore_signal_handler)
    
    # 启动主程序
    main()