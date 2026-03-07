"""会话相关数据模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import OpenCodeModel


class SessionCreate(OpenCodeModel):
    """创建会话请求。

    根据 OpenCode API 文档，创建会话只支持以下参数：
    - parentID: 父会话 ID（可选）
    - title: 会话标题（可选）
    """

    parent_id: str | None = Field(default=None, alias="parentID")
    title: str | None = None

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}


class SessionUpdate(OpenCodeModel):
    """更新会话请求。"""

    title: str | None = None


class SessionStatus(OpenCodeModel):
    """会话状态。"""

    status: str = Field(default="idle", description="会话状态")


class SessionTime(OpenCodeModel):
    """会话时间信息。"""

    created: int | None = Field(default=None, description="创建时间戳（毫秒）")
    updated: int | None = Field(default=None, description="更新时间戳（毫秒）")


class Session(OpenCodeModel):
    """会话信息。"""

    id: str = Field(..., description="会话 ID")
    title: str | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    parent_id: str | None = Field(default=None, alias="parentID")
    message_count: int = Field(default=0, ge=0, alias="messageCount")

    # 额外字段（OpenCode API 返回）
    slug: str | None = Field(default=None, description="会话 slug")
    version: str | None = Field(default=None, description="版本号")
    project_id: str | None = Field(default=None, alias="projectID", description="项目 ID")
    directory: str | None = Field(default=None, description="工作目录")
    time: SessionTime | dict[str, Any] | None = Field(default=None, description="时间信息")

    model_config = OpenCodeModel.model_config | {
        "populate_by_name": True,
        "extra": "allow",
    }
