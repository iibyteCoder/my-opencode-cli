# 客户端使用

本文档详细介绍异步客户端 `AsyncOpenCode` 和同步客户端 `OpenCode` 的使用方法。

## 异步客户端 AsyncOpenCode

### 初始化

```python
from opencode_client import AsyncOpenCode

# 方式 1: 连接到已有服务器
client = AsyncOpenCode(base_url="http://localhost:4096")

# 方式 2: 自动启动本地服务器
client = AsyncOpenCode(start_server=True)

# 方式 3: 使用配置
from opencode_client import ClientConfig

config = ClientConfig(
    server_port=4096,
    startup_timeout=30.0,
)
client = AsyncOpenCode(start_server=True, config=config)
```

### 连接管理

#### 使用上下文管理器（推荐）

```python
async with AsyncOpenCode(start_server=True) as client:
    # 自动连接和断开
    answer = await client.ask("Hello")
```

#### 手动管理连接

```python
client = AsyncOpenCode(start_server=True)
try:
    await client.connect()
    answer = await client.ask("Hello")
finally:
    await client.disconnect()
```

### 核心方法

#### ask - 快速提问

同步获取完整响应：

```python
answer = await client.ask(
    prompt="什么是 Python 装饰器？",
    model="anthropic/claude-3-5-sonnet-20241022",  # 可选
    agent="primary",                                # 可选
    session_id="existing-session-id",              # 可选，复用会话
    title="新会话标题",                             # 可选，新会话时使用
)
```

#### ask_stream - 流式提问

实时获取事件流：

```python
async for event in client.ask_stream(
    prompt="写一个快速排序",
    model="anthropic/claude-3-5-sonnet-20241022",
):
    # 处理事件
    pass
```

#### create_session - 创建会话

```python
session = await client.create_session(
    title="我的会话",
    parent_id="parent-session-id",  # 可选，创建子会话
)
print(f"会话 ID: {session.id}")
```

### API 属性访问

客户端提供对底层 API 的直接访问：

```python
# 会话 API
sessions = await client.session.list_all()
session = await client.session.get(session_id)
await client.session.delete(session_id)

# 消息 API
response = await client.message.send(session_id, "Hello")

# 文件 API
files = await client.file.list_all(".")
status = await client.file.status()

# 项目 API
info = await client.project.current()
root = await client.project.root()

# 代理 API
agents = await client.agent.list()

# 事件 API
async for event in client.event.subscribe():
    print(event.type)
```

## 同步客户端 OpenCode

同步客户端是异步客户端的包装器，提供相同的 API 但以同步方式执行。

### 初始化

```python
from opencode_client import OpenCode

# 方式 1: 连接到已有服务器
client = OpenCode(base_url="http://localhost:4096")

# 方式 2: 自动启动本地服务器
client = OpenCode(start_server=True)
```

### 连接管理

#### 使用上下文管理器（推荐）

```python
with OpenCode(start_server=True) as client:
    answer = client.ask("Hello")
```

#### 手动管理连接

```python
client = OpenCode(start_server=True)
try:
    client.connect()
    answer = client.ask("Hello")
finally:
    client.disconnect()
```

### 核心方法

```python
# 快速提问
answer = client.ask("什么是闭包？")

# 流式提问（收集所有事件后返回）
events = client.ask_stream("写一个快速排序")
for event in events:
    if event.type == "message.part.updated":
        text = event.properties.part.text
        if text:
            print(text, end="")

# 创建会话
session = client.create_session(title="同步会话")
```

### API 属性访问

同步客户端的 API 属性直接返回异步 API 实例。对于需要 await 的方法，需要使用异步客户端或在异步上下文中调用：

```python
with OpenCode(start_server=True) as client:
    # 同步便捷方法
    answer = client.ask("Hello")

    # 如果需要直接调用 API，建议使用异步客户端
    # 以下代码会产生警告（协程未 await）：
    # sessions = client.session.list_all()  # ❌ 不推荐
```

## 选择指南

| 场景 | 推荐客户端 |
| ---- | ---------- |
| 异步应用（FastAPI、aiohttp） | `AsyncOpenCode` |
| 流式输出需要实时处理 | `AsyncOpenCode` |
| 简单脚本 | `OpenCode` |
| Jupyter Notebook | `OpenCode` 或 `AsyncOpenCode` |
| 多并发请求 | `AsyncOpenCode` |

## 最佳实践

### 资源清理

始终使用上下文管理器确保资源正确释放：

```python
# ✅ 推荐
async with AsyncOpenCode(start_server=True) as client:
    answer = await client.ask("Hello")

# ❌ 不推荐（可能忘记断开连接）
client = AsyncOpenCode(start_server=True)
await client.connect()
answer = await client.ask("Hello")
# 忘记 disconnect()
```

### 会话复用

对于多轮对话，复用会话 ID：

```python
async with AsyncOpenCode(start_server=True) as client:
    session = await client.create_session()

    # 复用会话进行多轮对话
    for question in questions:
        answer = await client.ask(question, session_id=session.id)
```

### 错误处理

```python
from opencode_client import AsyncOpenCode, ConnectionError, APIError

try:
    async with AsyncOpenCode(start_server=True) as client:
        answer = await client.ask("Hello")
except ConnectionError as e:
    print(f"连接失败: {e}")
except APIError as e:
    print(f"API 错误: {e}")
```

## 下一步

- [会话管理](session.md) - 会话的完整操作
- [消息发送](message.md) - 消息 API 详解
- [事件处理](events.md) - SSE 事件流
