"""SSE 流处理工具。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import aiohttp


class SSEParser:
    """SSE (Server-Sent Events) 解析器。

    解析 SSE 流格式：
        event: <event_type>
        data: <json_data>

    或者：
        data: <json_data>
    """

    async def parse(
        self,
        response: aiohttp.ClientResponse,
    ) -> AsyncIterator[dict[str, Any]]:
        """解析 SSE 响应流。

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
                    event_data = self._parse_data(data_str)

                    if event_type:
                        event_data["event"] = event_type

                    yield event_data

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
                    # 事件 ID
                    pass
                elif field == "retry":
                    # 重试时间
                    pass

    def _parse_data(self, data_str: str) -> dict[str, Any]:
        """解析 data 字段内容。

        Args:
            data_str: data 字段的原始字符串

        Returns:
            解析后的字典
        """
        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            return {"raw": data_str}


async def parse_sse_stream(
    response: aiohttp.ClientResponse,
) -> AsyncIterator[dict[str, Any]]:
    """便捷函数：解析 SSE 流。

    Args:
        response: aiohttp 响应对象

    Yields:
        解析后的事件数据字典
    """
    parser = SSEParser()
    async for event in parser.parse(response):
        yield event
