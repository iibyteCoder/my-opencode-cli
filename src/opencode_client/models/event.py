"""SSE 事件相关数据模型。"""

from __future__ import annotations

from typing import Annotated, Any, Generic, Literal, TypeAlias, TypeVar

from pydantic import Discriminator, Field

from .base import OpenCodeModel

# 事件类型字面量
EventTypeLiteral = Literal["text", "tool_use", "tool_result", "error", "done"]
T = TypeVar("T", bound=EventTypeLiteral)


class SSEEvent(OpenCodeModel, Generic[T]):
    """SSE 事件基类。"""

    type: T = Field(..., description="事件类型")
    data: dict[str, Any] = Field(default_factory=dict, description="事件数据")


class TextEvent(SSEEvent[Literal["text"]]):
    """文本事件。"""

    type: Literal["text"] = "text"
    text: str = ""


class ToolUseEvent(SSEEvent[Literal["tool_use"]]):
    """工具调用事件。"""

    type: Literal["tool_use"] = "tool_use"
    tool: str = Field(..., description="工具名称")
    input: dict[str, Any] = Field(default_factory=dict, description="工具输入")


class ToolResultEvent(SSEEvent[Literal["tool_result"]]):
    """工具结果事件。"""

    type: Literal["tool_result"] = "tool_result"
    tool: str = Field(..., description="工具名称")
    output: Any = Field(..., description="工具输出")


class ErrorEvent(SSEEvent[Literal["error"]]):
    """错误事件。"""

    type: Literal["error"] = "error"
    message: str = Field(..., description="错误消息")
    code: str | None = Field(default=None, description="错误代码")


class DoneEvent(SSEEvent[Literal["done"]]):
    """完成事件。"""

    type: Literal["done"] = "done"


# 所有事件类型的联合（使用 Discriminator 实现自动反序列化）
EventType: TypeAlias = Annotated[
    TextEvent | ToolUseEvent | ToolResultEvent | ErrorEvent | DoneEvent,
    Discriminator("type"),
]
