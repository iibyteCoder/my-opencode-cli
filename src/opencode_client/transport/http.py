"""HTTP 传输实现。"""

from __future__ import annotations

import builtins
import json
from collections.abc import AsyncIterator
from typing import Any, Self

import aiohttp

from ..core.errors import APIError, ConnectionError, TimeoutError
from .base import Transport


class HTTPTransport(Transport):
    """基于 aiohttp 的 HTTP 传输实现。"""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 600.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        """初始化 HTTP 传输。

        Args:
            base_url: 服务器基础 URL
            timeout: 请求超时时间（秒）
            headers: 默认请求头
        """
        self._base_url: str = base_url.rstrip("/")
        self._timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=timeout)
        self._default_headers: dict[str, str] = headers or {}
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """确保 HTTP 会话已创建。

        Returns:
            aiohttp 客户端会话
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers=self._default_headers,
            )
        return self._session

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """发送 HTTP 请求。

        Args:
            method: HTTP 方法
            path: API 路径
            json: JSON 请求体
            params: URL 查询参数
            headers: 额外的请求头

        Returns:
            JSON 响应数据

        Raises:
            APIError: API 错误
            ConnectionError: 连接错误
            TimeoutError: 超时错误
        """
        session = await self._ensure_session()
        url = f"{self._base_url}{path}"

        try:
            async with session.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
            ) as response:
                if response.status >= 400:
                    error_body = await response.text()
                    raise APIError(
                        f"HTTP {response.status}: {error_body}",
                        status_code=response.status,
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"连接错误: {e}") from e
        except builtins.TimeoutError as e:
            raise TimeoutError(f"请求超时: {e}") from e

    async def stream(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """发送 SSE 流式请求。

        Args:
            method: HTTP 方法
            path: API 路径
            json: JSON 请求体
            headers: 额外的请求头

        Yields:
            SSE 事件数据字典

        Raises:
            APIError: API 错误
            ConnectionError: 连接错误
        """
        session = await self._ensure_session()
        url = f"{self._base_url}{path}"

        request_headers = headers or {}
        request_headers["Accept"] = "text/event-stream"

        try:
            async with session.request(
                method,
                url,
                json=json,
                headers=request_headers,
            ) as response:
                if response.status >= 400:
                    error_body = await response.text()
                    raise APIError(
                        f"HTTP {response.status}: {error_body}",
                        status_code=response.status,
                    )
                async for event in self._parse_sse(response):
                    yield event
        except aiohttp.ClientError as e:
            raise ConnectionError(f"连接错误: {e}") from e

    async def _parse_sse(
        self,
        response: aiohttp.ClientResponse,
    ) -> AsyncIterator[dict[str, Any]]:
        """解析 SSE 流。

        SSE 格式:
            event: <event_type>
            data: <json_data>

        或者:
            data: <json_data>

        Args:
            response: aiohttp 响应对象

        Yields:
            解析后的事件数据字典
        """
        event_type: str = ""
        data_buffer: list[str] = []

        async for line_bytes in response.content:
            line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")

            if not line:
                # 空行表示事件结束
                if data_buffer:
                    data_str = "\n".join(data_buffer)
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        data = {"raw": data_str}

                    if event_type:
                        data["event"] = event_type

                    yield data

                    event_type = ""
                    data_buffer = []
                continue

            if line.startswith(":"):
                # 注释行，忽略
                continue

            if ":" in line:
                field, value = line.split(":", 1)
                field = field.strip()
                value = value.lstrip()

                if field == "event":
                    event_type = value
                elif field == "data":
                    data_buffer.append(value)
                elif field == "id":
                    # 事件 ID，暂时忽略
                    pass
                elif field == "retry":
                    # 重试时间，暂时忽略
                    pass

    async def close(self) -> None:
        """关闭 HTTP 会话。"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> Self:
        """异步上下文管理器入口。"""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """异步上下文管理器出口。"""
        await self.close()
