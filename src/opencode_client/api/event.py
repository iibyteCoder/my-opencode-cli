"""事件订阅 API。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..models.event import SSEEvent
from .client import APIClient


class EventAPI(APIClient):
    """事件订阅 API。

    提供服务器事件订阅功能。
    """

    async def subscribe(
        self,
        *,
        event_types: list[str] | None = None,
    ) -> AsyncIterator[SSEEvent]:
        """订阅服务器事件。

        Args:
            event_types: 要订阅的事件类型列表（可选，            默认订阅所有事件

        Yields:
            SSE 事件对象
        """
        async for event_data in self._stream("/events"):
            yield SSEEvent.model_validate(event_data)

    async def wait_for(
        self,
        event_type: str,
    ) -> SSEEvent | None:
        """等待特定类型的事件。

        Args:
            event_type: 要等待的事件类型

        Returns:
            匹配的事件，如果没有匹配则返回 None
        """
        async for event in self.subscribe():
            if event.type == event_type:
                return event
        return None
