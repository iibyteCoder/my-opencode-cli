"""OpenCode Python Client.

一个用于与 OpenCode 服务器交互的 Python 客户端库。

Example:
    from opencode_client import AsyncOpenCode

    async with AsyncOpenCode(base_url="http://localhost:4096") as client:
        answer = await client.ask("什么是 Python 装饰器？")
        print(answer)

    # 或者使用同步客户端
    from opencode_client import OpenCode

    with OpenCode(base_url="http://localhost:4096") as client:
        answer = client.ask("什么是闭包？")
        print(answer)
"""

from __future__ import annotations

# 客户端
from .client import AsyncOpenCode, OpenCode

# 配置
from .core.config import ClientConfig

# 核心异常
from .core.errors import (
    APIError,
    ConnectionError,
    MessageError,
    OpenCodeError,
    ParseError,
    ServerStartError,
    SessionError,
    TimeoutError,
    ValidationError,
)

# 数据模型
from .models import (
    AgentConfig,
    DoneEvent,
    ErrorEvent,
    EventType,
    FileContent,
    FileInfo,
    FilePart,
    ImagePart,
    MessageContent,
    MessagePart,
    MessageSend,
    OpenCodeConfig,
    OpenCodeModel,
    ProviderConfig,
    Session,
    SessionCreate,
    SSEEvent,
    TextEvent,
    TextPart,
    ToolConfig,
    ToolResultEvent,
    ToolUseEvent,
)

__version__ = "0.2.0"

__all__ = [
    # 版本
    "__version__",
    # 异常
    "OpenCodeError",
    "ConnectionError",
    "ServerStartError",
    "SessionError",
    "MessageError",
    "APIError",
    "ParseError",
    "TimeoutError",
    "ValidationError",
    # 配置
    "ClientConfig",
    # 模型
    "OpenCodeModel",
    "Session",
    "SessionCreate",
    "TextPart",
    "ImagePart",
    "FilePart",
    "MessagePart",
    "MessageContent",
    "MessageSend",
    "SSEEvent",
    "TextEvent",
    "ToolUseEvent",
    "ToolResultEvent",
    "ErrorEvent",
    "DoneEvent",
    "EventType",
    "FileInfo",
    "FileContent",
    "ProviderConfig",
    "ToolConfig",
    "AgentConfig",
    "OpenCodeConfig",
    # 客户端
    "AsyncOpenCode",
    "OpenCode",
]
