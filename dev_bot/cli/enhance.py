#!/usr/bin/env python3

"""
Spec 增强命令 - 使用 AI 补充和完善 spec
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


class EnhanceSpecCommand:
    """增强 spec 文件 - 使用 AI 补充和完善 spec"""

    def __init__(self, args):
        self.args = args

    def execute(self):
        spec_file = Path(self.args.spec_file)
        aspect = self.args.aspect
        ai_tool = self.args.ai_tool or "iflow"

        if not spec_file.exists():
            self._print_error(f"spec 文件不存在: {spec_file}")
            sys.exit(1)

        self._print_info(f"增强 spec 文件: {spec_file}")
        self._print_info(f"增强方面: {aspect}")
        self._print_info(f"AI 工具: {ai_tool}")

        # 读取 spec 文件
        try:
            with open(spec_file, encoding='utf-8') as f:
                spec = json.load(f)
        except Exception as e:
            self._print_error(f"解析失败: {e}")
            sys.exit(1)

        # 验证 spec
        if 'metadata' not in spec or 'type' not in spec['metadata']:
            self._print_error("spec 文件格式不正确，缺少 metadata.type")
            sys.exit(1)

        spec_type = spec['metadata']['type']

        # 生成增强 prompt
        prompt = self._generate_enhance_prompt(spec, aspect)

        # 调用 AI 工具
        self._print_info("正在调用 AI 增强 spec...")
        enhancement = self._call_ai_tool(ai_tool, prompt)

        # 合并增强内容
        self._merge_enhancement(spec, enhancement, aspect)

        # 更新时间戳
        import datetime
        spec['metadata']['updated'] = datetime.datetime.now().isoformat()

        # 备份原文件
        backup_file = spec_file.with_suffix('.json.backup')
        shutil.copy2(spec_file, backup_file)
        self._print_info(f"原文件已备份到: {backup_file}")

        # 写入增强后的 spec
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)

        self._print_success(f"spec 文件增强完成: {spec_file}")
        self._print_info("使用 'sdd validate' 验证 spec 文件")

    def _generate_enhance_prompt(self, spec: Dict[str, Any], aspect: str) -> str:
        """生成增强 prompt"""

        aspect_prompts = {
            'requirements': "分析当前 spec 的需求部分，补充缺失的需求，优化现有需求的描述和优先级",
            'user_stories': "为所有需求添加对应的用户故事，确保用户故事格式正确且有价值",
            'acceptance_criteria': "为每个需求添加详细的验收标准，确保可测试和可验证",
            'api': "完善 API 规格细节，添加完整的请求/响应模型和错误处理",
            'components': "补充组件的属性、事件和方法定义，添加使用示例",
            'tests': "基于当前 spec 生成完整的测试用例和测试场景",
            'examples': "添加详细的使用示例和最佳实践",
            'security': "补充安全相关的考虑和安全要求",
            'performance': "添加性能要求和优化建议",
            'all': "全面分析和增强 spec 的所有方面，补充缺失内容，优化现有内容"
        }

        prompt = f"""请分析以下 spec 文件，并{aspect_prompts.get(aspect, aspect)}：

当前 spec 内容（JSON 格式）：
```json
{json.dumps(spec, indent=2, ensure_ascii=False)}
```

请严格按照以下 JSON 格式返回需要增强或补充的内容，只返回 JSON，不要有任何其他文字：

```json
{{
  "enhancements": [
    {{
      "section": "section_name",
      "action": "add|update|delete",
      "content": {{}}
    }}
  ],
  "suggestions": [
    "建议1",
    "建议2"
  ]
}}
```

注意事项：
1. action 为 "add" 时，content 是要添加的新内容
2. action 为 "update" 时，content 是要更新的字段和值
3. action 为 "delete" 时，content 是要删除的字段路径
4. 确保返回的内容符合 spec 的 JSON Schema
"""

        return prompt

    def _call_ai_tool(self, ai_tool: str, prompt: str) -> str:
        """调用 AI 工具"""
        try:
            result = subprocess.run(
                [ai_tool],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return result.stdout
            else:
                raise subprocess.CalledProcessError(result.returncode, ai_tool)

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            self._print_error(f"AI 工具调用失败: {e}")
            self._print_info("请确保 AI 工具已安装并配置正确")
            sys.exit(1)

    def _merge_enhancement(self, spec: Dict[str, Any], enhancement: str, aspect: str):
        """合并增强内容到 spec"""
        try:
            # 解析 AI 返回的内容
            content = enhancement.strip()

            # 移除 markdown 代码块标记
            if content.startswith('```'):
                lines = content.split('\n')
                if lines[0].startswith('```'):
                    content = '\n'.join(lines[1:])
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

            result = json.loads(content)

            # 应用增强
            if 'enhancements' in result:
                for item in result['enhancements']:
                    section = item.get('section')
                    action = item.get('action')
                    content_data = item.get('content')

                    if section and action and content_data:
                        self._apply_enhancement(spec, section, action, content_data)

            # 显示建议
            if 'suggestions' in result and result['suggestions']:
                self._print_info("AI 建议:")
                for suggestion in result['suggestions']:
                    self._print_info(f"  - {suggestion}")

        except json.JSONDecodeError:
            self._print_warning("AI 返回的内容无法解析，未应用增强")

    def _apply_enhancement(self, spec: Dict[str, Any], section: str, action: str, content: Any):
        """应用单个增强"""
        if action == 'add':
            if section in spec:
                if isinstance(spec[section], list):
                    spec[section].append(content)
                else:
                    self._print_warning(f"无法添加到非列表字段: {section}")
            else:
                spec[section] = content

        elif action == 'update':
            if isinstance(content, dict):
                for key, value in content.items():
                    if section in spec and key in spec[section]:
                        spec[section][key] = value
                    else:
                        self._print_warning(f"无法更新: {section}.{key}")

        elif action == 'delete':
            if isinstance(content, str) and '.' in content:
                # 处理嵌套路径删除
                parts = content.split('.')
                current = spec
                for part in parts[:-1]:
                    if part in current:
                        current = current[part]
                    else:
                        return
                if parts[-1] in current:
                    del current[parts[-1]]

    def _print_success(self, message: str):
        """打印成功消息"""
        print(f"✓ {message}")

    def _print_error(self, message: str):
        """打印错误消息"""
        print(f"✗ {message}", file=sys.stderr)

    def _print_info(self, message: str):
        """打印信息消息"""
        print(f"  {message}")

    def _print_warning(self, message: str):
        """打印警告消息"""
        print(f"! {message}")
