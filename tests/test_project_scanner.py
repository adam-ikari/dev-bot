#!/usr/bin/env python3
"""
测试 ProjectScanner 和 CodeAnalyzer 模块
"""

import json
from pathlib import Path

import pytest

from dev_bot.project_scanner import CodeAnalyzer, ProjectScanner, scan_project


@pytest.fixture
def test_project_root(tmp_path):
    """创建测试项目根目录"""
    return tmp_path


@pytest.fixture
def simple_python_project(test_project_root):
    """创建简单的 Python 测试项目"""
    # 创建主 Python 文件
    main_py = test_project_root / "main.py"
    main_py.write_text("""
def hello_world():
    print("Hello, World!")

class MyApp:
    def __init__(self):
        self.name = "TestApp"

    def run(self):
        hello_world()
""")

    # 创建 requirements.txt
    requirements = test_project_root / "requirements.txt"
    requirements.write_text("pytest>=7.0.0\nrequests>=2.28.0\nflask>=2.0.0\n")

    # 创建 pyproject.toml
    pyproject = test_project_root / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "pyyaml>=6.0",
    "click>=8.0.0",
]
""")

    # 创建子目录
    src_dir = test_project_root / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "utils.py").write_text("""
def utility_function():
    return "utility"

class UtilityClass:
    def process(self):
        return self.utility_function()
""")

    return test_project_root


@pytest.fixture
def javascript_project(test_project_root):
    """创建 JavaScript 测试项目"""
    # 创建 package.json
    package_json = test_project_root / "package.json"
    package_json.write_text(json.dumps({
        "name": "test-js-project",
        "version": "1.0.0",
        "dependencies": {
            "express": "^4.18.0",
            "react": "^18.0.0"
        },
        "devDependencies": {
            "jest": "^29.0.0"
        }
    }))

    # 创建 JavaScript 文件
    app_js = test_project_root / "app.js"
    app_js.write_text("""
const express = require('express');
const app = express();

function hello() {
    return 'Hello World';
}

app.get('/', (req, res) => {
    res.send(hello());
});

