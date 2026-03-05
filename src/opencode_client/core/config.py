"""OpenCode 客户端配置。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ClientConfig(BaseModel):
    """OpenCode 客户端配置。"""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    # 服务器配置
    server_hostname: str = Field(
        default="127.0.0.1",
        description="服务器主机名",
    )
    server_port: int = Field(
        default=4096,
        ge=1,
        le=65535,
        description="服务器端口",
    )
    startup_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="服务器启动超时（秒）",
    )

    # 请求配置
    request_timeout: int = Field(
        default=600,
        ge=10,
        le=3600,
        description="请求超时（秒）",
    )

    # 会话配置
    cleanup_sessions: bool = Field(
        default=True,
        description="是否自动清理临时会话",
    )

    # 重试配置
    retry_count: int = Field(
        default=0,
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

    # 日志配置
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="日志级别",
    )

    @property
    def base_url(self) -> str:
        """返回默认的服务器基础 URL。"""
        return f"http://{self.server_hostname}:{self.server_port}"
