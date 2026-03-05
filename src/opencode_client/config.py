"""OpenCode 客户端配置管理。

提供服务器配置、执行配置等配置类。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """OpenCode 服务器配置。

    Attributes:
        port: 服务器端口
        hostname: 服务器主机名
        startup_timeout: 启动超时（秒）
        password: 认证密码（可选）
        username: 认证用户名（可选，默认 'opencode'）
    """

    port: int = Field(
        default=4096,
        ge=1024,
        le=65535,
        description="服务器端口",
    )
    hostname: str = Field(
        default="127.0.0.1",
        description="服务器主机名",
    )
    startup_timeout: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="启动超时（秒）",
    )
    password: str | None = Field(
        default=None,
        description="认证密码（可选）",
    )
    username: str = Field(
        default="opencode",
        description="认证用户名",
    )

    @property
    def base_url(self) -> str:
        """返回服务器基础 URL。"""
        return f"http://{self.hostname}:{self.port}"


class ExecutionConfig(BaseModel):
    """执行配置。

    Attributes:
        cleanup_sessions: 是否在完成后清理会话
        retry_on_failure: 失败时是否重试
        retry_count: 失败重试次数
        retry_delay: 重试延迟（秒）
        request_timeout: 单次请求超时（秒）
    """

    cleanup_sessions: bool = Field(
        default=True,
        description="是否在完成后清理会话",
    )
    retry_on_failure: bool = Field(
        default=False,
        description="失败时是否重试",
    )
    retry_count: int = Field(
        default=2,
        ge=0,
        le=5,
        description="失败重试次数",
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="重试延迟（秒）",
    )
    request_timeout: int = Field(
        default=600,
        ge=60,
        le=3600,
        description="单次请求超时（秒）",
    )


@dataclass
class ClientOptions:
    """客户端选项。

    用于配置客户端行为。

    Attributes:
        server: 服务器配置
        execution: 执行配置
        log_level: 日志级别
        show_progress: 是否显示进度
        progress_callback: 进度回调函数
    """

    server: ServerConfig = field(default_factory=ServerConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    show_progress: bool = True
    progress_callback: callable | None = None  # type: ignore