app.listen(3000);
""")

    return test_project_root


class TestProjectScanner:
    """测试 ProjectScanner 类"""

    def test_scanner_initialization(self, test_project_root):
        """测试扫描器初始化"""
        scanner = ProjectScanner(test_project_root)
        assert scanner.project_path == test_project_root
        assert scanner.structure == {
            "directories": [],
            "files": [],
            "languages": {},
            "frameworks": [],
            "dependencies": {}
        }

    def test_scan_nonexistent_path(self):
        """测试扫描不存在的路径"""
        scanner = ProjectScanner(Path("/nonexistent/path"))
        with pytest.raises(ValueError, match="工程路径不存在"):
            scanner.scan()

    def test_scan_empty_directory(self, test_project_root):
        """测试扫描空目录"""
        scanner = ProjectScanner(test_project_root)
        result = scanner.scan()
        assert result["directories"] == []
        assert result["files"] == []
        assert result["languages"] == {}
        assert result["frameworks"] == []
        assert result["dependencies"] == {}

    def test_scan_simple_python_project(self, simple_python_project):
        """测试扫描简单的 Python 项目"""
        scanner = ProjectScanner(simple_python_project)
        result = scanner.scan()

        # 检查目录
        assert "src" in result["directories"]

        # 检查文件
        file_paths = [f["path"] for f in result["files"]]
        assert "main.py" in file_paths
        assert "requirements.txt" in file_paths
        assert "pyproject.toml" in file_paths
        assert "src/__init__.py" in file_paths
        assert "src/utils.py" in file_paths

        # 检查语言检测
        assert "Python" in result["languages"]
        assert result["languages"]["Python"] >= 3

        # 检查框架检测
        assert "Flask" in result["frameworks"]

        # 检查依赖
        assert "python" in result["dependencies"]
        python_deps = result["dependencies"]["python"]
        assert len(python_deps) > 0

    def test_scan_javascript_project(self, javascript_project):
        """测试扫描 JavaScript 项目"""
        scanner = ProjectScanner(javascript_project)
        result = scanner.scan()

        # 检查文件
        file_paths = [f["path"] for f in result["files"]]
        assert "package.json" in file_paths
        assert "app.js" in file_paths

        # 检查语言检测
        assert "JavaScript" in result["languages"]

        # 检查框架检测
        assert "Express.js" in result["frameworks"]
        assert "React" in result["frameworks"]

        # 检查依赖
        assert "nodejs" in result["dependencies"]
        node_deps = result["dependencies"]["nodejs"]
        assert "express" in node_deps
        assert "react" in node_deps

    def test_scan_with_hidden_directories(self, test_project_root):
        """测试扫描时跳过隐藏目录"""
        hidden_dir = test_project_root / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "secret.py").write_text("")

        normal_dir = test_project_root / "normal"
        normal_dir.mkdir()
        (normal_dir / "public.py").write_text("")

        scanner = ProjectScanner(test_project_root)
        result = scanner.scan()

        assert ".hidden" not in result["directories"]
        assert "normal" in result["directories"]

    def test_scan_with_ignored_directories(self, test_project_root):
        """测试扫描时跳过常见忽略目录"""
        for dirname in ['node_modules', 'venv', 'env', '__pycache__', 'dist', 'build']:
            dir_path = test_project_root / dirname
            dir_path.mkdir()
            (dir_path / "file.py").write_text("")

        scanner = ProjectScanner(test_project_root)
        result = scanner.scan()

        for dirname in ['node_modules', 'venv', 'env', '__pycache__', 'dist', 'build']:
            assert dirname not in result["directories"]

    def test_detect_languages_multiple(self, test_project_root):
        """测试检测多种编程语言"""
        (test_project_root / "script.py").write_text("")
        (test_project_root / "main.js").write_text("")
        (test_project_root / "app.ts").write_text("")
        (test_project_root / "module.go").write_text("")

        scanner = ProjectScanner(test_project_root)
        result = scanner.scan()

        assert result["languages"]["Python"] == 1
        assert result["languages"]["JavaScript"] == 1
        assert result["languages"]["TypeScript"] == 1
        assert result["languages"]["Go"] == 1

    def test_detect_fastapi_framework(self, test_project_root):
        """测试检测 FastAPI 框架"""
        requirements = test_project_root / "requirements.txt"
        requirements.write_text("fastapi>=0.68.0\nuvicorn>=0.15.0")

        scanner = ProjectScanner(test_project_root)
        scanner.scan()

        assert "FastAPI" in scanner.structure["frameworks"]

    def test_detect_react_framework(self, javascript_project):
        """测试检测 React 框架"""
        scanner = ProjectScanner(javascript_project)
        scanner.scan()

        assert "React" in scanner.structure["frameworks"]

    def test_detect_nextjs_framework(self, test_project_root):
        """测试检测 Next.js 框架"""
        package_json = test_project_root / "package.json"
        package_json.write_text(json.dumps({
            "dependencies": {
                "next": "^13.0.0",
                "react": "^18.0.0"
            }
        }))

        scanner = ProjectScanner(test_project_root)
        scanner.scan()

        assert "Next.js" in scanner.structure["frameworks"]

    def test_parse_requirements_txt_with_comments(self, test_project_root):
        """测试解析包含注释的 requirements.txt"""
        requirements = test_project_root / "requirements.txt"
        requirements.write_text("# Comment\npytest>=7.0.0\nrequests>=2.28.0\nflask>=2.0.0\n")

        scanner = ProjectScanner(test_project_root)
        scanner.scan()

        deps = scanner.structure["dependencies"]["python"]
        assert "pytest" in deps
        assert "requests" in deps
        assert "flask" in deps
        assert not any("#" in dep for dep in deps)

    def test_parse_requirements_txt_with_version_specifiers(self, test_project_root):
        """测试解析包含不同版本说明符的 requirements.txt"""
        requirements = test_project_root / "requirements.txt"
        requirements.write_text("package>=1.0.0\npackage==2.0.0\npackage<=3.0.0\npackage~=4.0.0\n")

        scanner = ProjectScanner(test_project_root)
        scanner.scan()

        deps = scanner.structure["dependencies"]["python"]
        assert all(dep == "package" for dep in deps)
        assert len(deps) == 4

    def test_parse_pyproject_toml(self, test_project_root):
        """测试解析 pyproject.toml"""
        pyproject = test_project_root / "pyproject.toml"
        pyproject.write_text("""
