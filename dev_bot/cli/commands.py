#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SDD CLI 命令实现
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

import yaml


class BaseCommand:
    """命令基类"""
    
    def __init__(self, args):
        self.args = args
    
    def execute(self):
        """执行命令"""
        raise NotImplementedError
    
    def _print_success(self, message: str):
        """打印成功消息"""
        print(f"✓ {message}")
    
    def _print_error(self, message: str):
        """打印错误消息"""
        print(f"✗ {message}", file=sys.stderr)
    
    def _print_info(self, message: str):
        """打印信息消息"""
        print(f"  {message}")


class InitCommand(BaseCommand):
    """初始化 SDD 项目"""
    
    def execute(self):
        project_name = self.args.project_name
        template = self.args.template
        
        project_path = Path.cwd() / project_name
        
        if project_path.exists():
            self._print_error(f"项目目录已存在: {project_path}")
            sys.exit(1)
        
        self._print_info(f"创建 SDD 项目: {project_name}")
        
        # 创建项目结构
        self._create_project_structure(project_path, template)
        
        # 创建配置文件
        self._create_config(project_path)
        
        # 创建示例 spec
        self._create_example_spec(project_path)
        
        self._print_success(f"项目创建完成: {project_path}")
        self._print_info(f"进入项目目录: cd {project_name}")
        self._print_info("使用 'sdd new-spec' 创建新的 spec 文件")
    
    def _create_project_structure(self, project_path: Path, template: str):
        """创建项目结构"""
        project_path.mkdir(parents=True)
        
        # 基础目录
        dirs = ['specs', 'src', 'tests', 'docs']
        for d in dirs:
            (project_path / d).mkdir()
        
        # 根据模板创建额外目录
        if template in ['standard', 'full']:
            (project_path / 'src' / 'components').mkdir()
            (project_path / 'src' / 'utils').mkdir()
        
        if template == 'full':
            (project_path / 'scripts').mkdir()
            (project_path / 'examples').mkdir()
            (project_path / 'config').mkdir()
        
        # 创建 __init__.py
        (project_path / 'src' / '__init__.py').touch()
        (project_path / 'tests' / '__init__.py').touch()
    
    def _create_config(self, project_path: Path):
        """创建配置文件"""
        config = {
            "project": {
                "name": project_path.name,
                "version": "0.1.0",
                "description": ""
            },
            "sdd": {
                "specs_dir": "specs",
                "src_dir": "src",
                "tests_dir": "tests",
                "default_spec_type": "feature"
            },
            "code_generation": {
                "framework": "auto",
                "style_guide": "pep8"
            }
        }
        
        config_path = project_path / 'sdd-config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _create_example_spec(self, project_path: Path):
        """创建示例 spec"""
        spec = {
            "spec_version": "1.0",
            "metadata": {
                "name": "example-feature",
                "type": "feature",
                "version": "1.0.0",
                "author": "",
                "created": ""
            },
            "description": "示例功能规格说明",
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "基础需求",
                    "description": "这是示例需求描述",
                    "priority": "high",
                    "status": "pending"
                }
            ],
            "api": [],
            "components": [],
            "tests": []
        }
        
        spec_path = project_path / 'specs' / 'example.json'
        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)


