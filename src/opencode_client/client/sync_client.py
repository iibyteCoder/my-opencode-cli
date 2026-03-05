"""同步高层客户端。"""

from __future__ import annotations

import asyncio
from concurrent.futures import Future
from typing import Any, Self

from ..core.config import ClientConfig
from ..models.event import SSEEvent
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
        """在事件循环中运行协程。

        Args:
            coro: 要运行的协程对象

        Returns:
            协程的返回值
        """
        try:
            # 尝试获取当前运行的事件循环
            loop = asyncio.get_running_loop()
            # 如果已经在异步上下文中，使用 run_coroutine_threadsafe
            future: Future[Any] = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        except RuntimeError:
            # 没有运行的事件循环，创建新的
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                self._owned_loop = True
            return self._loop.run_until_complete(coro)

    def connect(self) -> Self:
        """连接到 OpenCode 服务器。

        Returns:
            返回自身以支持链式调用
        """
        self._run(self._async_client.connect())
        return self

    def disconnect(self) -> None:
        """断开与 OpenCode 服务器的连接。"""
        self._run(self._async_client.disconnect())

        # 关闭自己创建的事件循环
        if self._owned_loop and self._loop is not None:
            self._loop.close()
            self._loop = None
            self._owned_loop = False

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
    ) -> str:
        """快速提问。

        Args:
            prompt: 问题内容
            model: 指定的模型（可选）
            agent: 指定的代理（可选）
            session_id: 复用的会话 ID（可选）

        Returns:
            AI 的回复文本
        """
        return self._run(
            self._async_client.ask(prompt, model=model, agent=agent, session_id=session_id)
        )

    def ask_stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        agent: str | None = None,
        session_id: str | None = None,
    ) -> list[SSEEvent]:
        """流式提问（收集所有事件后返回）。

        注意：这是同步方法，会等待所有事件收集完毕后返回。
        如需真正的流式处理，请使用异步客户端。

        Args:
            prompt: 问题内容
            model: 指定的模型（可选）
            agent: 指定的代理（可选）
            session_id: 复用的会话 ID（可选）

        Returns:
            所有事件的列表
        """

        async def _collect() -> list[SSEEvent]:
            events: list[SSEEvent] = []
            async for event in self._async_client.ask_stream(
                prompt, model=model, agent=agent, session_id=session_id
            ):
                events.append(event)
            return events

        return self._run(_collect())

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
        return self._run(self._async_client.create_session(title, parent_id=parent_id))

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
    def is_connected(self) -> bool:
        """检查是否已连接。"""
        return self._async_client.is_connected
