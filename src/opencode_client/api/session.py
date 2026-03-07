"""会话管理 API。"""

from __future__ import annotations

from typing import Any

from ..models.session import Session, SessionCreate, SessionUpdate
from .client import APIClient


class SessionAPI(APIClient):
    """会话管理 API。

    根据 OpenCode API 文档，提供会话的完整管理功能。
    """

    async def list_all(self) -> list[Session]:
        """列出所有会话。

        Returns:
            会话列表
        """
        data = await self._get("/session")
        return [Session.model_validate(item) for item in data]

    async def create(self, request: SessionCreate | None = None) -> Session:
        """创建新会话。

        Args:
            request: 会话创建请求（可选）
                - parent_id: 父会话 ID（可选）
                - title: 会话标题（可选）

        Returns:
            创建的会话
        """
        body = request.model_dump(exclude_none=True) if request else {}
        data = await self._post("/session", json=body)
        return Session.model_validate(data)

    async def get(self, session_id: str) -> Session:
        """获取会话详情。

        Args:
            session_id: 会话 ID

        Returns:
            会话信息
        """
        data = await self._get(f"/session/{session_id}")
        return Session.model_validate(data)

    async def update(self, session_id: str, request: SessionUpdate) -> Session:
        """更新会话属性。

        Args:
            session_id: 会话 ID
            request: 更新请求（目前只支持 title）

        Returns:
            更新后的会话
        """
        body = request.model_dump(exclude_none=True)
        data = await self._patch(f"/session/{session_id}", json=body)
        return Session.model_validate(data)

    async def delete(self, session_id: str) -> bool:
        """删除会话及其所有数据。

        Args:
            session_id: 会话 ID

        Returns:
            是否成功删除
        """
        try:
            await self._delete(f"/session/{session_id}")
            return True
        except Exception:
            return False

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在。

        Args:
            session_id: 会话 ID

        Returns:
            会话是否存在
        """
        try:
            await self.get(session_id)
            return True
        except Exception:
            return False

    async def children(self, session_id: str) -> list[Session]:
        """获取会话的子会话。

        Args:
            session_id: 会话 ID

        Returns:
            子会话列表
        """
        data = await self._get(f"/session/{session_id}/children")
        return [Session.model_validate(item) for item in data]

    async def abort(self, session_id: str) -> bool:
        """中止正在运行的会话。

        Args:
            session_id: 会话 ID

        Returns:
            是否成功中止
        """
        try:
            await self._post(f"/session/{session_id}/abort")
            return True
        except Exception:
            return False

    async def fork(self, session_id: str, *, message_id: str | None = None) -> Session:
        """在指定消息处派生会话。

        Args:
            session_id: 会话 ID
            message_id: 消息 ID（可选）

        Returns:
            新派生的会话
        """
        body: dict[str, Any] = {}
        if message_id is not None:
            body["messageID"] = message_id
        data = await self._post(f"/session/{session_id}/fork", json=body)
        return Session.model_validate(data)

    async def share(self, session_id: str) -> Session:
        """分享会话。

        Args:
            session_id: 会话 ID

        Returns:
            更新后的会话
        """
        data = await self._post(f"/session/{session_id}/share")
        return Session.model_validate(data)

    async def unshare(self, session_id: str) -> Session:
        """取消分享会话。

        Args:
            session_id: 会话 ID

        Returns:
            更新后的会话
        """
        data = await self._delete(f"/session/{session_id}/share")
        return Session.model_validate(data)