class NewSpecCommand(BaseCommand):
    """创建新的 spec 文件"""
    
    def execute(self):
        spec_name = self.args.spec_name
        spec_type = self.args.type
        output_dir = Path(self.args.output) if self.args.output else Path.cwd() / 'specs'
        
        spec_path = output_dir / f"{spec_name}.json"
        
        if spec_path.exists():
            self._print_error(f"spec 文件已存在: {spec_path}")
            sys.exit(1)
        
        self._print_info(f"创建 spec 文件: {spec_name}")
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成 spec 内容
        spec = self._generate_spec(spec_name, spec_type)
        
        # 写入文件
        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        self._print_success(f"spec 文件创建完成: {spec_path}")
        self._print_info("使用 'sdd validate' 验证 spec 文件")
    
    def _generate_spec(self, name: str, spec_type: str) -> Dict[str, Any]:
        """生成 spec 内容"""
        spec = {
            "spec_version": "1.0",
            "metadata": {
                "name": name,
                "type": spec_type,
                "version": "1.0.0",
                "author": "",
                "created": "",
                "updated": ""
            },
            "description": f"{spec_type} 规格说明",
        }
        
        # 根据 spec 类型添加特定字段
        if spec_type == 'feature':
            spec.update({
                "requirements": [],
                "user_stories": [],
                "acceptance_criteria": []
            })
        elif spec_type == 'api':
            spec.update({
                "base_path": "/api/v1",
                "endpoints": [],
                "models": [],
                "authentication": {}
            })
        elif spec_type == 'component':
            spec.update({
                "props": [],
                "events": [],
                "slots": [],
                "methods": []
            })
        elif spec_type == 'service':
            spec.update({
                "interfaces": [],
                "dependencies": [],
                "configuration": {}
            })
        
        return spec


class ValidateCommand(BaseCommand):
    """验证 spec 文件"""
    
    def __init__(self, args):
        self.args = args
    
    def execute(self):
        spec_file = Path(self.args.spec_file)
        
        if not spec_file.exists():
            self._print_error(f"spec 文件不存在: {spec_file}")
            sys.exit(1)
        
        self._print_info(f"验证 spec 文件: {spec_file}")
        
        # 读取 spec 文件
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                if spec_file.suffix in ['.yaml', '.yml']:
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)
        except Exception as e:
            self._print_error(f"解析失败: {e}")
            sys.exit(1)
        
        # 验证 spec
        errors = self._validate_spec(spec)
        
        if errors:
            self._print_error(f"验证失败，发现 {len(errors)} 个错误:")
            for error in errors:
                self._print_info(f"  - {error}")
            sys.exit(1)
        else:
            self._print_success("spec 文件验证通过")
    
    def _validate_spec(self, spec: Dict[str, Any]) -> list:
        """验证 spec 内容"""
        errors = []
        
        # 检查必需字段
        required_fields = ['spec_version', 'metadata']
        for field in required_fields:
            if field not in spec:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查 metadata
        if 'metadata' in spec:
            metadata = spec['metadata']
            metadata_required = ['name', 'type', 'version']
            for field in metadata_required:
                if field not in metadata:
                    errors.append(f"metadata 缺少必需字段: {field}")
        
        # 检查 spec 类型
        if 'metadata' in spec and 'type' in spec['metadata']:
            spec_type = spec['metadata']['type']
            valid_types = ['feature', 'api', 'component', 'service']
            if spec_type not in valid_types:
                errors.append(f"无效的 spec 类型: {spec_type}")
        
        return errors


