"""基础 API 客户端。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ..transport.base import Transport


class APIClient:
    """低层 API 客户端基类。

    提供与 OpenCode API 交互的基础方法。
    """

    def __init__(self, transport: Transport) -> None:
        """初始化 API 客户端。

        Args:
            transport: 传输层实例
        """
        self._transport: Transport = transport

    async def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """发送 GET 请求。"""
        str_params: dict[str, str] | None = None
        if params:
            str_params = {k: str(v) for k, v in params.items()}
        return await self._transport.request("GET", path, params=str_params, headers=headers)

    async def _post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """发送 POST 请求。"""
        return await self._transport.request("POST", path, json=json, headers=headers)

    async def _patch(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """发送 PATCH 请求。"""
        return await self._transport.request("PATCH", path, json=json, headers=headers)

    async def _delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """发送 DELETE 请求。"""
        return await self._transport.request("DELETE", path, headers=headers)

    async def _stream(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """发送流式请求。"""
        async for event in self._transport.stream("POST", path, json=json, headers=headers):
            yield event
