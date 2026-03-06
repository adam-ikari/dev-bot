"""
TechStackDetector 测试
"""

import json
import tempfile
from pathlib import Path

import pytest

from dev_bot.tech_stack_detector import (
    TechStackDetector,
    detect_tech_stack,
    generate_tech_stack_report,
)


@pytest.fixture
def temp_project_dir():
    """创建临时项目目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        yield project_path


@pytest.fixture
def python_project(temp_project_dir):
    """创建 Python 项目结构"""
    # 创建 Python 源文件
    (temp_project_dir / "src").mkdir()
    (temp_project_dir / "src" / "main.py").write_text("print('hello')")
    (temp_project_dir / "src" / "utils.py").write_text("def add(a, b): return a + b")

    # 创建 pyproject.toml
    pyproject_content = """
[project]
name = "test-project"
dependencies = [
    "fastapi>=0.100.0",
    "pytest>=7.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = ["ruff>=0.1.0"]
"""
    (temp_project_dir / "pyproject.toml").write_text(pyproject_content)

    # 创建 uv.lock
    (temp_project_dir / "uv.lock").write_text("")

    # 创建 ruff.toml
    (temp_project_dir / "ruff.toml").write_text("")

    return temp_project_dir


@pytest.fixture
def javascript_project(temp_project_dir):
    """创建 JavaScript 项目结构"""
    # 创建 JavaScript 源文件
    (temp_project_dir / "src").mkdir()
    (temp_project_dir / "src" / "index.js").write_text("console.log('hello')")
    (temp_project_dir / "src" / "app.js").write_text("function add(a, b) { return a + b; }")

    # 创建 package.json
    package_content = {
        "name": "test-project",
        "dependencies": {
            "react": "^18.0.0",
            "express": "^4.18.0"
        },
        "devDependencies": {
            "jest": "^29.0.0",
            "vite": "^4.0.0",
            "eslint": "^8.0.0"
        }
    }
    (temp_project_dir / "package.json").write_text(json.dumps(package_content, indent=2))

    return temp_project_dir


@pytest.fixture
def mixed_project(temp_project_dir):
    """创建混合项目结构（Python + JavaScript）"""
    # Python 部分
    (temp_project_dir / "src").mkdir()
    (temp_project_dir / "src" / "main.py").write_text("print('hello')")
    (temp_project_dir / "src" / "app.js").write_text("console.log('hello')")

    # Python 配置
    pyproject_content = """
[project]
name = "mixed-project"
dependencies = ["fastapi>=0.100.0"]
"""
    (temp_project_dir / "pyproject.toml").write_text(pyproject_content)

    # JavaScript 配置
    package_content = {
        "name": "mixed-project",
        "dependencies": {
            "react": "^18.0.0"
        }
    }
    (temp_project_dir / "package.json").write_text(json.dumps(package_content, indent=2))

    # GitHub Actions
    (temp_project_dir / ".github" / "workflows").mkdir(parents=True)
    (temp_project_dir / ".github" / "workflows" / "ci.yml").write_text("")

    # Docker
    (temp_project_dir / "Dockerfile").write_text("FROM python:3.13")

    return temp_project_dir


def test_detector_initialization(temp_project_dir):
    """测试检测器初始化"""
    detector = TechStackDetector(temp_project_dir)
    assert detector.project_root == temp_project_dir
    assert detector.tech_stack == {}


def test_detect_language_python(python_project):
    """检测 Python 项目"""
    detector = TechStackDetector(python_project)
    lang = detector._detect_language()
    assert "Python" in lang


def test_detect_language_javascript(javascript_project):
    """检测 JavaScript 项目"""
    detector = TechStackDetector(javascript_project)
    lang = detector._detect_language()
    assert "JavaScript" in lang


def test_detect_language_mixed(mixed_project):
    """检测混合项目"""
    detector = TechStackDetector(mixed_project)
    lang = detector._detect_language()
    # 应该检测到文件数量最多的语言
    # 两个项目各有 2 个文件，可能返回任一语言或 Unknown
    # Python 会返回带版本号的字符串，如 "Python 3.13.3"
    assert "Python" in lang or "JavaScript" in lang or lang == "Unknown"


def test_detect_frameworks_python(python_project):
    """检测 Python 框架"""
    detector = TechStackDetector(python_project)
    frameworks = detector._detect_frameworks()
    assert "FastAPI" in frameworks


def test_detect_frameworks_javascript(javascript_project):
    """检测 JavaScript 框架"""
    detector = TechStackDetector(javascript_project)
    frameworks = detector._detect_frameworks()
    assert "React" in frameworks
    assert "Express" in frameworks


def test_detect_frameworks_mixed(mixed_project):
    """检测混合项目框架"""
    detector = TechStackDetector(mixed_project)
    frameworks = detector._detect_frameworks()
    assert "FastAPI" in frameworks
    assert "React" in frameworks


def test_detect_test_framework_python(python_project):
    """检测 Python 测试框架"""
    detector = TechStackDetector(python_project)
    framework = detector._detect_test_framework()
    assert framework == "pytest"


def test_detect_test_framework_javascript(javascript_project):
    """检测 JavaScript 测试框架"""
    detector = TechStackDetector(javascript_project)
    framework = detector._detect_test_framework()
    assert framework == "Jest"


def test_detect_build_tool_python(python_project):
    """检测 Python 构建工具"""
    detector = TechStackDetector(python_project)
    tool = detector._detect_build_tool()
    assert tool == "Hatchling"


def test_detect_build_tool_javascript(javascript_project):
    """检测 JavaScript 构建工具"""
    detector = TechStackDetector(javascript_project)
    tool = detector._detect_build_tool()
    assert tool == "Vite"


def test_detect_dependency_manager_python(python_project):
    """检测 Python 依赖管理"""
    detector = TechStackDetector(python_project)
    manager = detector._detect_dependency_manager()
    assert manager == "uv (Python)"


def test_detect_dependency_manager_javascript(javascript_project):
    """检测 JavaScript 依赖管理"""
    detector = TechStackDetector(javascript_project)
    manager = detector._detect_dependency_manager()
    assert manager == "npm"


def test_detect_code_style(python_project):
    """检测代码规范工具"""
    detector = TechStackDetector(python_project)
    styles = detector._detect_code_style()
    assert "ruff" in styles


def test_detect_other_tools(mixed_project):
    """检测其他工具"""
    detector = TechStackDetector(mixed_project)
    tools = detector._detect_other_tools()
    assert "GitHub Actions" in tools
    assert "Docker" in tools


def test_detect_full_stack_python(python_project):
    """完整检测 Python 项目技术栈"""
    detector = TechStackDetector(python_project)
    tech_stack = detector.detect()

    assert "programming_language" in tech_stack
    assert "frameworks" in tech_stack
    assert "database" in tech_stack
    assert "test_framework" in tech_stack
    assert "build_tool" in tech_stack
    assert "dependency_manager" in tech_stack
    assert "code_style" in tech_stack
    assert "other_tools" in tech_stack

    assert "Python" in tech_stack["programming_language"]
    assert "FastAPI" in tech_stack["frameworks"]
    assert "pytest" == tech_stack["test_framework"]
    assert "Hatchling" == tech_stack["build_tool"]
    assert "uv (Python)" == tech_stack["dependency_manager"]


def test_detect_full_stack_javascript(javascript_project):
    """完整检测 JavaScript 项目技术栈"""
    detector = TechStackDetector(javascript_project)
    tech_stack = detector.detect()

    assert "JavaScript" in tech_stack["programming_language"]
    assert "React" in tech_stack["frameworks"]
    assert "Express" in tech_stack["frameworks"]
    assert "Jest" == tech_stack["test_framework"]
    assert "Vite" == tech_stack["build_tool"]
    assert "npm" == tech_stack["dependency_manager"]


def test_generate_report_python(python_project):
    """生成 Python 项目报告"""
    detector = TechStackDetector(python_project)
    report = detector.generate_report()

    assert "技术栈识别报告" in report
    assert "Python" in report
    assert "FastAPI" in report
    assert "pytest" in report
    assert "Hatchling" in report
    assert "uv" in report


def test_generate_report_javascript(javascript_project):
    """生成 JavaScript 项目报告"""
    detector = TechStackDetector(javascript_project)
    report = detector.generate_report()

    assert "技术栈识别报告" in report
    assert "JavaScript" in report
    assert "React" in report
    assert "Jest" in report
    assert "Vite" in report


def test_detect_tech_stack_function(python_project):
    """测试快捷函数 detect_tech_stack"""
    tech_stack = detect_tech_stack(python_project)

    assert isinstance(tech_stack, dict)
    assert "programming_language" in tech_stack


def test_generate_tech_stack_report_function(python_project):
    """测试快捷函数 generate_tech_stack_report"""
    report = generate_tech_stack_report(python_project)

    assert isinstance(report, str)
    assert "技术栈识别报告" in report


def test_empty_project(temp_project_dir):
    """测试空项目"""
    detector = TechStackDetector(temp_project_dir)
    tech_stack = detector.detect()

    assert tech_stack["programming_language"] == "Unknown"
    assert tech_stack["frameworks"] == []
    assert tech_stack["database"] == "Unknown"
    assert tech_stack["test_framework"] == "Unknown"
    assert tech_stack["build_tool"] == "Unknown"
    assert tech_stack["dependency_manager"] == "Unknown"


def test_project_with_docker_only(temp_project_dir):
    """测试仅有 Docker 配置的项目"""
    (temp_project_dir / "Dockerfile").write_text("FROM python:3.13")
    (temp_project_dir / "docker-compose.yml").write_text("version: '3'")

    detector = TechStackDetector(temp_project_dir)
    tools = detector._detect_other_tools()

    assert "Docker" in tools
    assert "Docker Compose" in tools


def test_project_with_github_actions(temp_project_dir):
    """测试仅有 GitHub Actions 配置的项目"""
    (temp_project_dir / ".github" / "workflows").mkdir(parents=True)
    (temp_project_dir / ".github" / "workflows" / "test.yml").write_text("")

    detector = TechStackDetector(temp_project_dir)
    tools = detector._detect_other_tools()

    assert "GitHub Actions" in tools


def test_project_with_docs(temp_project_dir):
    """测试有文档目录的项目"""
    (temp_project_dir / "docs").mkdir()
    (temp_project_dir / "docs" / "README.md").write_text("")

    detector = TechStackDetector(temp_project_dir)
    tools = detector._detect_other_tools()

    assert "Documentation" in tools


def test_multiple_python_files(temp_project_dir):
    """测试多个 Python 文件"""
    (temp_project_dir / "src").mkdir()
    for i in range(10):
        (temp_project_dir / "src" / f"file{i}.py").write_text("print('hello')")

    # 添加少量 JavaScript 文件
    for i in range(2):
        (temp_project_dir / "src" / f"file{i}.js").write_text("console.log('hello')")

    detector = TechStackDetector(temp_project_dir)
    lang = detector._detect_language()

    # Python 文件更多，应该检测为 Python
    assert "Python" in lang
