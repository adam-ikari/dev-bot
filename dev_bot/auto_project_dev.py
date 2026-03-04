#!/usr/bin/env python3

"""
Dev-Bot 自动化工程开发流程
适用于任何项目，包括自我开发
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dev_bot.cli.commands import ValidateCommand
from dev_bot.cli.enhance import EnhanceSpecCommand
from dev_bot.error_analyzer import analyze_and_handle_error
from dev_bot.git_manager import auto_setup_git
from dev_bot.project_scanner import scan_project
from dev_bot.spec_generator import SpecGenerator


class AutoProjectDevelopment:
    """自动化工程开发流程"""

    def __init__(self, project_path: Path, ai_tool: str = "iflow", mode: str = "auto", auto_fix: bool = True, auto_restart: bool = True, auto_git: bool = True):
        """
        初始化自动化开发流程
        
        Args:
            project_path: 项目路径
            ai_tool: AI 工具命令
            mode: 模式
            auto_fix: 是否自动修复错误
            auto_restart: 是否自动重启
            auto_git: 是否自动管理 Git
        """
        self.project_path = Path(project_path).resolve()
        self.ai_tool = ai_tool
        self.mode = mode
        self.auto_fix = auto_fix
        self.auto_restart = auto_restart
        self.auto_git = auto_git
        self.specs_dir = self.project_path / "specs"
        self.specs_dir.mkdir(exist_ok=True)
        self.cache_dir = self.project_path / ".dev-bot-cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.restart_count = 0
        self.max_restarts = 3
        self.git_manager = None

    def run(self):
        """运行自动化开发流程"""
        print("=" * 60)
        print(f"Dev-Bot 自动化工程开发流程 - {self.mode.upper()} 模式")
        print(f"项目: {self.project_path.name}")
        print(f"自动修复: {'启用' if self.auto_fix else '禁用'}")
        print(f"自动重启: {'启用' if self.auto_restart else '禁用'}")
        print(f"自动 Git: {'启用' if self.auto_git else '禁用'}")
        print("=" * 60)

        # 自动设置 Git
        if self.auto_git:
            try:
                self.git_manager = auto_setup_git(self.project_path)
            except Exception as e:
                print(f"  ! Git 设置失败: {e}")
                self.git_manager = None

        while self.restart_count < self.max_restarts:
            try:
                if self.mode == "auto":
                    self._run_auto_mode()
                elif self.mode == "analyze":
                    self._run_analyze_mode()
                elif self.mode == "generate":
                    self._run_generate_mode()
                elif self.mode == "validate":
                    self._run_validate_mode()
                elif self.mode == "enhance":
                    self._run_enhance_mode()
                elif self.mode == "suggest":
                    self._run_suggest_mode()
                else:
                    print(f"❌ 未知模式: {self.mode}")
                    sys.exit(1)

                # 成功完成，提交更改
                if self.auto_git and self.git_manager:
                    self._commit_changes()

                # 退出循环
                break

            except Exception as e:
                self.restart_count += 1

                if self.restart_count >= self.max_restarts:
                    print(f"\n❌ 达到最大重启次数 ({self.max_restarts})，停止执行")
                    break

                print(f"\n❌ 流程执行出错: {e}")

                # 分析错误
                analyze_and_handle_error(e, {
                    "mode": self.mode,
                    "project_path": str(self.project_path),
                    "restart_count": self.restart_count
                }, self.ai_tool)

                # 尝试自动修复和重启
                if self.auto_restart:
                    print(f"\n🔄 准备重启流程 (尝试 #{self.restart_count}/{self.max_restarts})...")

                    # 等待一段时间
                    import time
                    time.sleep(3)

                    print("✓ 正在重启...\n")
                    continue
                else:
                    print("\n自动重启已禁用，停止执行")
                    break

        print("\n" + "=" * 60)
        print("✓ 流程完成")
        print("=" * 60)

        # 显示 Git 状态
        if self.auto_git and self.git_manager:
            self.git_manager.display_status()

        self._show_next_steps()

    def _run_auto_mode(self):
        """全自动模式 - 直接启动 AI 开发循环"""
        print("\n" + "=" * 60)
        print("🤖 AI 开发循环")
        print("=" * 60)
        print("\n  AI 将根据 spec 和建议开始开发...")
        print("  按 Ctrl+C 可以随时停止")
        print("\n" + "=" * 60)

        # 直接启动 AI 开发循环
        self._start_ai_development_loop({})

    def _run_analyze_mode(self):
        """分析模式"""
        print("\n📊 分析项目...")
        project_info = self._analyze_project()
        self._save_analysis(project_info)
        print("\n✓ 分析完成")

    def _run_generate_mode(self):
        """生成模式"""
        print("\n📝 生成 Spec...")
        project_info = self._load_analysis()
        if not project_info:
            print("  ! 未找到分析结果，先进行分析...")
            project_info = self._analyze_project()

        self._generate_specs(project_info)
        print("\n✓ Spec 生成完成")

    def _run_validate_mode(self):
        """验证模式"""
        print("\n✅ 验证 Spec...")
        self._validate_specs()
        print("\n✓ 验证完成")

    def _run_enhance_mode(self):
        """增强模式"""
        print("\n🚀 增强 Spec...")
        self._enhance_specs()
        print("\n✓ 增强完成")

    def _run_suggest_mode(self):
        """建议模式"""
        print("\n💡 生成建议...")
        project_info = self._load_analysis()
        if not project_info:
            print("  ! 未找到分析结果，先进行分析...")
            project_info = self._analyze_project()

        self._generate_suggestions(project_info)
        print("\n✓ 建议生成完成")

    def _analyze_project(self) -> Dict[str, Any]:
        """分析项目"""
        project_info = scan_project(self.project_path)

        structure = project_info["structure"]
        code = project_info["code"]

        print(f"  ✓ 发现 {len(structure.get('files', []))} 个文件")
        print(f"  ✓ 发现 {len(structure.get('directories', []))} 个目录")
        print(f"  ✓ 发现 {len(code.get('classes', []))} 个类")
        print(f"  ✓ 发现 {len(code.get('functions', []))} 个函数")
        print(f"  ✓ 发现 {len(code.get('endpoints', []))} 个端点")

        # 检测语言和框架
        languages = structure.get('languages', {})
        frameworks = structure.get('frameworks', [])

        if languages:
            print(f"  ✓ 语言: {', '.join(languages.keys())}")
        if frameworks:
            print(f"  ✓ 框架: {', '.join(frameworks)}")

        # 保存分析结果
        self._save_analysis(project_info)

        return project_info

    def _save_analysis(self, project_info: Dict[str, Any]):
        """保存分析结果"""
        analysis_file = self.cache_dir / "analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(project_info, f, indent=2, ensure_ascii=False)
        print(f"  ✓ 分析结果已保存: {analysis_file}")

    def _load_analysis(self) -> Optional[Dict[str, Any]]:
        """加载分析结果"""
        analysis_file = self.cache_dir / "analysis.json"
        if analysis_file.exists():
            try:
                with open(analysis_file, encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def _generate_specs(self, project_info: Dict[str, Any]):
        """生成 spec"""
        generator = SpecGenerator(self.project_path, self.ai_tool)

        # 根据项目类型确定要生成的 spec 类型
        spec_types = self._determine_spec_types(project_info)

        for spec_type in spec_types:
            spec_name = self._get_spec_name(spec_type)
            spec_file = self.specs_dir / f"{spec_name}.json"

            # 检查是否已存在
            if spec_file.exists():
                print(f"  ✓ Spec 已存在: {spec_file.name}")
                continue

            try:
                spec = generator.generate_spec(spec_type, spec_name)

                with open(spec_file, 'w', encoding='utf-8') as f:
                    json.dump(spec, f, indent=2, ensure_ascii=False)

                print(f"  ✓ 生成 Spec: {spec_file.name}")
            except Exception as e:
                print(f"  ! 生成 Spec 失败: {spec_type} - {e}")

    def _determine_spec_types(self, project_info: Dict[str, Any]) -> List[str]:
        """确定需要生成的 spec 类型"""
        structure = project_info.get("structure", {})
        code = project_info.get("code", {})

        spec_types = ['feature']  # 默认生成 feature

        # 根据项目特征添加其他类型
        if code.get('endpoints'):
            spec_types.append('api')

        # 检查是否是前端项目
        frameworks = structure.get('frameworks', [])
        if any(fw in ['React', 'Vue', 'Angular'] for fw in frameworks):
            spec_types.append('component')

        # 检查是否有服务层
        languages = structure.get('languages', {})
        if 'Python' in languages or 'Java' in languages:
            spec_types.append('service')

        return spec_types

    def _get_spec_name(self, spec_type: str) -> str:
        """获取 spec 名称"""
        return f"{self.project_path.name}-{spec_type}"

    def _validate_specs(self):
        """验证 spec"""
        spec_files = list(self.specs_dir.glob("*.json"))

        if not spec_files:
            print("  ! 未找到 spec 文件")
            return

        for spec_file in spec_files:
            try:
                class Args:
                    def __init__(self, spec_file):
                        self.spec_file = str(spec_file)

                validator = ValidateCommand(Args(spec_file))
                validator.execute()

            except Exception as e:
                print(f"  ! 验证失败: {spec_file.name} - {e}")
                analyze_and_handle_error(e, {
                    "spec_file": str(spec_file),
                    "operation": "validate"
                }, self.ai_tool)

    def _enhance_specs(self):
        """增强 spec"""
        spec_files = list(self.specs_dir.glob("*.json"))

        if not spec_files:
            print("  ! 未找到 spec 文件")
            return

        for spec_file in spec_files:
            try:
                class Args:
                    def __init__(self, spec_file, ai_tool):
                        self.spec_file = str(spec_file)
                        self.aspect = "all"
                        self.ai_tool = ai_tool

                enhancer = EnhanceSpecCommand(Args(spec_file, self.ai_tool))
                enhancer.execute()

            except Exception as e:
                print(f"  ! 增强失败: {spec_file.name} - {e}")
                analyze_and_handle_error(e, {
                    "spec_file": str(spec_file),
                    "operation": "enhance"
                }, self.ai_tool)

    def _generate_suggestions(self, project_info: Dict[str, Any]):
        """生成开发建议"""
        suggestions = self._generate_ai_suggestions(project_info)

        # 保存建议
        suggestions_file = self.cache_dir / "suggestions.json"
        with open(suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(suggestions, f, indent=2, ensure_ascii=False)

        print(f"  ✓ 建议已保存: {suggestions_file}")

        # 显示建议摘要
        self._display_suggestions(suggestions)

    def _generate_ai_suggestions(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """使用 AI 生成建议"""
        prompt = f"""基于以下项目分析，提供开发建议：

