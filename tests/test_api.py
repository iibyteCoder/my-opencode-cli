"""API 层测试。"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from my_opencode_cli.api.agent import AgentAPI
from my_opencode_cli.api.file import FileAPI
from my_opencode_cli.api.message import MessageAPI
from my_opencode_cli.api.project import ProjectAPI
from my_opencode_cli.api.search import SearchAPI
from my_opencode_cli.api.session import SessionAPI
from my_opencode_cli.models.session import Session, SessionCreate, SessionUpdate
from my_opencode_cli.transport.http import HTTPTransport


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_transport() -> MagicMock:
    """创建模拟传输层。"""
    transport = MagicMock(spec=HTTPTransport)
    transport.request = AsyncMock()
    transport.close = AsyncMock()
    return transport


# =============================================================================
# SessionAPI 测试
# =============================================================================


class TestSessionAPI:
    """测试 SessionAPI。"""

    @pytest.mark.asyncio
    async def test_list_all(self, mock_transport: MagicMock) -> None:
        """测试列出所有会话。"""
        mock_transport.request.return_value = [
            {"id": "session-1", "title": "Session 1"},
            {"id": "session-2", "title": "Session 2"},
        ]

        api = SessionAPI(mock_transport)
        sessions = await api.list_all()

        assert len(sessions) == 2
        assert all(isinstance(s, Session) for s in sessions)
        mock_transport.request.assert_called_once_with(
            "GET", "/session", params=None, headers=None
        )

    @pytest.mark.asyncio
    async def test_create_with_request(self, mock_transport: MagicMock) -> None:
        """测试带请求体创建会话。"""
        mock_transport.request.return_value = {
            "id": "new-session",
            "title": "New Session",
        }

        api = SessionAPI(mock_transport)
        request = SessionCreate(title="New Session", parent_id="parent-1")
        session = await api.create(request)

        assert isinstance(session, Session)
        assert session.id == "new-session"
        mock_transport.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_without_request(self, mock_transport: MagicMock) -> None:
        """测试不带请求体创建会话。"""
        mock_transport.request.return_value = {"id": "new-session"}

        api = SessionAPI(mock_transport)
        session = await api.create()

        assert isinstance(session, Session)
        mock_transport.request.assert_called_once_with(
            "POST", "/session", json={}, headers=None
        )

    @pytest.mark.asyncio
    async def test_get(self, mock_transport: MagicMock) -> None:
        """测试获取会话。"""
        mock_transport.request.return_value = {
            "id": "session-1",
            "title": "Test Session",
        }

        api = SessionAPI(mock_transport)
        session = await api.get("session-1")

        assert session.id == "session-1"
        mock_transport.request.assert_called_once_with(
            "GET", "/session/session-1", params=None, headers=None
        )

    @pytest.mark.asyncio
    async def test_update(self, mock_transport: MagicMock) -> None:
        """测试更新会话。"""
        mock_transport.request.return_value = {
            "id": "session-1",
            "title": "Updated Title",
        }

        api = SessionAPI(mock_transport)
        request = SessionUpdate(title="Updated Title")
        session = await api.update("session-1", request)

        assert session.title == "Updated Title"
        mock_transport.request.assert_called_once_with(
            "PATCH", "/session/session-1", json={"title": "Updated Title"}, headers=None
        )

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_transport: MagicMock) -> None:
        """测试删除会话成功。"""
        mock_transport.request.return_value = None

        api = SessionAPI(mock_transport)
        result = await api.delete("session-1")

        assert result is True
        mock_transport.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_failure(self, mock_transport: MagicMock) -> None:
        """测试删除会话失败。"""
        mock_transport.request.side_effect = Exception("Not found")

        api = SessionAPI(mock_transport)
        result = await api.delete("session-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_true(self, mock_transport: MagicMock) -> None:
        """测试会话存在。"""
        mock_transport.request.return_value = {"id": "session-1"}

        api = SessionAPI(mock_transport)
        result = await api.exists("session-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, mock_transport: MagicMock) -> None:
        """测试会话不存在。"""
        mock_transport.request.side_effect = Exception("Not found")

        api = SessionAPI(mock_transport)
        result = await api.exists("non-existent")

        assert result is False

    @pytest.mark.asyncio
    async def test_children(self, mock_transport: MagicMock) -> None:
        """测试获取子会话。"""
        mock_transport.request.return_value = [
            {"id": "child-1", "parentID": "session-1"},
            {"id": "child-2", "parentID": "session-1"},
        ]

        api = SessionAPI(mock_transport)
        children = await api.children("session-1")

        assert len(children) == 2
        mock_transport.request.assert_called_once_with(
            "GET", "/session/session-1/children", params=None, headers=None
        )

    @pytest.mark.asyncio
    async def test_abort(self, mock_transport: MagicMock) -> None:
        """测试中止会话。"""
        mock_transport.request.return_value = None

        api = SessionAPI(mock_transport)
        result = await api.abort("session-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_fork(self, mock_transport: MagicMock) -> None:
        """测试派生会话。"""
        mock_transport.request.return_value = {
            "id": "forked-session",
            "parentID": "session-1",
        }

        api = SessionAPI(mock_transport)
        session = await api.fork("session-1", message_id="msg-1")

        assert session.parent_id == "session-1"
        mock_transport.request.assert_called_once_with(
            "POST", "/session/session-1/fork", json={"messageID": "msg-1"}, headers=None
        )

    @pytest.mark.asyncio
    async def test_fork_without_message(self, mock_transport: MagicMock) -> None:
        """测试不带消息 ID 的派生。"""
        mock_transport.request.return_value = {"id": "forked-session"}

        api = SessionAPI(mock_transport)
        session = await api.fork("session-1")

        mock_transport.request.assert_called_once_with(
            "POST", "/session/session-1/fork", json={}, headers=None
        )

    @pytest.mark.asyncio
    async def test_share(self, mock_transport: MagicMock) -> None:
        """测试分享会话。"""
        mock_transport.request.return_value = {
            "id": "session-1",
        }

        api = SessionAPI(mock_transport)
        session = await api.share("session-1")

        assert session.id == "session-1"
        mock_transport.request.assert_called_once_with(
            "POST", "/session/session-1/share", json=None, headers=None
        )

    @pytest.mark.asyncio
    async def test_unshare(self, mock_transport: MagicMock) -> None:
        """测试取消分享。"""
        mock_transport.request.return_value = {
            "id": "session-1",
        }

        api = SessionAPI(mock_transport)
        session = await api.unshare("session-1")

        assert session.id == "session-1"
        mock_transport.request.assert_called_once_with(
            "DELETE", "/session/session-1/share", headers=None
        )


# =============================================================================
# MessageAPI 测试
# =============================================================================


def make_message_response(texts: list[str]) -> dict[str, Any]:
    """创建模拟的消息响应。"""
    parts = [{"type": "text", "text": text} for text in texts]
    return {
        "info": {"id": "msg-1", "sessionID": "session-1", "role": "assistant"},
        "parts": parts,
    }


class TestMessageAPI:
    """测试 MessageAPI。"""

    @pytest.mark.asyncio
    async def test_list_messages(self, mock_transport: MagicMock) -> None:
        """测试列出消息。"""
        mock_transport.request.return_value = [
            {"info": {"id": "msg-1"}, "parts": []},
            {"info": {"id": "msg-2"}, "parts": []},
        ]

        api = MessageAPI(mock_transport)
        messages = await api.list_messages("session-1")

        assert len(messages) == 2
        mock_transport.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_messages_with_limit(self, mock_transport: MagicMock) -> None:
        """测试带限制列出消息。"""
        mock_transport.request.return_value = [
            {"info": {"id": "msg-1"}, "parts": []},
        ]

        api = MessageAPI(mock_transport)
        messages = await api.list_messages("session-1", limit=1)

        assert len(messages) == 1
        # 验证 params 被正确传递
        call_args = mock_transport.request.call_args
        assert call_args[1]["params"] == {"limit": "1"}

    @pytest.mark.asyncio
    async def test_send_text_message(self, mock_transport: MagicMock) -> None:
        """测试发送文本消息。"""
        mock_transport.request.return_value = make_message_response(["Hello"])

        api = MessageAPI(mock_transport)
        response = await api.send("session-1", "Hello")

        assert response["info"]["id"] == "msg-1"
        assert len(response["parts"]) == 1
        assert response["parts"][0]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_send_with_model_string(self, mock_transport: MagicMock) -> None:
        """测试带模型字符串发送消息。"""
        captured_json: dict[str, Any] = {}

        async def mock_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
            nonlocal captured_json
            captured_json = kwargs.get("json", {})
            return make_message_response(["OK"])

        mock_transport.request = mock_request

        api = MessageAPI(mock_transport)
        await api.send("session-1", "Hello", model="anthropic/claude-3")

        # 验证请求体中的 model 格式
        assert captured_json["model"] == {"providerID": "anthropic", "modelID": "claude-3"}

    @pytest.mark.asyncio
    async def test_send_with_model_dict(self, mock_transport: MagicMock) -> None:
        """测试带模型字典发送消息。"""
        captured_json: dict[str, Any] = {}

        async def mock_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
            nonlocal captured_json
            captured_json = kwargs.get("json", {})
            return make_message_response(["OK"])

        mock_transport.request = mock_request

        api = MessageAPI(mock_transport)
        await api.send(
            "session-1",
            "Hello",
            model={"providerID": "openai", "modelID": "gpt-4"},
        )

        assert captured_json["model"] == {"providerID": "openai", "modelID": "gpt-4"}

    @pytest.mark.asyncio
    async def test_send_with_agent(self, mock_transport: MagicMock) -> None:
        """测试带代理发送消息。"""
        captured_json: dict[str, Any] = {}

        async def mock_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
            nonlocal captured_json
            captured_json = kwargs.get("json", {})
            return make_message_response(["OK"])

        mock_transport.request = mock_request

        api = MessageAPI(mock_transport)
        await api.send("session-1", "Hello", agent="code-assistant")

        assert captured_json["agent"] == "code-assistant"

    @pytest.mark.asyncio
    async def test_send_async(self, mock_transport: MagicMock) -> None:
        """测试异步发送消息。"""
        mock_transport.request.return_value = None

        api = MessageAPI(mock_transport)
        result = await api.send_async("session-1", "Hello")

        assert result is True
        mock_transport.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message(self, mock_transport: MagicMock) -> None:
        """测试获取消息详情。"""
        mock_transport.request.return_value = {
            "info": {"id": "msg-1"},
            "parts": [{"type": "text", "text": "Hello"}],
        }

        api = MessageAPI(mock_transport)
        message = await api.get("session-1", "msg-1")

        assert message["info"]["id"] == "msg-1"
        mock_transport.request.assert_called_once_with(
            "GET", "/session/session-1/message/msg-1", params=None, headers=None
        )

    @pytest.mark.asyncio
    async def test_command(self, mock_transport: MagicMock) -> None:
        """测试执行命令。"""
        captured_json: dict[str, Any] = {}

        async def mock_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
            nonlocal captured_json
            captured_json = kwargs.get("json", {})
            return {
                "info": {"id": "msg-1"},
                "parts": [{"type": "text", "text": "Command result"}],
            }

        mock_transport.request = mock_request

        api = MessageAPI(mock_transport)
        result = await api.command("session-1", "help", arguments={"topic": "usage"})

        assert result["info"]["id"] == "msg-1"
        assert captured_json["command"] == "help"
        assert captured_json["arguments"] == {"topic": "usage"}

    @pytest.mark.asyncio
    async def test_shell(self, mock_transport: MagicMock) -> None:
        """测试运行 shell 命令。"""
        captured_json: dict[str, Any] = {}

        async def mock_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
            nonlocal captured_json
            captured_json = kwargs.get("json", {})
            return {
                "info": {"id": "msg-1"},
                "parts": [{"type": "text", "text": "ls output"}],
            }

        mock_transport.request = mock_request

        api = MessageAPI(mock_transport)
        result = await api.shell("session-1", "ls -la")

        assert captured_json["command"] == "ls -la"


# =============================================================================
# FileAPI 测试
# =============================================================================


class TestFileAPI:
    """测试 FileAPI。"""

    @pytest.mark.asyncio
    async def test_list_all(self, mock_transport: MagicMock) -> None:
        """测试列出文件。"""
        mock_transport.request.return_value = [
            {"name": "main.py", "type": "file", "path": "/src/main.py"},
            {"name": "utils.py", "type": "file", "path": "/src/utils.py"},
        ]

        api = FileAPI(mock_transport)
        files = await api.list_all("/src")

        assert len(files) == 2
        mock_transport.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_read(self, mock_transport: MagicMock) -> None:
        """测试读取文件。"""
        mock_transport.request.return_value = {
            "type": "raw",
            "content": "print('hello')",
        }

        api = FileAPI(mock_transport)
        content = await api.read("/src/main.py")

        assert content.content == "print('hello')"

    @pytest.mark.asyncio
    async def test_status(self, mock_transport: MagicMock) -> None:
        """测试获取文件状态。"""
        mock_transport.request.return_value = [
            {"path": "/src/main.py", "staged": "M", "unstaged": None, "untracked": False},
        ]

        api = FileAPI(mock_transport)
        status = await api.status()

        assert len(status) == 1
        assert status[0].path == "/src/main.py"

    @pytest.mark.asyncio
    async def test_search(self, mock_transport: MagicMock) -> None:
        """测试搜索文件内容。"""
        mock_transport.request.return_value = [
            {"path": "/src/main.py", "lines": "def hello", "line": 10, "absolute_offset": 200, "submatches": []},
        ]

        api = FileAPI(mock_transport)
        results = await api.search("def hello")

        assert len(results) == 1
        assert results[0].path == "/src/main.py"


# =============================================================================
# ProjectAPI 测试
# =============================================================================


class TestProjectAPI:
    """测试 ProjectAPI。"""

    @pytest.mark.asyncio
    async def test_current(self, mock_transport: MagicMock) -> None:
        """测试获取当前项目信息。"""
        mock_transport.request.return_value = {
            "name": "my-project",
            "path": "/home/user/project",
        }

        api = ProjectAPI(mock_transport)
        info = await api.current()

        assert info["name"] == "my-project"

    @pytest.mark.asyncio
    async def test_root(self, mock_transport: MagicMock) -> None:
        """测试获取项目根目录。"""
        mock_transport.request.return_value = {"root": "/home/user/project"}

        api = ProjectAPI(mock_transport)
        root = await api.root()

        assert root == "/home/user/project"


# =============================================================================
# AgentAPI 测试
# =============================================================================


class TestAgentAPI:
    """测试 AgentAPI。"""

    @pytest.mark.asyncio
    async def test_list(self, mock_transport: MagicMock) -> None:
        """测试列出代理。"""
        mock_transport.request.return_value = [
            {"name": "code-assistant", "model": "claude-3"},
            {"name": "data-analyst", "model": "gpt-4"},
        ]

        api = AgentAPI(mock_transport)
        agents = await api.list()

        assert len(agents) == 2
        assert agents[0].id == "code-assistant"  # id 是 name 的别名
        assert agents[0].name == "code-assistant"


# =============================================================================
# SearchAPI 测试
# =============================================================================


class TestSearchAPI:
    """测试 SearchAPI。"""

    @pytest.mark.asyncio
    async def test_text(self, mock_transport: MagicMock) -> None:
        """测试文本搜索。"""
        mock_transport.request.return_value = [
            {"path": "/src/main.py", "lines": "hello world", "line": 10, "absolute_offset": 200, "submatches": []},
        ]

        api = SearchAPI(mock_transport)
        results = await api.text("hello")

        assert len(results) == 1
        assert results[0].path == "/src/main.py"

    @pytest.mark.asyncio
    async def test_files(self, mock_transport: MagicMock) -> None:
        """测试文件名搜索。"""
        mock_transport.request.return_value = ["/src/main.py", "/src/utils.py"]

        api = SearchAPI(mock_transport)
        results = await api.files("main")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_symbols(self, mock_transport: MagicMock) -> None:
        """测试符号搜索。"""
        mock_transport.request.return_value = [
            {"name": "hello", "kind": "function", "path": "/src/main.py"},
        ]

        api = SearchAPI(mock_transport)
        results = await api.symbols("hello")

        assert len(results) == 1
        assert results[0].name == "hello"
        assert results[0].path == "/src/main.py"
