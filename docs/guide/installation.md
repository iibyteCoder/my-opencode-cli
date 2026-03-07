# 安装指南

本指南介绍如何安装和配置 OpenCode Python Client。

## 系统要求

- Python 3.11 或更高版本
- pip 或 uv 包管理器

## 安装方式

### 使用 uv（推荐）

[uv](https://github.com/astral-sh/uv) 是一个快速的 Python 包管理器：

```bash
uv add my-opencode-cli
```

### 使用 pip

```bash
pip install my-opencode-cli
```

### 从源码安装

```bash
git clone https://github.com/example/my-opencode-cli.git
cd my-opencode-cli
uv sync --all-extras
```

## 可选依赖

### OpenCode CLI

如果需要自动启动本地 OpenCode 服务器，需要安装 OpenCode CLI：

```bash
# macOS/Linux
curl -fsSL https://opencode.ai/install.sh | sh

# Windows (使用 Scoop)
scoop install opencode

# 或使用 npm
npm install -g @opencode-ai/cli
```

验证安装：

```bash
opencode --version
```

### 开发依赖

如需参与开发，安装开发依赖：

```bash
uv sync --all-extras
```

包含的工具：

| 工具 | 说明 |
| ---- | ---- |
| mypy | 静态类型检查 |
| ruff | 代码格式化和检查 |
| pytest | 测试框架 |
| pytest-asyncio | 异步测试支持 |

## 验证安装

### 基本验证

```python
from opencode_client import AsyncOpenCode, OpenCode
from opencode_client.models import Session, Event

print("安装成功！")
```

### 连接测试

```python
import asyncio
from opencode_client import AsyncOpenCode

async def test_connection():
    async with AsyncOpenCode(base_url="http://localhost:4096") as client:
        print(f"已连接: {client.is_connected}")

asyncio.run(test_connection())
```

### 自动启动服务器测试

```python
import asyncio
from opencode_client import AsyncOpenCode

async def test_with_server():
    # 自动启动本地服务器
    async with AsyncOpenCode(start_server=True) as client:
        answer = await client.ask("你好")
        print(f"响应: {answer}")

asyncio.run(test_with_server())
```

## 常见问题

### Q: 连接超时怎么办？

检查 OpenCode 服务器是否运行：

```bash
curl http://localhost:4096/health
```

### Q: 找不到 opencode 命令？

确保 OpenCode CLI 已安装并添加到 PATH：

```bash
which opencode  # macOS/Linux
where opencode  # Windows
```

### Q: Python 版本不兼容？

检查 Python 版本：

```bash
python --version  # 需要 3.11+
```

使用 uv 指定 Python 版本：

```bash
uv python install 3.11
uv venv --python 3.11
```

## 下一步

- [快速开始](quick-start.md) - 5 分钟上手教程
- [客户端使用](client.md) - 了解异步和同步客户端
