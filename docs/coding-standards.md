# OpenCode Client 代码规范

## 类型系统

### 泛型与基类设计

使用**非泛型基类**作为类型注解，避免泛型不变性问题：

```python
# ✅ 正确：非泛型基类用于类型注解
class SSEEventBase(OpenCodeModel):
    type: str
    data: dict[str, Any]

class SSEEvent(SSEEventBase, Generic[T]):
    type: T  # 泛型子类

# 类型别名
EventType = KnownEventType | SSEEventBase
```

### Transport 层返回类型

Transport 层返回 `Any`，由 API 层声明具体返回类型：

```python
# transport/base.py
async def request(...) -> Any:
    """返回 JSON 响应（可能是 dict、list 或其他 JSON 类型）。"""

# api/message.py
async def list(...) -> list[dict[str, Any]]:
    return await self._get(...)  # 类型由方法签名决定
```

### 禁止的类型取巧

- ❌ `# type: ignore[misc]` - 应重构类型层次
- ❌ `response_type` 参数 - 污染 API，增加复杂度
- ❌ `@overload` 滥用 - 简单场景不需要
- ❌ `cast()` 隐藏问题 - 修复根本原因

## 架构原则

### 分层设计

```
transport/  → 传输层（HTTP、进程）- 返回 Any
api/        → API 层（低层 API）- 声明具体类型
client/     → 客户端层（高层便捷接口）
models/     → 数据模型（Pydantic v2）
```

### 导入规范

```python
# 相对导入
from ..models.event import EventType
from .client import APIClient
```

### 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 类 | PascalCase | `AsyncOpenCode` |
| 方法/函数 | snake_case | `ask_stream` |
| 私有方法 | `_leading_underscore` | `_parse_event` |
| 类型别名 | PascalCase + Type/Event 后缀 | `EventType` |

## 类型系统进阶

### 避免方法名与内置类型冲突

当方法名与内置类型（如 `list`）冲突时，重命名方法：

```python
# ❌ 错误：list 方法名与 list 类型冲突
class SessionAPI:
    async def list(self) -> list[Session]:  # mypy: Function is not valid as a type
        ...

# ❌ 使用 typing.List（已废弃）
from typing import List
class SessionAPI:
    async def list(self) -> List[Session]:  # ruff: UP006 Use `list` instead

# ✅ 正确：重命名方法避免冲突
class SessionAPI:
    async def list_all(self) -> list[Session]:
        ...
```

### dict.get 返回值处理

`dict.get()` 返回 `Any`，需要显式类型注解：

```python
# ❌ 错误：返回 Any
async def root(self) -> str:
    data = cast(dict[str, Any], await self._get(...))
    return data.get("root", "")  # 返回 Any

# ✅ 正确：显式类型注解
async def root(self) -> str:
    data = cast(dict[str, Any], await self._get(...))
    root_value: str = data.get("root", "")
    return root_value
```

### Pydantic 模型初始化

配置 `pydantic.mypy` 插件以支持类型检查：

```toml
# pyproject.toml
[tool.mypy]
plugins = ["pydantic.mypy"]

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
```

对于严格模式模型，使用 `model_validate` 代替直接构造：

```python
# ❌ 可能出错：直接构造在严格模式下可能有问题
request = SessionCreate(title=title, parent_id=parent_id)

# ✅ 正确：使用 model_validate
request = SessionCreate.model_validate({"title": title, "parentID": parent_id})
```

### cast 的正确使用

`cast` 用于将 `Any` 转换为具体类型：

```python
from typing import cast

# ✅ 正确：将 Any 转换为具体类型
data = await self._get("/endpoint")
return cast(dict[str, Any], data)

# ✅ 正确：json.loads 返回 Any
return cast(dict[str, Any], json.loads(data_str))
```

## Pydantic 模型设计

### 外部 API 响应模型

外部 API 可能返回未预期的字段，使用 `extra="allow"` 避免验证错误：

