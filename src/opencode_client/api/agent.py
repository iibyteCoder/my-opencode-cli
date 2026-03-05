"""代理管理 API。

根据 OpenCode API 文档，Agent API 只有列表功能。
代理是通过配置文件创建的，不是通过 API 创建。
"""

from __future__ import annotations

from typing import Any

from ..models.agent import AgentInfo
from .client import APIClient


class AgentAPI(APIClient):
    """代理管理 API。

    提供代理列表查询功能。

    注意：代理是通过配置文件（opencode.json 或 .opencode/agents/）创建的，
    不是通过 API 创建。此 API 只提供只读的列表功能。
    """

    async def list(self) -> list[AgentInfo]:
        """列出所有可用的代理。

        Returns:
            代理列表
        """
        data: list[dict[str, Any]] = await self._get("/agent")
        return [AgentInfo.model_validate(item) for item in data]
