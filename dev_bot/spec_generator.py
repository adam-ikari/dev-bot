#!/usr/bin/env python3

"""
Spec 生成器 - 从已有工程代码生成 spec
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict

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
        """生成 AI prompt"""
        structure = self.project_info.get("structure", {})
        code = self.project_info.get("code", {})

        structure_str = json.dumps(structure, indent=2, ensure_ascii=False)
        code_str = json.dumps(code, indent=2, ensure_ascii=False)

        prompt = f"""请基于以下工程信息，生成一个 {spec_type} 类型的规格说明（spec）：

工程名称: {spec_name}
工程路径: {self.project_path}

工程结构：
```json
{structure_str}
```

代码分析：
```json
{code_str}
```

请按照以下 JSON 格式生成 spec，只返回 JSON，不要有任何其他文字：

{{
  "spec_version": "1.0",
  "metadata": {{
    "name": "{spec_name}",
    "type": "{spec_type}",
    "version": "1.0.0",
    "author": "",
    "created": "",
    "updated": ""
  }},
  "description": "基于代码分析生成的规格说明",
"""

        if spec_type == "feature":
            prompt += """
  "requirements": [
    {
      "id": "REQ-001",
      "title": "需求标题",
      "description": "基于代码实现的需求描述",
      "priority": "high",
      "status": "implemented"
    }
  ],
  "user_stories": [
    {
      "id": "US-001",
      "as_a": "用户角色",
      "i_want_to": "想要做什么",
      "so_that": "为了什么目的"
    }
  ],
  "acceptance_criteria": [
    {
      "requirement_id": "REQ-001",
      "criteria": [
        "验收条件1",
        "验收条件2"
      ]
    }
  ]
"""
        elif spec_type == "api":
            prompt += """
  "base_path": "/api",
  "endpoints": [
    {
      "path": "/endpoint",
      "method": "GET",
      "summary": "接口摘要",
      "description": "基于代码实现的接口描述",
      "parameters": [],
      "responses": {
        "200": {
          "description": "成功",
          "schema": {}
        }
      }
    }
  ],
  "models": [
    {
      "name": "ModelName",
      "properties": [
        {
          "name": "fieldName",
          "type": "string",
          "description": "字段描述"
        }
      ]
    }
  ],
  "authentication": {
    "type": "none",
    "description": "认证方式描述"
  }
"""
        elif spec_type == "component":
            prompt += """
  "props": [
    {
      "name": "propName",
      "type": "string",
      "required": false,
      "default": "",
      "description": "基于代码分析的属性描述"
    }
  ],
  "events": [
    {
      "name": "eventName",
      "description": "事件描述",
      "payload": {}
    }
  ],
  "slots": [
    {
      "name": "slotName",
      "description": "插槽描述"
    }
  ],
  "methods": [
    {
      "name": "methodName",
      "description": "基于代码分析的方法描述",
      "returns": "void"
    }
  ],
  "examples": [
    {
      "description": "使用示例",
      "code": "示例代码"
    }
  ]
"""
        elif spec_type == "service":
            prompt += """
  "interfaces": [
    {
      "name": "InterfaceName",
      "methods": [
        {
          "name": "methodName",
          "description": "基于代码分析的方法描述",
          "parameters": [],
          "returns": {}
        }
      ]
    }
  ],
  "dependencies": [
    {
      "name": "dependencyName",
      "version": ">=1.0.0",
      "type": "external"
    }
  ],
  "configuration": {
    "configKey": {
      "type": "string",
      "required": true,
      "description": "配置描述"
    }
  }
"""

        prompt += "\n}"

        return prompt

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
