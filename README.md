# OpenCode Client

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个用于连接 [OpenCode](https://opencode.ai) 服务器的 Python 客户端库。

## 特性

- 🚀 **异步支持** - 完全基于 asyncio 构建
- 🔄 **SSE 流式响应** - 支持 Server-Sent Events 流式输出
- 🛠️ **自动服务器管理** - 自动启动和清理 OpenCode 服务器
- 📊 **进度显示** - 内置 Rich 进度条支持
- 🔧 **灵活配置** - 支持自定义服务器、执行参数

## 安装

```bash
# 使用 uv
uv add opencode-client

# 或使用 pip
pip install opencode-client
```

### 前置要求

- Python 3.11+
- [OpenCode CLI](https://opencode.ai) 已安装并添加到 PATH

## 快速开始

### 基本用法

```python
import asyncio
from opencode_client import OpenCodeClient, ServerConfig

async def main():
    # 使用上下文管理器自动管理服务器生命周期
    async with OpenCodeClient(ServerConfig(port=4096)) as client:
        # 创建会话
        session_id = await client.create_session("我的会话")

        # 发送消息
        response = await client.send_message(session_id, "你好，请介绍一下你自己")
        print(response)

        # 会话会在退出时自动清理

asyncio.run(main())
```

### 批量执行

```python
import asyncio
from opencode_client import OpenCodeClient

async def main():
    tasks = ["任务1", "任务2", "任务3"]

    async with OpenCodeClient() as client:
        results = await client.execute_batch(
            tasks,
            title_prefix="批量测试",
            on_result=lambda i, task, result: print(f"任务 {i+1}: {'成功' if result.success else '失败'}")
        )

        print(f"完成 {len(results)} 个任务")

asyncio.run(main())
```

### 自定义配置

```python
from opencode_client import OpenCodeClient, ServerConfig, ExecutionConfig

# 自定义服务器配置
server_config = ServerConfig(
    port=8080,
    hostname="0.0.0.0",
    startup_timeout=60.0,
)

# 自定义执行配置
execution_config = ExecutionConfig(
    cleanup_sessions=False,
    retry_on_failure=True,
    retry_count=3,
    request_timeout=1200,  # 20 分钟
)

client = OpenCodeClient(
    config=server_config,
    execution=execution_config,
)
```

### 解析响应

```python
from opencode_client import EventParser

# 直接使用解析器
parser = EventParser()

# 解析事件列表
events = [{"type": "text", "part": {"text": "```json_result\n{\"sql\": \"SELECT 1\"}\n```"}}]
result = parser.parse_events(events)

print(result.sql)       # "SELECT 1"
print(result.success)   # True
```

## API 参考

