"""客户端工厂。"""

from __future__ import annotations

from ..core.config import ClientConfig
from .async_client import AsyncOpenCode
from .sync_client import OpenCode


class ClientFactory:
    """客户端工厂。

    提供创建客户端的便捷方法。
    """

    @classmethod
    def create_async(
        cls,
        *,
        base_url: str | None = None,
        start_server: bool = False,
        config: ClientConfig | None = None,
    ) -> AsyncOpenCode:
        """创建异步客户端。

        Args:
            base_url: OpenCode 服务器 URL
            start_server: 是否自动启动本地服务器
            config: 客户端配置

        Returns:
            异步客户端实例
        """
        return AsyncOpenCode(
            base_url=base_url,
            start_server=start_server,
            config=config,
        )

    @classmethod
    def create_sync(
        cls,
        *,
        base_url: str | None = None,
        start_server: bool = False,
        config: ClientConfig | None = None,
    ) -> OpenCode:
        """创建同步客户端。

        Args:
            base_url: OpenCode 服务器 URL
            start_server: 是否自动启动本地服务器
            config: 客户端配置

        Returns:
            同步客户端实例
        """
        return OpenCode(
            base_url=base_url,
            start_server=start_server,
            config=config,
        )

    @classmethod
    async def connect_async(
        cls,
        *,
        base_url: str | None = None,
        start_server: bool = False,
        config: ClientConfig | None = None,
    ) -> AsyncOpenCode:
        """创建并连接异步客户端。

        Args:
            base_url: OpenCode 服务器 URL
            start_server: 是否自动启动本地服务器
            config: 客户端配置

        Returns:
            已连接的异步客户端实例
        """
        client = cls.create_async(
            base_url=base_url,
            start_server=start_server,
            config=config,
        )
        await client.connect()
        return client

    @classmethod
    def connect_sync(
        cls,
        *,
        base_url: str | None = None,
        start_server: bool = False,
        config: ClientConfig | None = None,
    ) -> OpenCode:
        """创建并连接同步客户端。

        Args:
            base_url: OpenCode 服务器 URL
            start_server: 是否自动启动本地服务器
            config: 客户端配置

        Returns:
            已连接的同步客户端实例
        """
        client = cls.create_sync(
            base_url=base_url,
            start_server=start_server,
            config=config,
        )
        return client.connect()

    @classmethod
    def from_url(cls, url: str) -> AsyncOpenCode:
        """从 URL 创建异步客户端。

        Args:
            url: OpenCode 服务器 URL

        Returns:
            异步客户端实例
        """
        return cls.create_async(base_url=url)

    @classmethod
    def local(cls, port: int = 4096) -> AsyncOpenCode:
        """创建连接本地服务器的异步客户端。

        Args:
            port: 服务器端口

        Returns:
            异步客户端实例
        """
        return cls.create_async(base_url=f"http://127.0.0.1:{port}")

    @classmethod
    def with_server(cls, port: int = 4096) -> AsyncOpenCode:
        """创建自动启动本地服务器的异步客户端。

        Args:
            port: 服务器端口

        Returns:
            异步客户端实例
        """
        config = ClientConfig(server_port=port)
        return cls.create_async(start_server=True, config=config)
