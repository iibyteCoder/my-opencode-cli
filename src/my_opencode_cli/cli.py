"""OpenCode Python 客户端命令行工具。"""

from __future__ import annotations

import asyncio
from typing import Any

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .client.async_client import AsyncOpenCode
from .core.config import ClientConfig
from .models.event import TextEvent
from .models.session import SessionCreate

console: Console = Console()


@click.group()
@click.option(
    "--url",
    "-u",
    "base_url",
    default=None,
    help="OpenCode 服务器 URL",
)
@click.option(
    "--start-server",
    is_flag=True,
    default=False,
    help="启动本地 OpenCode 服务器",
)
@click.option(
    "--timeout",
    "-t",
    "timeout",
    type=int,
    default=600,
    help="请求超时时间（秒）",
)
@click.pass_context
def cli(
    ctx: click.Context,
    base_url: str | None,
    start_server: bool,
    timeout: int,
) -> None:
    """OpenCode Python 客户端命令行工具。

    用于与 OpenCode 服务器交互，支持快速提问、会话管理、文件操作等。
    """
    ctx.ensure_object(dict)
    ctx.obj["base_url"] = base_url
    ctx.obj["start_server"] = start_server
    ctx.obj["timeout"] = timeout


# ============================================================================
# ask 命令
# ============================================================================


@cli.command()
@click.argument("prompt", required=True)
@click.option("--stream", "-s", is_flag=True, help="流式输出")
@click.option("--model", "-m", default=None, help="指定模型")
@click.option("--agent", "-a", default=None, help="指定代理")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "markdown"]),
    default="text",
    help="输出格式",
)
@click.pass_context
def ask(
    ctx: click.Context,
    prompt: str,
    stream: bool,
    model: str | None,
    agent: str | None,
    output_format: str,
) -> None:
    """向 OpenCode 发送问题。

    PROMPT 是要发送的问题内容。
    """
    base_url: str | None = ctx.obj["base_url"]
    start_server: bool = ctx.obj["start_server"]
    timeout: int = ctx.obj["timeout"]

    config = ClientConfig(request_timeout=timeout)

    async def _ask() -> None:
        async with AsyncOpenCode(
            base_url=base_url,
            start_server=start_server,
            config=config,
        ) as client:
            if stream:
                async for event in client.ask_stream(prompt, model=model, agent=agent):
                    _print_event(event, output_format)
            else:
                answer = await client.ask(prompt, model=model, agent=agent)
                _print_answer(answer, output_format)

    asyncio.run(_ask())


def _print_event(event: Any, output_format: str) -> None:
    """打印单个事件。

    Args:
        event: 事件对象
        output_format: 输出格式
    """
    if isinstance(event, TextEvent) and event.text:
        if output_format == "markdown":
            console.print(Markdown(event.text))
        else:
            console.print(event.text, end="")


def _print_answer(answer: str, output_format: str) -> None:
    """打印回答。

    Args:
        answer: 回答文本
        output_format: 输出格式
    """
    if output_format == "markdown":
        console.print(Panel(Markdown(answer), title="回答", border_style="blue"))
    else:
        console.print(answer)


# ============================================================================
# session 命令组
# ============================================================================


@cli.group()
def session() -> None:
    """会话管理命令。"""
    pass


@session.command("list")
@click.pass_context
def list_sessions(ctx: click.Context) -> None:
    """列出所有会话。"""
    base_url: str | None = ctx.obj["base_url"]

    async def _list() -> None:
        async with AsyncOpenCode(base_url=base_url) as client:
            sessions = await client.session.list_all()
            if not sessions:
                console.print("[yellow]没有找到任何会话[/yellow]")
                return

            for s in sessions:
                title = s.title or "Untitled"
                console.print(f"[cyan]{s.id}[/] - {title} ({s.message_count} messages)")

    asyncio.run(_list())


@session.command("create")
@click.option("--title", "-t", default=None, help="会话标题")
@click.pass_context
def create_session_cmd(
    ctx: click.Context,
    title: str | None,
) -> None:
    """创建新会话。"""
    base_url: str | None = ctx.obj["base_url"]

    async def _create() -> None:
        async with AsyncOpenCode(base_url=base_url) as client:
                request = SessionCreate(title=title)
                session_obj = await client.session.create(request)
                console.print(f"[green]Created session:[/] {session_obj.id}")

    asyncio.run(_create())


@session.command("delete")
@click.argument("session_id", required=True)
@click.pass_context
def delete_session_cmd(ctx: click.Context, session_id: str) -> None:
    """删除会话。"""
    base_url: str | None = ctx.obj["base_url"]

    async def _delete() -> None:
        async with AsyncOpenCode(base_url=base_url) as client:
            success = await client.session.delete(session_id)
            if success:
                console.print(f"[green]Deleted session:[/] {session_id}")
            else:
                console.print(f"[red]Failed to delete session:[/] {session_id}")

    asyncio.run(_delete())


# ============================================================================
# file 命令组
# ============================================================================


@cli.group()
def file() -> None:
    """文件操作命令。"""
    pass


@file.command("read")
@click.argument("path", required=True)
@click.pass_context
def read_file_cmd(ctx: click.Context, path: str) -> None:
    """读取文件内容。"""
    base_url: str | None = ctx.obj["base_url"]

    async def _read() -> None:
        async with AsyncOpenCode(base_url=base_url) as client:
            content = await client.file.read(path)
            console.print(content.content)

    asyncio.run(_read())


@file.command("search")
@click.argument("pattern", required=True)
@click.option("--path", "-p", default=None, help="搜索路径")
@click.pass_context
def search_file_cmd(
    ctx: click.Context,
    pattern: str,
    path: str | None,
) -> None:
    """搜索文件内容。"""
    base_url: str | None = ctx.obj["base_url"]

    async def _search() -> None:
        async with AsyncOpenCode(base_url=base_url) as client:
            results = await client.file.search(pattern, path=path)
            for r in results:
                content_preview = (r.content or "")[:100]
                console.print(f"[cyan]{r.path}:{r.line}[/] {content_preview}")

    asyncio.run(_search())


# ============================================================================
# 项目命令
# ============================================================================


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """显示当前项目信息。"""
    base_url: str | None = ctx.obj["base_url"]

    async def _info() -> None:
        async with AsyncOpenCode(base_url=base_url) as client:
            project_info = await client.project.current()
            console.print_json(data=project_info)

    asyncio.run(_info())


# ============================================================================
# 入口点
# ============================================================================


def main() -> None:
    """CLI 主入口点。"""
    cli()


if __name__ == "__main__":
    main()
