"""OpenCode 客户端异常定义。"""

from __future__ import annotations

from typing import Any


class OpenCodeError(Exception):
    """OpenCode 客户端基础异常。

    所有客户端异常的基类。
    """

    def __init__(self, message: str) -> None:
        """初始化异常。

        Args:
            message: 错误消息
        """
        super().__init__(message)
        self.message: str = message


class ConnectionError(OpenCodeError):
    """连接错误。

    当无法连接到 OpenCode 服务器时抛出。
    """

    pass


class ServerStartError(OpenCodeError):
    """服务器启动失败。

    当无法启动本地 OpenCode 服务器时抛出。
    """

    pass


class SessionError(OpenCodeError):
    """会话相关错误。

    当会话创建、获取或删除失败时抛出。
    """

    pass


class MessageError(OpenCodeError):
    """消息相关错误。

    当消息发送失败时抛出。
    """

    pass


class APIError(OpenCodeError):
    """API 调用错误。

    包含 HTTP 状态码和响应详情。
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response: dict[str, Any] | None = None,
    ) -> None:
        """初始化 API 错误。

        Args:
            message: 错误消息
            status_code: HTTP 状态码
            response: 原始响应数据
        """
        super().__init__(message)
        self.status_code: int | None = status_code
        self.response: dict[str, Any] | None = response


class ParseError(OpenCodeError):
    """解析错误。

    当响应数据解析失败时抛出。
    """

    pass


class TimeoutError(OpenCodeError):
    """超时错误。

    当请求超时时抛出。
    """

    def __init__(
        self,
        message: str = "请求超时",
        *,
        timeout: float | None = None,
    ) -> None:
        """初始化超时错误。

        Args:
            message: 错误消息
            timeout: 超时时间（秒）
        """
        super().__init__(message)
        self.timeout: float | None = timeout


class ValidationError(OpenCodeError):
    """数据验证错误。

    当数据验证失败时抛出。
    """

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        value: Any = None,
    ) -> None:
        """初始化验证错误。

        Args:
            message: 错误消息
            field: 出错的字段名
            value: 出错的值
        """
        super().__init__(message)
        self.field: str | None = field
        self.value: Any = value
