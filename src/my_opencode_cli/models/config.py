"""配置相关数据模型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import OpenCodeModel


class ProviderConfig(OpenCodeModel):
    """LLM 提供商配置。"""

    api_key: str | None = None
    base_url: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ToolConfig(OpenCodeModel):
    """工具配置。"""

    enabled: bool = True
    permission: Literal["allow", "ask", "deny"] = "allow"


class AgentConfig(OpenCodeModel):
    """代理配置。"""

    description: str | None = None
    model: str | None = None
    prompt: str | None = None
    tools: dict[str, bool | ToolConfig] = Field(default_factory=dict)


class OpenCodeConfig(OpenCodeModel):
    """OpenCode 配置文件模型。"""

    model: str | None = None
    small_model: str | None = None
    theme: str | None = None
    autoupdate: bool = True
    provider: dict[str, ProviderConfig] = Field(default_factory=dict)
    tools: dict[str, bool | ToolConfig] = Field(default_factory=dict)
    agent: dict[str, AgentConfig] = Field(default_factory=dict)
    command: dict[str, Any] = Field(default_factory=dict)
    permission: dict[str, Literal["allow", "ask", "deny"]] = Field(default_factory=dict)
