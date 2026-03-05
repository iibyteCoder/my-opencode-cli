"""工具调用相关数据模型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import OpenCodeModel


class ToolCall(OpenCodeModel):
    """工具调用。"""

    tool: str = Field(..., description="工具名称")
    input: dict[str, Any] = Field(default_factory=dict, description="工具输入参数")


class ToolResult(OpenCodeModel):
    """工具结果。"""

    tool: str = Field(..., description="工具名称")
    output: Any = Field(..., description="工具输出")
    success: bool = Field(default=True, description="是否成功")
    error: str | None = Field(default=None, description="错误信息")


class ToolInfo(OpenCodeModel):
    """工具信息。"""

    name: str = Field(..., description="工具名称")
    description: str | None = Field(default=None, description="工具描述")
    parameters: dict[str, Any] | None = Field(default=None, description="工具参数 schema")
    enabled: bool = Field(default=True, description="是否启用")
    permission: Literal["allow", "ask", "deny"] = Field(default="allow", description="权限设置")
