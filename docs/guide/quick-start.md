# 快速开始

本教程帮助你在 5 分钟内上手 OpenCode Python Client。

## 基本使用

### 1. 快速提问

最简单的使用方式是 `ask` 方法：

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def main():
    # 自动启动服务器并提问
    async with AsyncOpenCode(start_server=True) as client:
        answer = await client.ask("什么是 Python 装饰器？")
        print(answer)

asyncio.run(main())
```

### 2. 流式输出

使用 `ask_stream` 获取实时响应：

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def main():
    async with AsyncOpenCode(start_server=True) as client:
        async for event in client.ask_stream("写一个快速排序"):
            if event.type == "message.part.updated":
                text = event.properties.part.text
                if text:
                    print(text, end="", flush=True)
        print()  # 换行

asyncio.run(main())
```

### 3. 同步客户端

如果你不使用 asyncio，可以使用同步客户端：

```python
from my_opencode_cli import OpenCode

with OpenCode(start_server=True) as client:
    answer = client.ask("什么是闭包？")
    print(answer)
```

## 连接方式

### 连接到已有服务器

如果 OpenCode 服务器已经在运行：

```python
from my_opencode_cli import AsyncOpenCode

async with AsyncOpenCode(base_url="http://localhost:4096") as client:
    answer = await client.ask("Hello")
```

### 连接到远程服务器

```python
from my_opencode_cli import AsyncOpenCode

async with AsyncOpenCode(base_url="http://remote-server:4096") as client:
    answer = await client.ask("Hello")
```

### 自动启动本地服务器

```python
from my_opencode_cli import AsyncOpenCode

# 自动启动、使用、关闭服务器
async with AsyncOpenCode(start_server=True) as client:
    answer = await client.ask("Hello")
# 退出时自动关闭服务器
```

## 指定模型

在发送消息时指定模型：

```python
from my_opencode_cli import AsyncOpenCode

async with AsyncOpenCode(start_server=True) as client:
    answer = await client.ask(
        "解释量子计算",
        model="anthropic/claude-3-5-sonnet-20241022",
    )
```

## 会话复用

保持上下文连续性：

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def main():
    async with AsyncOpenCode(start_server=True) as client:
        # 创建会话
        session = await client.create_session(title="连续对话")

        # 第一次提问
        answer1 = await client.ask(
            "请记住数字 42",
            session_id=session.id,
        )

        # 第二次提问（记住上下文）
        answer2 = await client.ask(
            "我刚才让你记住的数字是多少？",
            session_id=session.id,
        )
        print(answer2)  # 应该包含 42

asyncio.run(main())
```

## 完整示例

以下是一个完整的示例，展示常用功能：

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def main():
    async with AsyncOpenCode(start_server=True) as client:
        # 1. 创建会话
        session = await client.create_session(title="示例会话")
        print(f"会话 ID: {session.id}")

        # 2. 快速提问
        answer = await client.ask(
            "用一句话解释 Python",
            session_id=session.id,
        )
        print(f"回答: {answer}")

        # 3. 流式提问
        print("\n流式输出:")
        async for event in client.ask_stream(
            "从 1 数到 3",
            session_id=session.id,
        ):
            if event.type == "message.part.updated":
                text = event.properties.part.text
                if text:
                    print(text, end="")

        # 4. 列出会话
        sessions = await client.session.list_all()
        print(f"\n\n当前会话数: {len(sessions)}")

        # 5. 清理
        await client.session.delete(session.id)
        print("会话已删除")

asyncio.run(main())
```

## 下一步

- [客户端使用](client.md) - 深入了解异步和同步客户端
- [会话管理](session.md) - 会话的完整操作
- [事件处理](events.md) - SSE 事件流详解
