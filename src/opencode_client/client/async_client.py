"""异步高层客户端。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Self

from ..api.agent import AgentAPI
from ..api.file import FileAPI
from ..api.message import MessageAPI
from ..api.project import ProjectAPI
from ..api.search import SearchAPI
from ..api.session import SessionAPI
from ..core.config import ClientConfig
from ..core.errors import ConnectionError
from ..models.event import SSEEvent, TextEvent
from ..models.session import Session, SessionCreate
from ..transport.http import HTTPTransport
from ..transport.process import ServerProcess


class AsyncOpenCode:
    """异步高层客户端。

    提供与 OpenCode 服务器交互的便捷接口。

    Example:
        async with AsyncOpenCode(base_url="http://localhost:4096") as client:
            answer = await client.ask("什么是 Python 装饰器？")
            print(answer)

        # 或者自动启动本地服务器
        async with AsyncOpenCode(start_server=True) as client:
            async for event in client.ask_stream("写一个快速排序"):
                print(event)
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        start_server: bool = False,
        config: ClientConfig | None = None,
    ) -> None:
        """初始化异步客户端。

        Args:
            base_url: OpenCode 服务器 URL（如果 start_server=True 则忽略）
            start_server: 是否自动启动本地服务器
            config: 客户端配置
        """
        self._config: ClientConfig = config or ClientConfig()
        self._base_url: str | None = base_url
        self._start_server: bool = start_server
        self._server: ServerProcess | None = None
        self._transport: HTTPTransport | None = None

        # API 实例（延迟初始化）
        self._session_api: SessionAPI | None = None
        self._message_api: MessageAPI | None = None
        self._file_api: FileAPI | None = None
        self._project_api: ProjectAPI | None = None
        self._agent_api: AgentAPI | None = None
        self._search_api: SearchAPI | None = None

    # =========================================================================
    # 属性访问器（惰性初始化）
    # =========================================================================

    @property
    def session(self) -> SessionAPI:
        """获取会话 API。"""
        if self._session_api is None:
            raise ConnectionError("客户端未连接，请先调用 connect()")
        return self._session_api

    @property
    def message(self) -> MessageAPI:
        """获取消息 API。"""
        if self._message_api is None:
            raise ConnectionError("客户端未连接，请先调用 connect()")
        return self._message_api

    @property
    def file(self) -> FileAPI:
        """获取文件 API。"""
        if self._file_api is None:
            raise ConnectionError("客户端未连接，请先调用 connect()")
        return self._file_api

    @property
    def project(self) -> ProjectAPI:
        """获取项目 API。"""
        if self._project_api is None:
            raise ConnectionError("客户端未连接，请先调用 connect()")
        return self._project_api

    @property
    def agent(self) -> AgentAPI:
        """获取代理 API。

        注意：根据 OpenCode API 文档，代理只能通过配置文件创建，
        API 只提供列表功能。
        """
        if self._agent_api is None:
            raise ConnectionError("客户端未连接，请先调用 connect()")
        return self._agent_api

    @property
    def search(self) -> SearchAPI:
        """获取搜索 API。"""
        if self._search_api is None:
            raise ConnectionError("客户端未连接，请先调用 connect()")
        return self._search_api

    @property
    def is_connected(self) -> bool:
        """检查是否已连接。"""
        return self._transport is not None

    # =========================================================================
    # 连接管理
    # =========================================================================

    async def connect(self) -> Self:
        """连接到 OpenCode 服务器。

        Returns:
            返回自身以支持链式调用

        Raises:
            ConnectionError: 连接失败
            ServerStartError: 启动本地服务器失败（仅当 start_server=True）
        """
        if self._start_server:
            self._server = ServerProcess(
                port=self._config.server_port,
                hostname=self._config.server_hostname,
                startup_timeout=self._config.startup_timeout,
            )
            await self._server.start()
            self._base_url = self._server.base_url

        if not self._base_url:
            raise ConnectionError("需要指定 base_url 或设置 start_server=True")

        # 创建 HTTP 传输
        self._transport = HTTPTransport(
            base_url=self._base_url,
            timeout=float(self._config.request_timeout),
        )

        # 初始化 API 实例
        self._session_api = SessionAPI(self._transport)
        self._message_api = MessageAPI(self._transport)
        self._file_api = FileAPI(self._transport)
        self._project_api = ProjectAPI(self._transport)
        self._agent_api = AgentAPI(self._transport)
        self._search_api = SearchAPI(self._transport)

        return self

    async def disconnect(self) -> None:
        """断开与 OpenCode 服务器的连接。"""
        # 关闭传输层
        if self._transport is not None:
            await self._transport.close()
            self._transport = None

        # 停止本地服务器（如果有）
        if self._server is not None:
            await self._server.stop()
            self._server = None

        # 清除 API 实例
        self._session_api = None
        self._message_api = None
        self._file_api = None
        self._project_api = None
        self._agent_api = None
        self._search_api = None

    async def __aenter__(self) -> Self:
        """异步上下文管理器入口。"""
        return await self.connect()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """异步上下文管理器出口。"""
        await self.disconnect()

    # =========================================================================
    # 便捷方法
    # =========================================================================

    async def ask(
        self,
        prompt: str,
        *,
        model: str | None = None,
        agent: str | None = None,
        session_id: str | None = None,
        title: str | None = None,
    ) -> str:
        """快速提问（自动管理会话）。

        Args:
            prompt: 问题内容
            model: 指定的模型（可选，格式: "provider/model-id"）
            agent: 指定的代理（可选）
            session_id: 复用的会话 ID（可选，默认创建新会话）
            title: 新会话的标题（可选，仅当创建新会话时使用）

        Returns:
            AI 的回复文本

        Example:
            answer = await client.ask("什么是 Python 装饰器？")
        """
        if session_id:
            events = await self.message.send(session_id, prompt, model=model, agent=agent)
            return self._extract_text(events)

        async with self._auto_session(title=title) as sid:
            events = await self.message.send(sid, prompt, model=model, agent=agent)
            return self._extract_text(events)

    async def ask_stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        agent: str | None = None,
        session_id: str | None = None,
        title: str | None = None,
    ) -> AsyncIterator[SSEEvent]:
        """流式提问。

        Args:
            prompt: 问题内容
            model: 指定的模型（可选，格式: "provider/model-id"）
            agent: 指定的代理（可选）
            session_id: 复用的会话 ID（可选）
            title: 新会话的标题（可选，仅当创建新会话时使用）

        Yields:
            SSE 事件对象

        Example:
            async for event in client.ask_stream("写一个快速排序"):
                if isinstance(event, TextEvent):
                    print(event.text, end="")
        """
        if session_id:
            async for event in self.message.stream(session_id, prompt, model=model, agent=agent):
                yield event
        else:
            async with self._auto_session(title=title) as sid:
                async for event in self.message.stream(sid, prompt, model=model, agent=agent):
                    yield event

    async def create_session(
        self,
        title: str | None = None,
        *,
        parent_id: str | None = None,
    ) -> Session:
        """创建新会话。

        注意：根据 OpenCode API 文档，创建会话只支持 title 和 parentID 参数。
        model 和 agent 参数应该在发送消息时指定。

        Args:
            title: 会话标题
            parent_id: 父会话 ID（用于创建子会话）

        Returns:
            创建的会话对象
        """
        request = SessionCreate(title=title, parent_id=parent_id)
        return await self.session.create(request)

    # =========================================================================
    # 私有方法
    # =========================================================================

    @asynccontextmanager
    async def _auto_session(self, *, title: str | None = None) -> AsyncIterator[str]:
        """自动管理会话的上下文管理器。

        Args:
            title: 会话标题（可选）

        Yields:
            会话 ID
        """
        request = SessionCreate(title=title)
        session = await self.session.create(request)
        try:
            yield session.id
        finally:
            if self._config.cleanup_sessions:
                await self.session.delete(session.id)

    def _extract_text(self, events: list[SSEEvent]) -> str:
        """从事件列表提取文本内容。

        Args:
            events: 事件列表

        Returns:
            拼接后的文本内容
        """
        texts: list[str] = []
        for event in events:
            if isinstance(event, TextEvent) and event.text:
                texts.append(event.text)
        return "\n".join(texts)
