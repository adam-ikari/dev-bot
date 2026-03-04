#!/usr/bin/env python3

"""
提取 Spec 命令 - 从已有工程提取 spec
"""

import json
import sys
from pathlib import Path

from dev_bot.spec_generator import SpecGenerator


class ExtractSpecCommand:
    """从已有工程提取 spec"""

    def __init__(self, args):
        self.args = args

    def execute(self):
        project_path = Path(self.args.project_path).resolve()
        spec_type = self.args.type
        output_dir = Path(self.args.output) if self.args.output else Path.cwd() / 'specs'
        spec_name = self.args.spec_name
        ai_tool = self.args.ai_tool or "iflow"
        use_ai = not self.args.no_ai

        if not project_path.exists():
            self._print_error(f"工程路径不存在: {project_path}")
            sys.exit(1)

        self._print_info(f"分析工程: {project_path}")
        self._print_info(f"Spec 类型: {spec_type}")
        self._print_info(f"AI 工具: {ai_tool if use_ai else '禁用'}")

        # 创建生成器
        generator = SpecGenerator(project_path, ai_tool)

        # 分析工程
        self._print_info("正在扫描工程结构...")
        generator.analyze_project()

        project_info = generator.project_info
        structure = project_info.get("structure", {})
        code = project_info.get("code", {})

        # 显示分析结果
        self._print_info(f"发现 {len(structure.get('files', []))} 个文件")
        self._print_info(f"发现 {len(structure.get('directories', []))} 个目录")
        self._print_info(f"发现 {len(code.get('classes', []))} 个类")
        self._print_info(f"发现 {len(code.get('functions', []))} 个函数")
        self._print_info(f"发现 {len(code.get('endpoints', []))} 个端点")

        # 生成 spec
        self._print_info("正在生成 spec...")
        spec = generator.generate_spec(spec_type, spec_name)

        # 确定输出文件名
        if not spec_name:
            spec_name = project_path.name

        spec_file = output_dir / f"{spec_name}.json"

        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)

        # 写入 spec
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)

        self._print_success(f"spec 文件已生成: {spec_file}")

        # 显示统计信息
        self._print_summary(spec)

        # 下一步提示
        self._print_info("\n下一步:")
        self._print_info(f"  1. 查看 spec: cat {spec_file}")
        self._print_info(f"  2. 验证 spec: dev-bot sdd validate {spec_file}")
        self._print_info(f"  3. 增强 spec: dev-bot sdd enhance {spec_file}")
        self._print_info("  4. 开始开发: dev-bot run")

    def _print_success(self, message: str):
        """打印成功消息"""
        print(f"✓ {message}")

    def _print_error(self, message: str):
        """打印错误消息"""
        print(f"✗ {message}", file=sys.stderr)

    def _print_info(self, message: str):
        """打印信息消息"""
        print(f"  {message}")

    def _print_summary(self, spec: dict):
        """打印 spec 摘要"""
        print("\n📊 Spec 摘要:")
        print(f"  名称: {spec.get('metadata', {}).get('name', 'N/A')}")
        print(f"  类型: {spec.get('metadata', {}).get('type', 'N/A')}")
        print(f"  版本: {spec.get('metadata', {}).get('version', 'N/A')}")

        if spec.get('requirements'):
            print(f"  需求数: {len(spec['requirements'])}")
        if spec.get('endpoints'):
            print(f"  端点数: {len(spec['endpoints'])}")
        if spec.get('components'):
            print(f"  组件数: {len(spec['components'])}")
        if spec.get('services'):
            print(f"  服务数: {len(spec['services'])}")
