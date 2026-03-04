#!/usr/bin/env python3

################################################################################
# Dev-Bot - AI 驱动开发代理（可配置版本）
# 自动循环调用 AI 工具完成项目集成
# 版本: 2.0.0
################################################################################

import datetime
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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
            with open(self.config_path, encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件格式错误: {e}")
            sys.exit(1)

    def _validate_config(self) -> None:
        """验证配置"""
        if 'ai_command' not in self.config:
            print("错误: 缺少必需的配置项: ai_command")
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
    print(f"{Colors.CYAN}║{Colors.NC} {Colors.CYAN}DEV-Bot{Colors.NC} - AI 驱动开发代理系统 v2.0{Colors.NC}                                          {Colors.CYAN}║{Colors.NC}")
    print_border()


def print_logo() -> None:
    """打印 DEV-BOT LOGO"""
    logo = f"""
{Colors.CYAN}
███████╗██╗  ██╗███████╗███████╗███████╗██╗  ██╗███████╗
██╔════╝██║  ██║██╔════╝██╔════╝██╔════╝╚██╗██╔╝██╔════╝
███████╗███████║█████╗  ███████╗█████╗  ╚███╔╝ ███████╗
╚════██║██╔══██║██╔══╝  ╚════██║██╔══╝   ██╔██╗ ╚════██║
███████║██║  ██║███████╗███████║███████╗██╔╝ ██╗███████║
╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝
{Colors.NC}
"""
    print(logo)
    print()

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
            with open(counter_file, encoding='utf-8') as f:
                data = json.load(f)
                return data.get('current_session', 0)
        except (OSError, json.JSONDecodeError):
            return 0
    return 0

def update_session_num(config: Config, session_num: int) -> None:
    """更新会话编号（原子性）"""
    counter_file = config.get_session_counter_file()
    temp_file = counter_file.with_suffix('.tmp')
    start_time = datetime.datetime.now().isoformat()

    data = {
        "current_session": session_num,  # 保存当前会话编号
        "last_updated": start_time,
        "total_sessions": session_num   # 总会话数等于当前会话编号
    }

    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(counter_file)
    except OSError:
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
        except OSError:
            pass

def read_stat(config: Config, key: str, default: str = "0") -> str:
    """读取统计值（带默认值）"""
    stats_file = config.get_stats_file()
    if stats_file.exists():
        try:
            with open(stats_file, encoding='utf-8') as f:
                data = json.load(f)
                return str(data.get(key, default))
        except (OSError, json.JSONDecodeError):
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
            with open(log_file, encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
        except OSError:
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
    except OSError:
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
        with open(stats_file, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
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
    except OSError:
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
                except OSError:
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

    # 初始化自动重启管理器（在加载配置之前）
    from dev_bot.auto_restart import AutoRestartManager, setup_crash_handlers
    restart_manager = AutoRestartManager()

    # 记录启动命令
    restart_manager.record_startup(sys.argv[0], sys.argv[1:])

    # 设置崩溃处理器（信号和异常处理）
    setup_crash_handlers(restart_manager)

    # 加载配置
    config = Config()

    # 初始化
    log_dir = config.get_log_dir()
    ensure_log_dir(log_dir)

    # 创建 AI 日志目录（在配置文件所在目录）
    project_dir = config.config_path.parent
    ai_logs_dir = project_dir / ".ai-logs"
    ai_logs_dir.mkdir(exist_ok=True)

    init_stats(config)
    session_num = get_session_num(config)

    # 初始化用户输入管理器（REPL 模式）
    from dev_bot.repl_mode import get_user_input_manager
    user_input_manager = get_user_input_manager()
    user_input_manager.start()

    # 显示启动信息
    print_banner(config)
    print_status("info", f"项目路径: {project_dir}")
    print_status("info", f"日志目录: {log_dir}")
    print_status("info", f"AI日志目录: {ai_logs_dir}")
    ai_cmd = config.get_ai_command()
    ai_args = ' '.join(config.get_ai_command_args())
    print_status("info", f"AI工具: {ai_cmd} {ai_args}")
    print_status("info", f"提示词文件: {config.get_prompt_file()}")
    print_status("success", "自动重启已启用")
    print_status("warning", f"重启次数: {restart_manager._get_restart_count()}")
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

    # 显示 DEV-BOT ASCII ART LOGO
    print_logo()
    print()

    # 主循环
    while not shutdown_requested:
        session_num += 1
        session_start_time = time.time()
        session_output = log_dir / f"session_{session_num}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        # 更新会话编号（保存当前会话编号，这样下次启动时会从这个编号继续）
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
            with open(prompt_file, encoding='utf-8') as prompt_file_handle:
                prompt_content = prompt_file_handle.read()

            # 创建 AI 日志文件
            ai_log_file = ai_logs_dir / f"session_{session_num}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            # 使用 tee 同时输出到终端和日志文件
            with open(session_output, 'w', encoding='utf-8') as log_file, \
                 open(ai_log_file, 'w', encoding='utf-8') as ai_log:
                # 写入会话头部
                log_file.write(f"{'='*80}\n")
                log_file.write(f"会话 #{session_num}\n")
                log_file.write(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"{'='*80}\n\n")

                # 写入 AI 日志头部
                ai_log.write(f"{'='*80}\n")
                ai_log.write(f"AI 会话 #{session_num}\n")
                ai_log.write(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                ai_log.write(f"AI 工具: {ai_command}\n")
                ai_log.write(f"{'='*80}\n\n")

                # 执行 AI 工具并记录输出
                process = subprocess.Popen(
                    [ai_command] + config.get_ai_command_args(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=os.environ.copy()
                )

                # 读取提示词文件并传递给 AI 工具
                with open(prompt_file, encoding='utf-8') as prompt_file_handle:
                    prompt_content = prompt_file_handle.read()

                # 添加用户输入上下文（REPL 模式）
                pending_inputs = user_input_manager.get_pending_inputs()
                if pending_inputs:
                    print_status("info", f"发现 {len(pending_inputs)} 条用户输入，将传递给 AI...")
                    prompt_content += "\n\n" + "="*60 + "\n"
                    prompt_content += "用户输入（非阻塞 REPL 模式）：\n"
                    prompt_content += "="*60 + "\n"
                    for user_input in pending_inputs:
                        prompt_content += f"{user_input}\n"
                    prompt_content += "="*60 + "\n"

                # 将提示词写入 stdin 并关闭
                process.stdin.write(prompt_content)
                process.stdin.flush()
                process.stdin.close()

                # 实时输出并记录
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    print(line, end='')
                    sys.stdout.flush()
                    log_file.write(line)
                    log_file.flush()
                    ai_log.write(line)
                    ai_log.flush()

                # 等待进程结束
                process.wait()
                exit_code = process.returncode

                # 写入会话尾部
                log_file.write(f"\n{'='*80}\n")
                log_file.write(f"结束时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"退出码: {exit_code}\n")
                log_file.write(f"{'='*80}\n")

                # 写入 AI 日志尾部
                ai_log.write(f"\n{'='*80}\n")
                ai_log.write(f"结束时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                ai_log.write(f"退出码: {exit_code}\n")
                ai_log.write(f"{'='*80}\n")

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

        # AI 分析和决策
        print_status("system", "正在分析本轮 AI 输出...")
        decision = analyze_and_decide(config, session_output, session_num, ai_logs_dir)

        if decision.get('action_required'):
            print_status("warning", f"AI 建议: {decision.get('action_description', '')}")
            print_status("info", f"执行动作: {decision.get('action', '')}")

            # 执行 AI 建议的动作
            execute_decision_action(config, decision)
        else:
            print_status("success", "AI 分析完成，继续下一轮")
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

            # 停止用户输入管理器
            user_input_manager.stop()

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

        # 停止用户输入管理器
        user_input_manager.stop()

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

# 导出 main_loop 供外部调用
__all__ = ['Config', 'main_loop', 'main']

################################################################################
# AI 分析和决策
################################################################################

def analyze_and_decide(config: Config, session_output: Path, session_num: int, ai_logs_dir: Path) -> Dict[str, Any]:
    """
    使用 AI 分析输出并决策下一步动作
    
    Args:
        config: 配置对象
        session_output: 会话输出文件
        session_num: 会话编号
        ai_logs_dir: AI 日志目录
        
    Returns:
        决策字典，包含 action_required, action, action_description 等
    """
    default_decision = {
        'action_required': False,
        'action': None,
        'action_description': '',
        'should_stop': False,
        'should_rerun': False
    }

    try:
        # 读取 AI 输出
        with open(session_output, encoding='utf-8') as f:
            ai_output = f.read()

        # 检查代码质量
        code_quality = _check_code_quality()
        
        # 验证 spec 文件
        spec_validation = _validate_spec_files()
        
        # 检查测试结果
        test_results = _check_test_results()
        
        # 检查用户输入（REPL 模式）
        recent_user_inputs = user_input_manager.get_recent_inputs(count=5)
        user_inputs_text = ""
        if recent_user_inputs:
            user_inputs_text = "最近的用户输入：\n" + "\n".join(recent_user_inputs)
        
        # 构建质量评估报告
        quality_report = _build_quality_report(code_quality, spec_validation, test_results)

        # 使用内置提示词构建 AI 请求
        from dev_bot.ai_prompts import get_decision_prompt
        prompt = get_decision_prompt(quality_report, user_inputs_text, ai_output)

        # 调用 AI 工具进行分析
        ai_command = config.get_ai_command()
        result = subprocess.run(
            [ai_command] + config.get_ai_command_args(),
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            content = result.stdout.strip()

            # 解析 JSON 响应
            if content.startswith('```'):
                lines = content.split('\n')
                if lines[0].startswith('```'):
                    content = '\n'.join(lines[1:])
                if content.endswith('```'):
                    content = '\n'.join(content.split('\n')[:-1])

            try:
                decision = json.loads(content)

                # 验证必需字段
                required_fields = ['action_required', 'action', 'action_description']
                for field in required_fields:
                    if field not in decision:
                        print_status("warning", f"AI 返回的决策缺少字段: {field}")
                        return _traditional_fallback_analysis(ai_output)

                # 打印 AI 决策
                is_reasonable = decision.get('is_reasonable', True)
                status_icon = "✅" if is_reasonable else "⚠️"
                print_status("info", f"{status_icon} AI 评估: {'本轮调用合理' if is_reasonable else '本轮调用可能有问题'}")
                print_status("info", f"决策: {decision.get('action', 'none')}")
                print_status("info", f"原因: {decision.get('reason', '')}")
                print_separator()
                print()

                return decision

            except json.JSONDecodeError as e:
                print_status("warning", f"解析 AI 决策失败: {e}")
                print_status("warning", f"AI 响应: {content[:200]}")
                return _traditional_fallback_analysis(ai_output)

        else:
            print_status("warning", f"AI 分析失败: {result.stderr}")

            # AI 调用失败时，检查是否是 AI 工具本身的问题
            if _check_ai_tool_error(result.stderr):
                return {
                    'action_required': True,
                    'action': 'notify_user',
                    'action_description': 'AI 工具调用失败，可能需要重新登录或检查配置',
                    'should_stop': True,
                    'reason': 'AI 工具无法正常工作'
                }

            return _traditional_fallback_analysis(ai_output)

    except subprocess.TimeoutExpired:
        print_status("warning", "AI 分析超时")
        return _traditional_fallback_analysis(ai_output)
    except Exception as e:
        print_status("warning", f"分析 AI 输出时出错: {e}")
        return _traditional_fallback_analysis(ai_output)


def _check_critical_errors(ai_output: str) -> Optional[str]:
    """
    使用传统方法检测关键错误
    
    Args:
        ai_output: AI 输出内容
        
    Returns:
        错误描述，如果没有检测到错误返回 None
    """
    critical_patterns = [
        ('iflow需要重新登录', 'iflow 需要重新登录'),
        ('please log in', '需要登录'),
        ('authentication failed', '认证失败'),
        ('unauthorized', '未授权'),
        ('401 unauthorized', '401 未授权'),
        ('session expired', '会话已过期'),
        ('token expired', '令牌已过期'),
        ('login required', '需要登录'),
        ('重新登录', '需要重新登录'),
        ('请登录', '请登录'),
        ('认证失败', '认证失败'),
        ('未授权', '未授权'),
    ]

    output_lower = ai_output.lower()
    for pattern, description in critical_patterns:
        if pattern.lower() in output_lower:
            return description

    return None


def _check_ai_tool_error(stderr: str) -> bool:
    """
    检查是否是 AI 工具本身的错误
    
    Args:
        stderr: 标准错误输出
        
    Returns:
        是否是 AI 工具错误
    """
    error_patterns = [
        'login required',
        'authentication',
        'unauthorized',
        '401',
        'session expired',
        'token expired'
    ]

    stderr_lower = stderr.lower()
    return any(pattern in stderr_lower for pattern in error_patterns)


def _traditional_fallback_analysis(ai_output: str) -> Dict[str, Any]:
    """
    传统方法后备分析（仅在 AI 调用失败时使用）
    
    Args:
        ai_output: AI 输出内容
        
    Returns:
        决策字典
    """
    print_status("warning", "使用传统方法进行后备分析...")

    decision = {
        'action_required': False,
        'action': None,
        'action_description': '',
        'should_stop': False,
        'should_rerun': False,
        'reason': 'AI 调用失败，使用传统后备分析'
    }

    output_lower = ai_output.lower()

    # 只检查最关键的情况
    if 'error' in output_lower and ('critical' in output_lower or 'fatal' in output_lower):
        # 关键错误
        decision.update({
            'action_required': True,
            'action': 'notify_user',
            'action_description': '检测到关键错误，需要人工干预',
            'should_stop': True
        })
    elif 'error' in output_lower:
        # 一般错误
        decision.update({
            'action_required': True,
            'action': 'none',
            'action_description': '检测到错误，继续下一轮'
        })
    else:
        # 无特殊问题
        decision.update({
            'action_required': False,
            'action': 'none',
            'action_description': '未检测到特殊问题，继续下一轮'
        })

    return decision


def execute_decision_action(config: Config, decision: Dict[str, Any]) -> bool:
    """
    执行 AI 建议的动作
    
    Args:
        config: 配置对象
        decision: 决策字典
        
    Returns:
        是否成功执行
    """
    action = decision.get('action', '').lower()

    # 中英文映射
    action_map = {
        'notify_user': 'notify_user',
        '通知用户': 'notify_user',
        'run_tests': 'run_tests',
        '运行测试': 'run_tests',
        'git_commit': 'git_commit',
        '提交代码': 'git_commit',
        'rerun': 'rerun',
        '重新运行': 'rerun',
        'stop': 'stop',
        '停止': 'stop',
        'none': 'none',
        '无需动作': 'none',
        'run_lint': 'run_lint',
        '运行检查': 'run_lint',
        'fix_errors': 'fix_errors',
        '修复错误': 'fix_errors',
        'check_deps': 'check_deps',
        '检查依赖': 'check_deps',
        'update_spec': 'update_spec',
        '更新规格': 'update_spec'
    }

    # 标准化 action
    normalized_action = action_map.get(action, action)

    if normalized_action == 'notify_user':
        # 通知用户
        try:
            from dev_bot.notifier import Notifier
            notifier = Notifier()
            notifier.notify(
                title='Dev-Bot 工作中断',
                message=decision.get('action_description', ''),
                level='critical'
            )
        except Exception as e:
            print_status("warning", f"发送通知失败: {e}")
        return False

    elif normalized_action == 'run_tests':
        # 运行测试
        try:
            print_status("info", "运行测试...")
            result = subprocess.run(['pytest', '-v'], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print_status("success", "测试通过")
            else:
                print_status("warning", f"测试失败: {result.returncode}")
            return True
        except Exception as e:
            print_status("warning", f"运行测试失败: {e}")
            return False

    elif normalized_action == 'git_commit':
        # 提交代码
        try:
            print_status("info", "提交代码更改...")
            result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
            result = subprocess.run(['git', 'commit', '-m', 'Dev-Bot: AI 生成的代码更改'], capture_output=True, text=True)
            if result.returncode == 0:
                print_status("success", "代码已提交")
            else:
                print_status("warning", f"提交失败: {result.returncode}")
            return True
        except Exception as e:
            print_status("warning", f"提交代码失败: {e}")
            return False

    elif normalized_action == 'rerun':
        # 重新运行
        print_status("info", "准备重新运行...")
        return True

    elif normalized_action == 'run_lint':
        # 运行代码检查
        try:
            print_status("info", "运行代码检查...")
            result = subprocess.run(['ruff', 'check', '.'], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print_status("success", "代码检查通过")
            else:
                print_status("warning", f"代码检查发现问题: {result.returncode}")
                print(result.stdout)
            return True
        except Exception as e:
            print_status("warning", f"运行代码检查失败: {e}")
            return False

    elif normalized_action == 'fix_errors':
        # 修复错误（提示 AI）
        print_status("info", "需要修复错误，将在下一轮继续...")
        return True

    elif normalized_action == 'check_deps':
        # 检查依赖
        try:
            print_status("info", "检查依赖...")
            result = subprocess.run(['pip', 'check'], capture_output=True, text=True, timeout=30)
            print(result.stdout)
            return True
        except Exception as e:
            print_status("warning", f"检查依赖失败: {e}")
            return False

    elif normalized_action == 'update_spec':
        # 更新 spec
        try:
            print_status("info", "更新 spec 文件...")
            from dev_bot.cli.enhance import EnhanceSpecCommand
            # 找到 spec 文件并增强
            spec_files = list(Path('specs').glob('*.json'))
            for spec_file in spec_files:
                class Args:
                    def __init__(self, spec_file):
                        self.spec_file = str(spec_file)
                        self.aspect = "all"
                        self.ai_tool = config.get_ai_command()
                cmd = EnhanceSpecCommand(Args(spec_file))
                cmd.execute()
            return True
        except Exception as e:
            print_status("warning", f"更新 spec 失败: {e}")
            return False

    elif action == 'stop':
        # AI 建议停止，但需要确认是否真正完成
        print_status("warning", f"AI 建议停止: {decision.get('action_description', '')}")
        print_status("info", "需要 AI 确认是否真正完成...")

        # 再次调用 AI 确认是否真的需要停止
        confirmation_prompt = f"""AI 建议停止开发循环，理由如下：
{decision.get('reason', decision.get('action_description', ''))}

请确认是否真的应该停止开发循环，还是应该继续下一轮？

以 JSON 格式返回：
{{
  "should_stop": true/false,
  "reason": "确认原因"
}}

只返回 JSON，不要有任何其他文字。
"""

        try:
            ai_command = config.get_ai_command()
            result = subprocess.run(
                [ai_command] + config.get_ai_command_args(),
                input=confirmation_prompt,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                content = result.stdout.strip()
                if content.startswith('```'):
                    lines = content.split('\n')
                    if lines[0].startswith('```'):
                        content = '\n'.join(lines[1:])
                    if content.endswith('```'):
                        content = '\n'.join(content.split('\n')[:-1])

                confirmation = json.loads(content)
                if confirmation.get('should_stop', False):
                    print_status("success", f"AI 确认停止: {confirmation.get('reason', '')}")
                    import sys
                    sys.exit(0)
                else:
                    print_status("info", f"AI 建议继续: {confirmation.get('reason', '')}")
                    return True
            else:
                print_status("warning", "AI 确认失败，继续下一轮")
                return True

        except Exception as e:
            print_status("warning", f"AI 确认出错: {e}，继续下一轮")
            return True

    return False


################################################################################
# 代码质量检查和 Spec 验证
################################################################################

def _check_code_quality() -> Dict[str, Any]:
    """
    检查代码质量
    
    Returns:
        包含代码质量信息的字典
    """
    quality_info = {
        'has_errors': False,
        'has_warnings': False,
        'ruff_errors': 0,
        'ruff_warnings': 0,
        'syntax_errors': [],
        'summary': ''
    }
    
    try:
        # 运行 ruff 检查
        result = subprocess.run(
            ['ruff', 'check', 'dev_bot'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            output = result.stdout
            lines = output.split('\n')
            
            for line in lines:
                if 'E' in line and 'W' in line:
                    # 统计错误和警告
                    if 'E' in line:
                        quality_info['ruff_errors'] += 1
                    if 'W' in line:
                        quality_info['ruff_warnings'] += 1
                    
                    # 检查语法错误
                    if 'E999' in line or 'E902' in line or 'E9' in line:
                        quality_info['syntax_errors'].append(line.strip())
                        quality_info['has_errors'] = True
                    elif 'W' in line:
                        quality_info['has_warnings'] = True
        
        # 构建摘要
        if quality_info['ruff_errors'] > 0 or quality_info['ruff_warnings'] > 0:
            quality_info['summary'] = (
                f"Ruff 检查发现: {quality_info['ruff_errors']} 个错误, "
                f"{quality_info['ruff_warnings']} 个警告"
            )
            if quality_info['syntax_errors']:
                quality_info['summary'] += f", {len(quality_info['syntax_errors'])} 个语法错误"
        else:
            quality_info['summary'] = "代码质量检查通过"
            
    except Exception as e:
        quality_info['summary'] = f"代码质量检查失败: {e}"
        quality_info['has_errors'] = True
    
    return quality_info


def _validate_spec_files() -> Dict[str, Any]:
    """
    验证 spec 文件
    
    Returns:
        包含 spec 验证信息的字典
    """
    validation_info = {
        'has_errors': False,
        'has_warnings': False,
        'spec_count': 0,
        'invalid_specs': [],
        'summary': ''
    }
    
    specs_dir = Path('specs')
    if not specs_dir.exists():
        validation_info['summary'] = "specs 目录不存在"
        return validation_info
    
    try:
        spec_files = list(specs_dir.glob('*.json'))
        validation_info['spec_count'] = len(spec_files)
        
        for spec_file in spec_files:
            try:
                with open(spec_file, 'r', encoding='utf-8') as f:
                    spec_data = json.load(f)
                
                # 检查必需字段
                required_fields = ['name', 'type', 'description']
                missing_fields = [
                    field for field in required_fields if field not in spec_data
                ]
                
                if missing_fields:
                    validation_info['invalid_specs'].append({
                        'file': spec_file.name,
                        'error': f'缺少字段: {", ".join(missing_fields)}'
                    })
                    validation_info['has_errors'] = True
                
                # 检查 type 是否有效
                valid_types = ['feature', 'api', 'component', 'service']
                if 'type' in spec_data and spec_data['type'] not in valid_types:
                    validation_info['invalid_specs'].append({
                        'file': spec_file.name,
                        'error': f'无效的 type: {spec_data["type"]}'
                    })
                    validation_info['has_errors'] = True
                    
            except json.JSONDecodeError as e:
                validation_info['invalid_specs'].append({
                    'file': spec_file.name,
                    'error': f'JSON 解析错误: {e}'
                })
                validation_info['has_errors'] = True
        
        # 构建摘要
        if validation_info['invalid_specs']:
            validation_info['summary'] = (
                f"Spec 验证发现 {len(validation_info['invalid_specs'])} 个问题 "
                f"(共 {validation_info['spec_count']} 个 spec 文件)"
            )
        elif validation_info['spec_count'] == 0:
            validation_info['summary'] = "没有找到 spec 文件"
            validation_info['has_warnings'] = True
        else:
            validation_info['summary'] = f"所有 {validation_info['spec_count']} 个 spec 文件验证通过"
            
    except Exception as e:
        validation_info['summary'] = f"Spec 验证失败: {e}"
        validation_info['has_errors'] = True
    
    return validation_info


def _check_test_results() -> Dict[str, Any]:
    """
    检查测试结果
    
    Returns:
        包含测试结果信息的字典
    """
    test_info = {
        'has_errors': False,
        'has_failures': False,
        'passed': 0,
        'failed': 0,
        'errors': 0,
        'summary': ''
    }
    
    try:
        # 运行测试
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout
        
        # 解析测试结果
        import re
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        error_match = re.search(r'(\d+) error', output)
        
        if passed_match:
            test_info['passed'] = int(passed_match.group(1))
        if failed_match:
            test_info['failed'] = int(failed_match.group(1))
            test_info['has_failures'] = True
        if error_match:
            test_info['errors'] = int(error_match.group(1))
            test_info['has_errors'] = True
        
        # 构建摘要
        if test_info['failed'] > 0 or test_info['errors'] > 0:
            test_info['summary'] = (
                f"测试结果: {test_info['passed']} 通过, "
                f"{test_info['failed']} 失败, {test_info['errors']} 错误"
            )
        else:
            test_info['summary'] = f"所有 {test_info['passed']} 个测试通过"
            
    except Exception as e:
        test_info['summary'] = f"测试检查失败: {e}"
        test_info['has_errors'] = True
    
    return test_info


def _build_quality_report(code_quality: Dict[str, Any], 
                          spec_validation: Dict[str, Any],
                          test_results: Dict[str, Any]) -> str:
    """
    构建质量评估报告
    
    Args:
        code_quality: 代码质量信息
        spec_validation: spec 验证信息
        test_results: 测试结果信息
        
    Returns:
        格式化的质量报告字符串
    """
    report = [
        "=" * 60,
        "代码和 Spec 质量评估报告",
        "=" * 60,
        "",
        "📊 代码质量:",
        f"  - {code_quality['summary']}",
        f"  - 错误数: {code_quality['ruff_errors']}",
        f"  - 警告数: {code_quality['ruff_warnings']}",
        "",
        "📋 Spec 验证:",
        f"  - {spec_validation['summary']}",
        f"  - Spec 数量: {spec_validation['spec_count']}",
        f"  - 无效 Spec: {len(spec_validation['invalid_specs'])}",
        "",
        "🧪 测试结果:",
        f"  - {test_results['summary']}",
        f"  - 通过: {test_results['passed']}",
        f"  - 失败: {test_results['failed']}",
        f"  - 错误: {test_results['errors']}",
        "",
        "=" * 60
    ]
    
    # 添加详细信息
    if code_quality['syntax_errors']:
        report.append("\n⚠️  语法错误:")
        for error in code_quality['syntax_errors'][:3]:
            report.append(f"  - {error}")
    
    if spec_validation['invalid_specs']:
        report.append("\n⚠️  无效 Spec:")
        for invalid in spec_validation['invalid_specs'][:3]:
            report.append(f"  - {invalid['file']}: {invalid['error']}")
    
    return "\n".join(report)


# 为了兼容性，将 main 函数的逻辑提取为 main_loop
def main_loop(config: Config) -> None:
    """主开发循环 - 供外部调用"""
    # 直接调用 main 函数（它已经接收 config 参数）
    # 由于 main() 内部会创建 Config，我们需要临时修改全局配置路径
    import os
    original_cwd = os.getcwd()

    try:
        # 切换到配置文件所在的目录
        os.chdir(config.config_path.parent)

        # 直接调用 main 函数
        main()

    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)
