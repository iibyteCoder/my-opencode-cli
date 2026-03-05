"""OpenCode 客户端核心模块。

提供与 OpenCode 服务器交互的异步客户端，支持：
- 服务器模式启动和管理
- 会话创建和消息发送
- SSE 流式响应处理
- 自动资源清理
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import sys
import time
from typing import Any, Callable

import aiohttp
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .config import ClientOptions, ExecutionConfig, ServerConfig
from .exceptions import ConnectionError, OpenCodeError, ServerStartError, SessionError
from .parser import EventParser, ParsedResult

logger = logging.getLogger(__name__)


class OpenCodeClient:
    """OpenCode 异步客户端。

    使用 OpenCode 服务器模式执行任务，复用实例提升性能。

    Attributes:
        options: 客户端选项
        console: Rich 控制台（用于实时输出）
        server_process: 服务器子进程
        http_session: HTTP 会话
    """

    def __init__(
        self,
        config: ServerConfig | None = None,
        execution: ExecutionConfig | None = None,
        *,
        console: Console | None = None,
        log_level: str = "INFO",
    ) -> None:
        """初始化客户端。

        Args:
            config: 服务器配置
            execution: 执行配置
            console: Rich 控制台（可选，用于输出）
            log_level: 日志级别
        """
        self.config = config or ServerConfig()
        self.execution = execution or ExecutionConfig()
        self.console = console or Console()
        self.server_process: asyncio.subprocess.Process | None = None
        self._http_session: aiohttp.ClientSession | None = None
        self._parser = EventParser()
        self._shutdown = False
        self._log_tasks: list[asyncio.Task[None]] = []
        self._started = False

        # 配置日志
        logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))

    async def __aenter__(self) -> "OpenCodeClient":
        """异步上下文管理器入口。

        自动启动服务器。

        Returns:
            客户端实例
        """
        await self.start_server()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口。

        自动清理资源。
        """
        await self.close()

    async def start_server(self) -> None:
        """启动 OpenCode 服务器。

        如果服务器已经启动，则跳过。

        Raises:
            ServerStartError: 服务器启动失败
        """
        if self._started:
            return

        port = self.config.port
        hostname = self.config.hostname

        self.console.print(
            f"[cyan]* 启动 OpenCode 服务器（端口: {port}）...[/cyan]"
        )

        # 查找 opencode 命令
        opencode_path = shutil.which("opencode")
        if not opencode_path:
            raise ServerStartError(
                "找不到 opencode 命令，请确保已安装并添加到 PATH"
            )

        # 启动服务器进程
        self.server_process = await asyncio.create_subprocess_exec(
            opencode_path,
            "serve",
            "--port", str(port),
            "--hostname", hostname,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 创建后台任务持续读取服务器输出
        if self.server_process.stdout:
            task = asyncio.create_task(
                self._stream_reader(self.server_process.stdout, "OUT")
            )
            self._log_tasks.append(task)
        if self.server_process.stderr:
            task = asyncio.create_task(
                self._stream_reader(self.server_process.stderr, "ERR")
            )
            self._log_tasks.append(task)

        # 等待服务器就绪
        base_url = f"http://{hostname}:{port}"
        timeout = self.config.startup_timeout
        start_time = time.monotonic()

        async with aiohttp.ClientSession() as session:
            while True:
                elapsed = time.monotonic() - start_time
                if elapsed > timeout:
                    raise ServerStartError(f"服务器启动超时（{timeout}秒）")

                try:
                    async with session.get(
                        f"{base_url}/global/health",
                        timeout=aiohttp.ClientTimeout(total=2.0),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("healthy"):
                                break
                except Exception:
                    pass

                await asyncio.sleep(0.5)

        # 创建 HTTP 会话
        timeout_config = aiohttp.ClientTimeout(total=float(self.execution.request_timeout))
        self._http_session = aiohttp.ClientSession(timeout=timeout_config)

        self._started = True
        self.console.print("[green]OK OpenCode 服务器已启动[/green]")

    async def close(self) -> None:
        """关闭客户端并清理资源。

        确保在任何情况下（正常结束、异常、中断）都会执行。
        """
        if not self._started:
            return

        await self._cleanup()
        self._started = False

    async def _cleanup(self) -> None:
        """清理资源。

        关闭流程：
        1. 取消日志读取任务
        2. 通过 API 通知服务器释放资源
        3. 关闭 HTTP 会话
        4. 发送 SIGTERM 信号
        5. 等待进程退出（最多 10 秒）
        6. 超时则强制杀死
        """
        # 第一步：取消日志读取任务并关闭管道
        for task in self._log_tasks:
            task.cancel()
        if self._log_tasks:
            await asyncio.gather(*self._log_tasks, return_exceptions=True)
            self._log_tasks.clear()

        # 关闭管道传输
        if self.server_process:
            if self.server_process.stdout and hasattr(self.server_process.stdout, "_transport"):
                self.server_process.stdout._transport.close()  # type: ignore[attr-defined]
            if self.server_process.stderr and hasattr(self.server_process.stderr, "_transport"):
                self.server_process.stderr._transport.close()  # type: ignore[attr-defined]

        # 第二步：通过 API 优雅关闭
        await self._dispose_server_via_api()

        # 第三步：关闭 HTTP 会话
        if self._http_session:
            try:
                await self._http_session.close()
            except Exception as e:
                logger.warning(f"关闭 HTTP 会话失败: {e}")
            finally:
                self._http_session = None

        # 第四步：停止服务器进程
        if self.server_process:
            try:
                self.server_process.terminate()
                await asyncio.wait_for(self.server_process.wait(), timeout=10.0)
                logger.info("服务器已优雅关闭")
            except TimeoutError:
                try:
                    self.server_process.kill()
                    await self.server_process.wait()
                    logger.info("服务器已强制终止")
                except (ProcessLookupError, OSError) as e:
                    logger.warning(f"强制终止服务器失败: {e}")
            except (ProcessLookupError, OSError) as e:
                logger.debug(f"服务器进程已不存在: {e}")
            finally:
                self.server_process = None

    async def _dispose_server_via_api(self) -> None:
        """通过 API 通知服务器释放资源。"""
        if not self._http_session or not self.server_process:
            return

        try:
            base_url = self.config.base_url
            async with self._http_session.post(
                f"{base_url}/instance/dispose",
                timeout=aiohttp.ClientTimeout(total=5.0),
            ) as response:
                if response.status == 200:
                    logger.debug("API 优雅关闭成功")
                    await asyncio.sleep(0.5)
                else:
                    logger.debug(f"API 优雅关闭返回状态码: {response.status}")
        except Exception as e:
            logger.debug(f"API 优雅关闭失败（将使用信号关闭）: {e}")

    async def _stream_reader(self, stream: asyncio.StreamReader, prefix: str) -> None:
        """持续读取流并输出到日志。

        Args:
            stream: 输入流（stdout 或 stderr）
            prefix: 日志前缀（用于区分来源）
        """
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                if text:
                    sys.stderr.write(f"[Server:{prefix}] {text}\n")
                    sys.stderr.flush()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"读取服务器输出失败: {e}")

    # ========================================================================
    # 会话管理
    # ========================================================================

    async def create_session(self, title: str | None = None) -> str:
        """创建新会话。

        Args:
            title: 会话标题（可选）

        Returns:
            会话 ID

        Raises:
            SessionError: 创建会话失败
        """
        self._ensure_connected()

        base_url = self.config.base_url
        async with self._http_session.post(  # type: ignore[union-attr]
            f"{base_url}/session",
            json={"title": title or "OpenCode Client Session"},
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise SessionError(f"创建会话失败: HTTP {response.status} - {text}")

            data = await response.json()
            session_id = data.get("id") or data.get("sessionID")
            if not session_id:
                raise SessionError(f"创建会话失败：无效的响应 {data}")
            return session_id

    async def delete_session(self, session_id: str) -> bool:
        """删除会话。

        Args:
            session_id: 会话 ID

        Returns:
            是否成功
        """
        if not self._http_session:
            return False

        try:
            base_url = self.config.base_url
            async with self._http_session.delete(
                f"{base_url}/session/{session_id}",
            ) as response:
                return response.status in (200, 204)
        except Exception:
            return False

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """获取会话详情。

        Args:
            session_id: 会话 ID

        Returns:
            会话信息
        """
        self._ensure_connected()

        base_url = self.config.base_url
        async with self._http_session.get(  # type: ignore[union-attr]
            f"{base_url}/session/{session_id}",
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise SessionError(f"获取会话失败: HTTP {response.status} - {text}")
            return await response.json()

    async def list_sessions(self) -> list[dict[str, Any]]:
        """列出所有会话。

        Returns:
            会话列表
        """
        self._ensure_connected()

        base_url = self.config.base_url
        async with self._http_session.get(  # type: ignore[union-attr]
            f"{base_url}/session",
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise SessionError(f"列出会话失败: HTTP {response.status} - {text}")
            return await response.json()

    # ========================================================================
    # 消息发送
    # ========================================================================

    async def send_message(
        self,
        session_id: str,
        message: str,
        *,
        agent: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """发送消息并等待响应（支持 SSE 流式输出）。

        Args:
            session_id: 会话 ID
            message: 消息内容
            agent: 指定的 Agent（可选）
            model: 指定的模型（可选）

        Returns:
            响应数据
        """
        self._ensure_connected()

        base_url = self.config.base_url
        url = f"{base_url}/session/{session_id}/message"

        logger.debug(f"POST {url}")
        logger.debug(f"消息: {message[:50]}...")

        body: dict[str, Any] = {
            "parts": [{"type": "text", "text": message}],
        }
        if agent:
            body["agent"] = agent
        if model:
            body["model"] = model

        try:
            async with self._http_session.post(  # type: ignore[union-attr]
                url,
                json=body,
                headers={"Accept": "text/event-stream"},
            ) as response:
                logger.debug(f"响应状态: HTTP {response.status}")

                if response.status != 200:
                    text = await response.text()
                    logger.error(f"HTTP 错误响应: {text[:500]}")
                    raise SessionError(f"HTTP {response.status}: {text[:200]}")

                # 检查是否是 SSE 流式响应
                content_type = response.headers.get("Content-Type", "")
                if "text/event-stream" in content_type:
                    return await self._read_sse_response(response)
                else:
                    return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"HTTP 客户端错误: {e}")
            raise ConnectionError(f"连接错误: {e}") from e

    async def send_message_parsed(
        self,
        session_id: str,
        message: str,
        *,
        agent: str | None = None,
        model: str | None = None,
    ) -> ParsedResult:
        """发送消息并返回解析后的结果。

        这是 send_message 的便捷包装，自动解析响应。

        Args:
            session_id: 会话 ID
            message: 消息内容
            agent: 指定的 Agent（可选）
            model: 指定的模型（可选）

        Returns:
            解析后的结果
        """
        response = await self.send_message(
            session_id, message, agent=agent, model=model
        )
        return self._parser.parse_response(response)

    async def _read_sse_response(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """读取 SSE 流式响应并实时输出。

        Args:
            response: aiohttp 响应对象

        Returns:
            最终的响应数据
        """
        final_data: dict[str, Any] = {"parts": []}
        current_part: dict[str, Any] = {}
        buffer = ""

        async for line_bytes in response.content:
            line = line_bytes.decode("utf-8", errors="replace").rstrip()

            if not line:
                # 空行表示事件结束
                if current_part:
                    final_data["parts"].append(current_part)
                    self._print_sse_event(current_part)
                    current_part = {}
                continue

            if line.startswith(":"):
                # 注释行，忽略
                continue

            if ":" in line:
                field, value = line.split(":", 1)
                field = field.strip()
                value = value.lstrip()

                if field == "data":
                    if buffer:
                        buffer += value
                    else:
                        buffer = value
                elif field == "event":
                    current_part["event"] = value
                elif field == "id":
                    current_part["id"] = value

        # 处理最后一个事件
        if current_part:
            final_data["parts"].append(current_part)
            self._print_sse_event(current_part)

        return final_data

    def _print_sse_event(self, event: dict[str, Any]) -> None:
        """实时输出 SSE 事件。

        Args:
            event: SSE 事件数据
        """
        event_type = event.get("event", "unknown")
        data = event.get("data", "")

        try:
            if data:
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    # 工具调用
                    if "tool" in parsed:
                        tool_name = str(parsed.get("tool", "unknown"))
                        sys.stderr.write(f"[Agent] 🔧 工具: {tool_name}\n")
                    # 文本内容
                    elif "text" in parsed:
                        text = str(parsed["text"])
                        if len(text) > 100:
                            text = text[:100] + "..."
                        sys.stderr.write(f"[Agent] 📝 {text}\n")
                    else:
                        sys.stderr.write(f"[Agent] {event_type}: {str(parsed)[:100]}\n")
                else:
                    sys.stderr.write(f"[Agent] {event_type}: {str(parsed)[:100]}\n")
        except json.JSONDecodeError:
            if data:
                sys.stderr.write(f"[Agent] {event_type}: {data[:100]}\n")

        sys.stderr.flush()

    # ========================================================================
    # 批量执行
    # ========================================================================

    async def execute_batch(
        self,
        tasks: list[str],
        *,
        title_prefix: str = "Task",
        on_result: Callable[[int, str, ParsedResult], None] | None = None,
        retry_prompt: str | None = None,
    ) -> list[ParsedResult]:
        """批量执行任务。

        Args:
            tasks: 任务列表（字符串消息）
            title_prefix: 会话标题前缀
            on_result: 结果回调函数 (index, task, result)
            retry_prompt: 重试提示（当结果不成功时发送）

        Returns:
            解析结果列表
        """
        results: list[ParsedResult] = []
        total = len(tasks)

        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}", justify="left"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
            refresh_per_second=4,
        ) as progress:
            main_task = progress.add_task("[cyan]执行中[/cyan]", total=total)

            for i, task in enumerate(tasks, 1):
                if self._shutdown:
                    self.console.print("\n[yellow]收到中断信号，正在停止...[/yellow]")
                    break

                desc = f"[cyan][{i}/{total}][/cyan] {task[:40]}"
                progress.update(main_task, description=desc)

                # 执行任务
                result = await self._execute_single_task(
                    task, title_prefix, i, retry_prompt
                )
                results.append(result)

                # 回调
                if on_result:
                    on_result(i - 1, task, result)

                # 打印状态
                progress.stop()
                self._print_result_status(result, i, total)
                progress.start()

                progress.advance(main_task)

        return results

    async def _execute_single_task(
        self,
        task: str,
        title_prefix: str,
        index: int,
        retry_prompt: str | None = None,
    ) -> ParsedResult:
        """执行单个任务。

        Args:
            task: 任务内容
            title_prefix: 标题前缀
            index: 任务索引
            retry_prompt: 重试提示

        Returns:
            解析结果
        """
        session_id: str | None = None

        try:
            # 1. 创建会话
            session_id = await self.create_session(f"{title_prefix}: {task[:50]}")

            # 2. 发送消息
            response = await self.send_message(session_id, task)
            parsed = self._parser.parse_response(response)

            # 3. 重试逻辑
            retry_count = 0
            max_retries = (
                self.execution.retry_count
                if self.execution.retry_on_failure
                else 0
            )

            while not parsed.success and retry_count < max_retries and retry_prompt:
                retry_count += 1
                logger.info(f"第 {retry_count} 次重试: {task[:50]}")
                await asyncio.sleep(self.execution.retry_delay)

                response = await self.send_message(session_id, retry_prompt)
                parsed = self._parser.parse_response(response)

            return parsed

        except Exception as e:
            logger.exception(f"执行任务时发生异常: {e}")
            return ParsedResult(raw_text=str(e))

        finally:
            if session_id and self.execution.cleanup_sessions:
                await self.delete_session(session_id)

    def _print_result_status(
        self, result: ParsedResult, index: int, total: int
    ) -> None:
        """打印结果状态。

        Args:
            result: 解析结果
            index: 任务索引
            total: 总任务数
        """
        if result.success:
            status = "[green]OK[/green]"
            sql_preview = result.sql[:50] if result.sql else ""
            if sql_preview:
                self.console.print(
                    f"  {status} [dim]{sql_preview}...[/dim]"
                )
            else:
                self.console.print(f"  {status}")
        else:
            status = "[red]FAIL[/red]"
            error_msg = result.raw_text[:100] if result.raw_text else "未知错误"
            self.console.print(f"  {status} [red]{error_msg}[/red]")

    def request_shutdown(self) -> None:
        """请求优雅关闭。"""
        self._shutdown = True

    def _ensure_connected(self) -> None:
        """确保已连接到服务器。

        Raises:
            ConnectionError: 未连接到服务器
        """
        if not self._started or not self._http_session:
            raise ConnectionError("未连接到 OpenCode 服务器，请先调用 start_server()")
