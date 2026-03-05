"""SSE 事件相关数据模型。"""

from __future__ import annotations

from typing import Any, Literal, TypeAlias

from pydantic import Field

from .base import OpenCodeModel


class SSEEvent(OpenCodeModel):
    """SSE 事件基类。"""

    type: str = Field(..., description="事件类型")
    data: dict[str, Any] = Field(default_factory=dict, description="事件数据")


class TextEvent(SSEEvent):
    """文本事件。"""

    type: Literal["text"] = "text"
    text: str = ""


class ToolUseEvent(SSEEvent):
    """工具调用事件。"""

    type: Literal["tool_use"] = "tool_use"
    tool: str = Field(..., description="工具名称")
    input: dict[str, Any] = Field(default_factory=dict, description="工具输入")


class ToolResultEvent(SSEEvent):
    """工具结果事件。"""

    type: Literal["tool_result"] = "tool_result"
    tool: str = Field(..., description="工具名称")
    output: Any = Field(..., description="工具输出")


class ErrorEvent(SSEEvent):
    """错误事件。"""

    type: Literal["error"] = "error"
    message: str = Field(..., description="错误消息")
    code: str | None = Field(default=None, description="错误代码")


class DoneEvent(SSEEvent):
    """完成事件。"""

    type: Literal["done"] = "done"


# 所有事件类型的联合
EventType: TypeAlias = TextEvent | ToolUseEvent | ToolResultEvent | ErrorEvent | DoneEvent
