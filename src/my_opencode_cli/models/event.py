"""OpenCode 服务器事件模型。

事件格式：
    {"type": "<event_type>", "properties": {...}}
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypeAlias

from pydantic import Discriminator, Field

from .base import OpenCodeModel

# =============================================================================
# 事件属性模型
# =============================================================================


class MessageInfo(OpenCodeModel):
    """消息信息。"""

    model_config = OpenCodeModel.model_config | {
        "populate_by_name": True,
        "extra": "allow",  # 允许额外字段
    }

    id: str = Field(..., description="消息 ID")
    session_id: str = Field(..., alias="sessionID", description="会话 ID")
    role: str = Field(..., description="角色 (user/assistant)")
    time: dict[str, Any] | None = Field(default=None, description="时间信息")
    parent_id: str | None = Field(default=None, alias="parentID", description="父消息 ID")
    model_id: str | None = Field(default=None, alias="modelID", description="模型 ID")
    provider_id: str | None = Field(default=None, alias="providerID", description="提供商 ID")
    model: dict[str, Any] | str | None = Field(default=None, description="模型信息")
    mode: str | None = Field(default=None, description="模式")
    agent: str | None = Field(default=None, description="代理")
    path: dict[str, Any] | None = Field(default=None, description="路径信息")
    cost: float | None = Field(default=None, description="成本")
    tokens: dict[str, Any] | None = Field(default=None, description="Token 信息")
    finish: str | None = Field(default=None, description="完成原因")


class EventMessagePart(OpenCodeModel):
    """SSE 事件中的消息部分。"""

    model_config = OpenCodeModel.model_config | {
        "populate_by_name": True,
        "extra": "allow",  # 允许额外字段（如 snapshot）
    }

    id: str = Field(..., description="部分 ID")
    session_id: str = Field(..., alias="sessionID", description="会话 ID")
    message_id: str = Field(..., alias="messageID", description="消息 ID")
    type: str = Field(..., description="部分类型")
    text: str | None = Field(default=None, description="文本内容")
    time: dict[str, Any] | None = Field(default=None, description="时间信息")


class SessionStatusInfo(OpenCodeModel):
    """会话状态信息。"""

    session_id: str = Field(..., alias="sessionID", description="会话 ID")
    status: dict[str, Any] = Field(..., description="状态信息")

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}


# =============================================================================
# 事件属性容器
# =============================================================================


class ServerConnectedProperties(OpenCodeModel):
    """server.connected 事件属性。"""

    pass  # 空属性


class MessageUpdatedProperties(OpenCodeModel):
    """message.updated 事件属性。"""

    info: MessageInfo = Field(..., description="消息信息")


class MessagePartUpdatedProperties(OpenCodeModel):
    """message.part.updated 事件属性。"""

    part: EventMessagePart = Field(..., description="消息部分")


class MessagePartDeltaProperties(OpenCodeModel):
    """message.part.delta 事件属性。"""

    model_config = OpenCodeModel.model_config | {
        "populate_by_name": True,
        "extra": "allow",
    }

    delta: dict[str, Any] | str | None = Field(default=None, description="增量内容")
    part: EventMessagePart | None = Field(default=None, description="消息部分")


class SessionStatusProperties(OpenCodeModel):
    """session.status 事件属性。"""

    session_id: str = Field(..., alias="sessionID", description="会话 ID")
    status: dict[str, Any] = Field(..., description="状态")

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}


class SessionInfo(OpenCodeModel):
    """会话信息。"""

    model_config = OpenCodeModel.model_config | {"extra": "allow"}

    id: str | None = Field(default=None, description="会话 ID")
    title: str | None = Field(default=None, description="会话标题")
    parent_id: str | None = Field(default=None, alias="parentID", description="父会话 ID")


class SessionUpdatedProperties(OpenCodeModel):
    """session.updated 事件属性。"""

    info: SessionInfo = Field(..., description="会话信息")


class SessionDiffProperties(OpenCodeModel):
    """session.diff 事件属性。"""

    session_id: str = Field(..., alias="sessionID", description="会话 ID")
    diff: list[Any] = Field(default_factory=list, description="差异列表")

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}


# =============================================================================
# 事件类型
# =============================================================================


class ServerConnectedEvent(OpenCodeModel):
    """服务器连接事件。"""

    type: Literal["server.connected"] = "server.connected"
    properties: ServerConnectedProperties = Field(
        default_factory=ServerConnectedProperties,
        description="事件属性",
    )


class MessageUpdatedEvent(OpenCodeModel):
    """消息更新事件。"""

    type: Literal["message.updated"] = "message.updated"
    properties: MessageUpdatedProperties = Field(..., description="事件属性")


class MessagePartUpdatedEvent(OpenCodeModel):
    """消息部分更新事件。"""

    type: Literal["message.part.updated"] = "message.part.updated"
    properties: MessagePartUpdatedProperties = Field(..., description="事件属性")


class MessagePartDeltaEvent(OpenCodeModel):
    """消息部分增量事件。"""

    type: Literal["message.part.delta"] = "message.part.delta"
    properties: MessagePartDeltaProperties = Field(..., description="事件属性")


class SessionStatusEvent(OpenCodeModel):
    """会话状态事件。"""

    type: Literal["session.status"] = "session.status"
    properties: SessionStatusProperties = Field(..., description="事件属性")


class SessionUpdatedEvent(OpenCodeModel):
    """会话更新事件。"""

    type: Literal["session.updated"] = "session.updated"
    properties: SessionUpdatedProperties = Field(..., description="事件属性")


class SessionDiffEvent(OpenCodeModel):
    """会话差异事件。"""

    type: Literal["session.diff"] = "session.diff"
    properties: SessionDiffProperties = Field(..., description="事件属性")


# =============================================================================
# 通用事件基类和联合类型
# =============================================================================


class OpenCodeEvent(OpenCodeModel):
    """OpenCode 事件基类。

    使用宽松模式允许解析未知事件类型。
    """

    type: str = Field(..., description="事件类型")
    properties: dict[str, Any] = Field(default_factory=dict, description="事件属性")


# 已知事件类型的联合
KnownEvent: TypeAlias = (
    ServerConnectedEvent
    | MessageUpdatedEvent
    | MessagePartUpdatedEvent
    | MessagePartDeltaEvent
    | SessionStatusEvent
    | SessionUpdatedEvent
    | SessionDiffEvent
)

# 完整的事件类型（包含未知事件），使用 Discriminator 实现自动反序列化
Event: TypeAlias = Annotated[
    KnownEvent | OpenCodeEvent,
    Discriminator("type"),
]


# =============================================================================
# 便捷方法
# =============================================================================


def parse_event(data: dict[str, Any]) -> Event:
    """解析事件数据。

    Args:
        data: 原始事件数据

    Returns:
        解析后的事件对象
    """
    event_type = data.get("type", "")

    # 使用 match 语句分发到对应的事件类
    match event_type:
        case "server.connected":
            return ServerConnectedEvent.model_validate(data)
        case "message.updated":
            return MessageUpdatedEvent.model_validate(data)
        case "message.part.updated":
            return MessagePartUpdatedEvent.model_validate(data)
        case "message.part.delta":
            return MessagePartDeltaEvent.model_validate(data)
        case "session.status":
            return SessionStatusEvent.model_validate(data)
        case "session.updated":
            return SessionUpdatedEvent.model_validate(data)
        case "session.diff":
            return SessionDiffEvent.model_validate(data)
        case _:
            # 未知事件类型，使用通用类
            return OpenCodeEvent.model_validate(data)


def is_event_for_session(event: Event, session_id: str) -> bool:
    """检查事件是否属于指定会话。

    Args:
        event: 事件对象
        session_id: 会话 ID

    Returns:
        是否属于该会话
    """
    match event:
        case SessionStatusEvent(properties=p):
            return p.session_id == session_id
        case SessionDiffEvent(properties=p):
            return p.session_id == session_id
        case MessagePartUpdatedEvent(properties=p):
            return p.part.session_id == session_id
        case MessagePartDeltaEvent():
            # delta 事件无法确定会话，默认返回 True
            return True
        case MessageUpdatedEvent(properties=p):
            return p.info.session_id == session_id
        case SessionUpdatedEvent(properties=p):
            return p.info.id == session_id
        case _:
            return False


# =============================================================================
# 兼容旧 API 的类型别名（将在后续版本移除）
# =============================================================================

# 旧的事件类型别名（用于向后兼容）
EventTypeLiteral = Literal["text", "tool_use", "tool_result", "error", "done"]

SSEEventBase = OpenCodeEvent


class TextEvent(OpenCodeModel):
    """文本事件（兼容旧 API）。"""

    type: Literal["text"] = "text"
    text: str = ""


class DoneEvent(OpenCodeModel):
    """完成事件（兼容旧 API）。"""

    type: Literal["done"] = "done"


class ToolUseEvent(OpenCodeModel):
    """工具调用事件（兼容旧 API）。"""

    type: Literal["tool_use"] = "tool_use"
    tool: str = Field(..., description="工具名称")
    input: dict[str, Any] = Field(default_factory=dict, description="工具输入")


class ToolResultEvent(OpenCodeModel):
    """工具结果事件（兼容旧 API）。"""

    type: Literal["tool_result"] = "tool_result"
    tool: str = Field(..., description="工具名称")
    output: Any = Field(..., description="工具输出")


class ErrorEvent(OpenCodeModel):
    """错误事件（兼容旧 API）。"""

    type: Literal["error"] = "error"
    message: str = Field(..., description="错误消息")
    code: str | None = Field(default=None, description="错误代码")


# 旧的事件类型别名
EventType: TypeAlias = Event
