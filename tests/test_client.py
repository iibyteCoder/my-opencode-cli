"""高层客户端测试。"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from my_opencode_cli.client.async_client import AsyncOpenCode
from my_opencode_cli.client.sync_client import OpenCode
from my_opencode_cli.core.config import ClientConfig
from my_opencode_cli.core.errors import ConnectionError
from my_opencode_cli.models.event import TextEvent, DoneEvent
from my_opencode_cli.models.session import Session


# =============================================================================
# AsyncOpenCode 测试
# =============================================================================


class TestAsyncOpenCode:
    """测试 AsyncOpenCode 异步客户端。"""

    def test_init_with_base_url(self) -> None:
        """测试带 base_url 初始化。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        assert client._base_url == "http://localhost:4096"
        assert client._start_server is False

    def test_init_with_start_server(self) -> None:
        """测试带 start_server 初始化。"""
        client = AsyncOpenCode(start_server=True)
        assert client._start_server is True
        assert client._base_url is None

    def test_init_with_config(self) -> None:
        """测试带配置初始化。"""
        config = ClientConfig(server_port=8080)
        client = AsyncOpenCode(config=config)
        assert client._config is config

    def test_is_connected_initially_false(self) -> None:
        """测试初始未连接状态。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_with_base_url(self) -> None:
        """测试带 base_url 连接。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        result = await client.connect()

        assert result is client  # 返回自身支持链式调用
        assert client.is_connected is True
        assert client._transport is not None
        assert client._session_api is not None

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_connect_without_base_url_raises(self) -> None:
        """测试无 base_url 连接抛出异常。"""
        client = AsyncOpenCode()
        with pytest.raises(ConnectionError) as exc_info:
            await client.connect()
        assert "base_url" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """测试断开连接。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        await client.connect()
        assert client.is_connected is True

        await client.disconnect()
        assert client.is_connected is False
        assert client._transport is None
        assert client._session_api is None

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """测试异步上下文管理器。"""
        async with AsyncOpenCode(base_url="http://localhost:4096") as client:
            assert client.is_connected is True

        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_session_property_before_connect(self) -> None:
        """测试连接前访问 session 属性。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        with pytest.raises(ConnectionError):
            _ = client.session

    @pytest.mark.asyncio
    async def test_message_property_before_connect(self) -> None:
        """测试连接前访问 message 属性。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        with pytest.raises(ConnectionError):
            _ = client.message

    @pytest.mark.asyncio
    async def test_file_property_before_connect(self) -> None:
        """测试连接前访问 file 属性。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        with pytest.raises(ConnectionError):
            _ = client.file

    @pytest.mark.asyncio
    async def test_project_property_before_connect(self) -> None:
        """测试连接前访问 project 属性。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        with pytest.raises(ConnectionError):
            _ = client.project

    @pytest.mark.asyncio
    async def test_agent_property_before_connect(self) -> None:
        """测试连接前访问 agent 属性。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        with pytest.raises(ConnectionError):
            _ = client.agent

    @pytest.mark.asyncio
    async def test_api_properties_after_connect(self) -> None:
        """测试连接后访问所有 API 属性。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")
        await client.connect()

        assert client.session is not None
        assert client.message is not None
        assert client.file is not None
        assert client.project is not None
        assert client.agent is not None
        assert client.search is not None

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_create_session(self) -> None:
        """测试创建会话。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        with patch.object(client, "_session_api") as mock_session_api:
            mock_session_api.create = AsyncMock(
                return_value=Session(id="test-session", title="Test")
            )
            client._transport = MagicMock()  # 标记为已连接

            session = await client.create_session(title="Test")

            assert session.id == "test-session"
            assert session.title == "Test"
            mock_session_api.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_ask_new_session(self) -> None:
        """测试快速提问（新会话）。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        # Mock session API
        mock_session_api = MagicMock()
        mock_session_api.create = AsyncMock(
            return_value=Session(id="new-session")
        )
        mock_session_api.delete = AsyncMock()

        # Mock message API
        mock_message_api = MagicMock()
        mock_message_api.send = AsyncMock(
            return_value=[
                TextEvent(text="Hello, AI!"),
                DoneEvent(),
            ]
        )

        client._session_api = mock_session_api
        client._message_api = mock_message_api
        client._transport = MagicMock()

        answer = await client.ask("Hello")

        assert answer == "Hello, AI!"
        mock_session_api.create.assert_called_once()
        mock_message_api.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_ask_existing_session(self) -> None:
        """测试快速提问（复用会话）。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        mock_message_api = MagicMock()
        mock_message_api.send = AsyncMock(
            return_value=[
                TextEvent(text="Response"),
                DoneEvent(),
            ]
        )

        client._message_api = mock_message_api
        client._transport = MagicMock()

        answer = await client.ask("Hello", session_id="existing-session")

        assert answer == "Response"
        mock_message_api.send.assert_called_once()
        # 验证使用现有会话，不创建新会话
        call_args = mock_message_api.send.call_args
        assert call_args[0][0] == "existing-session"

    @pytest.mark.asyncio
    async def test_ask_with_model(self) -> None:
        """测试带模型的快速提问。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        mock_session_api = MagicMock()
        mock_session_api.create = AsyncMock(return_value=Session(id="session-1"))
        mock_session_api.delete = AsyncMock()

        mock_message_api = MagicMock()
        mock_message_api.send = AsyncMock(return_value=[TextEvent(text="OK")])

        client._session_api = mock_session_api
        client._message_api = mock_message_api
        client._transport = MagicMock()

        await client.ask("Hello", model="anthropic/claude-3")

        call_args = mock_message_api.send.call_args
        assert call_args[1]["model"] == "anthropic/claude-3"

    @pytest.mark.asyncio
    async def test_ask_with_agent(self) -> None:
        """测试带代理的快速提问。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        mock_session_api = MagicMock()
        mock_session_api.create = AsyncMock(return_value=Session(id="session-1"))
        mock_session_api.delete = AsyncMock()

        mock_message_api = MagicMock()
        mock_message_api.send = AsyncMock(return_value=[TextEvent(text="OK")])

        client._session_api = mock_session_api
        client._message_api = mock_message_api
        client._transport = MagicMock()

        await client.ask("Hello", agent="code-assistant")

        call_args = mock_message_api.send.call_args
        assert call_args[1]["agent"] == "code-assistant"

    @pytest.mark.asyncio
    async def test_ask_stream(self) -> None:
        """测试流式提问。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        async def mock_stream(*args: Any, **kwargs: Any) -> Any:
            yield TextEvent(text="Hello")
            yield TextEvent(text=" World")
            yield DoneEvent()

        mock_session_api = MagicMock()
        mock_session_api.create = AsyncMock(return_value=Session(id="session-1"))
        mock_session_api.delete = AsyncMock()

        mock_message_api = MagicMock()
        mock_message_api.stream = mock_stream

        client._session_api = mock_session_api
        client._message_api = mock_message_api
        client._transport = MagicMock()

        events = []
        async for event in client.ask_stream("Hello"):
            events.append(event)

        assert len(events) == 3
        assert isinstance(events[0], TextEvent)
        assert events[0].text == "Hello"

    @pytest.mark.asyncio
    async def test_cleanup_sessions_enabled(self) -> None:
        """测试会话自动清理（启用）。"""
        config = ClientConfig(cleanup_sessions=True)
        client = AsyncOpenCode(base_url="http://localhost:4096", config=config)

        mock_session_api = MagicMock()
        mock_session_api.create = AsyncMock(return_value=Session(id="session-1"))
        mock_session_api.delete = AsyncMock()

        mock_message_api = MagicMock()
        mock_message_api.send = AsyncMock(return_value=[TextEvent(text="OK")])

        client._session_api = mock_session_api
        client._message_api = mock_message_api
        client._transport = MagicMock()

        await client.ask("Hello")

        # 会话应该被清理
        mock_session_api.delete.assert_called_once_with("session-1")

    @pytest.mark.asyncio
    async def test_cleanup_sessions_disabled(self) -> None:
        """测试会话自动清理（禁用）。"""
        config = ClientConfig(cleanup_sessions=False)
        client = AsyncOpenCode(base_url="http://localhost:4096", config=config)

        mock_session_api = MagicMock()
        mock_session_api.create = AsyncMock(return_value=Session(id="session-1"))
        mock_session_api.delete = AsyncMock()

        mock_message_api = MagicMock()
        mock_message_api.send = AsyncMock(return_value=[TextEvent(text="OK")])

        client._session_api = mock_session_api
        client._message_api = mock_message_api
        client._transport = MagicMock()

        await client.ask("Hello")

        # 会话不应该被清理
        mock_session_api.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_text(self) -> None:
        """测试文本提取。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        events = [
            TextEvent(text="Line 1"),
            TextEvent(text="Line 2"),
            DoneEvent(),
        ]

        text = client._extract_text(events)
        assert text == "Line 1\nLine 2"

    @pytest.mark.asyncio
    async def test_extract_text_empty(self) -> None:
        """测试空事件列表的文本提取。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        text = client._extract_text([])
        assert text == ""

    @pytest.mark.asyncio
    async def test_extract_text_only_text_events(self) -> None:
        """测试只提取 TextEvent。"""
        client = AsyncOpenCode(base_url="http://localhost:4096")

        events: list[Any] = [
            TextEvent(text="Hello"),
            DoneEvent(),
            TextEvent(text="World"),
        ]

        text = client._extract_text(events)
        assert text == "Hello\nWorld"


# =============================================================================
# OpenCode (同步客户端) 测试
# =============================================================================


class TestOpenCode:
    """测试 OpenCode 同步客户端。"""

    def test_init_with_base_url(self) -> None:
        """测试带 base_url 初始化。"""
        client = OpenCode(base_url="http://localhost:4096")
        assert client._async_client._base_url == "http://localhost:4096"

    def test_init_with_config(self) -> None:
        """测试带配置初始化。"""
        config = ClientConfig(server_port=8080)
        client = OpenCode(config=config)
        assert client._async_client._config is config

    def test_is_connected_delegates_to_async(self) -> None:
        """测试 is_connected 属性委托给异步客户端。"""
        client = OpenCode(base_url="http://localhost:4096")
        assert client.is_connected == client._async_client.is_connected

    def test_connect(self) -> None:
        """测试同步连接。"""
        client = OpenCode(base_url="http://localhost:4096")
        result = client.connect()

        assert result is client
        assert client.is_connected is True

        client.disconnect()

    def test_disconnect(self) -> None:
        """测试同步断开连接。"""
        client = OpenCode(base_url="http://localhost:4096")
        client.connect()
        assert client.is_connected is True

        client.disconnect()
        assert client.is_connected is False

    def test_context_manager(self) -> None:
        """测试同步上下文管理器。"""
        with OpenCode(base_url="http://localhost:4096") as client:
            assert client.is_connected is True

        assert client.is_connected is False

    def test_context_manager_exception_handling(self) -> None:
        """测试上下文管理器异常处理。"""
        client = OpenCode(base_url="http://localhost:4096")
        try:
            with client:
                raise ValueError("Test error")
        except ValueError:
            pass

        # 即使有异常，也应该正确断开
        assert client.is_connected is False

    def test_ask(self) -> None:
        """测试同步快速提问。"""
        client = OpenCode(base_url="http://localhost:4096")

        with patch.object(
            client._async_client, "ask", new_callable=AsyncMock
        ) as mock_ask:
            mock_ask.return_value = "AI Response"

            with client:
                answer = client.ask("Hello")

            assert answer == "AI Response"
            mock_ask.assert_called_once()

    def test_ask_with_options(self) -> None:
        """测试带选项的同步快速提问。"""
        client = OpenCode(base_url="http://localhost:4096")

        with patch.object(
            client._async_client, "ask", new_callable=AsyncMock
        ) as mock_ask:
            mock_ask.return_value = "Response"

            with client:
                client.ask(
                    "Hello",
                    model="anthropic/claude-3",
                    agent="assistant",
                    session_id="session-1",
                )

            mock_ask.assert_called_once_with(
                "Hello",
                model="anthropic/claude-3",
                agent="assistant",
                session_id="session-1",
            )

    def test_ask_stream(self) -> None:
        """测试同步流式提问。"""
        client = OpenCode(base_url="http://localhost:4096")

        async def mock_ask_stream(*args: Any, **kwargs: Any) -> Any:
            yield TextEvent(text="Hello")
            yield DoneEvent()

        with patch.object(
            client._async_client, "ask_stream", side_effect=mock_ask_stream
        ):
            with client:
                events = client.ask_stream("Hello")

            assert len(events) == 2
            assert isinstance(events[0], TextEvent)

    def test_create_session(self) -> None:
        """测试同步创建会话。"""
        client = OpenCode(base_url="http://localhost:4096")

        with patch.object(
            client._async_client, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = Session(id="session-1", title="Test")

            with client:
                session = client.create_session("Test", parent_id="parent-1")

            assert session.id == "session-1"
            mock_create.assert_called_once_with("Test", parent_id="parent-1")

    def test_session_property_delegates(self) -> None:
        """测试 session 属性委托。"""
        client = OpenCode(base_url="http://localhost:4096")
        client.connect()
        assert client.session is client._async_client.session
        client.disconnect()

    def test_message_property_delegates(self) -> None:
        """测试 message 属性委托。"""
        client = OpenCode(base_url="http://localhost:4096")
        client.connect()
        assert client.message is client._async_client.message
        client.disconnect()

    def test_file_property_delegates(self) -> None:
        """测试 file 属性委托。"""
        client = OpenCode(base_url="http://localhost:4096")
        client.connect()
        assert client.file is client._async_client.file
        client.disconnect()

    def test_project_property_delegates(self) -> None:
        """测试 project 属性委托。"""
        client = OpenCode(base_url="http://localhost:4096")
        client.connect()
        assert client.project is client._async_client.project
        client.disconnect()

    def test_multiple_operations(self) -> None:
        """测试多次操作。"""
        client = OpenCode(base_url="http://localhost:4096")

        with patch.object(
            client._async_client, "ask", new_callable=AsyncMock
        ) as mock_ask:
            mock_ask.return_value = "Response"

            with client:
                r1 = client.ask("Question 1")
                r2 = client.ask("Question 2")

            assert r1 == "Response"
            assert r2 == "Response"
            assert mock_ask.call_count == 2

    def test_nested_context_managers_not_supported(self) -> None:
        """测试嵌套上下文管理器（不支持）。"""
        client1 = OpenCode(base_url="http://localhost:4096")
        client2 = OpenCode(base_url="http://localhost:4096")

        with client1:
            assert client1.is_connected is True
            with client2:
                assert client2.is_connected is True
            assert client2.is_connected is False
        assert client1.is_connected is False
