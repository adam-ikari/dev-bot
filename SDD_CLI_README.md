# SDD CLI - Spec Driven Development 工具

基于规格驱动的开发命令行工具，帮助用户创建 spec 和初始化 SDD 项目。

## 安装

```bash
pip install -e .
```

## 使用

### 初始化 SDD 项目

```bash
# 创建标准 SDD 项目
sdd init my-project

# 使用完整模板
sdd init my-project --template full

# 使用最小模板
sdd init my-project --template minimal
```

项目结构：
```
my-project/
├── specs/           # spec 文件目录
├── src/             # 源代码目录
├── tests/           # 测试目录
├── docs/            # 文档目录
└── sdd-config.json  # SDD 配置文件
```

### 创建 Spec 文件

```bash
# 创建功能 spec
sdd new-spec user-authentication --type feature

# 创建 API spec
sdd new-spec user-api --type api

# 创建组件 spec
sdd new-spec button --type component

# 创建服务 spec
sdd new-spec email --type service

# 指定输出目录
sdd new-spec feature --output ./specs
```

### 验证 Spec 文件

```bash
sdd validate specs/user-authentication.json
```

## Spec 格式

### Feature Spec

```json
{
  "spec_version": "1.0",
  "metadata": {
    "name": "feature-name",
    "type": "feature",
    "version": "1.0.0"
  },
  "description": "功能描述",
  "requirements": [],
  "user_stories": [],
  "acceptance_criteria": []
}
```

### API Spec

```json
{
  "spec_version": "1.0",
  "metadata": {
    "name": "api-name",
    "type": "api",
    "version": "1.0.0"
  },
  "description": "API 描述",
  "base_path": "/api/v1",
  "endpoints": [],
  "models": [],
  "authentication": {}
}
```

### Component Spec

```json
{
  "spec_version": "1.0",
  "metadata": {
    "name": "component-name",
    "type": "component",
    "version": "1.0.0"
  },
  "description": "组件描述",
  "props": [],
  "events": [],
  "slots": [],
  "methods": []
}
```

### Service Spec

```json
{
  "spec_version": "1.0",
  "metadata": {
    "name": "service-name",
    "type": "service",
    "version": "1.0.0"
  },
  "description": "服务描述",
  "interfaces": [],
  "dependencies": [],
  "configuration": {}
}
```

## 模板

工具内置了多种 spec 模板，位于 `templates/specs/` 目录：

- `feature.json` - 功能规格模板
- `api.json` - API 规格模板
- `component.json` - 组件规格模板
- `service.json` - 服务规格模板

## 工作流

1. **初始化项目**: `sdd init my-project`
2. **创建 spec**: `sdd new-spec feature-name`
3. **编辑 spec**: 详细填写规格内容
4. **验证 spec**: `sdd validate spec.json`
5. **生成代码**: 使用 AI 工具基于 spec 生成代码

## 配置文件

`sdd-config.json` 配置示例：

```json
{
  "project": {
    "name": "my-project",
    "version": "0.1.0"
  },
  "sdd": {
    "specs_dir": "specs",
    "src_dir": "src",
    "tests_dir": "tests"
  },
  "code_generation": {
    "framework": "auto",
    "style_guide": "pep8"
  }
}
```