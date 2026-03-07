"""事件订阅 API。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import nullcontext
from typing import TYPE_CHECKING, Any

from ..core.errors import APIError
from ..models.event import Event, parse_event

if TYPE_CHECKING:
    import aiohttp


class EventAPI:
    """事件订阅 API。

    提供服务器事件订阅功能。OpenCode 服务器通过 /event 端点
    返回 Server-Sent Events (SSE) 流。

    事件格式:
        data: {"type": "<event_type>", "properties": {...}}

    事件类型:
        - server.connected: 服务器连接
        - message.updated: 消息更新
        - message.part.updated: 消息部分更新（包含文本内容）
        - session.status: 会话状态（busy/idle）
        - session.updated: 会话更新
        - session.diff: 会话差异
    """

    def __init__(self, base_url: str, timeout: float = 600.0) -> None:
        """初始化事件 API。

        Args:
            base_url: 服务器基础 URL
            timeout: 请求超时时间（秒）
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """确保 HTTP 会话已创建。"""
        import aiohttp

        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """关闭 HTTP 会话。"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def subscribe(self) -> AsyncIterator[Event]:
        """订阅服务器事件流。

        Yields:
            事件对象
        """

        session = await self._ensure_session()
        url = f"{self._base_url}/event"
        headers = {"Accept": "text/event-stream"}

        async with session.get(url, headers=headers) as response:
            if response.status >= 400:
                error_body = await response.text()
                raise APIError(
                    f"HTTP {response.status}: {error_body}",
                    status_code=response.status,
                )

            # 解析 SSE 流
            buffer = ""
            async for chunk in response.content:
                buffer += chunk.decode("utf-8", errors="replace")

                # 处理缓冲区中的完整事件（以双换行分隔）
                while "\n\n" in buffer:
                    event_text, buffer = buffer.split("\n\n", 1)
                    event_data = self._parse_sse_event(event_text)
                    if event_data:
                        yield parse_event(event_data)

    def _parse_sse_event(self, event_text: str) -> dict[str, Any] | None:
        """解析单个 SSE 事件。

        Args:
            event_text: 事件文本

        Returns:
            解析后的事件数据，如果解析失败返回 None
        """
        lines = event_text.strip().split("\n")
        data_lines: list[str] = []

        for line in lines:
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
            elif line.startswith(":"):
                # 注释行，忽略
                continue

        if data_lines:
            data_str = "\n".join(data_lines)
            try:
                data: dict[str, Any] = json.loads(data_str)
                return data
            except json.JSONDecodeError:
                return {"raw": data_str, "type": "raw"}

        return None

    async def wait_for(
        self,
        event_type: str,
        *,
        timeout: float | None = None,
    ) -> Event | None:
        """等待特定类型的事件。

        Args:
            event_type: 要等待的事件类型
            timeout: 超时时间（秒）

        Returns:
            匹配的事件，如果超时则返回 None
        """
        import asyncio

        cm = asyncio.timeout(timeout) if timeout else nullcontext()
        try:
            async with cm:
                async for event in self.subscribe():
                    if event.type == event_type:
                        return event
        except TimeoutError:
            pass
        return None

    async def subscribe_to_session(
        self,
        session_id: str,
    ) -> AsyncIterator[Event]:
        """订阅特定会话的事件。

        Args:
            session_id: 会话 ID

        Yields:
            与该会话相关的事件
        """
        async for event in self.subscribe():
            # 过滤与该会话相关的事件
            if self._is_event_for_session(event, session_id):
                yield event

    def _is_event_for_session(self, event: Event, session_id: str) -> bool:
        """检查事件是否属于指定会话。"""
        # 使用 getattr 安全访问属性
        properties = getattr(event, "properties", None)
        if properties is None:
            return False

        # 检查 session_id 属性
        if getattr(properties, "session_id", None) == session_id:
            return True

        # 检查 part.session_id
        part = getattr(properties, "part", None)
        if part is not None and getattr(part, "session_id", None) == session_id:
            return True

        # 检查 info 字典或对象
        info = getattr(properties, "info", None)
        if info is not None:
            if isinstance(info, dict):
                if info.get("sessionID") == session_id or info.get("id") == session_id:
                    return True
            elif getattr(info, "session_id", None) == session_id:
                return True

        return False
