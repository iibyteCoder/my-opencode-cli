"""数据模型层。

提供所有 Pydantic 数据模型定义。
"""

from __future__ import annotations

from .agent import AgentInfo
from .base import OpenCodeModel
from .config import AgentConfig, OpenCodeConfig, ProviderConfig, ToolConfig
from .event import (
    DoneEvent,
    ErrorEvent,
    EventType,
    SSEEvent,
    TextEvent,
    ToolResultEvent,
    ToolUseEvent,
)
from .file import FileContent, FileInfo
from .message import FilePart, ImagePart, MessageContent, MessagePart, MessageSend, TextPart
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
    # Event
    "SSEEvent",
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
