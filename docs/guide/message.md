# 消息发送

本文档介绍如何使用 OpenCode Python Client 发送消息。

## 概述

消息发送有两种方式：
1. **便捷方法**：`ask()` 和 `ask_stream()`
2. **底层 API**：`message.send()`

## 便捷方法

### ask - 同步响应

获取完整响应：

```python
from opencode_client import AsyncOpenCode

async with AsyncOpenCode(start_server=True) as client:
    # 简单提问
    answer = await client.ask("什么是 Python 装饰器？")
    print(answer)

    # 带参数提问
    answer = await client.ask(
        prompt="解释闭包",
        model="anthropic/claude-3-5-sonnet-20241022",
        session_id="existing-session-id",  # 复用会话
        title="新会话标题",  # 创建新会话时使用
    )
```

### ask_stream - 流式响应

实时获取事件流：

```python
async with AsyncOpenCode(start_server=True) as client:
    async for event in client.ask_stream("写一个快速排序"):
        if event.type == "message.part.updated":
            text = event.properties.part.text
            if text:
                print(text, end="", flush=True)
```

## 底层 API

### message.send

发送消息并等待响应：

```python
async with AsyncOpenCode(start_server=True) as client:
    session = await client.create_session()

    # 发送文本消息
    response = await client.message.send(
        session.id,
        "Hello!",
        model="anthropic/claude-3-5-sonnet-20241022",  # 可选
        agent="primary",  # 可选
    )

    # 响应结构
    # {
    #     "info": {...},  # 消息信息
    #     "parts": [...],  # 消息部分
    # }

    # 提取文本
    for part in response.get("parts", []):
        if isinstance(part, dict) and part.get("type") == "text":
            print(part.get("text", ""))
```

### message.list_messages

列出会话中的消息：

```python
messages = await client.message.list_messages(session_id)
for msg in messages:
    print(f"消息 ID: {msg.get('info', {}).get('id')}")
    for part in msg.get("parts", []):
        if part.get("type") == "text":
            print(f"  内容: {part.get('text', '')[:50]}...")
```

## 参数说明

### ask / ask_stream 参数

| 参数 | 类型 | 说明 |
| ---- | ---- | ---- |
| `prompt` | `str` | 问题内容 |
| `model` | `str \| None` | 模型（格式: "provider/model-id"） |
| `agent` | `str \| None` | 代理名称 |
| `session_id` | `str \| None` | 复用的会话 ID |
| `title` | `str \| None` | 新会话的标题 |

### message.send 参数

| 参数 | 类型 | 说明 |
| ---- | ---- | ---- |
| `session_id` | `str` | 会话 ID |
| `content` | `str` | 消息内容 |
| `model` | `str \| None` | 模型 |
| `agent` | `str \| None` | 代理 |

## 指定模型

模型格式为 `"provider/model-id"`：

```python
# Anthropic
await client.ask("Hello", model="anthropic/claude-3-5-sonnet-20241022")

# OpenAI
await client.ask("Hello", model="openai/gpt-4")

# 本地模型
await client.ask("Hello", model="ollama/llama3")
```

## 使用代理

```python
# 指定代理
answer = await client.ask(
    "优化这段代码",
    agent="code-reviewer",
)

# 列出可用代理
agents = await client.agent.list()
for agent in agents:
    print(f"- {agent.name}: {agent.description}")
```

## 响应格式

### ask 响应

返回字符串（拼接所有文本部分）：

```python
answer = await client.ask("Hello")
# answer: "Hello! How can I help you?"
```

### message.send 响应

返回字典：

```python
response = await client.message.send(session_id, "Hello")
# response:
# {
#     "info": {
#         "id": "msg-xxx",
#         "sessionID": "session-xxx",
#         "role": "assistant",
#         "model": {"providerID": "anthropic", "modelID": "claude-3-5-sonnet"},
#         ...
#     },
#     "parts": [
#         {"id": "part-xxx", "type": "text", "text": "Hello! ..."}
#     ]
# }
```

## 完整示例

### 对话循环

```python
import asyncio
from opencode_client import AsyncOpenCode

async def chat_loop():
    async with AsyncOpenCode(start_server=True) as client:
        session = await client.create_session(title="对话")

        print("开始对话（输入 'quit' 退出）")
        while True:
            user_input = input("\n你: ")
            if user_input.lower() == "quit":
                break

            # 流式输出
            print("\nAI: ", end="", flush=True)
            async for event in client.ask_stream(
                user_input,
                session_id=session.id,
            ):
                if event.type == "message.part.updated":
                    text = event.properties.part.text
                    if text:
                        print(text, end="", flush=True)
            print()

        await client.session.delete(session.id)

asyncio.run(chat_loop())
```

### 批量提问

```python
import asyncio
from opencode_client import AsyncOpenCode

async def batch_questions(questions):
    async with AsyncOpenCode(start_server=True) as client:
        session = await client.create_session(title="批量问答")

        results = []
        for question in questions:
            answer = await client.ask(question, session_id=session.id)
            results.append({"question": question, "answer": answer})

        await client.session.delete(session.id)
        return results

questions = ["什么是 Python?", "什么是 JavaScript?", "什么是 Go?"]
results = asyncio.run(batch_questions(questions))
for r in results:
    print(f"Q: {r['question']}")
    print(f"A: {r['answer'][:100]}...\n")
```

## 下一步

- [会话管理](session.md) - 会话操作
- [事件处理](events.md) - SSE 事件流
- [客户端使用](client.md) - 客户端详解
