"""传输层抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Self


class Transport(ABC):
    """传输层抽象基类。

    定义了与 OpenCode 服务器通信的通用接口。
    """

    @abstractmethod
    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """发送 HTTP 请求并返回 JSON 响应。

        Args:
            method: HTTP 方法（GET, POST, DELETE 等）
            path: API 路径
            json: JSON 请求体
            params: URL 查询参数
            headers: 额外的请求头

        Returns:
            JSON 响应数据

        Raises:
            APIError: API 调用失败
            ConnectionError: 连接失败
            TimeoutError: 请求超时
        """
        ...

    @abstractmethod
    def stream(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """发送 SSE 流式请求，返回事件迭代器。

        Args:
            method: HTTP 方法
            path: API 路径
            json: JSON 请求体
            headers: 额外的请求头

        Yields:
            SSE 事件数据字典

        Raises:
            APIError: API 调用失败
            ConnectionError: 连接失败
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """关闭连接并释放资源。"""
        ...

    async def __aenter__(self) -> Self:
        """异步上下文管理器入口。"""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """异步上下文管理器出口。"""
        await self.close()