[project]
dependencies = [
    "pyyaml>=6.0",
    "click>=8.0.0",
    "requests>=2.28.0",
]
""")

        scanner = ProjectScanner(test_project_root)
        scanner.scan()

        deps = scanner.structure["dependencies"]["python"]
        assert len(deps) > 0

    def test_parse_package_json(self, test_project_root):
        """测试解析 package.json"""
        package_json = test_project_root / "package.json"
        package_json.write_text(json.dumps({
            "dependencies": {
                "express": "^4.18.0",
                "lodash": "^4.17.0"
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "eslint": "^8.0.0"
            }
        }))

        scanner = ProjectScanner(test_project_root)
        scanner.scan()

        deps = scanner.structure["dependencies"]["nodejs"]
        assert "express" in deps
        assert "lodash" in deps
        assert "jest" in deps
        assert "eslint" in deps

    def test_parse_pom_xml(self, test_project_root):
        """测试解析 pom.xml"""
        pom = test_project_root / "pom.xml"
        pom.write_text("""
<project>
    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>5.3.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-web</artifactId>
            <version>5.3.0</version>
        </dependency>
    </dependencies>
</project>
""")

        scanner = ProjectScanner(test_project_root)
        scanner.scan()

        deps = scanner.structure["dependencies"]["java"]
        assert "spring-core" in deps
        assert "spring-web" in deps

    def test_file_size_collection(self, simple_python_project):
        """测试文件大小收集"""
        scanner = ProjectScanner(simple_python_project)
        result = scanner.scan()

        for file_info in result["files"]:
            assert "size" in file_info
            assert file_info["size"] >= 0
            assert "extension" in file_info

        # 至少有一些非空文件
        non_empty_files = [f for f in result["files"] if f["size"] > 0]
        assert len(non_empty_files) > 0

    def test_nested_directory_scan(self, test_project_root):
        """测试嵌套目录扫描"""
        deep_dir = test_project_root / "level1" / "level2" / "level3"
        deep_dir.mkdir(parents=True)
        (deep_dir / "deep.py").write_text("")

        scanner = ProjectScanner(test_project_root)
        result = scanner.scan()

        assert "level1" in result["directories"]
        assert any("level2" in d for d in result["directories"])
        assert any("level3" in d for d in result["directories"])
        file_paths = [f["path"] for f in result["files"]]
        assert any("deep.py" in path for path in file_paths)


class TestCodeAnalyzer:
    """测试 CodeAnalyzer 类"""

    def test_analyzer_initialization(self, test_project_root):
        """测试分析器初始化"""
        analyzer = CodeAnalyzer(test_project_root)
        assert analyzer.project_path == test_project_root
        assert analyzer.classes == []
        assert analyzer.functions == []
        assert analyzer.endpoints == []

    def test_analyze_nonexistent_path(self):
        """测试分析不存在的路径"""
        analyzer = CodeAnalyzer(Path("/nonexistent/path"))
        with pytest.raises(ValueError, match="工程路径不存在"):
            analyzer.analyze()

    def test_analyze_python_files(self, simple_python_project):
        """测试分析 Python 文件"""
        analyzer = CodeAnalyzer(simple_python_project)
        result = analyzer.analyze()

        assert len(result["functions"]) > 0
        function_names = [f["name"] for f in result["functions"]]
        assert "hello_world" in function_names

        assert len(result["classes"]) > 0
        class_names = [c["name"] for c in result["classes"]]
        assert "MyApp" in class_names

        myapp_class = next(c for c in result["classes"] if c["name"] == "MyApp")
        assert "__init__" in myapp_class["methods"]
        assert "run" in myapp_class["methods"]

    def test_analyze_python_with_flask_routes(self, test_project_root):
        """测试分析带 Flask 路由的 Python 文件"""
        flask_app = test_project_root / "app.py"
        flask_app.write_text("""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello'

@app.get('/api/users')
def get_users():
    return []

