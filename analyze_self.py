#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分析 dev-bot 项目本身
"""

from pathlib import Path

from dev_bot.project_scanner import scan_project
from dev_bot.spec_generator import SpecGenerator


def analyze_dev_bot():
    """分析 dev-bot 项目"""
    project_path = Path.cwd()
    
    print("=" * 60)
    print("分析 Dev-Bot 项目")
    print("=" * 60)
    
    # 扫描项目
    print("\n📂 扫描项目结构...")
    project_info = scan_project(project_path)
    
    structure = project_info["structure"]
    code = project_info["code"]
    
    # 显示统计信息
    print(f"\n📊 项目统计:")
    print(f"  文件数: {len(structure.get('files', []))}")
    print(f"  目录数: {len(structure.get('directories', []))}")
    print(f"  语言: {', '.join(structure.get('languages', {}).keys())}")
    print(f"  框架: {', '.join(structure.get('frameworks', []))}")
    
    print(f"\n💻 代码分析:")
    print(f"  类: {len(code.get('classes', []))}")
    print(f"  函数: {len(code.get('functions', []))}")
    print(f"  端点: {len(code.get('endpoints', []))}")
    
    # 显示主要模块
    print(f"\n📦 主要模块:")
    if code.get('classes'):
        for cls in code.get('classes', [])[:10]:
            print(f"  - {cls['name']} ({cls['file']})")
    
    # 生成 spec
    print(f"\n🔧 生成 Spec...")
    generator = SpecGenerator(project_path)
    spec = generator.generate_spec("feature", "dev-bot")
    
    # 保存 spec
    specs_dir = project_path / "specs"
    specs_dir.mkdir(exist_ok=True)
    
    spec_file = specs_dir / "dev-bot.json"
    import json
    with open(spec_file, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Spec 已生成: {spec_file}")
    
    # 显示 spec 摘要
    print(f"\n📋 Spec 摘要:")
    print(f"  名称: {spec.get('metadata', {}).get('name')}")
    print(f"  类型: {spec.get('metadata', {}).get('type')}")
    print(f"  版本: {spec.get('metadata', {}).get('version')}")
    
    if spec.get('requirements'):
        print(f"  需求数: {len(spec['requirements'])}")
        for req in spec.get('requirements', [])[:5]:
            print(f"    - {req.get('id')}: {req.get('title')}")
    
    print(f"\n📝 下一步:")
    print(f"  1. 查看 spec: cat {spec_file}")
    print(f"  2. 验证 spec: dev-bot sdd validate {spec_file}")
    print(f"  3. 增强 spec: dev-bot sdd enhance {spec_file} --aspect all")
    print(f"  4. 继续开发: dev-bot run")


if __name__ == "__main__":
    analyze_dev_bot()