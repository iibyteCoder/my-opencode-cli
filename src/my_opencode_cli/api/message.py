"""消息 API。"""

from __future__ import annotations

from typing import Any, cast

from ..models.message import MessageContent
from .client import APIClient


class MessageAPI(APIClient):
    """消息 API。

    根据 OpenCode API 文档提供消息相关功能：
    - GET /session/:id/message - 列出消息
    - POST /session/:id/message - 发送消息并等待响应（同步）
    - GET /session/:id/message/:messageID - 获取消息详情
    - POST /session/:id/prompt_async - 异步发送消息（不等待响应）
    - POST /session/:id/command - 执行斜杠命令
    - POST /session/:id/shell - 运行 shell 命令

    注意：流式事件通过 EventAPI 的 /event 端点获取。
    """

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
    ) -> dict[str, Any]:
        """发送消息并等待响应（同步）。

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
            消息响应，包含 info 和 parts
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

        # 发送同步请求
        data = await self._post(f"/session/{session_id}/message", json=body)
        return cast(dict[str, Any], data)

    async def list_messages(
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
        data = await self._get(
            f"/session/{session_id}/message",
            params=params if params else None,
        )
        return cast(list[dict[str, Any]], data)

    async def get(self, session_id: str, message_id: str) -> dict[str, Any]:
        """获取消息详情。

        Args:
            session_id: 会话 ID
            message_id: 消息 ID

        Returns:
            消息详情，包含 info 和 parts
        """
        data = await self._get(f"/session/{session_id}/message/{message_id}")
        return cast(dict[str, Any], data)

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
