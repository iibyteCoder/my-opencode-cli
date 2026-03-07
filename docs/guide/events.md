# 事件处理

OpenCode 使用 Server-Sent Events (SSE) 推送实时事件。本文档介绍如何处理事件流。

## 事件类型

### 事件列表

| 事件类型 | 说明 | 主要属性 |
| -------- | ---- | -------- |
| `server.connected` | 服务器连接成功 | 无 |
| `message.updated` | 消息状态更新 | `info`（消息信息） |
| `message.part.updated` | 消息内容增量更新 | `part`（消息部分） |
| `session.status` | 会话状态变化 | `session_id`, `status` |
| `session.updated` | 会话信息更新 | `info`（会话信息） |
| `session.diff` | 会话差异 | `session_id`, `diff` |

### 事件模型

所有事件都继承自 `OpenCodeModel`：

```python
from my_opencode_cli.models import (
    Event,                    # 联合类型（所有事件）
    ServerConnectedEvent,     # 服务器连接
    MessageUpdatedEvent,      # 消息更新
    MessagePartUpdatedEvent,  # 消息部分更新
    SessionStatusEvent,       # 会话状态
    SessionUpdatedEvent,      # 会话更新
    SessionDiffEvent,         # 会话差异
)
```

## 基本用法

### 订阅事件流

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def main():
    async with AsyncOpenCode(start_server=True) as client:
        # 订阅所有事件
        async for event in client.event.subscribe():
            print(f"事件类型: {event.type}")
            # 退出条件
            if event.type == "server.connected":
                break

asyncio.run(main())
```

### 使用 ask_stream

`ask_stream` 方法自动过滤当前会话的事件：

```python
async with AsyncOpenCode(start_server=True) as client:
    async for event in client.ask_stream("写一个快速排序"):
        if event.type == "message.part.updated":
            text = event.properties.part.text
            if text:
                print(text, end="")
```

## 事件详解

### message.part.updated

最常见的流式输出事件，包含增量文本：

```python
async for event in client.ask_stream("Hello"):
    if event.type == "message.part.updated":
        part = event.properties.part
        print(f"消息 ID: {part.message_id}")
        print(f"部分 ID: {part.id}")
        print(f"文本: {part.text}")
```

### session.status

会话状态变化，用于判断 AI 是否完成：

```python
async for event in client.ask_stream("Hello"):
    if event.type == "session.status":
        status_type = event.properties.status.get("type")
        if status_type == "idle":
            print("\n[AI 已完成]")
            break
        elif status_type == "busy":
            print("[AI 正在处理...]")
```

### message.updated

消息整体更新，包含完整消息信息：

```python
async for event in client.event.subscribe():
    if event.type == "message.updated":
        info = event.properties.info
        print(f"消息 ID: {info.id}")
        print(f"角色: {info.role}")
        print(f"模型: {info.model}")
```

## 实用模式

### 收集完整响应

```python
async def get_full_response(client, prompt):
    text_parts = []

    async for event in client.ask_stream(prompt):
        if event.type == "message.part.updated":
            text = event.properties.part.text
            if text:
                text_parts.append(text)
        elif event.type == "session.status":
            if event.properties.status.get("type") == "idle":
                break

    return "".join(text_parts)

async with AsyncOpenCode(start_server=True) as client:
    response = await get_full_response(client, "写一个快速排序")
    print(response)
```

### 带进度显示

```python
async for event in client.ask_stream("写一个复杂程序"):
    if event.type == "message.part.updated":
        text = event.properties.part.text
        if text:
            print(text, end="", flush=True)
    elif event.type == "session.status":
        status = event.properties.status.get("type")
        print(f"\n[状态: {status}]")
```

### 事件过滤

只处理特定会话的事件：

```python
async def filter_session_events(client, session_id):
    async for event in client.event.subscribe():
        # 检查事件是否属于该会话
        if hasattr(event, "properties"):
            props = event.properties

            # SessionStatusEvent
            if hasattr(props, "session_id") and props.session_id == session_id:
                yield event

            # MessagePartUpdatedEvent
            elif hasattr(props, "part"):
                if props.part.session_id == session_id:
                    yield event
```

### 超时处理

```python
import asyncio

async def ask_with_timeout(client, prompt, timeout=30.0):
    try:
        async with asyncio.timeout(timeout):
            async for event in client.ask_stream(prompt):
                if event.type == "message.part.updated":
                    text = event.properties.part.text
                    if text:
                        print(text, end="")
    except asyncio.TimeoutError:
        print("\n[超时]")
```

## 完整示例

### 流式聊天应用

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def chat():
    async with AsyncOpenCode(start_server=True) as client:
        session = await client.create_session(title="聊天")

        print("开始聊天（输入 'quit' 退出）")
        while True:
            user_input = input("\n你: ")
            if user_input.lower() == "quit":
                break

            print("\nAI: ", end="", flush=True)
            async for event in client.ask_stream(
                user_input,
                session_id=session.id,
            ):
                if event.type == "message.part.updated":
                    text = event.properties.part.text
                    if text:
                        print(text, end="", flush=True)

            print()  # 换行

        await client.session.delete(session.id)

asyncio.run(chat())
```

### 事件日志记录

```python
import asyncio
import json
from datetime import datetime
from my_opencode_cli import AsyncOpenCode

async def log_events():
    async with AsyncOpenCode(start_server=True) as client:
        log_file = open("events.log", "a", encoding="utf-8")

        async def logger():
            async for event in client.event.subscribe():
                log_entry = {
                    "time": datetime.now().isoformat(),
                    "type": event.type,
                    "data": event.model_dump(),
                }
                log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                log_file.flush()

        # 在后台运行日志
        logger_task = asyncio.create_task(logger())

        try:
            # 主应用逻辑
            await client.ask("Hello")
            await asyncio.sleep(1)
        finally:
            logger_task.cancel()
            log_file.close()

asyncio.run(log_events())
```

## 下一步

- [消息发送](message.md) - 消息 API 详解
- [会话管理](session.md) - 会话操作
- [配置选项](configuration.md) - 客户端配置
