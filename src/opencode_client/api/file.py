"""文件操作 API。"""

from __future__ import annotations

from typing import Any

from ..models.file import FileContent, FileNode, FileStatus
from .client import APIClient


class FileAPI(APIClient):
    """文件操作 API。

    根据 OpenCode API 文档：
    - GET /file?path=<path> - 列出文件和目录
    - GET /file/content?path=<p> - 读取文件内容
    - GET /file/status - 获取跟踪文件的状态
    """

    async def list(self, path: str) -> list[FileNode]:
        """列出目录内容。

        Args:
            path: 目录路径

        Returns:
            目录中的文件和子目录列表
        """
        data: list[dict[str, Any]] = await self._get("/file", params={"path": path})
        return [FileNode.model_validate(item) for item in data]

    async def read(self, path: str) -> FileContent:
        """读取文件内容。

        Args:
            path: 文件路径

        Returns:
            文件内容
        """
        data: dict[str, Any] = await self._get("/file/content", params={"path": path})
        return FileContent.model_validate(data)

    async def status(self) -> list[FileStatus]:
        """获取跟踪文件的状态。

        Returns:
            文件状态列表
        """
        data: list[dict[str, Any]] = await self._get("/file/status")
        return [FileStatus.model_validate(item) for item in data]
