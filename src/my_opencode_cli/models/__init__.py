"""数据模型层。

提供所有 Pydantic 数据模型定义。
"""

from __future__ import annotations

from .agent import AgentInfo
from .base import OpenCodeModel
from .config import AgentConfig, OpenCodeConfig, ProviderConfig, ToolConfig
from .event import (
    # 兼容旧 API 的事件类型
    DoneEvent,
    ErrorEvent,
    # 新的 OpenCode 事件类型
    Event,
    EventMessagePart,
    EventType,
    KnownEvent,
    MessageInfo,
    MessagePartUpdatedEvent,
    MessageUpdatedEvent,
    OpenCodeEvent,
    ServerConnectedEvent,
    SessionDiffEvent,
    SessionStatusEvent,
    SessionStatusInfo,
    SessionUpdatedEvent,
    TextEvent,
    ToolResultEvent,
    ToolUseEvent,
    parse_event,
)
from .file import FileContent, FileInfo
from .message import (
    FilePart,
    ImagePart,
    Message,
    MessageContent,
    MessagePart,
    MessageSend,
    ModelRef,
    TextPart,
)
from .session import Session, SessionCreate
from .tool import ToolCall, ToolInfo, ToolResult

__all__ = [
    # Base
    "OpenCodeModel",
    # Session
    "Session",
    "SessionCreate",
    # Message
    "TextPart",
    "ImagePart",
    "FilePart",
    "MessagePart",
    "MessageContent",
    "MessageSend",
    "Message",
    "ModelRef",
    # Event (新)
    "Event",
    "KnownEvent",
    "MessageInfo",
    "EventMessagePart",
    "MessagePartUpdatedEvent",
    "MessageUpdatedEvent",
    "OpenCodeEvent",
    "ServerConnectedEvent",
    "SessionDiffEvent",
    "SessionStatusEvent",
    "SessionStatusInfo",
    "SessionUpdatedEvent",
    "parse_event",
    # Event (兼容旧 API)
    "TextEvent",
    "ToolUseEvent",
    "ToolResultEvent",
    "ErrorEvent",
    "DoneEvent",
    "EventType",
    # File
    "FileInfo",
    "FileContent",
    # Config
    "ProviderConfig",
    "ToolConfig",
    "AgentConfig",
    "OpenCodeConfig",
    # Agent
    "AgentInfo",
    # Tool
    "ToolCall",
    "ToolResult",
    "ToolInfo",
]