class AISpecCommand(BaseCommand):
    """使用 AI 创建 spec"""
    
    def execute(self):
        spec_name = self.args.spec_name
        spec_type = self.args.type
        description = self.args.description or ""
        ai_tool = self.args.ai_tool or "iflow"
        
        output_dir = Path(self.args.output) if self.args.output else Path.cwd() / 'specs'
        spec_path = output_dir / f"{spec_name}.json"
        
        if spec_path.exists():
            self._print_error(f"spec 文件已存在: {spec_path}")
            sys.exit(1)
        
        self._print_info(f"使用 AI 创建 spec: {spec_name}")
        self._print_info(f"AI 工具: {ai_tool}")
        self._print_info(f"Spec 类型: {spec_type}")
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成 prompt
        prompt = self._generate_prompt(spec_name, spec_type, description)
        
        # 调用 AI 工具
        self._print_info("正在调用 AI 生成 spec...")
        spec_content = self._call_ai_tool(ai_tool, prompt)
        
        # 解析 AI 返回的内容
        spec = self._parse_ai_response(spec_content, spec_name, spec_type)
        
        # 写入文件
        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        self._print_success(f"spec 文件创建完成: {spec_path}")
        self._print_info("使用 'sdd validate' 验证 spec 文件")
    
    def _generate_prompt(self, name: str, spec_type: str, description: str) -> str:
        """生成 AI prompt"""
        
        type_descriptions = {
            'feature': '功能规格说明，包含需求、用户故事和验收标准',
            'api': 'API 规格，包含端点、模型和认证信息',
            'component': 'UI 组件规格，包含属性、事件和方法',
            'service': '服务规格，包含接口、依赖和配置'
        }
        
        prompt = f"""请为以下内容创建一个 {spec_type} 类型的规格说明：

名称: {name}
类型: {type_descriptions.get(spec_type, spec_type)}
描述: {description if description else '请根据名称合理推测'}

请严格按照以下 JSON 格式输出，只返回 JSON，不要有任何其他文字：

{{
  "spec_version": "1.0",
  "metadata": {{
    "name": "{name}",
    "type": "{spec_type}",
    "version": "1.0.0",
    "author": "",
    "created": "",
    "updated": ""
  }},
  "description": "详细的功能描述",
"""

        if spec_type == 'feature':
            prompt += """
  "requirements": [
    {
      "id": "REQ-001",
      "title": "需求标题",
      "description": "详细的需求描述",
      "priority": "high",
      "status": "pending"
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
        elif spec_type == 'api':
            prompt += """
  "base_path": "/api/v1",
  "endpoints": [
    {
      "path": "/resource",
      "method": "GET",
      "summary": "接口摘要",
      "description": "接口描述",
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
    "type": "bearer",
    "description": "认证方式描述"
  }
"""
        elif spec_type == 'component':
            prompt += """
  "props": [
    {
      "name": "propName",
      "type": "string",
      "required": false,
      "default": "",
      "description": "属性描述"
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
      "description": "方法描述",
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
        elif spec_type == 'service':
            prompt += """
  "interfaces": [
    {
      "name": "InterfaceName",
      "methods": [
        {
          "name": "methodName",
          "description": "方法描述",
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
    
    def _call_ai_tool(self, ai_tool: str, prompt: str) -> str:
        """调用 AI 工具"""
        try:
            # 尝试使用配置的 AI 工具
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
    
    def _parse_ai_response(self, response: str, name: str, spec_type: str) -> Dict[str, Any]:
        """解析 AI 返回的内容"""
        # 尝试提取 JSON（处理可能的 markdown 代码块）
        content = response.strip()
        
        # 移除 markdown 代码块标记
        if content.startswith('```'):
            lines = content.split('\n')
            if lines[0].startswith('```'):
                content = '\n'.join(lines[1:])
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
        
        # 尝试解析 JSON
        try:
            spec = json.loads(content)
        except json.JSONDecodeError:
            self._print_error("AI 返回的内容无法解析为 JSON")
            self._print_info("将创建一个空的 spec 模板")
            spec = self._generate_spec(name, spec_type)
        
        return spec
    
    def _generate_spec(self, name: str, spec_type: str) -> Dict[str, Any]:
        """生成基础 spec 模板"""
        spec = {
            "spec_version": "1.0",
            "metadata": {
                "name": name,
                "type": spec_type,
                "version": "1.0.0",
                "author": "",
                "created": "",
                "updated": ""
            },
            "description": f"{spec_type} 规格说明",
        }
        
        if spec_type == 'feature':
            spec.update({
                "requirements": [],
                "user_stories": [],
                "acceptance_criteria": []
            })
        elif spec_type == 'api':
            spec.update({
                "base_path": "/api/v1",
                "endpoints": [],
                "models": [],
                "authentication": {}
            })
        elif spec_type == 'component':
            spec.update({
                "props": [],
                "events": [],
                "slots": [],
                "methods": []
            })
        elif spec_type == 'service':
            spec.update({
                "interfaces": [],
                "dependencies": [],
                "configuration": {}
            })
        
        return spec