@app.post('/api/users')
def create_user():
    return {}
""")

        analyzer = CodeAnalyzer(test_project_root)
        result = analyzer.analyze()

        function_names = [f["name"] for f in result["functions"]]
        assert "index" in function_names or len(result["functions"]) >= 3

    def test_analyze_javascript_files(self, javascript_project):
        """测试分析 JavaScript 文件"""
        analyzer = CodeAnalyzer(javascript_project)
        result = analyzer.analyze()

        assert len(result["functions"]) > 0
        function_names = [f["name"] for f in result["functions"]]
        assert "hello" in function_names

        assert len(result["endpoints"]) > 0
        endpoint_paths = [e["name"] for e in result["endpoints"]]
        assert "/" in endpoint_paths

    def test_analyze_skips_venv_and_cache(self, test_project_root):
        """测试分析时跳过虚拟环境和缓存"""
        # 先创建正常文件
        main_py = test_project_root / "main.py"
        main_py.write_text('def normal_function():\n    print("test")\n')

        # 验证正常文件可以被分析
        analyzer = CodeAnalyzer(test_project_root)
        result = analyzer.analyze()
        function_names = [f["name"] for f in result["functions"]]
        assert "normal_function" in function_names

        # 创建 venv 目录
        venv_dir = test_project_root / "venv" / "lib" / "python3.9" / "site-packages"
        venv_dir.mkdir(parents=True)
        (venv_dir / "package.py").write_text("def venv_function(): pass\n")

        # 创建 __pycache__ 目录
        cache_dir = test_project_root / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "module.cpython-39.pyc").write_text("")

        # 重新分析
        analyzer = CodeAnalyzer(test_project_root)
        result = analyzer.analyze()

        function_names = [f["name"] for f in result["functions"]]
        assert "venv_function" not in function_names
        assert "normal_function" in function_names

    def test_analyze_with_function_arguments(self, test_project_root):
        """测试分析函数参数"""
        test_file = test_project_root / "test.py"
        test_file.write_text("""
def func_with_args(a, b, c=None):
    pass

def func_no_args():
    pass
""")

        analyzer = CodeAnalyzer(test_project_root)
        result = analyzer.analyze()

        func_with_args = next(f for f in result["functions"] if f["name"] == "func_with_args")
        assert "a" in func_with_args["args"]
        assert "b" in func_with_args["args"]
        assert "c" in func_with_args["args"]

        func_no_args = next(f for f in result["functions"] if f["name"] == "func_no_args")
        assert len(func_no_args["args"]) == 0


class TestScanProject:
    """测试 scan_project 函数"""

    def test_scan_project_function(self, simple_python_project):
        """测试 scan_project 便利函数"""
        result = scan_project(simple_python_project)

        assert "structure" in result
        assert "code" in result

        assert "directories" in result["structure"]
        assert "files" in result["structure"]
        assert "languages" in result["structure"]
        assert "frameworks" in result["structure"]
        assert "dependencies" in result["structure"]

        assert "classes" in result["code"]
        assert "functions" in result["code"]
        assert "endpoints" in result["code"]

    def test_scan_project_complete(self, simple_python_project):
        """测试完整的 scan_project 流程"""
        result = scan_project(simple_python_project)

        assert len(result["structure"]["directories"]) > 0
        assert len(result["structure"]["files"]) > 0
        assert "Python" in result["structure"]["languages"]

        assert len(result["code"]["functions"]) > 0
        assert len(result["code"]["classes"]) > 0

    def test_scan_project_with_multiple_languages(self, test_project_root):
        """测试扫描包含多种语言的项目"""
        (test_project_root / "app.py").write_text("def main(): pass\n")
        (test_project_root / "client.js").write_text("function init() {}\n")

        result = scan_project(test_project_root)

        assert "Python" in result["structure"]["languages"]
        assert "JavaScript" in result["structure"]["languages"]

        python_funcs = [f for f in result["code"]["functions"] if f["file"].endswith(".py")]
        js_funcs = [f for f in result["code"]["functions"] if f["file"].endswith(".js")]
        assert len(python_funcs) > 0
        assert len(js_funcs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
