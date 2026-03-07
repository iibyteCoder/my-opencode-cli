"""传输层测试。

使用 pytest-aiohttp 的 aiohttp_server fixture 进行 HTTP 传输测试。
"""

from __future__ import annotations

from typing import Any

import pytest
from aiohttp import web

from my_opencode_cli.core.errors import APIError, ConnectionError
from my_opencode_cli.transport.http import HTTPTransport


# =============================================================================
# Test Server Handlers
# =============================================================================


async def json_handler(request: web.Request) -> web.Response:
    """返回 JSON 响应。"""
    path = request.path

    if path == "/api/test":
        return web.json_response({"success": True, "data": "hello"})
    elif path == "/api/echo":
        data = await request.json()
        return web.json_response({"echo": data})
    elif path == "/api/error":
        return web.json_response({"error": "Not found"}, status=404)
    elif path == "/api/empty":
        return web.json_response({})
    elif path == "/api/large":
        return web.json_response({"items": list(range(1000))})
    elif path == "/api/unicode":
        return web.json_response({
            "chinese": "中文测试",
            "emoji": "🎉",
        })
    elif path == "/api/query":
        return web.json_response({"query": dict(request.query)})

    return web.json_response({"path": path}, status=404)


async def sse_handler(request: web.Request) -> web.StreamResponse:
    """SSE 流式响应。"""
    path = request.path

    response = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
        },
    )
    await response.prepare(request)

    if path == "/api/sse":
        events = [
            "event: text\ndata: {\"type\": \"text\", \"text\": \"Hello\"}\n\n",
            "event: text\ndata: {\"type\": \"text\", \"text\": \"World\"}\n\n",
            "event: done\ndata: {\"type\": \"done\"}\n\n",
        ]
        for event in events:
            await response.write(event.encode("utf-8"))
    elif path == "/api/sse_data_only":
        events = [
            "data: {\"message\": \"test1\"}\n\n",
            "data: {\"message\": \"test2\"}\n\n",
        ]
        for event in events:
            await response.write(event.encode("utf-8"))
    elif path == "/api/sse_multiline":
        await response.write(b"data: line1\ndata: line2\ndata: line3\n\n")
    elif path == "/api/sse_comments":
        await response.write(b": this is a comment\ndata: {\"value\": 1}\n\n")

    return response


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def server(aiohttp_server: Any) -> Any:
    """创建测试服务器。"""
    app = web.Application()
    # JSON 端点
    app.router.add_route("*", "/api/test", json_handler)
    app.router.add_route("*", "/api/echo", json_handler)
    app.router.add_route("*", "/api/error", json_handler)
    app.router.add_route("*", "/api/empty", json_handler)
    app.router.add_route("*", "/api/large", json_handler)
    app.router.add_route("*", "/api/unicode", json_handler)
    app.router.add_route("*", "/api/query", json_handler)
    # SSE 端点
    app.router.add_route("*", "/api/sse", sse_handler)
    app.router.add_route("*", "/api/sse_data_only", sse_handler)
    app.router.add_route("*", "/api/sse_multiline", sse_handler)
    app.router.add_route("*", "/api/sse_comments", sse_handler)
    return await aiohttp_server(app)


# =============================================================================
# HTTPTransport Tests
# =============================================================================


