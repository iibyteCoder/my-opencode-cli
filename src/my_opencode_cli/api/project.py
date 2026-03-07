"""项目信息 API。"""

from __future__ import annotations

from typing import Any, cast

from ..models.config import OpenCodeConfig
from .client import APIClient


class ProjectAPI(APIClient):
    """项目信息 API。

    提供项目信息和配置查询功能。
    """

    async def current(self) -> dict[str, Any]:
        """获取当前项目信息。

        Returns:
            项目信息字典
        """
        data: dict[str, Any] = await self._get("/project/current")
        return data

    async def config(self) -> OpenCodeConfig:
        """获取项目配置。

        Returns:
            OpenCode 配置对象
        """
        data: dict[str, Any] = await self._get("/project/config")
        return OpenCodeConfig.model_validate(data)

    async def root(self) -> str:
        """获取项目根目录。

        Returns:
            项目根目录路径
        """
        data = await self._get("/project/root")
        result = cast(dict[str, Any], data)
        root_value: str = result.get("root", "")
        return root_value
