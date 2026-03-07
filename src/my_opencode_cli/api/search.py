"""搜索 API。"""

from __future__ import annotations

from typing import Any, Literal

from ..models.file import FileInfo, Symbol
from .client import APIClient


class SearchAPI(APIClient):
    """搜索 API。

    根据 OpenCode API 文档：
    - GET /find?pattern=<pat> - 搜索文本
    - GET /find/file?query=<q> - 按名称查找文件
    - GET /find/symbol?query=<q> - 查找工作区符号
    """

    async def text(
        self,
        pattern: str,
        *,
        path: str | None = None,
        case_sensitive: bool = False,
    ) -> list[FileInfo]:
        """搜索文件内容（文本搜索）。

        Args:
            pattern: 搜索模式（正则表达式）
            path: 搜索起始路径（可选）
            case_sensitive: 是否区分大小写

        Returns:
            匹配的文件信息列表，包含 path, lines, line_number, absolute_offset, submatches
        """
        params: dict[str, Any] = {"pattern": pattern}
        if path is not None:
            params["path"] = path
        if case_sensitive:
            params["caseSensitive"] = "true"

        data: list[dict[str, Any]] = await self._get("/find", params=params)
        return [FileInfo.model_validate(item) for item in data]

    async def files(
        self,
        query: str,
        *,
        type: Literal["file", "directory"] | None = None,
        directory: str | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """按名称查找文件和目录。

        Args:
            query: 搜索字符串（模糊匹配）
            type: 限制结果类型，"file" 或 "directory"
            directory: 覆盖项目根目录进行搜索
            limit: 最大结果数（1-200）

        Returns:
            匹配的文件路径列表
        """
        params: dict[str, Any] = {"query": query}
        if type is not None:
            params["type"] = type
        if directory is not None:
            params["directory"] = directory
        if limit is not None:
            params["limit"] = str(limit)

        data: list[str] = await self._get("/find/file", params=params)
        return data

    async def symbols(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[Symbol]:
        """查找工作区符号。

        Args:
            query: 搜索字符串
            limit: 最大结果数

        Returns:
            匹配的符号列表
        """
        params: dict[str, Any] = {"query": query}
        if limit is not None:
            params["limit"] = str(limit)

        data: list[dict[str, Any]] = await self._get("/find/symbol", params=params)
        return [Symbol.model_validate(item) for item in data]
