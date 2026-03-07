# 错误处理

本文档介绍 OpenCode Python Client 的异常类型和处理方式。

## 异常层次

```text
OpenCodeError (基类)
├── ConnectionError       # 连接相关错误
├── ServerStartError      # 服务器启动失败
├── APIError              # API 调用错误
│   ├── NotFoundError     # 资源不存在
│   └── ValidationError   # 请求验证失败
└── TimeoutError          # 请求超时
```

## 异常类型

### OpenCodeError

所有异常的基类：

```python
from opencode_client import OpenCodeError

try:
    async with AsyncOpenCode(start_server=True) as client:
        answer = await client.ask("Hello")
except OpenCodeError as e:
    print(f"OpenCode 错误: {e}")
```

### ConnectionError

连接服务器失败：

```python
from opencode_client import ConnectionError

try:
    async with AsyncOpenCode(base_url="http://invalid:4096") as client:
        await client.connect()
except ConnectionError as e:
    print(f"连接失败: {e}")
```

### ServerStartError

自动启动服务器失败：

```python
from opencode_client import ServerStartError

try:
    async with AsyncOpenCode(start_server=True) as client:
        pass
except ServerStartError as e:
    print(f"服务器启动失败: {e}")
    print("请确保已安装 opencode 命令")
```

### APIError

API 调用返回错误：

```python
from opencode_client import APIError

try:
    session = await client.session.get("invalid-id")
except APIError as e:
    print(f"API 错误 (HTTP {e.status_code}): {e}")
```

### TimeoutError

请求超时：

```python
from opencode_client import TimeoutError

try:
    async with asyncio.timeout(5.0):
        answer = await client.ask("Hello")
except TimeoutError as e:
    print(f"请求超时: {e}")
```

## 处理模式

### 基本错误处理

```python
from opencode_client import (
    AsyncOpenCode,
    OpenCodeError,
    ConnectionError,
    APIError,
)

async def safe_ask(prompt):
    try:
        async with AsyncOpenCode(start_server=True) as client:
            return await client.ask(prompt)
    except ConnectionError as e:
        print(f"连接错误: {e}")
        return None
    except APIError as e:
        print(f"API 错误: {e}")
        return None
    except OpenCodeError as e:
        print(f"其他错误: {e}")
        return None
```

### 重试逻辑

```python
import asyncio
from opencode_client import AsyncOpenCode, ConnectionError, APIError

async def ask_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with AsyncOpenCode(start_server=True) as client:
                return await client.ask(prompt)
        except ConnectionError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            raise
```

### 超时处理

```python
import asyncio
from opencode_client import AsyncOpenCode

async def ask_with_timeout(prompt, timeout=30.0):
    async with AsyncOpenCode(start_server=True) as client:
        try:
            async with asyncio.timeout(timeout):
                return await client.ask(prompt)
        except asyncio.TimeoutError:
            print(f"请求超时（{timeout}秒）")
            return None
```

### 会话不存在处理

```python
from opencode_client import AsyncOpenCode, APIError

async def get_or_create_session(client, session_id=None, title="新会话"):
    if session_id:
        try:
            return await client.session.get(session_id)
        except APIError:
            print(f"会话 {session_id} 不存在，创建新会话")
    return await client.create_session(title=title)
```

## 完整示例

```python
import asyncio
from opencode_client import (
    AsyncOpenCode,
    OpenCodeError,
    ConnectionError,
    ServerStartError,
    APIError,
    TimeoutError,
)

async def robust_ask(prompt):
    """带完整错误处理的提问函数。"""
    try:
        async with AsyncOpenCode(start_server=True) as client:
            try:
                async with asyncio.timeout(60.0):
                    return await client.ask(prompt)
            except asyncio.TimeoutError:
                raise TimeoutError("请求超时")

    except ServerStartError as e:
        print(f"无法启动服务器: {e}")
        print("请确保已安装 opencode 命令并添加到 PATH")
        return None

    except ConnectionError as e:
        print(f"连接失败: {e}")
        return None

    except APIError as e:
        print(f"API 错误 (HTTP {e.status_code}): {e}")
        return None

    except TimeoutError as e:
        print(f"超时: {e}")
        return None

    except OpenCodeError as e:
        print(f"未知错误: {e}")
        return None

# 使用
answer = asyncio.run(robust_ask("Hello"))
if answer:
    print(answer)
```

## 常见错误

### 连接被拒绝

```
ConnectionError: Cannot connect to http://localhost:4096
```

**解决方案**：
- 确保 OpenCode 服务器正在运行
- 或使用 `start_server=True`

### 服务器启动超时

```
ServerStartError: Server did not start within 30 seconds
```

**解决方案**：
- 增加 `startup_timeout`
- 检查 opencode 命令是否正确安装

### 会话不存在

```
APIError: Session not found (HTTP 404)
```

**解决方案**：
- 检查 session_id 是否正确
- 会话可能已被删除

## 下一步

- [客户端使用](client.md) - 客户端详解
- [配置选项](configuration.md) - 配置详解
