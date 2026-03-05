"""文件操作相关数据模型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import OpenCodeModel


class FileNode(OpenCodeModel):
    """文件节点（文件或目录）。

    用于表示目录列表中的文件或目录。
    """

    name: str = Field(..., description="文件或目录名")
    path: str = Field(..., description="相对路径")
    type: Literal["file", "directory"] = Field(..., description="类型")
    size: int | None = Field(default=None, description="文件大小（字节）")
    modified: str | None = Field(default=None, description="修改时间")


class FileContent(OpenCodeModel):
    """文件内容。

    根据 OpenCode API 文档，文件内容返回格式为：
    { type: "raw" | "patch", content: string }
    """

    type: Literal["raw", "patch"] = Field(default="raw", description="内容类型")
    content: str = Field(default="", description="文件内容")


class FileInfo(OpenCodeModel):
    """文件信息（搜索结果）。

    用于文本搜索结果，包含匹配的文件路径和行信息。
    """

    path: str = Field(..., description="文件路径")
    lines: str = Field(default="", description="匹配的行内容")
    line_number: int = Field(default=0, ge=0, alias="line_number")
    absolute_offset: int = Field(default=0, description="绝对偏移量")
    submatches: list[dict[str, Any]] = Field(default_factory=list, description="子匹配")


class FileStatus(OpenCodeModel):
    """文件状态。

    用于表示 Git 跟踪文件的状态。
    """

    path: str = Field(..., description="文件路径")
    staged: str | None = Field(default=None, description="暂存状态")
    unstaged: str | None = Field(default=None, description="未暂存状态")
    untracked: bool = Field(default=False, description="是否未跟踪")


class Symbol(OpenCodeModel):
    """工作区符号。

    用于符号搜索结果。
    """

    name: str = Field(..., description="符号名称")
    kind: str = Field(..., description="符号类型")
    path: str = Field(..., description="所在文件路径")
    line: int = Field(default=0, description="行号")
    container_name: str | None = Field(default=None, alias="containerName", description="容器名称")

    model_config = OpenCodeModel.model_config | {"populate_by_name": True}
