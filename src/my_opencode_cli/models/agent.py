"""代理相关数据模型。

根据 OpenCode API 文档，代理只能通过配置文件创建，
API 只提供列表功能（GET /agent）。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import OpenCodeModel


class AgentInfo(OpenCodeModel):
    """代理信息。

    代理是配置的 AI 助手，可以通过 Tab 键切换或 @ 提及调用。
    """

    model_config = OpenCodeModel.model_config | {"extra": "allow"}

    name: str = Field(..., description="代理名称")
    description: str | None = Field(default=None, description="代理描述")
    mode: Literal["primary", "subagent", "all"] | None = Field(default=None, description="代理模式")
    model: dict[str, Any] | str | None = Field(default=None, description="使用的模型")
    prompt: str | None = Field(default=None, description="代理系统提示")
    disabled: bool = Field(default=False, description="是否禁用")
    hidden: bool = Field(default=False, description="是否隐藏（仅对 subagent）")

    @property
    def id(self) -> str:
        """代理 ID（使用名称作为 ID）。"""
        return self.name
