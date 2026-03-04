#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工程扫描器 - 扫描已有工程并分析代码结构
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class ProjectScanner:
    """工程扫描器"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.structure = {
            "directories": [],
            "files": [],
            "languages": {},
            "frameworks": [],
            "dependencies": {}
        }
    
    def scan(self) -> Dict[str, Any]:
        """扫描工程"""
        if not self.project_path.exists():
            raise ValueError(f"工程路径不存在: {self.project_path}")
        
        self._scan_directory(self.project_path)
        self._detect_languages()
        self._detect_frameworks()
        self._detect_dependencies()
        
        return self.structure
    
    def _scan_directory(self, path: Path, base_path: Optional[Path] = None):
        """扫描目录"""
        if base_path is None:
            base_path = self.project_path
        
        try:
            for item in path.iterdir():
                # 跳过隐藏目录和常见的忽略目录
                if item.name.startswith('.') or item.name in ['node_modules', 'venv', 'env', '__pycache__', 'dist', 'build']:
                    continue
                
                if item.is_dir():
                    rel_path = item.relative_to(base_path)
                    self.structure["directories"].append(str(rel_path))
                    self._scan_directory(item, base_path)
                elif item.is_file():
                    rel_path = item.relative_to(base_path)
                    self.structure["files"].append({
                        "path": str(rel_path),
                        "size": item.stat().st_size,
                        "extension": item.suffix
                    })
        except PermissionError:
            pass
    
    def _detect_languages(self):
        """检测使用的编程语言"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala'
        }
        
        for file_info in self.structure["files"]:
            ext = file_info["extension"]
            if ext in language_map:
                lang = language_map[ext]
                self.structure["languages"][lang] = self.structure["languages"].get(lang, 0) + 1
    
    def _detect_frameworks(self):
        """检测使用的框架"""
        frameworks = []
        
        # 检查 Python 框架
        if self._has_file('requirements.txt'):
            content = self._read_file('requirements.txt')
            if 'django' in content.lower():
                frameworks.append('Django')
            if 'flask' in content.lower():
                frameworks.append('Flask')
            if 'fastapi' in content.lower():
                frameworks.append('FastAPI')
        
        if self._has_file('pyproject.toml'):
            content = self._read_file('pyproject.toml')
            if 'fastapi' in content.lower():
                frameworks.append('FastAPI')
            if 'flask' in content.lower():
                frameworks.append('Flask')
        
        # 检查 Node.js 框架
        if self._has_file('package.json'):
            content = self._read_file('package.json')
            try:
                pkg = json.loads(content)
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                if 'react' in deps:
                    frameworks.append('React')
                if 'vue' in deps:
                    frameworks.append('Vue.js')
                if 'angular' in deps:
                    frameworks.append('Angular')
                if 'express' in deps:
                    frameworks.append('Express.js')
                if 'next' in deps:
                    frameworks.append('Next.js')
            except json.JSONDecodeError:
                pass
        
        self.structure["frameworks"] = list(set(frameworks))
    
    def _detect_dependencies(self):
        """检测依赖"""
        dependencies = {}
        
        # Python 依赖
        if self._has_file('requirements.txt'):
            dependencies['python'] = self._parse_requirements_txt()
        
        if self._has_file('pyproject.toml'):
            dependencies['python'] = self._parse_pyproject_toml()
        
        # Node.js 依赖
        if self._has_file('package.json'):
            dependencies['nodejs'] = self._parse_package_json()
        
        # Java 依赖
        if self._has_file('pom.xml'):
            dependencies['java'] = self._parse_pom_xml()
        
        self.structure["dependencies"] = dependencies
    
    def _has_file(self, filename: str) -> bool:
        """检查文件是否存在"""
        return (self.project_path / filename).exists()
    
    def _read_file(self, filename: str) -> str:
        """读取文件内容"""
        try:
            with open(self.project_path / filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    def _parse_requirements_txt(self) -> List[str]:
        """解析 requirements.txt"""
        content = self._read_file('requirements.txt')
        deps = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # 提取包名（去除版本号）
                pkg = line.split('>=')[0].split('==')[0].split('<=')[0].split('~=')[0].strip()
                if pkg:
                    deps.append(pkg)
        return deps
    
    def _parse_pyproject_toml(self) -> List[str]:
        """解析 pyproject.toml"""
        content = self._read_file('pyproject.toml')
        deps = []
        # 简单解析，实际应该使用 toml 库
        lines = content.split('\n')
        in_deps = False
        for line in lines:
            if 'dependencies' in line:
                in_deps = True
            if in_deps and line.strip().startswith('['):
                if 'dependencies' not in line:
                    in_deps = False
            if in_deps:
                # 提取依赖名
                if '=' in line and not line.strip().startswith('#'):
                    dep = line.split('=')[0].strip().replace('"', '').replace("'", '')
                    if dep:
                        deps.append(dep)
        return deps
    
    def _parse_package_json(self) -> Dict[str, str]:
        """解析 package.json"""
        content = self._read_file('package.json')
        try:
            pkg = json.loads(content)
            return {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
        except json.JSONDecodeError:
            return {}
    
    def _parse_pom_xml(self) -> List[str]:
        """解析 pom.xml"""
        content = self._read_file('pom.xml')
        deps = []
        # 简单解析，实际应该使用 XML 解析器
        if '<dependency>' in content:
            import re
            artifact_ids = re.findall(r'<artifactId>(.*?)</artifactId>', content)
            deps.extend(artifact_ids)
        return deps


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.classes = []
        self.functions = []
        self.endpoints = []
    
    def analyze(self) -> Dict[str, Any]:
        """分析代码"""
        if not self.project_path.exists():
            raise ValueError(f"工程路径不存在: {self.project_path}")
        
        self._analyze_python_files()
        self._analyze_js_files()
        
        return {
            "classes": self.classes,
            "functions": self.functions,
            "endpoints": self.endpoints
        }
    
    def _analyze_python_files(self):
        """分析 Python 文件"""
        py_files = list(self.project_path.rglob('*.py'))
        
        for py_file in py_files:
            # 跳过虚拟环境和缓存
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        self.classes.append({
                            "name": node.name,
                            "file": str(py_file.relative_to(self.project_path)),
                            "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                        })
                    
                    elif isinstance(node, ast.FunctionDef):
                        # 检查是否是 API 端点
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Attribute):
                                if decorator.attr in ['route', 'get', 'post', 'put', 'delete']:
                                    self.endpoints.append({
                                        "name": node.name,
                                        "file": str(py_file.relative_to(self.project_path)),
                                        "method": decorator.attr.upper() if decorator.attr in ['get', 'post', 'put', 'delete'] else 'GET'
                                    })
                        self.functions.append({
                            "name": node.name,
                            "file": str(py_file.relative_to(self.project_path)),
                            "args": [arg.arg for arg in node.args.args]
                        })
            except Exception:
                continue
    
    def _analyze_js_files(self):
        """分析 JavaScript/TypeScript 文件"""
        js_files = list(self.project_path.rglob('*.js')) + list(self.project_path.rglob('*.ts'))
        
        for js_file in js_files:
            # 跳过 node_modules
            if 'node_modules' in str(js_file):
                continue
            
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单的函数检测
                import re
                functions = re.findall(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\()', content)
                for func_match in functions:
                    func_name = func_match[0] if func_match[0] else func_match[1]
                    if func_name:
                        self.functions.append({
                            "name": func_name,
                            "file": str(js_file.relative_to(self.project_path)),
                            "args": []
                        })
                
                # 检测 Express 路由
                app_routes = re.findall(r'app\.(get|post|put|delete|patch)\s*\([\'"]([^\'"]+)', content)
                for method, path in app_routes:
                    self.endpoints.append({
                        "name": path,
                        "file": str(js_file.relative_to(self.project_path)),
                        "method": method.upper()
                    })
            except Exception:
                continue


def scan_project(project_path: Path) -> Dict[str, Any]:
    """扫描工程"""
    scanner = ProjectScanner(project_path)
    structure = scanner.scan()
    
    analyzer = CodeAnalyzer(project_path)
    code_info = analyzer.analyze()
    
    return {
        "structure": structure,
        "code": code_info
    }
