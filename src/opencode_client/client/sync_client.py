"""同步高层客户端。"""

from __future__ import annotations

import asyncio
from concurrent.futures import Future
from typing import Any, Self

from ..core.config import ClientConfig
from ..models.event import Event
from ..models.session import Session
from .async_client import AsyncOpenCode


class OpenCode:
    """同步高层客户端。

    同步包装器，内部使用 AsyncOpenCode 实现。

    Example:
        with OpenCode(base_url="http://localhost:4096") as client:
            answer = client.ask("什么是闭包？")
            print(answer)
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        start_server: bool = False,
        config: ClientConfig | None = None,
    ) -> None:
        """初始化同步客户端。

        Args:
            base_url: OpenCode 服务器 URL
            start_server: 是否自动启动本地服务器
            config: 客户端配置
        """
        self._async_client: AsyncOpenCode = AsyncOpenCode(
            base_url=base_url,
            start_server=start_server,
            config=config,
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._owned_loop: bool = False

    def _run(self, coro: Any) -> Any:
        """在事件循环中运行协程。"""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
                self._owned_loop = False
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                self._owned_loop = True

        if self._owned_loop:
            return self._loop.run_until_complete(coro)
        else:
            # 已有运行中的循环，使用 run_coroutine_threadsafe
            future: Future[Any] = asyncio.run_coroutine_threadsafe(coro, self._loop)
            return future.result()

    def connect(self) -> Self:
        """连接到 OpenCode 服务器。"""
        self._run(self._async_client.connect())
        return self

    def disconnect(self) -> None:
        """断开与 OpenCode 服务器的连接。"""
        self._run(self._async_client.disconnect())

        if self._owned_loop and self._loop:
            self._loop.close()
            self._loop = None

    def __enter__(self) -> Self:
        """上下文管理器入口。"""
        return self.connect()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """上下文管理器出口。"""
        self.disconnect()

    # =========================================================================
    # 便捷方法
    # =========================================================================

    def ask(
        self,
        prompt: str,
        *,
        model: str | None = None,
        agent: str | None = None,
        session_id: str | None = None,
        title: str | None = None,
    ) -> str:
        """快速提问（同步模式，等待完整响应）。

        Args:
            prompt: 问题内容
            model: 指定的模型（可选，格式: "provider/model-id"）
            agent: 指定的代理（可选）
            session_id: 复用的会话 ID（可选，默认创建新会话）
            title: 新会话的标题（可选，仅当创建新会话时使用）

        Returns:
            AI 的回复文本
        """
        result: str = self._run(
            self._async_client.ask(
                prompt,
                model=model,
                agent=agent,
                session_id=session_id,
                title=title,
            )
        )
        return result

    def ask_stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        agent: str | None = None,
        session_id: str | None = None,
        title: str | None = None,
    ) -> list[Event]:
        """流式提问（收集所有事件后返回）。

        注意：同步客户端会收集所有事件后一次性返回。
        如需实时处理事件，请使用 AsyncOpenCode。

        Args:
            prompt: 问题内容
            model: 指定的模型（可选，格式: "provider/model-id"）
            agent: 指定的代理（可选）
            session_id: 复用的会话 ID（可选）
            title: 新会话的标题（可选，仅当创建新会话时使用）

        Returns:
            事件列表
        """
        events: list[Event] = []

        async def collect_events() -> None:
            async for event in self._async_client.ask_stream(
                prompt,
                model=model,
                agent=agent,
                session_id=session_id,
                title=title,
            ):
                events.append(event)

        self._run(collect_events())
        return events

    def create_session(
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
        result: Session = self._run(self._async_client.create_session(title, parent_id=parent_id))
        return result

    # =========================================================================
    # 代理属性访问
    # =========================================================================

    @property
    def session(self) -> Any:
        """获取会话 API。"""
        return self._async_client.session

    @property
    def message(self) -> Any:
        """获取消息 API。"""
        return self._async_client.message

    @property
    def file(self) -> Any:
        """获取文件 API。"""
        return self._async_client.file

    @property
    def project(self) -> Any:
        """获取项目 API。"""
        return self._async_client.project

    @property
    def event(self) -> Any:
        """获取事件 API。"""
        return self._async_client.event

    @property
    def is_connected(self) -> bool:
        """检查是否已连接。"""
        return self._async_client.is_connected
