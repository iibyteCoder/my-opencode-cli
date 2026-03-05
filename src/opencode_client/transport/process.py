"""服务器进程管理。"""

from __future__ import annotations

import asyncio
import shutil
import time
from typing import Any, Self

import aiohttp

from ..core.errors import ServerStartError


class ServerProcess:
    """OpenCode 服务器进程管理。

    负责启动、监控和停止本地 OpenCode 服务器进程。
    """

    def __init__(
        self,
        *,
        port: int = 4096,
        hostname: str = "127.0.0.1",
        startup_timeout: float = 30.0,
    ) -> None:
        """初始化服务器进程管理器。

        Args:
            port: 服务器端口
            hostname: 服务器主机名
            startup_timeout: 启动超时时间（秒）
        """
        self.port: int = port
        self.hostname: str = hostname
        self.startup_timeout: float = startup_timeout
        self._process: asyncio.subprocess.Process | None = None

    @property
    def base_url(self) -> str:
        """返回服务器基础 URL。"""
        return f"http://{self.hostname}:{self.port}"

    @property
    def is_running(self) -> bool:
        """检查服务器是否正在运行。"""
        return self._process is not None and self._process.returncode is None

    async def start(self) -> None:
        """启动服务器进程。

        Raises:
            ServerStartError: 启动失败
        """
        if self.is_running:
            return

        # 查找 opencode 命令
        opencode_path = shutil.which("opencode")
        if not opencode_path:
            raise ServerStartError("找不到 opencode 命令，请确保已安装并添加到 PATH")

        # 启动服务器进程
        self._process = await asyncio.create_subprocess_exec(
            opencode_path,
            "serve",
            "--port",
            str(self.port),
            "--hostname",
            self.hostname,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 等待服务器就绪
        await self._wait_for_ready()

    async def _wait_for_ready(self) -> None:
        """等待服务器就绪。

        Raises:
            ServerStartError: 超时
        """
        start_time = time.monotonic()
        timeout = aiohttp.ClientTimeout(total=2.0)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                elapsed = time.monotonic() - start_time
                if elapsed > self.startup_timeout:
                    raise ServerStartError(f"服务器启动超时（{self.startup_timeout}秒）")

                try:
                    async with session.get(f"{self.base_url}/global/health") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("healthy"):
                                return
                except (TimeoutError, aiohttp.ClientError):
                    pass

                await asyncio.sleep(0.5)

    async def stop(self) -> None:
        """停止服务器进程。"""
        if not self._process:
            return

        try:
            # 尝试优雅关闭
            self._process.terminate()
            async with asyncio.timeout(10.0):
                await self._process.wait()
        except TimeoutError:
            # 超时则强制杀死
            if self._process.returncode is None:
                self._process.kill()
                await self._process.wait()
        except ProcessLookupError:
            pass
        finally:
            self._process = None

    async def __aenter__(self) -> Self:
        """异步上下文管理器入口。"""
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """异步上下文管理器出口。"""
        await self.stop()
