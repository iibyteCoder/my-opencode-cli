"""消息相关数据模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypeAlias

from pydantic import Field

from .base import OpenCodeModel


class TextPart(OpenCodeModel):
    """文本消息部分。"""

    model_config = OpenCodeModel.model_config | {"extra": "allow"}

    type: Literal["text"] = "text"
    text: str


class ImagePart(OpenCodeModel):
    """图片消息部分。"""

    type: Literal["image"] = "image"
    source: str  # base64 或 URL
    media_type: str


class FilePart(OpenCodeModel):
    """文件附件。"""

    type: Literal["file"] = "file"
    path: str


# 消息部分的联合类型
MessagePart: TypeAlias = TextPart | ImagePart | FilePart


class MessageContent(OpenCodeModel):
    """消息内容（多个部分）。"""

    parts: list[MessagePart]

    @classmethod
    def from_text(cls, text: str) -> MessageContent:
        """从文本创建消息内容。

        Args:
            text: 文本内容

        Returns:
            MessageContent 实例
        """
        return cls(parts=[TextPart(text=text)])


class ModelRef(OpenCodeModel):
    """模型引用。

    用于指定要使用的模型，包含提供商 ID 和模型 ID。
    """

    provider_id: str = Field(..., alias="providerID")
    model_id: str = Field(..., alias="modelID")

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}


class MessageSend(OpenCodeModel):
    """发送消息请求。

    根据 OpenCode API 文档：
    - messageID: 可选的消息 ID
    - model: 可选的模型引用 { providerID, modelID }
    - agent: 可选的代理名称字符串
    - noReply: 是否不触发 AI 响应（用于注入上下文）
    - system: 可选的系统提示
    - tools: 可选的工具配置
    - parts: 消息部分列表
    """

    message_id: str | None = Field(default=None, alias="messageID")
    model: ModelRef | str | None = None
    agent: str | None = None
    no_reply: bool = Field(default=False, alias="noReply")
    system: str | None = None
    tools: dict[str, Any] | None = None
    parts: list[dict[str, Any]] = Field(default_factory=list)

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}


class Message(OpenCodeModel):
    """消息信息。"""

    id: str = Field(..., description="消息 ID")
    role: str = Field(..., description="消息角色")
    created_at: datetime | None = Field(default=None, alias="createdAt")

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}
