# 会话管理

会话（Session）是 OpenCode 中管理对话上下文的核心概念。本文档介绍会话的创建、查询、更新和删除操作。

## 概述

会话用于：
- 保持多轮对话的上下文
- 组织相关的对话
- 支持会话分支（子会话）

## 创建会话

### 使用便捷方法

```python
from opencode_client import AsyncOpenCode

async with AsyncOpenCode(start_server=True) as client:
    # 创建简单会话
    session = await client.create_session()

    # 创建带标题的会话
    session = await client.create_session(title="代码审查")

    # 创建子会话
    parent = await client.create_session(title="父会话")
    child = await client.create_session(
        title="子会话",
        parent_id=parent.id,
    )
```

### 使用 Session API

```python
from opencode_client import AsyncOpenCode, SessionCreate

async with AsyncOpenCode(start_server=True) as client:
    request = SessionCreate(title="我的会话")
    session = await client.session.create(request)
```

## 查询会话

### 获取单个会话

```python
session = await client.session.get(session_id)
print(f"标题: {session.title}")
print(f"创建时间: {session.created_at}")
```

### 列出所有会话

```python
sessions = await client.session.list_all()
for s in sessions:
    print(f"- {s.id}: {s.title}")
```

### 检查会话是否存在

```python
exists = await client.session.exists(session_id)
if exists:
    print("会话存在")
else:
    print("会话不存在")
```

### 获取子会话

```python
children = await client.session.children(parent_id)
for child in children:
    print(f"- {child.id}: {child.title}")
```

## 更新会话

```python
from opencode_client import AsyncOpenCode, SessionUpdate

async with AsyncOpenCode(start_server=True) as client:
    # 更新标题
    updated = await client.session.update(
        session_id,
        SessionUpdate(title="新标题"),
    )

    print(f"更新后标题: {updated.title}")
```

## 删除会话

```python
# 删除会话
result = await client.session.delete(session_id)
if result:
    print("删除成功")
```

## 会话模型

### Session

```python
from opencode_client.models import Session

session = await client.session.get(session_id)

# 主要属性
session.id           # 会话 ID
session.title        # 会话标题
session.parent_id    # 父会话 ID
session.created_at   # 创建时间
session.updated_at   # 更新时间
session.path         # 会话路径
```

### SessionCreate

创建会话的请求模型：

```python
from opencode_client.models import SessionCreate

request = SessionCreate(
    title="我的会话",
    parent_id="parent-session-id",  # 可选
)
```

### SessionUpdate

更新会话的请求模型：

```python
from opencode_client.models import SessionUpdate

request = SessionUpdate(
    title="新标题",
)
```

## 使用场景

### 多轮对话

保持上下文连续性：

```python
async with AsyncOpenCode(start_server=True) as client:
    session = await client.create_session(title="连续对话")

    # 第一轮
    answer1 = await client.ask(
        "请记住数字 42",
        session_id=session.id,
    )

    # 第二轮（记住上下文）
    answer2 = await client.ask(
        "我刚才让你记住的数字是多少？",
        session_id=session.id,
    )
    print(answer2)  # 包含 42
```

### 会话分支

从某个点创建分支对话：

```python
async with AsyncOpenCode(start_server=True) as client:
    # 主会话
    main = await client.create_session(title="主线")
    await client.ask("讨论主题 A", session_id=main.id)

    # 创建分支
    branch = await client.create_session(
        title="分支讨论",
        parent_id=main.id,
    )
    await client.ask("讨论主题 A 的变体", session_id=branch.id)
```

### 会话清理

```python
async with AsyncOpenCode(start_server=True) as client:
    # 列出所有会话
    sessions = await client.session.list_all()

    # 删除旧会话
    for s in sessions:
        if s.title.startswith("临时"):
            await client.session.delete(s.id)
            print(f"已删除: {s.id}")
```

## 自动清理

使用配置自动清理临时会话：

```python
from opencode_client import AsyncOpenCode, ClientConfig

# ask/ask_stream 创建的会话会自动清理
config = ClientConfig(cleanup_sessions=True)

async with AsyncOpenCode(start_server=True, config=config) as client:
    # 这个会话会在退出时自动删除
    answer = await client.ask("Hello")
```

## 完整示例

### 会话管理工具

```python
import asyncio
from opencode_client import AsyncOpenCode

async def session_manager():
    async with AsyncOpenCode(start_server=True) as client:
        while True:
            print("\n=== 会话管理 ===")
            print("1. 列出会话")
            print("2. 创建会话")
            print("3. 删除会话")
            print("4. 在会话中对话")
            print("5. 退出")

            choice = input("选择: ")

            if choice == "1":
                sessions = await client.session.list_all()
                for s in sessions:
                    print(f"  {s.id}: {s.title}")

            elif choice == "2":
                title = input("标题: ")
                session = await client.create_session(title=title)
                print(f"创建成功: {session.id}")

            elif choice == "3":
                session_id = input("会话 ID: ")
                await client.session.delete(session_id)
                print("删除成功")

            elif choice == "4":
                session_id = input("会话 ID: ")
                prompt = input("问题: ")
                answer = await client.ask(prompt, session_id=session_id)
                print(f"回答: {answer}")

            elif choice == "5":
                break

asyncio.run(session_manager())
```

## 下一步

- [消息发送](message.md) - 消息 API 详解
- [事件处理](events.md) - SSE 事件流
- [配置选项](configuration.md) - 客户端配置