```python
# ✅ 正确：允许额外字段
class MessageInfo(OpenCodeModel):
    model_config = OpenCodeModel.model_config | {
        "populate_by_name": True,  # 支持 alias
        "extra": "allow",  # 允许 API 返回额外字段
    }

    id: str = Field(..., description="消息 ID")
    session_id: str = Field(..., alias="sessionID", description="会话 ID")
    model: dict[str, Any] | str | None = Field(default=None, description="模型信息")
```

### 字段别名处理

OpenCode API 使用 camelCase（如 `sessionID`），Python 使用 snake_case：

```python
# ✅ 正确：使用 alias 和 populate_by_name
class SessionStatusProperties(OpenCodeModel):
    session_id: str = Field(..., alias="sessionID", description="会话 ID")
    status: dict[str, Any] = Field(..., description="状态")

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}
```

### 命名冲突避免

不同模块中相同用途的类应使用不同名称：

```python
# ❌ 错误：两个模块都有 MessagePart，导致导入冲突
from .event import MessagePart  # SSE 事件中的消息部分
from .message import MessagePart  # 消息内容部分（Union）

# ✅ 正确：使用区分性命名
from .event import EventMessagePart  # SSE 事件专用
from .message import MessagePart  # 消息内容专用
```

## 异步编程模式

### SSE 事件流模式

SSE 端点与消息发送分离，使用 asyncio.Queue 传递事件：

```python
async def _stream_with_session(self, session_id: str, prompt: str) -> AsyncIterator[Event]:
    event_queue: asyncio.Queue[Event | None] = asyncio.Queue()
    stop_event = asyncio.Event()

    async def listen_events() -> None:
        try:
            async for event in self.event.subscribe():
                if self._is_event_for_session(event, session_id):
                    await event_queue.put(event)
                    if stop_event.is_set():
                        break
        finally:
            await event_queue.put(None)  # 结束信号

    # 启动监听任务
    listener_task = asyncio.create_task(listen_events())
    await asyncio.sleep(0.1)  # 等待监听器启动

    # 发送消息
    await self.message.send(session_id, prompt)

    # 从队列获取事件
    try:
        while True:
            event = await event_queue.get()
            if event is None:
                break
            yield event
    finally:
        stop_event.set()
        listener_task.cancel()
```

### 同步客户端包装

同步客户端使用事件循环包装异步方法：

```python
from concurrent.futures import Future
import asyncio

class OpenCode:
    def _run(self, coro: Any) -> Any:
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
                self._owned_loop = False
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                self._owned_loop = True

        if self._owned_loop:
            return self._loop.run_until_complete(coro)
        else:
            future: Future[Any] = asyncio.run_coroutine_threadsafe(coro, self._loop)
            return future.result()
```

### aiohttp 会话管理

独立的 API 模块应管理自己的 aiohttp 会话：

```python
class EventAPI:
    def __init__(self, base_url: str, timeout: float = 600.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                base_url=self._base_url,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            )
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None
```

## 错误处理

### 异常捕获与日志

避免静默捕获异常，至少记录日志：

```python
# ❌ 错误：静默捕获
except Exception:
    pass

# ✅ 正确：使用 contextlib.suppress（预期异常）
from contextlib import suppress
with suppress(asyncio.CancelledError):
    await listener_task

# ✅ 正确：记录异常（非预期异常）
import logging
logger = logging.getLogger(__name__)
except Exception as e:
    logger.debug("事件监听异常: %s", e)
```

## 测试规范

### 集成测试端口隔离

每个测试使用不同端口避免冲突：

```python
class TestAsyncClientE2E:
    async def test_connect(self):
        config = ClientConfig(server_port=4097)  # 唯一端口

    async def test_ask(self):
        config = ClientConfig(server_port=4098)  # 不同端口
```

### 条件跳过

使用 `pytest.mark.skipif` 处理依赖缺失：

```python
import shutil

OPENCODE_INSTALLED = shutil.which("opencode") is not None
e2e_skip = pytest.mark.skipif(
    not OPENCODE_INSTALLED,
    reason="未安装 opencode 命令",
)
```
