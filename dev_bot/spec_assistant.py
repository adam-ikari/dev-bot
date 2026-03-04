#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Spec 交互工具 - 在开发循环中与 AI 交互补充 spec
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class SpecAssistant:
    """Spec 助手 - 辅助在开发循环中管理和增强 spec"""
    
    def __init__(self, spec_file: Optional[Path] = None, ai_tool: str = "iflow"):
        self.spec_file = spec_file
        self.ai_tool = ai_tool
        self.spec = None
        
        if spec_file and spec_file.exists():
            self._load_spec()
    
    def _load_spec(self):
        """加载 spec 文件"""
        if self.spec_file and self.spec_file.exists():
            with open(self.spec_file, 'r', encoding='utf-8') as f:
                self.spec = json.load(f)
    
    def _save_spec(self):
        """保存 spec 文件"""
        if self.spec_file and self.spec:
            with open(self.spec_file, 'w', encoding='utf-8') as f:
                json.dump(self.spec, f, indent=2, ensure_ascii=False)
    
    def interactive_enhance(self, aspect: str = "all"):
        """交互式增强 spec"""
        if not self.spec:
            print("❌ 未加载 spec 文件")
            return False
        
        print(f"📝 正在增强 spec: {aspect}")
        
        # 生成 prompt
        prompt = self._generate_interactive_prompt(aspect)
        
        # 调用 AI
        try:
            result = subprocess.run(
                [self.ai_tool],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("\n" + result.stdout)
                return True
            else:
                print(f"❌ AI 调用失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def _generate_interactive_prompt(self, aspect: str) -> str:
        """生成交互式 prompt"""
        spec_content = json.dumps(self.spec, indent=2, ensure_ascii=False)
        
        prompts = {
            'analyze': f"""请分析以下 spec 文件，提供详细的改进建议：

当前 spec：
```json
{spec_content}
```

请从以下方面分析：
1. 完整性：是否有缺失的部分
2. 一致性：内容是否自洽
3. 可实现性：需求是否明确可实现
4. 优先级：是否需要调整优先级

请提供具体的改进建议。
""",
            'add_requirement': f"""基于当前 spec，帮助我添加一个新的需求：

当前 spec：
```json
{spec_content}
```

请引导我完成新需求的添加，包括：
1. 需求的 ID 和标题
2. 详细的描述
3. 优先级
4. 相关的用户故事
5. 验收标准

请以对话的形式引导我输入信息。
""",
            'refine': f"""请帮助我优化当前 spec 的描述：

当前 spec：
```json
{spec_content}
```

请：
1. 优化描述的语言，使其更清晰
2. 补充缺失的细节
3. 修正不一致的地方
4. 添加必要的注释说明

请返回优化后的完整 spec。
""",
            'all': f"""全面分析并增强以下 spec：

当前 spec：
```json
{spec_content}
```

请：
1. 分析完整性和一致性
2. 补充缺失的需求、用户故事、验收标准
3. 优化现有内容的描述
4. 提供改进建议

请返回增强后的完整 spec。
"""
        }
        
        return prompts.get(aspect, prompts['all'])
    
    def ask_question(self, question: str) -> str:
        """向 AI 提问关于 spec 的问题"""
        if not self.spec:
            return "❌ 未加载 spec 文件"
        
        prompt = f"""基于以下 spec 回答问题：

Spec 内容：
```json
{json.dumps(self.spec, indent=2, ensure_ascii=False)}
```

问题：{question}

请提供详细的答案。
"""
        
        try:
            result = subprocess.run(
                [self.ai_tool],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"❌ AI 调用失败: {result.stderr}"
        except Exception as e:
            return f"❌ 错误: {e}"
    
    def generate_missing_parts(self) -> Dict[str, Any]:
        """生成缺失的部分"""
        if not self.spec:
            return {}
        
        spec_type = self.spec.get('metadata', {}).get('type', 'feature')
        
        missing = {}
        
        if spec_type == 'feature':
            if not self.spec.get('requirements'):
                missing['requirements'] = []
            if not self.spec.get('user_stories'):
                missing['user_stories'] = []
            if not self.spec.get('acceptance_criteria'):
                missing['acceptance_criteria'] = []
        
        elif spec_type == 'api':
            if not self.spec.get('endpoints'):
                missing['endpoints'] = []
            if not self.spec.get('models'):
                missing['models'] = []
        
        elif spec_type == 'component':
            if not self.spec.get('props'):
                missing['props'] = []
            if not self.spec.get('methods'):
                missing['methods'] = []
        
        return missing
    
    def suggest_improvements(self) -> list:
        """建议改进"""
        suggestions = []
        
        if not self.spec:
            return ["❌ 未加载 spec 文件"]
        
        # 检查描述
        description = self.spec.get('description', '')
        if len(description) < 50:
            suggestions.append("描述过于简短，建议补充更多细节")
        
        # 检查需求
        requirements = self.spec.get('requirements', [])
        if not requirements:
            suggestions.append("缺少需求列表，建议添加")
        
        # 检查用户故事
        user_stories = self.spec.get('user_stories', [])
        if not user_stories and requirements:
            suggestions.append("有需求但缺少用户故事，建议补充")
        
        # 检查验收标准
        acceptance_criteria = self.spec.get('acceptance_criteria', [])
        if not acceptance_criteria and requirements:
            suggestions.append("有需求但缺少验收标准，建议补充")
        
        return suggestions


def create_spec_assistant(spec_file: Path, ai_tool: str = "iflow") -> SpecAssistant:
    """创建 spec 助手实例"""
    return SpecAssistant(spec_file, ai_tool)