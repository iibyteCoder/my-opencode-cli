# OpenCode Python Client

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

一个现代化的 Python 客户端库，用于与 [OpenCode](https://opencode.ai) 服务器交互。

## 特性

- 🚀 **异步优先** - 完全基于 `asyncio` 构建，同时提供同步接口
- 📦 **分层架构** - 清晰的传输层、API 层、客户端层分层设计
- 🔷 **Pydantic v2** - 完整的类型安全数据模型
- 🔄 **SSE 流式响应** - 支持 Server-Sent Events 实时流式输出
- 🖥️ **自动服务器管理** - 可选的本地服务器自动启动和清理
- 🔌 **远程连接支持** - 支持连接到本地或远程 OpenCode 服务器
- 🛠️ **CLI 工具** - 内置命令行工具，支持快速提问、会话管理、文件操作
- ✅ **严格类型检查** - 使用 mypy 严格模式，完整的类型提示

## 安装

```bash
# 使用 uv (推荐)
uv add opencode-client

# 或使用 pip
pip install opencode-client
```

### 前置要求

- Python 3.11+
- [OpenCode CLI](https://opencode.ai) 已安装并添加到 PATH（仅当需要自动启动本地服务器时）

## 快速开始

### 异步客户端

```python
import asyncio
from opencode_client import AsyncOpenCode

async def main():
    # 连接到远程服务器
    async with AsyncOpenCode(base_url="http://localhost:4096") as client:
        # 快速提问
        answer = await client.ask("什么是 Python 装饰器？")
        print(answer)

    # 自动启动本地服务器
    async with AsyncOpenCode(start_server=True) as client:
        # 流式提问
        async for event in client.ask_stream("写一个快速排序"):
            if hasattr(event, 'text') and event.text:
                print(event.text, end="", flush=True)

asyncio.run(main())
```

### 同步客户端

```python
from opencode_client import OpenCode

# 使用上下文管理器
with OpenCode(base_url="http://localhost:4096") as client:
    answer = client.ask("什么是闭包？")
    print(answer)

# 链式调用
client = OpenCode(start_server=True).connect()
try:
    answer = client.ask("解释 Python 的 GIL")
    print(answer)
finally:
    client.disconnect()
```

## 架构设计

项目采用分层架构设计：

```text
┌─────────────────────────────────────────────────────────────┐
│                    High-Level Client                         │
│           (AsyncOpenCode / OpenCode - 便捷 API)             │
├─────────────────────────────────────────────────────────────┤
│                      API Layer                               │
│     (SessionAPI, MessageAPI, FileAPI, ProjectAPI...)        │
├─────────────────────────────────────────────────────────────┤
│                    Transport Layer                           │
│           (HTTPTransport, SSE Parser, ServerProcess)        │
├─────────────────────────────────────────────────────────────┤
│                     Data Models                              │
│                (Pydantic v2 Models)                          │
└─────────────────────────────────────────────────────────────┘
```

### 模块说明

| 模块 | 说明 |
| ----------- | ----------- |
| `models/` | Pydantic 数据模型（会话、消息、事件、文件、配置等） |
| `transport/` | 传输层（HTTP、SSE 流处理、服务器进程管理） |
| `api/` | 低层 API 封装（会话、消息、文件、搜索、事件订阅等） |
| `client/` | 高层客户端（异步客户端、同步客户端、工厂） |
| `core/` | 核心功能（配置、异常、常量） |
| `utils/` | 工具函数（JSON 解析等） |

## 详细用法

### 会话管理

```python
from opencode_client import AsyncOpenCode, SessionCreate

async def session_example():
    async with AsyncOpenCode(base_url="http://localhost:4096") as client:
        # 创建会话
        session = await client.create_session(
            title="代码审查",
            model="anthropic/claude-sonnet-4-5",
        )
        print(f"会话 ID: {session.id}")

        # 列出所有会话
        sessions = await client.session.list()
        for s in sessions:
            print(f"- {s.id}: {s.title}")

        # 删除会话
        await client.session.delete(session.id)
```

### 消息发送

```python
from opencode_client import AsyncOpenCode, MessageContent, TextPart

async def message_example():
    async with AsyncOpenCode(base_url="http://localhost:4096") as client:
        session = await client.create_session()

        # 发送文本消息
        events = await client.message.send(session.id, "你好！")

        # 流式发送
        async for event in client.message.stream(session.id, "写一个冒泡排序"):
            print(f"Event: {event.type}")

        # 发送多部分消息
        content = MessageContent(parts=[
            TextPart(text="请分析这段代码："),
            TextPart(text="def foo(): pass"),
        ])
        await client.message.send(session.id, content)
```

### 文件操作

```python
from opencode_client import AsyncOpenCode

async def file_example():
    async with AsyncOpenCode(base_url="http://localhost:4096") as client:
        # 读取文件
        content = await client.file.read("src/main.py")
        print(content.content)

        # 搜索文件内容
        results = await client.file.search("def.*async")
        for r in results:
            print(f"{r.path}:{r.line}")
```

### 项目信息

```python
from opencode_client import AsyncOpenCode

async def project_example():
    async with AsyncOpenCode(base_url="http://localhost:4096") as client:
        # 获取当前项目信息
        info = await client.project.current()
        print(info)

        # 获取项目配置
        config = await client.project.config()
        print(f"Model: {config.model}")
```

## 配置

### 客户端配置

```python
from opencode_client import AsyncOpenCode, ClientConfig

config = ClientConfig(
    # 服务器配置
    server_hostname="127.0.0.1",
    server_port=4096,
    startup_timeout=30.0,

    # 请求配置
    request_timeout=600,  # 10 分钟

    # 会话配置
    cleanup_sessions=True,  # 自动清理临时会话

    # 重试配置
    retry_count=2,
    retry_delay=1.0,

    # 日志配置
    log_level="INFO",
)

client = AsyncOpenCode(config=config)
```

### 环境变量

| 变量 | 说明 | 默认值 |
| --------------- | -------------------------- | --------------------------- |
| `OPENCODE_URL` | 默认服务器 URL | `http://127.0.0.1:4096` |
| `OPENCODE_TIMEOUT` | 请求超时（秒） | `600` |

## CLI 命令行工具

安装后，可以使用 `opencode-client` 命令：

```bash
# 快速提问
opencode-client ask "什么是 Python 装饰器？"

# 流式输出
opencode-client ask --stream "写一个快速排序"

# 连接到远程服务器
opencode-client --url http://remote-server:4096 ask "解释闭包"

# 启动本地服务器并提问
opencode-client --start-server ask "写一个冒泡排序"

# Markdown 格式输出
opencode-client ask --format markdown "解释 async/await"

# 会话管理
opencode-client session list
opencode-client session create --title "代码审查"
opencode-client session delete <session-id>

# 文件操作
opencode-client file read src/main.py
opencode-client file search "def.*async"

# 项目信息
opencode-client info
```

### CLI 选项

| 选项 | 说明 |
| ----------------- | ---------------------------- |
| `--url, -u` | OpenCode 服务器 URL |
| `--start-server` | 启动本地 OpenCode 服务器 |
| `--timeout, -t` | 请求超时时间（秒） |

## 异常处理

```python
from opencode_client import (
    OpenCodeError,
    ConnectionError,
    ServerStartError,
    SessionError,
    APIError,
    TimeoutError,
)

try:
    async with AsyncOpenCode(start_server=True) as client:
        answer = await client.ask("Hello")
except ServerStartError as e:
    print(f"服务器启动失败: {e}")
except ConnectionError as e:
    print(f"连接错误: {e}")
except APIError as e:
    print(f"API 错误 (HTTP {e.status_code}): {e}")
except TimeoutError as e:
    print(f"请求超时: {e}")
except OpenCodeError as e:
    print(f"OpenCode 错误: {e}")
```

## 数据模型

所有数据模型都使用 Pydantic v2 定义，提供完整的类型安全和验证：

```python
from opencode_client import (
    # 会话
    Session,
    SessionCreate,

    # 消息
    TextPart,
    ImagePart,
    FilePart,
    MessageContent,
    MessageSend,

    # 事件
    SSEEvent,
    TextEvent,
    ToolUseEvent,
    ToolResultEvent,
    ErrorEvent,
    DoneEvent,

    # 文件
    FileInfo,
    FileContent,

    # 配置
    OpenCodeConfig,
    AgentConfig,
    ToolConfig,
)
```

## 开发

### 安装开发依赖

```bash
# 克隆仓库
git clone https://github.com/example/opencode-client.git
cd opencode-client

# 使用 uv 安装
uv sync --all-extras
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 带覆盖率
uv run pytest --cov=opencode_client

# 类型检查
uv run mypy src/opencode_client
```

### 代码风格

项目使用 Ruff 进行代码格式化和检查：

```bash
# 格式化
uv run ruff format src/

# 检查
uv run ruff check src/
```

## API 参考

### AsyncOpenCode

| 方法 | 说明 |
| --------------------------- | ------------------ |
| `connect()` | 连接到服务器 |
| `disconnect()` | 断开连接 |
| `ask(prompt, **kwargs)` | 快速提问 |
| `ask_stream(prompt, **kwargs)` | 流式提问 |
| `create_session(title, **kwargs)` | 创建会话 |
| `session` | 会话 API |
| `message` | 消息 API |
| `file` | 文件 API |
| `project` | 项目 API |

### OpenCode (同步)

同步客户端提供与异步客户端相同的 API，但所有方法都是同步的。

## 许可证

[MIT License](LICENSE)

## 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 相关链接

- [OpenCode 官网](https://opencode.ai)
- [OpenCode 文档](https://opencode.ai/docs)
- [问题反馈](https://github.com/example/opencode-client/issues)