class TestHTTPTransport:
    """测试 HTTPTransport。"""

    @pytest.mark.asyncio
    async def test_get_request(self, server: Any) -> None:
        """测试 GET 请求。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            result = await transport.request("GET", "/test")
            assert result == {"success": True, "data": "hello"}

    @pytest.mark.asyncio
    async def test_post_request(self, server: Any) -> None:
        """测试 POST 请求。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            result = await transport.request(
                "POST",
                "/echo",
                json={"name": "test"},
            )
            assert result == {"echo": {"name": "test"}}

    @pytest.mark.asyncio
    async def test_error_response(self, server: Any) -> None:
        """测试错误响应。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            with pytest.raises(APIError) as exc_info:
                await transport.request("GET", "/error")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_connection_error(self) -> None:
        """测试连接错误。"""
        async with HTTPTransport("http://localhost:1") as transport:
            with pytest.raises(ConnectionError):
                await transport.request("GET", "/test")

    @pytest.mark.asyncio
    async def test_sse_stream(self, server: Any) -> None:
        """测试 SSE 流。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            events = []
            async for event in transport.stream("GET", "/sse"):
                events.append(event)

            assert len(events) == 3
            assert events[0]["type"] == "text"
            assert events[0]["text"] == "Hello"
            assert events[1]["type"] == "text"
            assert events[1]["text"] == "World"
            assert events[2]["type"] == "done"

    @pytest.mark.asyncio
    async def test_sse_stream_with_event_type(self, server: Any) -> None:
        """测试带 event 字段的 SSE 流。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            events = []
            async for event in transport.stream("GET", "/sse"):
                events.append(event)

            # 验证 event 字段被正确解析
            assert events[0].get("event") == "text"
            assert events[1].get("event") == "text"
            assert events[2].get("event") == "done"

    @pytest.mark.asyncio
    async def test_sse_data_only(self, server: Any) -> None:
        """测试只有 data 字段的 SSE。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            events = []
            async for event in transport.stream("GET", "/sse_data_only"):
                events.append(event)

            assert len(events) == 2
            assert events[0]["message"] == "test1"
            assert events[1]["message"] == "test2"

    @pytest.mark.asyncio
    async def test_context_manager(self, server: Any) -> None:
        """测试上下文管理器。"""
        base_url = str(server.make_url("/api"))
        async with HTTPTransport(base_url) as transport:
            # 会话是延迟创建的，需要先发起请求
            result = await transport.request("GET", "/test")
            assert result["success"]
            # 现在会话应该存在
            assert transport._session is not None

        # 退出上下文后会话应已关闭
        assert transport._session is None

    @pytest.mark.asyncio
    async def test_close(self, server: Any) -> None:
        """测试手动关闭。"""
        transport = HTTPTransport(str(server.make_url("/api")))
        await transport._ensure_session()
        assert transport._session is not None

        await transport.close()
        assert transport._session is None

    @pytest.mark.asyncio
    async def test_base_url_trailing_slash(self, server: Any) -> None:
        """测试 base_url 尾部斜杠处理。"""
        base_url = str(server.make_url("/api/"))  # 带尾部斜杠
        async with HTTPTransport(base_url) as transport:
            assert transport._base_url == base_url.rstrip("/")

    @pytest.mark.asyncio
    async def test_custom_timeout(self, server: Any) -> None:
        """测试自定义超时。"""
        async with HTTPTransport(
            str(server.make_url("/api")),
            timeout=30.0,
        ) as transport:
            assert transport._timeout.total == 30.0

    @pytest.mark.asyncio
    async def test_custom_headers(self, server: Any) -> None:
        """测试自定义请求头。"""
        async with HTTPTransport(
            str(server.make_url("/api")),
            headers={"X-Custom": "value"},
        ) as transport:
            assert transport._default_headers == {"X-Custom": "value"}

    @pytest.mark.asyncio
    async def test_stream_with_json_body(self, server: Any) -> None:
        """测试带 JSON body 的流式请求。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            events = []
            async for event in transport.stream(
                "POST",
                "/sse",
                json={"prompt": "test"},
            ):
                events.append(event)

            assert len(events) == 3

    @pytest.mark.asyncio
    async def test_stream_error_response(self, server: Any) -> None:
        """测试流式请求的错误响应。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            with pytest.raises(APIError) as exc_info:
                async for _ in transport.stream("GET", "/error"):
                    pass
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_reuse_session(self, server: Any) -> None:
        """测试会话重用。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            # 第一次请求
            await transport.request("GET", "/test")
            session1 = transport._session

            # 第二次请求应该重用同一会话
            await transport.request("GET", "/test")
            session2 = transport._session

            assert session1 is session2


class TestHTTPTransportEdgeCases:
    """测试边界情况。"""

    @pytest.mark.asyncio
    async def test_empty_response(self, server: Any) -> None:
        """测试空响应。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            result = await transport.request("GET", "/empty")
            assert result == {}

    @pytest.mark.asyncio
    async def test_large_json_response(self, server: Any) -> None:
        """测试大型 JSON 响应。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            result = await transport.request("GET", "/large")
            assert len(result["items"]) == 1000

    @pytest.mark.asyncio
    async def test_unicode_in_response(self, server: Any) -> None:
        """测试 Unicode 响应。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            result = await transport.request("GET", "/unicode")
            assert result["chinese"] == "中文测试"
            assert result["emoji"] == "🎉"

    @pytest.mark.asyncio
    async def test_sse_multiline_data(self, server: Any) -> None:
        """测试多行 data 的 SSE。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            events = []
            async for event in transport.stream("GET", "/sse_multiline"):
                events.append(event)

            # 多行 data 应该被合并
            assert len(events) == 1
            # 不是有效 JSON，所以应该返回 raw
            assert "raw" in events[0]
            assert "line1" in events[0]["raw"]

    @pytest.mark.asyncio
    async def test_sse_with_comments(self, server: Any) -> None:
        """测试带注释的 SSE。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            events = []
            async for event in transport.stream("GET", "/sse_comments"):
                events.append(event)

            assert len(events) == 1
            assert events[0] == {"value": 1}

    @pytest.mark.asyncio
    async def test_params_encoding(self, server: Any) -> None:
        """测试 URL 参数编码。"""
        async with HTTPTransport(str(server.make_url("/api"))) as transport:
            result = await transport.request(
                "GET",
                "/query",
                params={"key": "value with spaces", "num": "123"},
            )
            assert result["query"]["key"] == "value with spaces"
            assert result["query"]["num"] == "123"
