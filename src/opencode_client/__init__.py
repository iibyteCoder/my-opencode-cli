"""OpenCode Client - 通用的 OpenCode 服务器客户端库。

提供与 OpenCode 服务器交互的 Python 客户端，支持：
- 服务器模式启动和管理
- 会话创建和消息发送
- SSE 流式响应处理
- 事件解析

示例用法:
    from opencode_client import OpenCodeClient, ServerConfig

    async with OpenCodeClient(ServerConfig(port=4096)) as client:
        session_id = await client.create_session("测试会话")
        response = await client.send_message(session_id, "你好")
        print(response)
"""

from __future__ import annotations

from .config import ServerConfig
from .exceptions import OpenCodeError, ServerStartError, SessionError
from .parser import EventParser, ParsedResult, StructuredData
from .client import OpenCodeClient

__all__ = [
    "OpenCodeClient",
    "ServerConfig",
    "OpenCodeError",
    "ServerStartError",
    "SessionError",
    "EventParser",
    "ParsedResult",
    "StructuredData",
]

__version__ = "0.1.0"