项目信息：
```json
{json.dumps(project_info, indent=2, ensure_ascii=False)}
```

请按照以下 JSON 格式返回建议：
```json
{{
  "improvements": [
    "改进建议1",
    "改进建议2"
  ],
  "next_steps": [
    "下一步1",
    "下一步2"
  ],
  "priority_features": [
    {{
      "name": "功能名称",
      "priority": "high|medium|low",
      "description": "功能描述"
    }}
  ],
  "code_quality": {{
    "score": 85,
    "issues": ["问题1", "问题2"]
  }}
}}
```

只返回 JSON，不要有任何其他文字。
"""

        try:
            result = subprocess.run(
                [self.ai_tool],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                content = result.stdout.strip()

                if content.startswith('```'):
                    lines = content.split('\n')
                    if lines[0].startswith('```'):
                        content = '\n'.join(lines[1:])
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()

                return json.loads(content)
        except Exception as e:
            print(f"  ! AI 建议生成失败: {e}")

        return self._get_fallback_suggestions()

    def _get_fallback_suggestions(self) -> Dict[str, Any]:
        """获取回退建议"""
        return {
            "improvements": [
                "完善测试覆盖",
                "添加错误处理",
                "改进文档",
                "优化性能"
            ],
            "next_steps": [
                "编写单元测试",
                "添加配置验证",
                "完善错误处理",
                "更新文档"
            ],
            "priority_features": [],
            "code_quality": {
                "score": 70,
                "issues": ["缺少测试", "文档不完整"]
            }
        }

    def _display_suggestions(self, suggestions: Dict[str, Any]):
        """显示建议"""
        if suggestions.get('improvements'):
            print(f"\n  改进建议 ({len(suggestions['improvements'])}):")
            for i, improvement in enumerate(suggestions['improvements'][:5], 1):
                print(f"    {i}. {improvement}")

        if suggestions.get('next_steps'):
            print(f"\n  下一步 ({len(suggestions['next_steps'])}):")
            for i, step in enumerate(suggestions['next_steps'][:5], 1):
                print(f"    {i}. {step}")

        if suggestions.get('priority_features'):
            print(f"\n  优先功能 ({len(suggestions['priority_features'])}):")
            for i, feature in enumerate(suggestions['priority_features'][:5], 1):
                print(f"    {i}. {feature['name']} ({feature['priority']})")

        if suggestions.get('code_quality'):
            quality = suggestions['code_quality']
            print(f"\n  代码质量: {quality.get('score', 0)}/100")
            if quality.get('issues'):
                print(f"  问题: {', '.join(quality['issues'][:3])}")

    def _start_ai_development_loop(self, suggestions: Dict[str, Any]):
        """启动 AI 开发循环"""
        # 检查是否有配置文件
        config_file = self.project_path / "config.json"
        if not config_file.exists():
            print("  ! 未找到 config.json，创建默认配置...")
            self._create_default_config()

        try:
            # 导入并运行开发循环
            # 切换到项目目录
            import os

            from dev_bot.main import main
            original_cwd = os.getcwd()
            os.chdir(self.project_path)

            try:
                # 使用 TUI 模式运行
                print("\n  🖥️  启动 TUI 模式...")
                sys.argv = ['dev-bot', 'run', '--tui']
                main()

            finally:
                # 恢复原始工作目录
                os.chdir(original_cwd)
        except Exception as e:
            print(f"  ! AI 开发循环出错: {e}")

    def _create_default_config(self):
        """创建默认配置文件"""
        config = {
            "prompt_file": "PROMPT.md",
            "ai_command": self.ai_tool,
            "ai_command_args": [],
            "timeout_seconds": 300,
            "wait_interval": 0.5,
            "log_dir": ".ai-logs",
            "stats_file": ".ai-logs/stats.json",
            "session_counter_file": ".ai-logs/session_counter.json",
            "auto_commit": False,
            "git_commit_template": "chore: record AI session #{session_num} ({status})"
        }

        config_file = self.project_path / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"  ✓ 配置文件已创建: {config_file}")

    def _show_next_steps(self):
        """显示下一步"""
        print("\n📌 下一步操作:")
        print("  1. 查看生成的 spec: ls specs/")
        print("  2. 查看分析结果: cat .dev-bot-cache/analysis.json")
        print("  3. 查看开发建议: cat .dev-bot-cache/suggestions.json")
        print("  4. 基于建议开始开发")
        print("  5. 运行测试: pytest tests/")

        if self.auto_git and self.git_manager and self.git_manager.is_repo:
            print("\n📌 Git 操作:")
            print("  - 查看状态: git status")
            print("  - 查看历史: git log")
            print("  - 创建分支: git branch feature-name")
            print("  - 提交更改: git commit -m 'message'")

        print("\n💡 提示:")
        print("  - 可选择不同模式运行: analyze | generate | validate | enhance | suggest")
        print("  - 自动模式会执行完整流程: auto")
        print("  - 可随时重新运行以更新分析和建议")
        if self.auto_git:
            print("  - Git 仓库会自动管理，也可手动操作")

    def _commit_changes(self):
        """提交更改到 Git"""
        if not self.git_manager or not self.git_manager.is_repo:
            return

        try:
            # 检查是否有更改
            status = self.git_manager.get_status()
            if not status.get('modified', 0) and not status.get('added', 0):
                print("  ✓ 没有需要提交的更改")
                return

            # 创建分支（如果不在 main 分支）
            current_branch = status.get('current_branch')
            if current_branch and current_branch != 'main':
                branch_name = f"dev-bot-{self.mode}-{int(time.time())}"
                self.git_manager.create_branch(branch_name)
                self.git_manager.switch_branch(branch_name)

            # 提交更改
            commit_message = f"Dev-Bot: {self.mode} 流程完成"
            self.git_manager.commit_changes(commit_message)

        except Exception as e:
            print(f"  ! Git 提交失败: {e}")


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        prog='dev-bot-auto-dev',
        description='Dev-Bot 自动化工程开发流程',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 全自动模式（默认）
  python -m dev_bot.auto_project_dev
  
  # 仅分析项目
  python -m dev_bot.auto_project_dev --mode analyze
  
  # 仅生成 spec
  python -m dev_bot.auto_project_dev --mode generate
  
  # 仅验证 spec
  python -m dev_bot.auto_project_dev --mode validate
  
  # 仅增强 spec
  python -m dev_bot.auto_project_dev --mode enhance
  
  # 仅生成建议
  python -m dev_bot.auto_project_dev --mode suggest
  
  # 指定项目路径
  python -m dev_bot.auto_project_dev --project-path /path/to/project
  
  # 指定 AI 工具
  python -m dev_bot.auto_project_dev --ai-tool claude
  
  # 禁用自动 Git
  python -m dev_bot.auto_project_dev --no-auto-git
        """
    )

    parser.add_argument(
        '--project-path', '-p',
        default='.',
        help='项目路径（默认：当前目录）'
    )
    parser.add_argument(
        '--ai-tool', '-t',
        default='iflow',
        help='AI 工具命令（默认：iflow）'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['auto', 'analyze', 'generate', 'validate', 'enhance', 'suggest'],
        default='auto',
        help='运行模式（默认：auto）'
    )
    parser.add_argument(
        '--no-auto-git',
        action='store_true',
        help='禁用自动 Git 管理'
    )

    args = parser.parse_args()

    try:
        auto_dev = AutoProjectDevelopment(
            Path(args.project_path),
            args.ai_tool,
            args.mode,
            auto_git=not args.no_auto_git
        )
        auto_dev.run()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
