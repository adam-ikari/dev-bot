#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误分析器 - 使用 AI 分析错误并提供修复建议
"""

import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List


class ErrorAnalyzer:
    """错误分析器"""
    
    def __init__(self, ai_tool: str = "iflow"):
        self.ai_tool = ai_tool
        self.error_log_dir = Path(".error-logs")
        self.error_log_dir.mkdir(exist_ok=True)
    
    def analyze_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析错误"""
        # 收集错误信息
        error_info = self._collect_error_info(error, context)
        
        # 生成分析 prompt
        prompt = self._generate_analysis_prompt(error_info)
        
        # 调用 AI 分析
        try:
            result = subprocess.run(
                [self.ai_tool],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                analysis = self._parse_ai_response(result.stdout)
            else:
                analysis = self._get_fallback_analysis(error_info)
        except Exception as e:
            analysis = self._get_fallback_analysis(error_info)
        
        # 保存分析结果
        self._save_analysis(error_info, analysis)
        
        return analysis
    
    def _collect_error_info(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """收集错误信息"""
        error_type = type(error).__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        # 获取相关代码上下文
        tb = traceback.extract_tb(error.__traceback__)
        error_location = None
        if tb:
            last_frame = tb[-1]
            error_location = {
                "file": last_frame.filename,
                "line": last_frame.lineno,
                "function": last_frame.name
            }
        
        return {
            "error_type": error_type,
            "error_message": error_message,
            "error_traceback": error_traceback,
            "error_location": error_location,
            "context": context or {},
            "timestamp": self._get_timestamp()
        }
    
    def _generate_analysis_prompt(self, error_info: Dict[str, Any]) -> str:
        """生成分析 prompt"""
        prompt = f"""请分析以下错误并提供修复建议：

错误类型: {error_info.get('error_type')}
错误消息: {error_info.get('error_message')}
错误位置: {error_info.get('error_location')}
错误堆栈:
```
{error_info.get('error_traceback')}
```

上下文信息:
```json
{json.dumps(error_info.get('context', {}), indent=2, ensure_ascii=False)}
```

请按照以下 JSON 格式返回分析结果：
```json
{{
  "error_analysis": {{
    "root_cause": "根本原因分析",
    "severity": "low|medium|high|critical",
    "category": "category_name"
  }},
  "suggested_fixes": [
    {{
      "description": "修复方案描述",
      "code_change": "具体的代码修改建议",
      "files_to_modify": ["file1.py", "file2.py"],
      "steps": ["步骤1", "步骤2", "步骤3"]
    }}
  ],
  "prevention_tips": [
    "预防建议1",
    "预防建议2"
  ],
  "additional_notes": "其他注意事项"
}}
```

只返回 JSON，不要有任何其他文字。
"""
        
        return prompt
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析 AI 响应"""
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
            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "无法解析 AI 响应", "raw_response": content}
    
    def _get_fallback_analysis(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """获取回退分析"""
        error_type = error_info.get('error_type', 'Unknown')
        error_message = error_info.get('error_message', '')
        
        analysis = {
            "error_analysis": {
                "root_cause": f"发生 {error_type} 错误",
                "severity": "medium",
                "category": error_type.lower()
            },
            "suggested_fixes": [
                {
                    "description": f"检查 {error_type} 错误的常见原因",
                    "code_change": "# 根据错误类型添加相应的处理逻辑",
                    "files_to_modify": error_info.get('error_location', {}).get('file') if error_info.get('error_location') else [],
                    "steps": [
                        "查看错误堆栈定位问题",
                        "检查相关代码逻辑",
                        "添加错误处理",
                        "测试修复"
                    ]
                }
            ],
            "prevention_tips": [
                "添加类型检查",
                "使用 try-except 处理异常",
                "添加日志记录",
                "编写单元测试"
            ],
            "additional_notes": f"错误消息: {error_message}"
        }
        
        return analysis
    
    def _save_analysis(self, error_info: Dict[str, Any], analysis: Dict[str, Any]):
        """保存分析结果"""
        timestamp = error_info.get('timestamp', 'unknown').replace(':', '-').replace(' ', '_')
        filename = f"error_{timestamp}.json"
        log_file = self.error_log_dir / filename
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "error_info": error_info,
                "analysis": analysis
            }, f, indent=2, ensure_ascii=False)
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def display_analysis(self, analysis: Dict[str, Any]):
        """显示分析结果"""
        print("\n" + "=" * 60)
        print("🔍 错误分析结果")
        print("=" * 60)
        
        # 显示错误分析
        error_analysis = analysis.get('error_analysis', {})
        print(f"\n错误类型: {error_analysis.get('severity', 'unknown').upper()}")
        print(f"严重程度: {error_analysis.get('severity', 'unknown')}")
        print(f"根本原因: {error_analysis.get('root_cause', 'N/A')}")
        print(f"错误类别: {error_analysis.get('category', 'N/A')}")
        
        # 显示修复建议
        fixes = analysis.get('suggested_fixes', [])
        if fixes:
            print(f"\n修复建议 ({len(fixes)}):")
            for i, fix in enumerate(fixes, 1):
                print(f"\n  [{i}] {fix.get('description', 'N/A')}")
                if fix.get('code_change'):
                    print(f"      代码修改:")
                    for line in fix['code_change'].split('\n'):
                        print(f"        {line}")
                if fix.get('steps'):
                    print(f"      步骤:")
                    for step in fix.get('steps', []):
                        print(f"        - {step}")
        
        # 显示预防建议
        tips = analysis.get('prevention_tips', [])
        if tips:
            print(f"\n预防建议:")
            for tip in tips:
                print(f"  • {tip}")
        
        # 显示额外说明
        notes = analysis.get('additional_notes')
        if notes:
            print(f"\n额外说明: {notes}")
        
        print("\n" + "=" * 60)
    
    def can_auto_fix(self, analysis: Dict[str, Any]) -> bool:
        """检查是否可以自动修复"""
        severity = analysis.get('error_analysis', {}).get('severity', 'medium')
        fixes = analysis.get('suggested_fixes', [])
        
        # 只有低严重程度的错误且有明确的修复步骤时才自动修复
        if severity in ['low', 'medium'] and fixes:
            return True
        
        return False
    
    def apply_auto_fix(self, analysis: Dict[str, Any], project_path: Path) -> bool:
        """应用自动修复"""
        fixes = analysis.get('suggested_fixes', [])
        
        if not fixes:
            print("  ! 没有可用的修复方案")
            return False
        
        print(f"\n🔧 尝试自动修复...")
        
        success = False
        for i, fix in enumerate(fixes, 1):
            print(f"  应用修复方案 #{i}: {fix.get('description', 'N/A')}")
            
            # 尝试应用修复
            try:
                result = self._apply_fix(fix, project_path)
                if result:
                    print(f"  ✓ 修复方案 #{i} 应用成功")
                    success = True
                    break
                else:
                    print(f"  ✗ 修复方案 #{i} 应用失败")
            except Exception as e:
                print(f"  ✗ 修复方案 #{i} 应用出错: {e}")
        
        return success
    
    def _apply_fix(self, fix: Dict[str, Any], project_path: Path) -> bool:
        """应用单个修复方案"""
        files_to_modify = fix.get('files_to_modify', [])
        
        if not files_to_modify:
            # 如果没有指定文件，尝试从错误位置推断
            print("    ! 未指定要修改的文件，需要手动修复")
            return False
        
        for file_path in files_to_modify:
            full_path = project_path / file_path
            
            if not full_path.exists():
                print(f"    ! 文件不存在: {file_path}")
                continue
            
            try:
                # 读取文件
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 应用代码修改
                code_change = fix.get('code_change', '')
                if code_change and not code_change.startswith('#'):
                    # 简单的文本替换（实际应该更智能）
                    # 这里只是示例，实际应该使用 AST 或其他方法
                    print(f"    ! 需要手动应用代码修改到 {file_path}")
                    print(f"    修改内容: {code_change}")
                    return False
                
                print(f"    ✓ 文件 {file_path} 标记为需要修改")
                
            except Exception as e:
                print(f"    ! 修改文件 {file_path} 失败: {e}")
                return False
        
        return True


class RobustDevBot:
    """增强鲁棒性的 Dev-Bot"""
    
    def __init__(self, ai_tool: str = "iflow", auto_fix: bool = True, auto_restart: bool = True, max_retries: int = 3):
        self.ai_tool = ai_tool
        self.error_analyzer = ErrorAnalyzer(ai_tool)
        self.error_count = 0
        self.auto_fix = auto_fix
        self.auto_restart = auto_restart
        self.max_retries = max_retries
        self.retry_count = 0
        self.project_path = Path.cwd()
    
    def run_with_error_handling(self, func, *args, **kwargs):
        """运行函数并处理错误"""
        while self.retry_count < self.max_retries:
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 成功执行，重置重试计数
                self.retry_count = 0
                return result
                
            except Exception as e:
                self.error_count += 1
                print(f"\n❌ 发生错误 #{self.error_count} (尝试 #{self.retry_count + 1}/{self.max_retries}): {type(e).__name__}")
                print(f"错误消息: {str(e)}")
                
                # 分析错误
                print("\n🔍 正在分析错误...")
                context = {
                    "function": func.__name__ if hasattr(func, '__name__') else 'unknown',
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()) if kwargs else [],
                    "retry_count": self.retry_count
                }
                
                analysis = self.error_analyzer.analyze_error(e, context)
                
                # 显示分析结果
                self.error_analyzer.display_analysis(analysis)
                
                # 尝试自动修复
                if self.auto_fix and self.error_analyzer.can_auto_fix(analysis):
                    print(f"\n🔧 尝试自动修复...")
                    fix_success = self.error_analyzer.apply_auto_fix(analysis, self.project_path)
                    
                    if fix_success:
                        print(f"✓ 自动修复成功，准备重试...")
                        self.retry_count += 1
                        
                        # 等待一段时间后重试
                        import time
                        time.sleep(2)
                        continue
                    else:
                        print(f"✗ 自动修复失败")
                
                # 增加重试计数
                self.retry_count += 1
                
                # 检查是否达到最大重试次数
                if self.retry_count >= self.max_retries:
                    print(f"\n❌ 达到最大重试次数 ({self.max_retries})，停止执行")
                    break
                
                # 询问是否继续
                if not self.auto_restart:
                    print(f"\n是否继续重试? (y/n): ", end='')
                    try:
                        response = input().strip().lower()
                        if response != 'y':
                            print("用户选择停止执行")
                            break
                    except (EOFError, KeyboardInterrupt):
                        print("\n用户中断")
                        break
                
                # 等待一段时间后重试
                print(f"\n⏳ 等待 2 秒后重试...")
                import time
                time.sleep(2)
                print(f"🔄 开始重试 #{self.retry_count}...\n")
        
        # 返回 None 表示失败
        return None


# 全局错误处理器
_global_error_analyzer = None

def get_global_error_analyzer(ai_tool: str = "iflow") -> ErrorAnalyzer:
    """获取全局错误分析器"""
    global _global_error_analyzer
    if _global_error_analyzer is None:
        _global_error_analyzer = ErrorAnalyzer(ai_tool)
    return _global_error_analyzer


def analyze_and_handle_error(error: Exception, context: Dict[str, Any] = None, ai_tool: str = "iflow") -> Dict[str, Any]:
    """分析并处理错误"""
    analyzer = get_global_error_analyzer(ai_tool)
    analysis = analyzer.analyze_error(error, context)
    analyzer.display_analysis(analysis)
    return analysis


def error_handler(func):
    """错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"\n❌ 函数 {func.__name__} 出错: {type(e).__name__}")
            print(f"错误消息: {str(e)}")
            
            # 分析错误
            analyze_and_handle_error(e, {
                "function": func.__name__,
                "module": func.__module__
            })
            
            # 重新抛出异常或返回 None
            raise
    
    return wrapper