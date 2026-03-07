# 发布指南

本文档介绍如何将 opencode-client 发布到 PyPI。

## 前置准备

### 1. 注册 PyPI 账号

1. 访问 [PyPI](https://pypi.org/account/register/) 注册账号
2. 访问 [TestPyPI](https://test.pypi.org/account/register/) 注册测试账号（可选但推荐）
3. 启用两步验证（2FA）

### 2. 创建 API Token

1. 登录 PyPI → Account settings → API tokens
2. 创建新 token（选择 "Entire account" 或特定项目）
3. **保存 token**，只显示一次

### 3. 配置认证

创建 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-xxx...  # 你的 API token

[testpypi]
username = __token__
password = pypi-xxx...  # TestPyPI 的 API token
```

或使用环境变量：

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxx...
```

## 发布步骤

### 方式一：使用 uv（推荐）

```bash
# 1. 更新版本号（在 pyproject.toml 中）
# version = "0.2.0" → "0.3.0"

# 2. 构建包
uv build

# 3. 检查包
uv run twine check dist/*

# 4. 上传到 TestPyPI（测试）
uv publish --index testpypi

# 5. 上传到 PyPI（正式）
uv publish
```

### 方式二：使用传统工具

```bash
# 安装工具
pip install build twine

# 构建
python -m build

# 检查
twine check dist/*

# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 上传到 PyPI
twine upload dist/*
```

## 发布前检查清单

```bash
# 1. 更新版本号
# 编辑 pyproject.toml 中的 version

# 2. 运行测试
uv run pytest

# 3. 类型检查
uv run mypy src/opencode_client --strict

# 4. 代码风格
uv run ruff check src/opencode_client

# 5. 构建检查
uv build
uv run twine check dist/*

# 6. 本地安装测试
uv pip install dist/opencode_client-0.2.0-py3-none-any.whl
```

## 版本号规范

使用 [语义化版本](https://semver.org/lang/zh-CN/)：

- `0.1.0` → `0.1.1`: Bug 修复
- `0.1.0` → `0.2.0`: 新功能（向后兼容）
- `0.1.0` → `1.0.0`: 重大更新（可能不兼容）

## GitHub Release

发布后创建 GitHub Release：

```bash
git tag v0.2.0
git push origin v0.2.0
```

然后在 GitHub 上创建 Release，填写更新日志。

## 自动化发布（可选）

创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Build
        run: uv build

      - name: Publish
        run: uv publish --token ${{ secrets.PYPI_TOKEN }}
```

需要在 GitHub 仓库设置中添加 `PYPI_TOKEN` secret。

## 安装验证

发布后验证安装：

```bash
# 从 PyPI 安装
pip install opencode-client

# 或使用 uv
uv add opencode-client

# 验证
python -c "from opencode_client import AsyncOpenCode; print('OK')"
```
