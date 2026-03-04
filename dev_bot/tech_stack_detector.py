"""
技术栈检测器

自动识别项目的技术栈，包括：
- 编程语言
- 框架
- 数据库
- 测试框架
- 构建工具
- 依赖管理
- 代码规范
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


class TechStackDetector:
    """技术栈检测器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.tech_stack = {}
    
    def detect(self) -> Dict[str, Any]:
        """检测技术栈"""
        self.tech_stack = {
            "programming_language": self._detect_language(),
            "frameworks": self._detect_frameworks(),
            "database": self._detect_database(),
            "test_framework": self._detect_test_framework(),
            "build_tool": self._detect_build_tool(),
            "dependency_manager": self._detect_dependency_manager(),
            "code_style": self._detect_code_style(),
            "other_tools": self._detect_other_tools(),
        }
        return self.tech_stack
    
    def _detect_language(self) -> str:
        """检测编程语言"""
        # 检查源代码文件
        source_files = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
        }
        
        counts = {ext: 0 for ext in source_files}
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                for ext in source_files:
                    if file_path.suffix == ext:
                        counts[ext] += 1
        
        # 返回文件数量最多的语言
        dominant_lang = max(counts, key=counts.get)
        if counts[dominant_lang] > 0:
            # 尝试获取版本
            if dominant_lang == '.py':
                return f"Python {sys.version.split()[0]}"
            return source_files[dominant_lang]
        
        return "Unknown"
    
    def _detect_frameworks(self) -> List[str]:
        """检测框架"""
        frameworks = []
        
        # 检查 Python 框架
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'fastapi' in content.lower():
                    frameworks.append("FastAPI")
                if 'flask' in content.lower():
                    frameworks.append("Flask")
                if 'django' in content.lower():
                    frameworks.append("Django")
        
        # 检查 JavaScript/TypeScript 框架
        package_json = self.project_root / "package.json"
        if package_json.exists():
            with open(package_json, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'react' in deps:
                    frameworks.append("React")
                if 'vue' in deps:
                    frameworks.append("Vue")
                if '@angular/core' in deps:
                    frameworks.append("Angular")
                if 'express' in deps:
                    frameworks.append("Express")
                if 'next' in deps:
                    frameworks.append("Next.js")
                if 'nuxt' in deps:
                    frameworks.append("Nuxt.js")
        
        return frameworks
    
    def _detect_database(self) -> str:
        """检测数据库"""
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'sqlalchemy' in content.lower():
                    return "SQLAlchemy ORM"
                if 'postgres' in content.lower() or 'psycopg' in content.lower():
                    return "PostgreSQL"
                if 'mysql' in content.lower():
                    return "MySQL"
                if 'sqlite' in content.lower():
                    return "SQLite"
                if 'mongodb' in content.lower() or 'pymongo' in content.lower():
                    return "MongoDB"
        
        package_json = self.project_root / "package.json"
        if package_json.exists():
            with open(package_json, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'pg' in deps or 'postgres' in deps:
                    return "PostgreSQL"
                if 'mysql' in deps or 'mysql2' in deps:
                    return "MySQL"
                if 'sqlite' in deps or 'sqlite3' in deps:
                    return "SQLite"
                if 'mongodb' in deps or 'mongoose' in deps:
                    return "MongoDB"
        
        return "Unknown"
    
    def _detect_test_framework(self) -> str:
        """检测测试框架"""
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'pytest' in content.lower():
                    return "pytest"
                if 'unittest' in content.lower():
                    return "unittest"
        
        package_json = self.project_root / "package.json"
        if package_json.exists():
            with open(package_json, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'jest' in deps:
                    return "Jest"
                if 'mocha' in deps:
                    return "Mocha"
                if 'jasmine' in deps:
                    return "Jasmine"
        
        return "Unknown"
    
    def _detect_build_tool(self) -> str:
        """检测构建工具"""
        # 检查 Python 构建工具
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'hatchling' in content.lower():
                    return "Hatchling"
                if 'setuptools' in content.lower():
                    return "Setuptools"
                if 'poetry' in content.lower():
                    return "Poetry"
        
        # 检查 JavaScript/TypeScript 构建工具
        package_json = self.project_root / "package.json"
        if package_json.exists():
            with open(package_json, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'vite' in deps:
                    return "Vite"
                if 'webpack' in deps:
                    return "Webpack"
                if 'rollup' in deps:
                    return "Rollup"
                if 'esbuild' in deps:
                    return "esbuild"
        
        return "Unknown"
    
    def _detect_dependency_manager(self) -> str:
        """检测依赖管理工具"""
        if (self.project_root / "pyproject.toml").exists():
            if (self.project_root / "uv.lock").exists():
                return "uv (Python)"
            if (self.project_root / "poetry.lock").exists():
                return "Poetry"
            if (self.project_root / "Pipfile").exists():
                return "Pipenv"
            if (self.project_root / "requirements.txt").exists():
                return "pip"
        
        if (self.project_root / "package.json").exists():
            if (self.project_root / "yarn.lock").exists():
                return "Yarn"
            if (self.project_root / "pnpm-lock.yaml").exists():
                return "pnpm"
            return "npm"
        
        if (self.project_root / "go.mod").exists():
            return "Go Modules"
        
        if (self.project_root / "Cargo.toml").exists():
            return "Cargo"
        
        return "Unknown"
    
    def _detect_code_style(self) -> List[str]:
        """检测代码规范工具"""
        style_tools = []
        
        # Python 代码规范
        if (self.project_root / "ruff.toml").exists():
            style_tools.append("ruff")
        if (self.project_root / "pyproject.toml").exists():
            with open(self.project_root / "pyproject.toml", 'r', encoding='utf-8') as f:
                content = f.read()
                if 'black' in content.lower():
                    style_tools.append("Black")
                if 'flake8' in content.lower():
                    style_tools.append("Flake8")
                if 'pylint' in content.lower():
                    style_tools.append("Pylint")
        
        # JavaScript/TypeScript 代码规范
        if (self.project_root / ".eslintrc.js").exists() or (self.project_root / ".eslintrc.json").exists():
            style_tools.append("ESLint")
        if (self.project_root / ".prettierrc").exists() or (self.project_root / ".prettierrc.json").exists():
            style_tools.append("Prettier")
        
        return style_tools if style_tools else ["None"]
    
    def _detect_other_tools(self) -> List[str]:
        """检测其他工具"""
        tools = []
        
        # CI/CD
        if (self.project_root / ".github" / "workflows").exists():
            tools.append("GitHub Actions")
        if (self.project_root / ".gitlab-ci.yml").exists():
            tools.append("GitLab CI")
        if (self.project_root / "Jenkinsfile").exists():
            tools.append("Jenkins")
        
        # 容器化
        if (self.project_root / "Dockerfile").exists():
            tools.append("Docker")
        if (self.project_root / "docker-compose.yml").exists():
            tools.append("Docker Compose")
        
        # 文档
        if (self.project_root / "docs").exists():
            tools.append("Documentation")
        
        return tools if tools else ["None"]
    
    def generate_report(self) -> str:
        """生成技术栈报告"""
        if not self.tech_stack:
            self.detect()
        
        report = [
            "技术栈识别报告：",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"编程语言: {self.tech_stack['programming_language']}",
            f"主要框架: {', '.join(self.tech_stack['frameworks']) if self.tech_stack['frameworks'] else 'None'}",
            f"数据库: {self.tech_stack['database']}",
            f"测试框架: {self.tech_stack['test_framework']}",
            f"构建工具: {self.tech_stack['build_tool']}",
            f"依赖管理: {self.tech_stack['dependency_manager']}",
            f"代码规范: {', '.join(self.tech_stack['code_style'])}",
            f"其他工具: {', '.join(self.tech_stack['other_tools'])}",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        
        return "\n".join(report)


def detect_tech_stack(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """检测技术栈的快捷函数"""
    detector = TechStackDetector(project_root)
    return detector.detect()


def generate_tech_stack_report(project_root: Optional[Path] = None) -> str:
    """生成技术栈报告的快捷函数"""
    detector = TechStackDetector(project_root)
    return detector.generate_report()


if __name__ == "__main__":
    # 演示使用
    detector = TechStackDetector()
    tech_stack = detector.detect()
    
    print("检测到的技术栈:")
    print(json.dumps(tech_stack, indent=2, ensure_ascii=False))
    print()
    print(detector.generate_report())
