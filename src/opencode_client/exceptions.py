"""OpenCode 客户端异常定义。

定义客户端可能抛出的异常类型。
"""

from __future__ import annotations


class OpenCodeError(Exception):
    """OpenCode 客户端基础异常。"""


class ServerStartError(OpenCodeError):
    """服务器启动失败异常。

    当 OpenCode 服务器无法在指定时间内启动时抛出。
    """


class SessionError(OpenCodeError):
    """会话相关异常。

    当会话创建、删除或消息发送失败时抛出。
    """


class ConnectionError(OpenCodeError):
    """连接相关异常。

    当无法连接到 OpenCode 服务器时抛出。
    """


class ParseError(OpenCodeError):
    """解析相关异常。

    当响应解析失败时抛出。
    """
