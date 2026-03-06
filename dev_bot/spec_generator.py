#!/usr/bin/env python3

"""
Spec 生成器 - 从已有工程代码生成 spec
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from dev_bot.ai_prompts import get_spec_generation_prompt
from dev_bot.project_scanner import scan_project


class SpecGenerator:
    """Spec 生成器"""

    def __init__(self, project_path: Path, ai_tool: str = "iflow"):
        self.project_path = Path(project_path)
        self.ai_tool = ai_tool
        self.project_info = None

    def analyze_project(self) -> Dict[str, Any]:
        """分析工程"""
        self.project_info = scan_project(self.project_path)
        return self.project_info

    def generate_spec(self, spec_type: str = "feature", spec_name: str = None) -> Dict[str, Any]:
        """生成 spec"""
        if not self.project_info:
            self.analyze_project()

        if spec_name is None:
            spec_name = self.project_path.name

        prompt = self._generate_prompt(spec_type, spec_name)

        try:
            result = subprocess.run(
                [self.ai_tool],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=180
            )

            if result.returncode == 0:
                spec = self._parse_ai_response(result.stdout, spec_name, spec_type)
                return spec
            else:
                raise Exception(f"AI 调用失败: {result.stderr}")
        except Exception as e:
            print(f"错误: {e}")
            return self._generate_fallback_spec(spec_name, spec_type)

    def _generate_prompt(self, spec_type: str, spec_name: str) -> str:
        """生成 AI prompt（使用新的提示词模板）"""
        structure = self.project_info.get("structure", {})
        code = self.project_info.get("code", {})

        # 提取技术栈信息
        languages = structure.get("languages", {})
        frameworks = structure.get("frameworks", [])
        dependencies = structure.get("dependencies", [])

        tech_stack_parts = []
        if languages:
            tech_stack_parts.append(f"语言: {', '.join(languages.keys())}")
        if frameworks:
            tech_stack_parts.append(f"框架: {', '.join(frameworks)}")
        if dependencies:
            tech_stack_parts.append(f"主要依赖: {', '.join(dependencies[:5])}")
        tech_stack = "\n".join(tech_stack_parts) if tech_stack_parts else "未知"

        # 格式化结构信息
        structure_str = json.dumps(structure, indent=2, ensure_ascii=False)

        # 格式化代码分析信息
        code_str = json.dumps(code, indent=2, ensure_ascii=False)

        # 使用新的提示词模板
        return get_spec_generation_prompt(
            project_name=spec_name,
            project_path=str(self.project_path),
            spec_type=spec_type,
            tech_stack=tech_stack,
            structure=structure_str,
            code_analysis=code_str,
            timestamp=datetime.now().isoformat()
        )

    def _parse_ai_response(self, response: str, name: str, spec_type: str) -> Dict[str, Any]:
        """解析 AI 返回的内容"""
        content = response.strip()

        # 移除 markdown 代码块标记
        if content.startswith('```'):
            lines = content.split('\n')
            if lines[0].startswith('```'):
                content = '\n'.join(lines[1:])
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

        try:
            spec = json.loads(content)
            return spec
        except json.JSONDecodeError:
            print("AI 返回的内容无法解析为 JSON，使用回退方案")
            return self._generate_fallback_spec(name, spec_type)

    def _generate_fallback_spec(self, name: str, spec_type: str) -> Dict[str, Any]:
        """生成回退 spec（基于代码分析）"""
        import datetime

        spec = {
            "spec_version": "1.0",
            "metadata": {
                "name": name,
                "type": spec_type,
                "version": "1.0.0",
                "author": "Dev-Bot Auto-Generated",
                "created": datetime.datetime.now().isoformat(),
                "updated": datetime.datetime.now().isoformat()
            },
            "description": f"基于代码分析自动生成的 {spec_type} 规格",
        }

        structure = self.project_info.get("structure", {})
        code = self.project_info.get("code", {})

        if spec_type == "feature":
            # 从代码中提取需求
            requirements = []
            for cls in code.get("classes", []):
                requirements.append({
                    "id": f"REQ-{len(requirements)+1:03d}",
                    "title": f"实现 {cls['name']} 类",
                    "description": f"在 {cls['file']} 中定义的类",
                    "priority": "medium",
                    "status": "implemented"
                })

            spec.update({
                "requirements": requirements,
                "user_stories": [],
                "acceptance_criteria": []
            })

        elif spec_type == "api":
            # 从代码中提取端点
            endpoints = []
            for endpoint in code.get("endpoints", []):
                endpoints.append({
                    "path": endpoint.get("name", "/"),
                    "method": endpoint.get("method", "GET"),
                    "summary": f"{endpoint['method']} {endpoint['name']}",
                    "description": f"在 {endpoint['file']} 中定义",
                    "parameters": [],
                    "responses": {
                        "200": {
                            "description": "成功",
                            "schema": {}
                        }
                    }
                })

            spec.update({
                "base_path": "/api",
                "endpoints": endpoints,
                "models": [],
                "authentication": {}
            })

        elif spec_type == "component":
            # 从代码中提取方法
            methods = []
            for func in code.get("functions", []):
                methods.append({
                    "name": func["name"],
                    "description": f"在 {func['file']} 中定义的函数",
                    "returns": "any"
                })

            spec.update({
                "props": [],
                "events": [],
                "slots": [],
                "methods": methods,
                "examples": []
            })

        elif spec_type == "service":
            # 从代码中提取依赖
            dependencies = []
            deps = structure.get("dependencies", {})
            for lang, deps_list in deps.items():
                for dep in deps_list:
                    dependencies.append({
                        "name": dep,
                        "version": "latest",
                        "type": lang
                    })

            spec.update({
                "interfaces": [],
                "dependencies": dependencies,
                "configuration": {}
            })

        return spec


def generate_spec_from_project(project_path: Path, spec_type: str = "feature",
                                spec_name: str = None, ai_tool: str = "iflow") -> Dict[str, Any]:
    """从工程生成 spec"""
    generator = SpecGenerator(project_path, ai_tool)
    return generator.generate_spec(spec_type, spec_name)
