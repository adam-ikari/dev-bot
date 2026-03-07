# UV 虚拟环境使用指南

## 当前状态

✅ **虚拟环境已正确配置**：`.venv/`
✅ **所有依赖通过 uv 管理**：pydantic、loguru、watchdog、textual 等
⚠️ **系统环境有残留包**：需要手动清理

## 使用 UV 虚拟环境

### 方法 1：使用 uv run（推荐）

```bash
# 运行 Python 脚本
uv run python your_script.py

# 运行测试
uv run pytest

# 运行主程序
uv run python -m dev_bot
```

### 方法 2：激活虚拟环境

```bash
# 激活虚拟环境
source .venv/bin/activate

# 验证环境
which python  # 应该显示 .venv/bin/python

# 运行 Python
python your_script.py

# 退出虚拟环境
deactivate
```

### 方法 3：直接使用虚拟环境 Python

```bash
# 使用虚拟环境中的 Python
.venv/bin/python your_script.py

# 使用虚拟环境中的 pip
.venv/bin/pip list
```

## 清理系统环境中的残留包

### 自动清理脚本

```bash
./cleanup_system_packages.sh
```

### 手动清理

由于权限限制，需要手动执行以下命令：

```bash
# 卸载系统包
sudo pip3 uninstall -y pydantic pydantic-core textual

# 或手动删除目录
sudo rm -rf /usr/local/lib/python3.9/dist-packages/pydantic*
sudo rm -rf /usr/local/lib/python3.9/dist-packages/textual*
```

## 验证环境

### 验证虚拟环境

```bash
# 检查虚拟环境中的包版本
.venv/bin/python -c "import pydantic; print('Pydantic:', pydantic.__version__)"
.venv/bin/python -c "import loguru; print('Loguru:', loguru.__version__)"
.venv/bin/python -c "import textual; print('Textual:', textual.__version__)"
.venv/bin/python -c "import watchdog; print('Watchdog:', watchdog.__version__)"

# 应该输出：
# Pydantic: 2.12.5
# Loguru: 0.7.3
# Textual: 8.0.2
# Watchdog: 3.0.0
```

### 检查系统环境

```bash
# 检查系统环境是否还有残留
pip3 list | grep -E "(pydantic|loguru|watchdog|textual)"

# 清理后应该无输出
```

## 管理依赖

### 安装新依赖

```bash
# 添加到 pyproject.toml 并安装
uv add package_name

# 添加开发依赖
uv add --dev package_name
```

### 移除依赖

```bash
# 从 pyproject.toml 移除并卸载
uv remove package_name
```

### 同步依赖

```bash
# 根据 pyproject.toml 同步依赖
uv sync
```

## 常见问题

### Q: 如何确保使用的是虚拟环境？

A: 始终使用以下任一方法：
1. `uv run python script.py`（推荐）
2. `source .venv/bin/activate` 后使用 `python script.py`
3. `.venv/bin/python script.py`

### Q: 为什么不能直接用 `python` 命令？

A: 系统 Python 是 `/usr/bin/python`，虚拟环境是 `.venv/bin/python`。直接用 `python` 会使用系统 Python。

### Q: 系统环境中的残留包会影响使用吗？

A: 不会。虚拟环境优先使用自己的包。但为了保持整洁，建议清理系统环境。

### Q: 如何查看当前 Python 环境？

A:
```bash
python -c "import sys; print(sys.executable)"
# 或
which python
```

## 最佳实践

1. **始终使用 uv run**：避免手动激活/停用虚拟环境
2. **不要直接使用 pip**：通过 `uv add/remove` 管理依赖
3. **定期运行 uv sync**：确保依赖与 pyproject.toml 一致
4. **检查虚拟环境**：运行验证命令确保使用正确的 Python

## 环境状态

**虚拟环境位置**：`.venv/`
**Python 版本**：3.9.2
**包管理器**：uv
**依赖文件**：`pyproject.toml`, `uv.lock`

**当前依赖**：
- pydantic: 2.12.5
- pydantic-settings: 2.13.1
- loguru: 0.7.3
- textual: 8.0.2
- watchdog: 3.0.0
- psutil: 6.1.1
- 其他依赖见 `uv pip list`