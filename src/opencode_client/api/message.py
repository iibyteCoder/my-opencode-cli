"""消息 API。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ..models.event import DoneEvent, ErrorEvent, SSEEvent, TextEvent, ToolResultEvent, ToolUseEvent
from ..models.message import MessageContent
from .client import APIClient


class MessageAPI(APIClient):
    """消息 API。

    根据 OpenCode API 文档提供消息相关功能：
    - GET /session/:id/message - 列出消息
    - POST /session/:id/message - 发送消息并等待响应
    - GET /session/:id/message/:messageID - 获取消息详情
    - POST /session/:id/prompt_async - 异步发送消息（不等待响应）
    - POST /session/:id/command - 执行斜杠命令
    - POST /session/:id/shell - 运行 shell 命令
    """

    async def list(
        self,
        session_id: str,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """列出会话中的消息。

        Args:
            session_id: 会话 ID
            limit: 返回消息数量限制（可选）

        Returns:
            消息列表，每条消息包含 info 和 parts
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        data: list[dict[str, Any]] = await self._get(
            f"/session/{session_id}/message",
            params=params if params else None,
        )
        return data

    async def send(
        self,
        session_id: str,
        content: str | MessageContent,
        *,
        model: str | dict[str, str] | None = None,
        agent: str | None = None,
        no_reply: bool = False,
        system: str | None = None,
        tools: dict[str, Any] | None = None,
    ) -> list[SSEEvent]:
        """发送消息并收集所有事件。

        Args:
            session_id: 会话 ID
            content: 消息内容（字符串或 MessageContent 对象）
            model: 指定的模型（可选）
                - 字符串格式: "provider/model-id"
                - 对象格式: {"providerID": "...", "modelID": "..."}
            agent: 指定的代理名称（可选）
            no_reply: 是否不触发 AI 响应（用于注入上下文）
            system: 系统提示（可选）
            tools: 工具配置（可选）

        Returns:
            事件列表
        """
        events: list[SSEEvent] = []
        async for event in self.stream(
            session_id,
            content,
            model=model,
            agent=agent,
            no_reply=no_reply,
            system=system,
            tools=tools,
        ):
            events.append(event)
        return events

    async def stream(
        self,
        session_id: str,
        content: str | MessageContent,
        *,
        model: str | dict[str, str] | None = None,
        agent: str | None = None,
        no_reply: bool = False,
        system: str | None = None,
        tools: dict[str, Any] | None = None,
    ) -> AsyncIterator[SSEEvent]:
        """发送消息并流式返回事件。

        Args:
            session_id: 会话 ID
            content: 消息内容（字符串或 MessageContent 对象）
            model: 指定的模型（可选）
            agent: 指定的代理名称（可选）
            no_reply: 是否不触发 AI 响应
            system: 系统提示（可选）
            tools: 工具配置（可选）

        Yields:
            SSE 事件
        """
        # 规范化消息内容
        if isinstance(content, str):
            content = MessageContent.from_text(content)

        # 构建请求体
        body: dict[str, Any] = {
            "parts": [part.model_dump() for part in content.parts],
            "noReply": no_reply,
        }

        # 处理 model 参数
        if model is not None:
            if isinstance(model, str):
                # 解析 "provider/model-id" 格式
                if "/" in model:
                    provider_id, model_id = model.split("/", 1)
                    body["model"] = {"providerID": provider_id, "modelID": model_id}
                else:
                    body["model"] = model
            else:
                body["model"] = model

        if agent is not None:
            body["agent"] = agent
        if system is not None:
            body["system"] = system
        if tools is not None:
            body["tools"] = tools

        # 流式处理响应
        async for event_data in self._stream(
            f"/session/{session_id}/message",
            json=body,
        ):
            yield self._parse_event(event_data)

    async def get(self, session_id: str, message_id: str) -> dict[str, Any]:
        """获取消息详情。

        Args:
            session_id: 会话 ID
            message_id: 消息 ID

        Returns:
            消息详情，包含 info 和 parts
        """
        data: dict[str, Any] = await self._get(f"/session/{session_id}/message/{message_id}")
        return data

    async def send_async(
        self,
        session_id: str,
        content: str | MessageContent,
        *,
        model: str | dict[str, str] | None = None,
        agent: str | None = None,
        system: str | None = None,
        tools: dict[str, Any] | None = None,
    ) -> bool:
        """异步发送消息（不等待响应）。

        用于插件注入上下文等场景。

        Args:
            session_id: 会话 ID
            content: 消息内容
            model: 指定的模型（可选）
            agent: 指定的代理名称（可选）
            system: 系统提示（可选）
            tools: 工具配置（可选）

        Returns:
            是否成功发送
        """
        # 规范化消息内容
        if isinstance(content, str):
            content = MessageContent.from_text(content)

        body: dict[str, Any] = {
            "parts": [part.model_dump() for part in content.parts],
        }

        if model is not None:
            if isinstance(model, str):
                if "/" in model:
                    provider_id, model_id = model.split("/", 1)
                    body["model"] = {"providerID": provider_id, "modelID": model_id}
                else:
                    body["model"] = model
            else:
                body["model"] = model

        if agent is not None:
            body["agent"] = agent
        if system is not None:
            body["system"] = system
        if tools is not None:
            body["tools"] = tools

        await self._post(f"/session/{session_id}/prompt_async", json=body)
        return True

    async def command(
        self,
        session_id: str,
        command: str,
        *,
        arguments: dict[str, Any] | None = None,
        model: str | dict[str, str] | None = None,
        agent: str | None = None,
    ) -> dict[str, Any]:
        """执行斜杠命令。

        Args:
            session_id: 会话 ID
            command: 命令名称（不带斜杠）
            arguments: 命令参数
            model: 指定的模型（可选）
            agent: 指定的代理名称（可选）

        Returns:
            命令执行结果，包含 info 和 parts
        """
        body: dict[str, Any] = {"command": command}
        if arguments:
            body["arguments"] = arguments
        if model is not None:
            if isinstance(model, str):
                if "/" in model:
                    provider_id, model_id = model.split("/", 1)
                    body["model"] = {"providerID": provider_id, "modelID": model_id}
                else:
                    body["model"] = model
            else:
                body["model"] = model
        if agent is not None:
            body["agent"] = agent

        data: dict[str, Any] = await self._post(f"/session/{session_id}/command", json=body)
        return data

    async def shell(
        self,
        session_id: str,
        command: str,
        *,
        model: str | dict[str, str] | None = None,
        agent: str | None = None,
    ) -> dict[str, Any]:
        """运行 shell 命令。

        Args:
            session_id: 会话 ID
            command: shell 命令
            model: 指定的模型（可选）
            agent: 指定的代理名称（可选）

        Returns:
            命令执行结果，包含 info 和 parts
        """
        body: dict[str, Any] = {"command": command}
        if model is not None:
            if isinstance(model, str):
                if "/" in model:
                    provider_id, model_id = model.split("/", 1)
                    body["model"] = {"providerID": provider_id, "modelID": model_id}
                else:
                    body["model"] = model
            else:
                body["model"] = model
        if agent is not None:
            body["agent"] = agent

        data: dict[str, Any] = await self._post(f"/session/{session_id}/shell", json=body)
        return data

    def _parse_event(self, data: dict[str, Any]) -> SSEEvent:
        """解析 SSE 事件数据。

        Args:
            data: 原始事件数据

        Returns:
            解析后的事件对象
        """
        event_type = data.get("type", "unknown")

        # 根据类型分发到对应的事件类
        if event_type == "text":
            return TextEvent.model_validate(data)
        elif event_type == "tool_use":
            return ToolUseEvent.model_validate(data)
        elif event_type == "tool_result":
            return ToolResultEvent.model_validate(data)
        elif event_type == "error":
            return ErrorEvent.model_validate(data)
        elif event_type == "done":
            return DoneEvent.model_validate(data)
        else:
            return SSEEvent.model_validate(data)
