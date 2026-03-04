#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
技术栈检测器测试
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dev_bot.tech_stack_detector import TechStackDetector, detect_tech_stack, generate_tech_stack_report


def test_tech_stack_detector():
    """测试技术栈检测器"""
    print("测试技术栈检测器...")
    
    # 测试 1: 检测 Python 项目
    print("  测试 1: 检测 Python 项目...")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建 pyproject.toml
        pyproject = temp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
dependencies = [
    "fastapi",
    "pytest",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")
        
        # 创建一些 Python 文件
        (temp_path / "src").mkdir()
        (temp_path / "src" / "main.py").write_text("print('Hello')")
        (temp_path / "src" / "utils.py").write_text("def test(): pass")
        
        detector = TechStackDetector(temp_path)
        tech_stack = detector.detect()
        
        assert "Python" in tech_stack["programming_language"]
        assert "FastAPI" in tech_stack["frameworks"]
        assert "pytest" == tech_stack["test_framework"]
        assert "Hatchling" == tech_stack["build_tool"]
        print("    ✓ Python 项目检测成功")
    
    # 测试 2: 检测 JavaScript 项目
    print("  测试 2: 检测 JavaScript 项目...")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建 package.json
        package_json = temp_path / "package.json"
        package_json.write_text("""
{
  "name": "test-project",
  "dependencies": {
    "react": "^18.0.0",
    "express": "^4.18.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "vite": "^4.0.0"
  }
}
""")
        
        # 创建一些 JavaScript 文件
        (temp_path / "src").mkdir()
        (temp_path / "src" / "App.jsx").write_text("export default function App() {}")
        (temp_path / "src" / "index.js").write_text("console.log('Hello')")
        
        detector = TechStackDetector(temp_path)
        tech_stack = detector.detect()
        
        assert "JavaScript" in tech_stack["programming_language"]
        assert "React" in tech_stack["frameworks"]
        assert "Express" in tech_stack["frameworks"]
        assert "Jest" == tech_stack["test_framework"]
        assert "Vite" == tech_stack["build_tool"]
        print("    ✓ JavaScript 项目检测成功")
    
    # 测试 3: 生成报告
    print("  测试 3: 生成报告...")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        detector = TechStackDetector(temp_path)
        report = detector.generate_report()
        
        assert "技术栈识别报告" in report
        assert "编程语言" in report
        assert "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" in report
        print("    ✓ 报告生成成功")
    
    print("\n✅ 所有测试通过!")


def test_detect_tech_stack():
    """测试快捷函数"""
    print("\n测试快捷函数...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建 pyproject.toml
        (temp_path / "pyproject.toml").write_text('[project]\nname = "test"')
        
        tech_stack = detect_tech_stack(temp_path)
        
        assert isinstance(tech_stack, dict)
        assert "programming_language" in tech_stack
        assert "frameworks" in tech_stack
        print("  ✓ detect_tech_stack 函数工作正常")
    
    print("\n✅ 所有测试通过!")


def test_generate_tech_stack_report():
    """测试报告生成函数"""
    print("\n测试报告生成函数...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建 pyproject.toml
        (temp_path / "pyproject.toml").write_text('[project]\nname = "test"')
        
        report = generate_tech_stack_report(temp_path)
        
        assert "技术栈识别报告" in report
        assert "编程语言" in report
        print("  ✓ generate_tech_stack_report 函数工作正常")
    
    print("\n✅ 所有测试通过!")


if __name__ == "__main__":
    try:
        test_tech_stack_detector()
        test_detect_tech_stack()
        test_generate_tech_stack_report()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！技术栈检测器工作正常！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)